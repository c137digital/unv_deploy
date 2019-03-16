import copy

from pathlib import Path

from unv.utils.collections import update_dict_recur

from .helpers import (
    apt_install, mkdir, rmrf, run, cd, download_and_unpack, sudo,
    upload_template, filter_hosts, local, copy_ssh_key_for_user, quiet,
    update_local_known_hosts
)
from .settings import SETTINGS


class Package:
    DEFAULT = {}

    def __init__(self, root, settings):
        self.package_root = Path(root).parent
        self.settings = update_dict_recur(
            copy.deepcopy(self.DEFAULT), settings)

    @property
    def user(self):
        return self.settings['user']

    @property
    def home(self):
        return Path('/', 'home', self.user)

    def upload_template(
            self, local_path: Path, remote_path: Path, context: dict = None):
        context = context or {}
        context['COMPONENT'] = self
        upload_template(self.package_root / local_path, remote_path, context)

    def yield_systemd_services(self):
        systemd = self.settings['systemd']
        instances = self.settings.get('instances', 1)

        for template, original in systemd['services'].items():
            name = original['name']
            for instance in range(1, instances + 1):
                service = original.copy()
                service['name'] = name.format(INSTANCE=instance)
                service['instance'] = instance
                service['template'] = template
                yield service

    def setup_systemd_units(self):
        services = list(self.yield_systemd_services())
        systemd = self.settings['systemd']
        mkdir(systemd['dir'], remove_existing=True)

        for service in services:
            service_remote_path = Path(
                self.home, systemd['dir'], service['name'])
            self.upload_template(
                Path(service['template']), service_remote_path,
                {'INSTANCE': service['instance']}
            )

            with quiet():
                sudo(f"rm /etc/systemd/system/{service['name']}")
            sudo(f"cp -f {service_remote_path} /etc/systemd/system/")

        sudo('systemctl daemon-reload')

        for service in services:
            if service['boot']:
                sudo(f'systemctl enable {service["name"]}')

    def systemctl(self, command):
        for service in self.yield_systemd_services():
            if 'manage' in service and not service['manage']:
                continue

            sudo(f'systemctl {command} {service["name"]}')

    def start(self):
        self.systemctl('start')

    def stop(self):
        self.systemctl('stop')

    def restart(self):
        self.systemctl('restart')

    def status(self):
        self.systemctl('status')


class PythonPackage(Package):
    DEFAULT = {
        'root': 'python',
        'version': '3.7.2',
        'build': {
            'fast': True,
            'dir': '/tmp/python'
        }
    }

    @property
    def _root(self):
        return self.home / self.settings['root']

    def pip(self, command: str):
        self.bin(f'pip3 {command}')

    def run(self, command: str):
        self.bin(f'python3 {command}')

    def bin(self, command: str, command_only=False):
        command = str(self._root / 'bin' / command)
        if command_only:
            return command
        return run(command)

    def build(self):
        version = self.settings['version']
        fast_build = self.settings['build']['fast']
        build_dir = Path(self.settings['build']['dir'])

        apt_install(
            'make', 'build-essential', 'libssl-dev', 'zlib1g-dev',
            'libbz2-dev', 'libreadline-dev', 'libsqlite3-dev', 'wget', 'curl',
            'llvm', 'libncurses5-dev', 'libncursesw5-dev', 'xz-utils',
            'tk-dev', 'tcl-dev', 'libffi-dev', 'wget'
        )

        mkdir(build_dir, remove_existing=True)
        mkdir(self._root, remove_existing=True)

        with cd(build_dir):
            url = 'https://www.python.org/ftp/' \
                f'python/{version}/Python-{version}.tar.xz'
            download_and_unpack(url, Path('./'))

            run(
                './configure --prefix={0} '
                '--enable-loadable-sqlite-extensions --enable-shared '
                '--with-system-expat --enable-optimizations '
                'LDFLAGS="-L{0}/extlib/lib -Wl,--rpath={0}/lib '
                '-Wl,--rpath={0}/extlib/lib" '
                'CPPFLAGS="-I{0}/extlib/include"'.format(self._root)
            )
            run('make -j$(nproc) {}'.format(
                'build_all' if fast_build else 'build'))
            run('make install > /dev/null')
        rmrf(build_dir)

        self.pip('install wheel')
        self.pip('install -U pip')
        self.pip('install -U setuptools')


class NginxPackage(Package):
    DEFAULT = {
        'master': False,
        'versions': {
            'nginx': '1.15.9',
            'pcre': '8.42',
            'zlib': '1.2.11',
            'openssl': '1.1.1a'
        },
        'connections': 1000,
        'workers': 1
    }

    @property
    def root(self):
        return self.home / self.settings['dir']

    @property
    def workers(self):
        return self.settings['workers']

    @property
    def connections(self):
        return self.settings['connections']

    @staticmethod
    def get_upstream_hosts():
        from unv.web.settings import SETTINGS as WEB_SETTINGS

        app = SETTINGS['components']['app']

        for _, host in filter_hosts(SETTINGS['hosts'], 'app'):
            for instance in range(app['instances']):
                yield '{}:{}'.format(
                    host['private'], WEB_SETTINGS['port'] + instance
                )

    def build(self):
        # https://www.nginx.com/blog/thread-pools-boost-performance-9x/
        #  --with-threads
        # http://nginx.org/en/docs/http/ngx_http_core_module.html#aio
        #  --with-file-aio

        sudo('apt-get update && apt-get upgrade -y')
        sudo('apt-get build-dep -y --no-install-recommends '
             '--no-install-suggests nginx')

        packages = {
            'nginx': 'http://nginx.org/download/nginx-{}.tar.gz',
            'pcre': 'https://ftp.pcre.org/pub/pcre/pcre-{}.tar.gz',
            'zlib': 'http://www.zlib.net/zlib-{}.tar.gz',
            'openssl': 'https://www.openssl.org/source/openssl-{}.tar.gz'
        }

        mkdir(self.root)

        build_path = self.root.parent / 'build'
        mkdir(build_path, remove_existing=True)

        with cd(build_path):
            for package, url in packages.items():
                download_and_unpack(
                    url.format(self.settings['versions'][package]),
                    Path('.', package)
                )

            with cd('nginx'):
                run("./configure --prefix={nginx_dir} "
                    "--user='{user}' --group='{user}' --with-pcre=../pcre "
                    "--with-pcre-jit --with-zlib=../zlib "
                    "--with-openssl=../openssl --with-http_ssl_module "
                    "--with-http_v2_module --with-threads "
                    "--with-file-aio".format(
                        nginx_dir=self.root,
                        user=self.settings['user']
                    ))
                run('make > /dev/null')
                run('make install')

        rmrf(build_path)

    def sync(self):
        if self.settings['master']:
            self.upload_template(
                Path(self.settings['config']['template']),
                self.root / 'conf' / self.settings['config']['name']
            )

        mkdir(self.root / 'conf' / 'apps')

        for local_path, remote_name in self.settings['include'].items():
            self.upload_template(
                Path(local_path),
                self.root / 'conf' / 'apps' / remote_name,
            )

        self.setup_systemd_units()


class VagrantPackage(Package):
    def setup(self):
        local('vagrant destroy -f')
        local('vagrant up')

        local('rm -f *.log')

        update_local_known_hosts()

        copy_ssh_key_for_user('root', Path(self.settings['keys']['public']))

    def start(self):
        local('vagrant up')

    @property
    def running(self):
        pass
