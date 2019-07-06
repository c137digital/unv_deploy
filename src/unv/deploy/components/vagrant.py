import time
import socket


from unv.utils.os import get_homepath
from unv.utils.tasks import register, Tasks

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


class VagrantTasks(Tasks):
    NAMESPACE = 'vagrant'

    @register
    async def setup(self):
        # TODO: add config path to run commands from other dirs
        await self._local('vagrant destroy -f')
        await self._local('vagrant up')
        await self.update_hosts()

    @register
    async def update_hosts(self):
        ips = [host['public_ip'] for _, host in SETTINGS.get_hosts()]
        known_hosts = get_homepath() / '.ssh' / 'known_hosts'

        for ip in ips:
            if not wait_ping(ip, 22):
                print(f"Can't setup ssh key for {ip} because host is down")
                print("After host up, please run vagrant.update_hosts")
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
            await self._local(f'ssh-keyscan {ip} >> {known_hosts}')
