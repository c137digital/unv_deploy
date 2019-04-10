import asyncio
import logging
import contextlib

from pathlib import Path

import jinja2

from unv.utils.tasks import TasksBase, TasksManager, TaskRunError

from .helpers import filter_hosts, as_root
from .settings import SETTINGS
from .helpers import ComponentSettingsBase


def parallel(task):
    task.__parallel__ = True
    return task


class DeployTasksBase(TasksBase):
    def __init__(self, storage, user, host, port):
        self._storage = storage

        self._user = user
        self._host = host
        self._port = port

        self._original_user = user
        self._current_prefix = ''

        self._logger = logging.getLogger(self.__class__.__name__)

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

    @as_root
    async def _create_user(self):
        """Create user if not exist and sync ssh keys."""
        try:
            await self._run("id -u {}".format(self._original_user))
        except TaskRunError:
            await self._run(
                "adduser --quiet --disabled-password"
                " --gecos \"{0}\" {0}".format(self._original_user)
            )

            local_ssh_public_key = Path('~/.ssh/id_rsa.pub')
            local_ssh_public_key = local_ssh_public_key.expanduser()
            keys_path = Path(
                '/', 'home' if self._original_user != 'root' else '',
                self._original_user, '.ssh'
            )

            await self._mkdir(keys_path)
            await self._run(f'chown -hR {self._original_user} {keys_path}')
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
            f'run [{self._user}@{self._host}:{self._port}] '
            f'{self._current_prefix}{command}'
        )
        interactive_flag = '-t' if interactive else ''
        response = await self._local(
            f"ssh {interactive_flag} -p {self._port} {self._user}@{self._host} "
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
            f'{self._user}@{self._host}:{path}'
        )

    async def _upload_template(
            self, local_path: Path, path: Path, context: dict = None):
        context = context or {}
        render_path = Path(f'{local_path}.render')
        template = jinja2.Template(local_path.read_text())
        render_path.write_text(template.render(context))
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


class DeployComponentTasksBase(DeployTasksBase):
    SETTINGS = None

    def __init__(self, storage, user, host, port, settings=None):
        super().__init__(storage, user, host, port)
        settings = settings or self.__class__.SETTINGS

        if settings is None or not isinstance(settings, ComponentSettingsBase):
            raise ValueError(
                "Provide correct 'SETTINGS' value "
                "shoult be an instance of class 'ComponentSettingsBase'")

        self._settings = settings


class DeployTasksManager(TasksManager):
    def run_task(self, task_class, name, args):
        if issubclass(task_class, DeployTasksBase):
            method = getattr(task_class, name)
            user, hosts = self._select_hosts(task_class.NAMESPACE)
            parallel = hasattr(method, '__parallel__')
            tasks = [
                getattr(task_class(
                    self.storage, user, host['ip'], host['port']),
                    name
                )(*args)
                for host in hosts
            ]

            if parallel:
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
            SETTINGS['components'][name]['user'],
            [
                {'ip': host_['public'], 'port': host_.get('ssh', 22)}
                for name, host_ in filter_hosts(name)
            ]
        )
