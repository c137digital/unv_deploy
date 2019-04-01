import copy

from pathlib import Path

from unv.utils.collections import update_dict_recur
from unv.app.core import create_component_settings


DEFAULT = {}

SCHEMA = {}

SETTINGS = create_component_settings('deploy', DEFAULT, SCHEMA)


class ComponentSettingsBase:
    def __init__(self, root, settings=None):
        if settings is None:
            settings = SETTINGS['components'].get(self.__class__.NAME, {})
        self.local_root = Path(root).parent
        self._data = update_dict_recur(
            copy.deepcopy(self.__class__.DEFAULT), settings)

    @property
    def user(self):
        return self._data['user']

    @property
    def home(self):
        return Path('~')

    @property
    def home_abs(self):
        return Path('/', 'home', self.user)

    @property
    def systemd(self):
        return self._data.get('systemd', {})
