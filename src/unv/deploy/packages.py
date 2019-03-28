import copy

from pathlib import Path

from unv.utils.os import get_homepath
from unv.utils.tasks import register
from unv.utils.collections import update_dict_recur

from unv.web.settings import SETTINGS as WEB_SETTINGS

from .helpers import filter_hosts
from .tasks import DeployTasksBase
from .settings import SETTINGS


# class Package:
#     DEFAULT = {}

#     def __init__(self, root, settings):
#         self.package_root = Path(root).parent
#         self.settings = update_dict_recur(
#             copy.deepcopy(self.DEFAULT), settings)

#     @property
#     def user(self):
#         return self.settings['user']

#     @property
#     def home(self):
#         return Path('/', 'home', self.user)

#     def upload_template(
#             self, local_path: Path, remote_path: Path, context: dict = None):
#         context = context or {}
#         context['COMPONENT'] = self
#         upload_template(self.package_root / local_path, remote_path, context)

#     def yield_systemd_services(self):
#         systemd = self.settings['systemd']
#         instances = self.settings.get('instances', 1)

#         for template, original in systemd['services'].items():
#             name = original['name']
#             for instance in range(1, instances + 1):
#                 service = original.copy()
#                 service['name'] = name.format(INSTANCE=instance)
#                 service['instance'] = instance
#                 service['template'] = template
#                 yield service

#     def setup_systemd_units(self):
#         services = list(self.yield_systemd_services())
#         systemd = self.settings['systemd']
#         mkdir(systemd['dir'], remove_existing=True)

#         for service in services:
#             service_remote_path = Path(
#                 self.home, systemd['dir'], service['name'])
#             self.upload_template(
#                 Path(service['template']), service_remote_path,
#                 {'INSTANCE': service['instance']}
#             )

#             with quiet():
#                 sudo(f"rm /etc/systemd/system/{service['name']}")
#             sudo(f"cp -f {service_remote_path} /etc/systemd/system/")

#         sudo('systemctl daemon-reload')

#         for service in services:
#             if service['boot']:
#                 sudo(f'systemctl enable {service["name"]}')

#     def systemctl(self, command):
#         for service in self.yield_systemd_services():
#             if 'manage' in service and not service['manage']:
#                 continue

#             sudo(f'systemctl {command} {service["name"]}')

#     def start(self):
#         self.systemctl('start')

#     def stop(self):
#         self.systemctl('stop')

#     def restart(self):
#         self.systemctl('restart')

#     def status(self):
#         self.systemctl('status')


# class PythonPackage(Package):
#     DEFAULT = {
#         'root': 'python',
#         'version': '3.7.2',
#         'build': {
#             'fast': True,
#             'dir': '/tmp/python'
#         }
#     }

#     @property
#     def _root(self):
#         return self.home / self.settings['root']

#     def pip(self, command: str):
#         self.bin(f'pip3 {command}')

#     def run(self, command: str):
#         self.bin(f'python3 {command}')

#     def bin(self, command: str, command_only=False):
#         command = str(self._root / 'bin' / command)
#         if command_only:
#             return command
#         return run(command)

#     def build(self):
#         version = self.settings['version']
#         fast_build = self.settings['build']['fast']
#         build_dir = Path(self.settings['build']['dir'])

#         apt_install(
#             'make', 'build-essential', 'libssl-dev', 'zlib1g-dev',
#             'libbz2-dev', 'libreadline-dev', 'libsqlite3-dev', 'wget', 'curl',
#             'llvm', 'libncurses5-dev', 'libncursesw5-dev', 'xz-utils',
#             'tk-dev', 'tcl-dev', 'libffi-dev', 'wget'
#         )

#         mkdir(build_dir, remove_existing=True)
#         mkdir(self._root, remove_existing=True)

#         with cd(build_dir):
#             url = 'https://www.python.org/ftp/' \
#                 f'python/{version}/Python-{version}.tar.xz'
#             download_and_unpack(url, Path('./'))

