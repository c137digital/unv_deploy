import os
import json
import time
import copy
import socket
import pprint
import asyncio
import inspect
import importlib

from pathlib import Path

import jinja2

from unv.utils.os import run_in_shell, get_homepath
from unv.utils.collections import update_dict_recur
from unv.app.settings import validate_schema, SETTINGS as APP_SETTINGS

from ..settings import SETTINGS


def wait_ping(host, port, timeout=5):
    start = time.time()
    ready = False
    while time.time() - start < timeout:
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.settimeout(1)
        result = connection.connect_ex((host, port))
        if result == 0:
            ready = True
            break

    return ready


class DeployProvider:
    NAME = ''
    DEFAULT = {}
    SCHEMA = {}

    def __init__(self, services):
        self._servers = []

        self.services = services
        self.project_dir = Path().cwd()
        self.local_root = Path(inspect.getfile(self.__class__)).parent
# TODO: drop support for static ips for
# install vagrant plugin install vagrant-address
# install vagrant plugin install vagrant-parallels

    @property
    def servers(self):
        if self._servers:
            return self._servers
        for scope, services in self.services.items():
            for info in services:
                for host in info['hosts']:
                    if host['provider'] != self.NAME:
                        continue
                    host = update_dict_recur(self.DEFAULT, host)
                    host = validate_schema(self.SCHEMA, host)
                    name = host['name']
                    for count in range(1, host['count'] + 1):
                        service_name = scope
                        if scope != name:
                            service_name = f"{scope}-{name}"
                        env = SETTINGS._data['env']
                        host['name'] = f"{env}-{service_name}-{count}"
                        host['components'] = info['components']
                        self._servers.append(host.copy())
        return self._servers

    async def update_ssh_keys(self, ips):
        known_hosts = get_homepath() / '.ssh' / 'known_hosts'

        for ip in ips:
            if not wait_ping(ip, 22):
                print(f"Can't setup ssh key for {ip} because host is down")
                return

        if known_hosts.exists():
            with known_hosts.open('r+') as f:
                hosts = f.readlines()
                f.seek(0)
                for host in hosts:
                    if any(ip in host for ip in ips):
                        continue
                    f.write(host)
                f.truncate()

        for ip in ips:
            await run_in_shell(f'ssh-keyscan {ip} >> {known_hosts}')

    async def initialize(self):
        raise NotImplementedError('Initialize servers from provided services')


class VagrantProvider(DeployProvider):
    NAME = 'vagrant'
    DEFAULT = {
        'count': 1,
        'cpus': 1,
        'ram': 256,
        'image': 'generic/debian11',
        'vm': 'virtualbox'
    }
    SCHEMA = {
        'name': {'type': 'string'},
        'count': {'type': 'integer'},
        'provider': {'type': 'string'},
        'cpus': {'type': 'integer'},
        'ram': {'type': 'integer'},
        'image': {'type': 'string'},
        'vm': {'type': 'string', 'allowed': ['virtualbox', 'parallels']}
    }

    def generate_vagrant_file(self):
        template = jinja2.Template(
            (self.local_root / 'Vagrantfile').read_text())
        result = template.render(**{'provider': self})
        current_file = (self.project_dir / 'Vagrantfile')
        changed = not (
            current_file.exists() and current_file.read_text() == result
        )
        return changed, current_file, result

    async def initialize(self):
        changed, vagrant_file, vagrant_contents = self.generate_vagrant_file()
        # compare only hosts not vagrant file use vagrant file
        current_hosts = SETTINGS.current_settings_dir / 'hosts.json'
        if not changed and current_hosts.exists():
            return json.loads(current_hosts.read_text())

        print('** updating servers')
        current_host_names = set()
        hosts = {}
        for server in self.servers:
            for component in server['components']:
                hosts.setdefault(component, []).append(server)
                current_host_names.add(server['name'])

        if current_hosts.exists():
            old_hosts = json.loads(current_hosts.read_text())
            for host_list in old_hosts.values():
                for host in host_list:
                    if host['name'] not in current_host_names:
                        await run_in_shell(
                            f"vagrant destroy {host['name']} -g -f")

        vagrant_file.write_text(vagrant_contents)
        await run_in_shell(f"vagrant up --provider parallels")

        print('** servers updated, updating IPs')

        async def grab_ip(server):
            ips = await run_in_shell(
                f"vagrant ssh {server['name']} --no-color "
                "--no-tty -c 'ip -j addr show dev eth1'"
            )
            ip = json.loads(ips)[0]['addr_info'][0]['local']
            server['public_ip'] = ip.strip()
            server['private_ip'] = server['public_ip']

        tasks = [
            grab_ip(server)
            for server in self.servers
        ]
        await asyncio.gather(*tasks)

        print('** updating ssh keys')
        await self.update_ssh_keys([
            server['public_ip'] for server in self.servers
        ])

        current_hosts.write_text(json.dumps(hosts, indent=2))
        
        print('** server setup completed')

        return hosts

        # await run_in_shell('vagrant destroy -f')
