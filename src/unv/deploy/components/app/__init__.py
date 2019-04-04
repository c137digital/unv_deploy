from unv.utils.tasks import register

from ...tasks import DeployComponentTasksBase
from ...settings import ComponentSettingsBase
from ..python import PythonComponentTasks, PythonComponentSettings


class AppComponentSettings(ComponentSettingsBase):
    NAME = 'app'
    DEFAULT = {
        'settings': 'secure.production',
        'bin': 'app'
    }

    @property
    def python(self):
        return PythonComponentSettings(__file__, self._data.get('python', {}))

    @property
    def bin(self):
        return self.python.root_abs / 'bin' / self._data['bin']

    @property
    def module(self):
        return self._data['settings']


class AppComponentTasks(DeployComponentTasksBase):
    SETTINGS = AppComponentSettings(__file__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._python = 

    @register
    async def sync(self):
        pass
