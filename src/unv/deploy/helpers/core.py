import os
import pwd
import pathlib
import functools

from fabric.api import execute, run, env, task, runs_once, cd as base_cd

local_task = runs_once(task)()


def cd(path: pathlib.Path):
    return base_cd(str(path))


def rmrf(path: pathlib.Path):
    run(f'rm -rf {path}')


def mkdir(path: pathlib.Path, remove_exist=False):
    if remove_exist:
        rmrf(path)
    run(f'mkdir -p {path}')


def get_local_username():
    return pwd.getpwuid(os.getuid())[0]


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


def get_host_components():
    for host_ in env.HOSTS.values():
        host_string = '{}:{}'.format(host_['public'], host_.get('ssh', 22))
        if env.host_string == host_string:
            return host_['components']


def apt_install(*packages):
    sudo('apt-get update && apt-get upgrade -y')
    sudo('apt-get install -y --no-install-recommends '
         '--no-install-suggests {}'.format(' '.join(packages)))
