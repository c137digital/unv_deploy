import copy

from pathlib import Path

from unv.utils.os import get_homepath
from unv.utils.tasks import register
from unv.utils.collections import update_dict_recur

# from unv.web.settings import SETTINGS as WEB_SETTINGS

from .helpers import filter_hosts
from .tasks import DeployTasksBase


class VagrantTasks(DeployTasksBase):
    async def setup(self):
        await self._local('vagrant destroy -f')
        await self._local('vagrant up')
        await self._update_local_known_hosts()
        await self._local('vagrant ssh -c "sleep 1"')

    async def _update_local_known_hosts(self):
        ips = [host['public'] for _, host in filter_hosts()]
        known_hosts = get_homepath() / '.ssh' / 'known_hosts'

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
