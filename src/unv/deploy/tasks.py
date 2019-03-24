import asyncio
import contextlib

from unv.utils.os import get_homepath
from unv.utils.tasks import TasksBase, TasksManager

from .helpers import filter_hosts
from .settings import SETTINGS


class DeployTasksManager(TasksManager):
    def run_task(self, task_class, command, args):
        method = getattr(task_class, command)
        if getattr(method, '__parallel__'):
            # task_class(user, host, port)
            pass
        return super().run_task(task_class, command, args)

    # TODO: add select or load current hosts to process
    # async def select(self, component: str, host: str = ''):
    #     self.user = SETTINGS['components'][component]['user']
    #     self.hosts = [
    #         {'ip': host_['public'], 'port': host_.get('ssh', 22)}
    #         for name, host_ in filter_hosts(component)
    #         if not host or name == host
    #     ]



class DeployTasksBase(TasksBase):
    def __init__(self, user, host, port):
        self._user = user
        self._host = host
        self._port = port

    async def run(self, command):
        command = f'{self.prefix} {command}'
        for host in self.hosts:
            # responses handling ?
            await self.subprocess(
                f'ssh -p {host.port} {self.user}@{host.ip} {command}'
            )

    @contextlib.contextmanager
    def cd(self, directory):
        old_prefix = self.prefix
        self.prefix = f'{self.prefix} cd {directory} &&'
        yield
        self.prefix = old_prefix
