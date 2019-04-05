from unv.utils.tasks import register

from ...tasks import DeployComponentTasksBase
from ...settings import ComponentSettingsBase
from ..python import PythonComponentTasks, PythonComponentSettings


class AppComponentSettings(ComponentSettingsBase):
    NAME = 'app'
    DEFAULT = {
        'settings': 'secure.production',
        'bin': 'app',
        'description': "Web application",
    }

    @property
    def python(self):
        settings = self._data.get('python', {})
        settings['user'] = self._data['user']
        return PythonComponentSettings(__file__, settings)

    @property
    def bin(self):
        return self.python.root_abs / 'bin' / self._data['bin']

    @property
    def module(self):
        return self._data['settings']


class AppComponentTasks(DeployComponentTasksBase):
    SETTINGS = AppComponentSettings(__file__)

    def __init__(self, storage, user, host, port, settings=None):
        super().__init__(storage, user, host, port)
        self._python = PythonComponentTasks(
            storage, user, host, port, self._settings.python)

    @register
    async def build(self):
        await self._create_user()
        await self._python.build()

    @register
    async def run(self):
        print(await self._python.run('-c "print(2+2)"'))
