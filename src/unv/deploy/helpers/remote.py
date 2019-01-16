import importlib
import functools

from fabric.api import execute, run, env


def load(module_path: str):
    """Load deploy environment from module."""
    module = importlib.import_module(module_path)
    components, hosts = module.COMPONENTS, module.HOSTS
    raise NotImplementedError(components, hosts)


def as_user(user, func):
    """Task will run from any user, sets to env.user."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        old_user = env.user
        env.user = user
        result = func(*args, **kwargs)
        env.user = old_user
        return result
    return wrapper


def sudo(command):
    run_as_root = as_user('root', run)
    execute(run_as_root, command)


def as_root(func):
    """Task will run from "root" user, sets to env.user."""
    return as_user('root', func)


def filter_hosts(hosts, component, parent_key=''):
    for key, value in hosts.items():
        if not isinstance(value, dict):
            continue

        key = '{}.{}'.format(parent_key, key) if parent_key else key
        if 'public' in value and 'private' in value and \
                (component in value.get('components', []) or not component):
            yield key, value
        else:
            yield from filter_hosts(value, component, key)
