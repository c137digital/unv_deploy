import copy

from pathlib import Path

from unv.utils.collections import update_dict_recur

from .helpers import (
    apt_install, mkdir, rmrf, run, cd, download_and_unpack, sudo,
    upload_template
)


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

    def setup_systemd_units(self):
        systemd = self.settings['systemd']
        mkdir(systemd['dir'], remove_existing=True)

        for service in systemd['services']:
            service_remote_path = Path(
                self.home, systemd['dir'], service['name'])
            self.upload_template(
                Path(service['template']), service_remote_path)
            sudo(f'ln -sf {service_remote_path} /etc/systemd/system/')

        sudo('systemctl daemon-reload')

        for service in systemd['services']:
            if service['boot']:
                sudo(f'systemctl enable {service["name"]}')


class PythonPackage(Package):
    @property
    def _root(self):
        return Path(self.settings['root'])

    def pip(self, command: str):
        root = self._root / 'bin'
        run(f'{root}/pip3 {command}')

    def run(self, command: str):
        root = self._root / 'bin'
        run(f'{root}/python3 {command}')

    def build(self):
        version = self.settings.get('version', '3.7.2')
        fast_build = self.settings.get('fast_build', True)
        build_dir = Path(self.settings.get('build_dir', '/tmp/python'))

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

        self.pip('install -U wheel')
        self.pip('install -U pip')
        self.pip('install -U setuptools')


class NginxPackage(Package):
    DEFAULT = {
        'master': False,
        'versions': {
            'nginx': '1.15.8',
            'pcre': '8.42',
            'zlib': '1.2.11',
            'openssl': '1.1.1a'
        }
    }

    @property
    def root(self):
        return self.home / self.settings['dir']

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
                self.root / 'conf' / 'apps' / remote_name
            )

        self.setup_systemd_units()

    def start(self):
        sudo('systemctl start nginx')

    def status(self):
        sudo('systemctl status nginx')

    def restart(self):
        sudo('systemctl restart nginx')
