import importlib
import pathlib

from fabric.api import env, task

from ..helpers.remote import filter_hosts


@task
def host(host_filter=''):
    env.user = env.DEPLOY['user']
    env.hosts = [
        '{}:{}'.format(host_['public'], host_.get('ssh', 22))
        for name, host_ in filter_hosts(env.HOSTS, env.COMPONENT)
        if not host_filter or name.startswith(host_filter)
    ]
    env.key_filename = str(env.KEYS['private'])


@task
def load(module_path: str, component: str):
    """Load deploy environment from module."""
    module = importlib.import_module(module_path)

    env.COMPONENTS = module.COMPONENTS
    env.HOSTS = module.HOSTS
    env.COMPONENT = component
    env.DEPLOY = env.COMPONENTS[component]
    env.KEYS = getattr(module, 'KEYS', {
        'private': pathlib.Path('~/.ssh/id_rsa'),
        'public': pathlib.Path('~/.ssh/id_rsa.pub')
    })
