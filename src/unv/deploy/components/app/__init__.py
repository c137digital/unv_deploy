import pkg_resources

from pathlib import Path

from unv.utils.tasks import register
from unv.app.settings import SETTINGS as APP_SETTINGS

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
            'services': {
                'app.service': {
                    'name': 'app_{instance}.service',
                    'boot': True,
                    'instances': 1,
                    'context': {
                        'limit_nofile': 2000,
                        'description': "Application description",
                    }
                }
            }
        }
    }

    @property
    def python(self):
        settings = self._data.get('python', {})
        settings['user'] = self._data['user']
        return PythonComponentSettings(__file__, settings)

    @property
    def bin(self):
        return str(self.python.root_abs / 'bin' / self._data['bin'])

    @property
    def module(self):
        return self._data['settings']


class AppComponentTasks(DeployComponentTasksBase, SystemdTasksMixin):
    SETTINGS = AppComponentSettings(__file__)
    NAMESPACE = 'app'

    def __init__(self, storage, user, host, port, settings=None):
        super().__init__(storage, user, host, port)
        self._python = PythonComponentTasks(
            storage, user, host, port, self._settings.python)

    @register
    async def build(self):
        await self._create_user()
        await self._python.build()

        await self.sync()

    @register
    async def sync(self):
        name = APP_SETTINGS['name']
        app_pkg = pkg_resources.require(name)
        version = app_pkg[0].version
        package = f'{name}-{version}.tar.gz'

        await self._local('python setup.py sdist bdist_wheel')
        await self._upload(Path('dist', package))
        await self._python.pip(f'install -U {package}')
        await self._rmrf(Path(package))
        await self._upload(Path('secure'))
        await self._setup_systemd_units()
