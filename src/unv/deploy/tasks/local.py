from fabric.api import local

from ..helpers.local import task, get_local_username


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
