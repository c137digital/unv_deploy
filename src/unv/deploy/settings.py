import os
import json
import copy
import inspect
import importlib

from pathlib import Path

import jinja2

from unv.utils.os import run_in_shell
from unv.utils.collections import update_dict_recur
from unv.app.settings import (
    ComponentSettings, validate_schema, SETTINGS as APP_SETTINGS
)


SERVICES_SCHEMA = {
    'type': 'dict',
    'keyschema': {'type': 'string'},
    'valueschema': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'hosts': {
                    'type': 'list',
                    'required': True,
                    'schema': {'type': 'dict'}
                },
                'components': {'type': 'dict', 'required': False},
            }
        }
    }
}


class DeploySettings(ComponentSettings):
    KEY = 'deploy'
    SCHEMA = {
        'env': {'type': 'string'},
        'tasks': {'type': 'list'},
        'providers': {'type': 'list'},
        'services': SERVICES_SCHEMA,
    }
    DEFAULT = {
        'tasks': [
            'unv.deploy.components.app',
            'unv.deploy.components.iptables',
            'unv.deploy.components.nginx',
            'unv.deploy.components.postgres',
            'unv.deploy.components.redis'
        ],
        'providers': [
            'unv.deploy.providers.vagrant'
        ],
        'services': {},
    }

    @property
    def current_settings_dir(self):
        current_settings = importlib.import_module(os.environ['SETTINGS'])
        return Path(inspect.getfile(current_settings)).parent

    @property
    def services(self):
        return self._data['services']

    @property
    def tasks_classes(self):
        return self._find_classes(self._data['tasks'], 'DeployTasks')

    @property
    def providers(self):
        return [
            provider_class(self.services)
            for provider_class in self._find_classes(
                self._data['providers'], 'DeployProvider'
            )
        ]

    def _find_classes(self, modules, subclass):
        classes = []
        for module_path in modules:
            class_path = ''
            if ':' in module_path:
                module_path, class_path = module_path.split(':')
            module = importlib.import_module(module_path)
            if not class_path:
                for name, value in module.__dict__.items():
                    if name == subclass:
                        continue

                    for mro in getattr(value, '__mro__', []):
                        if mro.__name__ == subclass:
                            class_path = name
                            break

            if not class_path:
                raise ValueError(
                    f"Can't find subclassed {subclass} in {module}")
            classes.append(getattr(module, class_path))
        return classes


SETTINGS = DeploySettings()


class DeployComponentSettings:
    NAME = ''
    DEFAULT = {}
    SCHEMA = {}

    def __init__(self, settings=None, use_from_host=True):
        settings = update_dict_recur(
            settings or {},
            self.get_for_host() if use_from_host else {}
        )
        self._prepare_and_validate_data(settings)
        self.local_root = Path(inspect.getfile(self.__class__)).parent

    def _prepare_and_validate_data(self, settings):
        settings = update_dict_recur(self.DEFAULT, settings)
        self._data = validate_schema(self.SCHEMA, settings)

    def get_for_host(self, host=None):
        settings = {}
        hosts_file = SETTINGS.current_settings_dir / 'hosts.json'
        if hosts_file.exists():
            hosts = json.loads(hosts_file.read_text())
            current = host or hosts.get('__current__')
            if not current:
                return settings
            for host in hosts.get(self.NAME, []):
                if host['public_ip'] == current.get('public_ip') and \
                        host.get('private_ip') == current.get('private_ip'):
                    settings = host['components'][self.NAME]
        return settings

    def update_from_host(self, host):
        self._prepare_and_validate_data(self.get_for_host(host))

    @property
    def user(self):
        return self._data.get('user', self.__class__.NAME)

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
    def systemd_config(self):
        # TODO: move to class all systemd stuff
        return self.systemd.get('config', [])

    @property
    def systemd_dir(self):
        return Path('/etc', 'systemd', 'system')

    @property
    def systemd_type(self):
        return self.systemd.get('type', 'simple')

    @property
    def root(self):
        return self.home / self._data['root']

    @property
    def root_abs(self):
        return self.home_abs / self._data['root']
