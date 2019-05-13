import asyncio
import logging
import contextlib

from pathlib import Path

import jinja2

from unv.utils.tasks import TasksBase, TasksManager, TaskRunError, register

from .helpers import get_hosts, as_root
from .settings import SETTINGS
from .helpers import ComponentSettingsBase


def parallel(task):
    task.__parallel__ = True
    return task


def local(task):
    task.__local__ = True
    return task


class DeployTasksBase(TasksBase):
    def __init__(self, manager, user, host):
        self._user = user
        self._public_ip = host['public']
        self._private_ip = host['private']
        self._port = host.get('ssh', 22)
        self._current_prefix = ''
        self._logger = logging.getLogger(self.__class__.__name__)

        super().__init__(manager)

    def get_all_deploy_tasks(self):
        for task_class in self._manager.tasks.values():
            if issubclass(task_class, DeployTasksBase):
                yield task_class(self._manager, self._user, {
                    'public': self._public_ip,
                    'private': self._private_ip,
                    'ssh': self._port
                })

    @contextlib.contextmanager
    def _set_user(self, user):
        old_user = self._user
        self._user = user
        yield self
        self._user = old_user

    @contextlib.contextmanager
    def _set_host(self, host):
        old_public_ip, old_private_ip, old_port =\
            self._public_ip, self._private_ip, self._port
        self._public_ip, self._private_ip, self._port =\
            host['public'], host['private'], host.get('ssh', 22)
        yield self
        self._public_ip, self._private_ip, self._port =\
            old_public_ip, old_private_ip, old_port

    @contextlib.contextmanager
    def _prefix(self, command):
        old_prefix = self._current_prefix
        self._current_prefix = f'{self._current_prefix} {command} '
        yield
        self._current_prefix = old_prefix

    @contextlib.asynccontextmanager
    async def _cd(self, path: Path, temporary=False):
        if temporary:
            await self._mkdir(path, delete=True)
        with self._prefix(f'cd {path} &&'):
            yield
        if temporary:
            await self._rmrf(path)

    @as_root
    async def _sudo(self, command, strip=True):
        """Run command on server as root user."""
        return await self._run(command, strip)

    async def _create_user(self):
        """Create user if not exist and sync ssh keys."""
        user = self._user

        with self._set_user('root'):
            try:
                await self._run("id -u {}".format(user))
            except TaskRunError:
                await self._run(
                    "adduser --quiet --disabled-password"
                    " --gecos \"{0}\" {0}".format(user)
                )

                local_ssh_public_key = Path('~/.ssh/id_rsa.pub')
                local_ssh_public_key = local_ssh_public_key.expanduser()
                keys_path = Path(
                    '/', 'home' if user != 'root' else '',
                    user, '.ssh'
                )

                await self._mkdir(keys_path)
                await self._run(f'chown -hR {user} {keys_path}')
                await self._run('echo "{}" >> {}'.format(
                    local_ssh_public_key.read_text().strip(),
                    keys_path / 'authorized_keys'
                ))

    @as_root
    async def _apt_install(self, *packages):
        with self._prefix('DEBIAN_FRONTEND=noninteractive'):
            await self._run('apt-get update -y -q')
            await self._run('apt-get upgrade -y -q')
            await self._run(
                'apt-get install -y -q --no-install-recommends '
                '--no-install-suggests {}'.format(' '.join(packages))
            )

    async def _run(self, command, strip=True, interactive=False) -> str:
        self._logger.debug(
            f'run [{self._user}@{self._public_ip}:{self._port}] '
            f'{self._current_prefix}{command}'
        )
        interactive_flag = '-t' if interactive else ''
        response = await self._local(
            f"ssh {interactive_flag} -p {self._port} "
            f"{self._user}@{self._public_ip} "
            f"'{self._current_prefix}{command}'",
            interactive=interactive
        ) or ''
        if strip:
            response = response.strip()
        return response

    async def _rmrf(self, path: Path):
        await self._run(f'rm -rf {path}')

    async def _mkdir(self, path: Path, delete=False):
        if delete:
            await self._rmrf(path)
        await self._run(f'mkdir -p {path}')

    async def _upload(self, local_path: Path, path: Path = '~/'):
        await self._local(
            f'scp -r -P {self._port} {local_path} '
            f'{self._user}@{self._public_ip}:{path}'
        )

    async def _rsync(self, local_dir, root_dir, exclude=None):
        exclude = [f"--exclude '{path}'" for path in exclude or []]
        exclude = ' '.join(exclude)
        await self._local(
            f'rsync -rave ssh --delete {exclude} {local_dir}/ '
            f'{self._user}@{self._public_ip}:{root_dir}'
        )

    async def _upload_template(
            self, local_path: Path, path: Path, context: dict = None):
        context = context or {}
        context.setdefault('deploy', self)
        render_path = Path(f'{local_path}.render')
        template = jinja2.Template(local_path.read_text(), enable_async=True)
        render_path.write_text(await template.render_async(context))
        try:
            await self._upload(render_path, path)
        finally:
            render_path.unlink()

    async def _download_and_unpack(self, url: str, dest_dir: Path = Path('.')):
        await self._run(f'wget -q {url}')
        archive = url.split('/')[-1]
        await self._run(f'tar xf {archive}')
        archive_dir = archive.split('.tar')[0]

        await self._mkdir(dest_dir)
        await self._run(f'mv {archive_dir}/* {dest_dir}')

        await self._rmrf(archive)
        await self._rmrf(archive_dir)

    @register
    async def ssh(self):
        return await self._run('bash', interactive=True)


class DeployComponentTasksBase(DeployTasksBase):
    SETTINGS = None

    def __init__(self, manager, user, host, settings=None):
        settings = settings or self.__class__.SETTINGS
        if settings is None or not isinstance(settings, ComponentSettingsBase):
            raise ValueError(
                "Provide correct 'SETTINGS' value "
                "shoult be an instance of class 'ComponentSettingsBase' not "
                f"[{settings}] value and type {type(settings)}"
            )
        self.settings = settings
        super().__init__(manager, self.settings.user, host)


class DeployTasksManager(TasksManager):
    def run_task(self, task_class, name, args):
        method = getattr(task_class, name)
        is_local = hasattr(method, '__local__')
        is_parallel = hasattr(method, '__parallel__')

        if issubclass(task_class, DeployTasksBase):
            if is_local:
                user = 'local'
                hosts = [{'public': None, 'private': None, 'ssh': 0}]
            else:
                user, hosts = self._select_hosts(task_class.NAMESPACE)

            tasks = [
                getattr(task_class(self, user, host), name)(*args)
                for host in hosts
            ]

            if is_parallel:
                async def run():
                    await asyncio.gather(*tasks)
                asyncio.run(run())
            else:
                for task in tasks:
                    asyncio.run(task)
        else:
            return super().run_task(task_class, name, args)

    def _select_hosts(self, name: str = ''):
        return (
            SETTINGS['components'].get(name, {}).get('user', name),
            [host for _, host in get_hosts(name)]
        )