#             run(
#                 './configure --prefix={0} '
#                 '--enable-loadable-sqlite-extensions --enable-shared '
#                 '--with-system-expat --enable-optimizations '
#                 'LDFLAGS="-L{0}/extlib/lib -Wl,--rpath={0}/lib '
#                 '-Wl,--rpath={0}/extlib/lib" '
#                 'CPPFLAGS="-I{0}/extlib/include"'.format(self._root)
#             )
#             run('make -j$(nproc) {}'.format(
#                 'build_all' if fast_build else 'build'))
#             run('make install > /dev/null')
#         rmrf(build_dir)

#         self.pip('install wheel')
#         self.pip('install -U pip')
#         self.pip('install -U setuptools')


class NginxComponentSettings:
    NAME = 'nginx'
    DEFAULT = {
        'master': True,
        'root': 'app',
        'packages': {
            'nginx': 'http://nginx.org/download/nginx-1.15.9.tar.gz',
            'pcre': 'https://ftp.pcre.org/pub/pcre/pcre-8.42.tar.gz',
            'zlib': 'http://www.zlib.net/zlib-1.2.11.tar.gz',
            'openssl': 'https://www.openssl.org/source/openssl-1.1.1a.tar.gz'
        },
        'connections': 1000,
        'workers': 1,
        'config': {
        },
        'include': {}
    }

    def __init__(self, root, settings=None):
        if settings is None:
            settings = SETTINGS['components'].get('nginx', {})
        # self.root = Path(root).parent
        self._data = update_dict_recur(
            copy.deepcopy(self.__class__.DEFAULT), settings)

    @property
    def home(self):
        return Path('~')

    @property
    def root(self):
        return self.home / self._data['root']

    @property
    def build(self):
        return self.root / 'build'

    @property
    def packages(self):
        return self._data['packages']

    @property
    def workers(self):
        return self._data['workers']

    @property
    def connections(self):
        return self._data['connections']

    @property
    def domain(self):
        return WEB_SETTINGS['domain']

    @property
    def static(self):
        return WEB_SETTINGS['static']

    @staticmethod
    def get_upstream_hosts():
        app = SETTINGS['components']['app']

        for _, host in filter_hosts('app'):
            for instance in range(app['instances']):
                yield '{}:{}'.format(
                    host['private'], WEB_SETTINGS['port'] + instance
                )


class NginxTasks(DeployTasksBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings = NginxComponentSettings(__file__)

    @register
    async def build(self):
        # https://www.nginx.com/blog/thread-pools-boost-performance-9x/
        #  --with-threads
        # http://nginx.org/en/docs/http/ngx_http_core_module.html#aio
        #  --with-file-aio

        await self._create_user()
        await self._apt_install(
            'build-essential', 'autotools-dev', 'libexpat-dev',
            'libgd-dev', 'libgeoip-dev', 'libluajit-5.1-dev',
            'libmhash-dev', 'libpam0g-dev', 'libperl-dev',
            'libxslt1-dev'
        )

        await self._mkdir(self._settings.build, delete=True)
        with self._cd(self._settings.build, delete=True):
            for package, url in self._settings.packages.items():
                await self._download_and_unpack(url, Path('.', package))

            with self._cd('nginx'):
                await self._run(
                    f"./configure --prefix={self._settings.root} "
                    f"--user='{self._user}' --group='{self._user}' "
                    "--with-pcre=../pcre "
                    "--with-pcre-jit --with-zlib=../zlib "
                    "--with-openssl=../openssl --with-http_ssl_module "
                    "--with-http_v2_module --with-threads "
                    "--with-file-aio"
                )
                await self._run('make')
                await self._run('make install')

    def sync(self):
        if self._settings.master:
            await self._upload_template(
                Path(self.settings['config']['template']),
                self.root / 'conf' / self.settings['config']['name']
            )

        await self._mkdir(self.root / 'conf' / 'apps')

        for local_path, remote_name in self.settings['include'].items():
            self.upload_template(
                Path(local_path),
                self.root / 'conf' / 'apps' / remote_name,
            )

        self.setup_systemd_units()


class VagrantTasks(DeployTasksBase):
    async def setup(self):
        await self._local('vagrant destroy -f')
        await self._local('vagrant up')
        await self._update_local_known_hosts()
        await self._local('vagrant ssh -c "sleep 1"')

    async def _update_local_known_hosts(self):
        ips = [host['public'] for _, host in filter_hosts()]
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
            await self._local(f'ssh-keyscan {ip} >> {known_hosts}')
