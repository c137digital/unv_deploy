import asyncio
import pathlib
import contextlib

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
        self.host = host
        self.port = port
        self.prefix = ''

    async def run(self, command, strip=True) -> str:
        if self.prefix:
            command = f'{self.prefix} {command}'
        response = await self.subprocess(
            f"ssh -p {self.port} {self.user}@{self.host} {command}"
        ) or ''
        if strip:
            response = response.strip()
        return response

    async def rmrf(self, path: pathlib.Path):
        await self.run(f'rm -rf {path}')

    async def mkdir(self, path: pathlib.Path, remove_existing=False):
        if remove_existing:
            await self.rmrf(path)
        await self.run(f'mkdir -p {path}')

    async def sudo(self, command, strip=True):
        old_user = self.user
        response = await self.run(command, strip)
        self.user = old_user
        return response

    @as_root
    def create_user(self, username: str):
        try:
            await self.run("id -u {}".format(username))
        except TaskSubprocessError:
            await self.run(
                "adduser --quiet --disabled-password"
                " --gecos \"{0}\" {0}".format(username)
            )

    # def put(local_path: pathlib.Path, remote_path: pathlib.Path):
    #     await self.subprocess()

    @contextlib.contextmanager
    def cd(self, directory):
        old_prefix = self.prefix
        self.prefix = f'{self.prefix} cd {directory} &&'
        yield
        self.prefix = old_prefix


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
