import copy
import inspect

from pathlib import Path

from unv.utils.collections import update_dict_recur
from unv.app.core import ComponentSettings


class DeploySettings(ComponentSettings):
    KEY = 'deploy'
    SCHEMA = {
        'hosts': {
            'type': 'dict',
            'keyschema': {'type': 'string'},
            'valueschema': {
                'type': 'dict',
                'schema': {
                    'public_ip': {'type': 'string', 'required': True},
                    'private_ip': {'type': 'string'},
                    'port': {'type': 'integer', 'required': True},
                    'provider': {'type': 'string', 'required': False},
                    'components': {
                        'type': 'list',
                        'schema': {'type': 'string'}
                    }
                }
            }
        },
        'components': {'allow_unknown': True}
    }
    DEFAULT = {
        'hosts': {},
        'components': {},
    }

    def get_hosts(self, component=''):
        for key, value in self._data['hosts'].items():
            if component in value.get('components', []) or not component:
                yield key, value

    def get_components(self, public_ip):
        for value in self._data['hosts'].values():
            if value['public_ip'] == public_ip:
                return value['components']
        return []

    def get_component_user(self, name):
        return self._data.get(name, {}).get('user', name)

    def get_component_settings(self, name):
        return self._data['components'].get(name, {})


SETTINGS = DeploySettings()


class DeployComponentSettings:
    def __init__(self, settings=None, root=None):
        if settings is None:
            settings = SETTINGS.get_component_settings(self.__class__.NAME)
        # TODO: add schema validation
        self._data = update_dict_recur(
            copy.deepcopy(self.__class__.DEFAULT), settings)
        self.local_root = root or Path(inspect.getfile(self.__class__)).parent

    @property
    def user(self):
        return self._data.get('user', self.__class__.NAME)

    @property
    def enabled(self):
        if 'enabled' in self._data:
            return self._data['enabled']
        for _, host in SETTINGS.get_hosts():
            if self.__class__.NAME in host['components']:
                return True
        return False

    @property
    def home(self):
        return Path('~')

    @property
    def home_abs(self):
        return Path('/', 'home', self.user)

    @property
    def systemd(self):
        return self._data.get('systemd', {})

    @property
    def root(self):
        return self.home / self._data['root']

    @property
    def root_abs(self):
        return self.home_abs / self._data['root']
