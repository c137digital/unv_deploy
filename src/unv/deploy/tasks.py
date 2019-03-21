import asyncio
import contextlib

from unv.utils.os import get_homepath
from unv.utils.tasks import TasksBase

from .helpers import filter_hosts
from .settings import SETTINGS


# @task
# def hosts(component: str, host: str = ''):
#     """Set env user and hosts from component settings."""
#     keys = SETTINGS.get('keys', {
#         'private': str(get_homepath() / '.ssh' / 'id_rsa'),
#         'public': str(get_homepath() / '.ssh' / 'id_rsa.pub')
#     })
#     env.key_filename = keys['private']
#     env.hosts = [
#         '{}:{}'.format(host_['public'], host_.get('ssh', 22))
#         for name, host_ in filter_hosts(SETTINGS['hosts'], component)
#         if not host or name == host
#     ]
#     env.connection_attempts = 10

class DeployTasksManager(TasksManager):
     def run(self, command):
        args = command.split()
        namespace, command = args[0].split('.')
        task = self.tasks[namespace].tasks[command]

        task_args = []
        if len(args) > 1:
            task_args = args[1:]

        if getattr(task, '__parallel__'):
            task.host = '10.50.25.11'
            task.user = '232'
            asyncio.gather()

        return asyncio.run(task(*task_args))


class DeployTasksBase(TasksBase):
    def __init__(self):
        self.user = ''
        self.hosts = [] 

    async def select(self, component: str, host: str = ''):
        self.user = SETTINGS['components'][component]['user']
        self.hosts = [
            {'ip': host_['public'], 'port': host_.get('ssh', 22)}
            for name, host_ in filter_hosts(component)
            if not host or name == host
        ]

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
