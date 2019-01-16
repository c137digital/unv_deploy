import os
import pwd

from fabric.api import local, task, runs_once

task = runs_once(task)()


def get_local_username():
    return pwd.getpwuid(os.getuid())[0]


@task
def chown(dir_path):
    """Chown all dirs to current user."""
    local('sudo chown -hR {} {}'.format(get_local_username(), dir_path))


@task
def generate_cert(dir_path: str):
    local('mkdir -p {}'.format(dir_path))
    local(
        'openssl req -x509 -nodes -days 365'
        ' -newkey rsa:2048 -keyout {path}/privkey.pem'
        ' -out {path}/fullchain.pem'.format(path=dir_path)
    )
