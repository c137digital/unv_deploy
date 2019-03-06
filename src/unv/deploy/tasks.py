from fabric.api import env, task

from .helpers import filter_hosts
from .settings import SETTINGS


@task
def hosts(component: str, host: str = ''):
    """Set env user and hosts from component settings."""
    keys = SETTINGS.get('keys', {
        'private': '~/.ssh/id_rsa',
        'public': '~/.ssh/id_rsa.pub'
    })
    env.key_filename = keys['private']
    env.hosts = [
        '{}:{}'.format(host_['public'], host_.get('ssh', 22))
        for name, host_ in filter_hosts(SETTINGS['hosts'], component)
        if not host or name == host
    ]
    env.connection_attempts = 10
