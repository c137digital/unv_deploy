import functools

from .settings import SETTINGS


def as_user(user, func=None):
    """Task will run from any user, sets to env.user."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            old_user = self._user
            self._user = user
            result = await func(self, *args, **kwargs)
            self._user = old_user
            return result
        return wrapper

    return decorator if func is None else decorator(func)


def as_root(func):
    return as_user('root', func)


def filter_hosts(component='', parent_key='', hosts=None):
    hosts = hosts or SETTINGS['hosts']
    for key, value in hosts.items():
        if not isinstance(value, dict):
            continue

        key = '{}.{}'.format(parent_key, key) if parent_key else key
        if 'public' in value and 'private' in value and \
                (component in value.get('components', []) or not component):
            yield key, value
        else:
            yield from filter_hosts(component, key, value)
