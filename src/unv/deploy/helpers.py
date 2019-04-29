import functools
import copy
import inspect

from pathlib import Path

from unv.utils.collections import update_dict_recur

from .settings import SETTINGS


class ComponentSettingsBase:
    NAME = ''

    def __init__(self, settings=None, root=None):
        if settings is None:
            settings = SETTINGS['components'].get(self.__class__.NAME, {})
        # TODO: add schema validation
        self._data = update_dict_recur(
            copy.deepcopy(self.__class__.DEFAULT), settings)
        self.local_root = root or Path(inspect.getfile(self.__class__)).parent

    @property
    def user(self):
        return self._data['user']

    @property
    def enabled(self):
        if 'enabled' in self._data:
            return self._data['enabled']
        return 'user' in self._data

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


def as_user(user, func=None):
    """Task will run from any user, sets to env.user."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            with self._set_user(user):
                return await func(self, *args, **kwargs)
        return wrapper

    return decorator if func is None else decorator(func)


def as_root(func):
    return as_user('root', func)


def get_hosts(component=''):
    for key, value in SETTINGS['hosts'].items():
        if component in value.get('components', []) or not component:
            yield key, value
