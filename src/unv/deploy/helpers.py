import pathlib
import functools

from fabric.api import (  # noqa
    execute, run, env, task, runs_once, quiet,
    cd as base_cd, quiet, local, put as base_put
)
from fabric.contrib import files, project

from unv.utils.os import get_homepath

from .settings import SETTINGS

local_task = runs_once(task)()


def cd(path: pathlib.Path):
    return base_cd(str(path))


def put(local_path: pathlib.Path, remote_path: pathlib.Path):
    return base_put(str(local_path), str(remote_path))


def rmrf(path: pathlib.Path):
    run(f'rm -rf {path}')


def mkdir(path: pathlib.Path, remove_existing=False):
    if remove_existing:
        rmrf(path)
    run(f'mkdir -p {path}')


def update_local_known_hosts():
    ips = [
        host['public']
        for _, host in filter_hosts(SETTINGS['hosts'])
    ]

    known_hosts = get_homepath() / '.ssh' / 'known_hosts'
    if known_hosts.exists():
        with known_hosts.open('r+') as f:
            hosts = f.readlines()
            f.seek(0)
            for host in hosts:
                if any(ip in host for ip in ips):
                    continue
                f.write(host)
            f.truncate()

    for ip in ips:
        local(f'ssh-keyscan {ip} >> ~/.ssh/known_hosts')


def as_user(user, func=None):
    """Task will run from any user, sets to env.user."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            old_user = env.user
            env.user = user
            result = func(*args, **kwargs)
            env.user = old_user
            return result
        return wrapper

    return decorator if func is None else decorator(func)


def sudo(command: str):
    run_as_root = as_user('root', run)
    execute(run_as_root, command)


def as_root(func):
    """Task will run from "root" user, sets to env.user."""
    return as_user('root', func)


def filter_hosts(hosts, component='', parent_key=''):
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
    return None


def apt_install(*packages):
    sudo('apt-get update && apt-get upgrade -y')
    sudo('apt-get install -y --no-install-recommends '
         '--no-install-suggests {}'.format(' '.join(packages)))


@as_root
def create_user(username: str):
    username = username

    with quiet():
        has_user = run("id -u {}".format(username)).succeeded

    if not has_user:
        run("adduser --quiet --disabled-password"
            " --gecos \"{0}\" {0}".format(username))

    return has_user


@as_root
def copy_ssh_key_for_user(username: str, public_key_path: pathlib.Path):
    username = username
    local_ssh_public_key = public_key_path
    local_ssh_public_key = local_ssh_public_key.expanduser()
    keys_path = pathlib.Path(
        '/', 'home' if username != 'root' else '', username, '.ssh')

    mkdir(keys_path, remove_existing=True)
    run(f'chown -hR {username} {keys_path}')

    files.append(
        (keys_path / 'authorized_keys').as_posix(),
        local_ssh_public_key.read_text()
    )


def sync_dir(
        local_dir: pathlib.Path, remote_dir: pathlib.Path,
        exclude: list = None, force=False):
    """Sync local files with remote host."""
    if force:
        rmrf(remote_dir)
    update_local_known_hosts()
    project.rsync_project(
        str(remote_dir), local_dir=f'{local_dir}/', exclude=exclude,
        delete=True
    )


def upload_template(
        local_path: pathlib.Path, remote_path: pathlib.Path,
        context: dict = None):
    files.upload_template(
        local_path.name, str(remote_path),
        template_dir=str(local_path.parent),
        context=context or {}, use_jinja=True
    )


def download_and_unpack(url: str, dest_dir: pathlib.Path):
    run(f'wget {url}')
    archive = url.split('/')[-1]
    run(f'tar xf {archive}')
    archive = archive.split('.tar')[0]
    mkdir(dest_dir)
    run(f'mv {archive}/* {dest_dir}')
