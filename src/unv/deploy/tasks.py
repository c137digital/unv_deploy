import asyncio
import shutil
import contextlib

from pathlib import Path

import jinja2

from unv.utils.os import get_homepath
from unv.utils.tasks import TasksBase, TasksManager, TaskSubprocessError

from .helpers import filter_hosts, as_root
from .settings import SETTINGS


def parallel(task):
    task.__parallel__ = True
    return task


class DeployTasksBase(TasksBase):
    def __init__(self, storage, user, host, port=22):
        self.storage = storage
        self.user = user
        self.original_user = user
        self.host = host
        self.port = port
        self.prefix = ''

    @as_root
    async def sudo(self, command, strip=True):
        """Run command on server as root user."""
        return await self.run(command, strip)

    @as_root
    async def create_user(self):
        """Create user if not exist and sync ssh keys."""
        try:
            await self.run("id -u {}".format(self.original_user))
        except TaskSubprocessError:
            await self.run(
                "adduser --quiet --disabled-password"
                " --gecos \"{0}\" {0}".format(self.original_user)
            )

            local_ssh_public_key = Path('~/.ssh/id_rsa.pub')
            local_ssh_public_key = local_ssh_public_key.expanduser()
            keys_path = Path(
                '/', 'home' if self.original_user != 'root' else '',
                self.original_user, '.ssh'
            )

            await self.mkdir(keys_path)
            await self.run(f'chown -hR {self.original_user} {keys_path}')
            await self.run('echo "{}" >> {}'.format(
                local_ssh_public_key.read_text().strip(),
                keys_path / 'authorized_keys'
            ))

    @as_root
    async def apt_install(self, *packages):
        await self.run('DEBIAN_FRONTEND=noninteractive apt-get update -y -q && apt-get upgrade -y -q')
        await self.run(
            'DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends '
            '--no-install-suggests {}'.format(' '.join(packages))
        )

    async def run(self, command, strip=True) -> str:
        if self.prefix:
            command = f'{self.prefix} {command}'
        response = await self.subprocess(
            f"ssh -p {self.port} {self.user}@{self.host} '{command}'"
        ) or ''
        if strip:
            response = response.strip()
        return response

    async def rmrf(self, path: Path):
        await self.run(f'rm -rf {path}')

    async def mkdir(self, path: Path, remove_existing=False):
        if remove_existing:
            await self.rmrf(path)
        await self.run(f'mkdir -p {path}')

    async def upload(self, local_path: Path, remote_path: Path):
        await self.subprocess(
            f'scp -r -P {self.port} {local_path} '
            f'{self.user}@{self.host}:{remote_path}')

    async def upload_template(
            self, local_path: Path, remote_path: Path, context: dict = None):
        render_path = Path(f'{local_path}.render')
        template = jinja2.Template(local_path.read_text())
        render_path.write_text(template.render(context))
        try:
            await self.upload(render_path, remote_path)
        finally:
            render_path.unlink()

    async def download_and_unpack(self, url: str, dest_dir: Path = Path('.')):
        await self.run(f'wget -q {url}')
        archive = url.split('/')[-1]
        await self.run(f'tar xf {archive}')
        archive_dir = archive.split('.tar')[0]

        await self.mkdir(dest_dir)
        await self.run(f'mv {archive_dir}/* {dest_dir}')

        await self.rmrf(archive)
        await self.rmrf(archive_dir)

    @contextlib.contextmanager
    def cd(self, path: Path):
        old_prefix = self.prefix
        self.prefix = f'cd {path} && {self.prefix}'
        yield
        self.prefix = old_prefix

    def get_components(self):
        for host_ in SETTINGS['hosts'].values():
            if self.host == host_['public']:
                return host_['components']
        return None


class DeployComponentTasks(DeployTasksBase):
    pass


class DeployTasksManager(TasksManager):
    def run_task(self, task_class, command, args):
        if issubclass(task_class, DeployTasksBase):
            method = getattr(task_class, command)
            user = self.storage['deploy']['user']
            parallel = hasattr(method, '__parallel__')

            tasks = [
                getattr(task_class(
                    self.storage, user, host['ip'], host['port']),
                    command
                )(*args)
                for host in self.storage['deploy']['hosts']
            ]

            if parallel:
                async def run():
                    await asyncio.gather(*tasks)
                asyncio.run(run())
            else:
                for task in tasks:
                    asyncio.run(task)

            return
        return super().run_task(task_class, command, args)

    def select_component(self, name: str = '', host: str = ''):
        self.storage['deploy'] = {
            'user': SETTINGS['components'][name]['user'],
            'hosts': [
                {'ip': host_['public'], 'port': host_.get('ssh', 22)}
                for name, host_ in filter_hosts(name)
                if not host or name == host
            ]
        }
