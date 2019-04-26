from pathlib import Path

from unv.utils.tasks import register

from ...tasks import DeployComponentTasksBase
from ...helpers import ComponentSettingsBase

from ..python import PythonComponentTasks, PythonComponentSettings
from ..systemd import SystemdTasksMixin


class AppComponentSettings(ComponentSettingsBase):
    NAME = 'app'
    DEFAULT = {
        'bin': 'app {instance}',
        'settings': 'secure.production',
        'systemd': {
            'template': 'app.service',
            'name': 'app_{instance}.service',
            'boot': True,
            'instances': {'count': 1},
            'context': {
                'limit_nofile': 2000,
                'description': "Application description",
            }
        }
    }

    @property
    def python(self):
        settings = self._data.get('python', {})
        settings['user'] = self._data['user']
        return PythonComponentSettings(settings)

    @property
    def bin(self):
        return str(self.python.root_abs / 'bin' / self._data['bin'])

    @property
    def module(self):
        return self._data['settings']


class AppComponentTasks(DeployComponentTasksBase, SystemdTasksMixin):
    SETTINGS = AppComponentSettings()
    NAMESPACE = 'app'

    def __init__(self, user, host, settings=None):
        super().__init__(user, host, settings)
        self._python = PythonComponentTasks(user, host, self._settings.python)

    @register
    async def build(self):
        await self._create_user()
        await self._python.build()

    @register
    async def shell(self):
        return await self._python.shell()

    @register
    async def ssh(self):
        return await self._run('bash', interactive=True)

    @register
    async def sync(self):
        name = (await self._local('python setup.py --name')).strip()
        version = (await self._local('python setup.py --version')).strip()
        package = f'{name}-{version}.tar.gz'

        await self._local('pip install -e .')
        await self._local('python setup.py sdist bdist_wheel')
        await self._upload(Path('dist', package))
        await self._local('rm -rf ./build ./dist')
        await self._python.pip(f'install -I {package}')
        await self._rmrf(Path(package))
        await self._upload(Path('secure'))
        await self._sync_systemd_units()
