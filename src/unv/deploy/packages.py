from pathlib import Path

from .helpers import (
    apt_install, mkdir, rmrf, run, cd, download_and_unpack, sudo
)


class Package:
    def __init__(self, settings):
        self.settings = settings


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

        mkdir(build_dir, remove_exist=True)
        mkdir(self._root, remove_exist=True)

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
    def build(self):
        # NOTE: some of boosted flags
        # https://www.nginx.com/blog/thread-pools-boost-performance-9x/
        #  --with-threads
        # http://nginx.org/en/docs/http/ngx_http_core_module.html#aio
        #  --with-file-aio

        packages = {
            'nginx': 'http://nginx.org/download/nginx-1.15.4.tar.gz',
            'pcre': 'https://ftp.pcre.org/pub/pcre/pcre-8.42.tar.gz',
            'zlib': 'http://www.zlib.net/zlib-1.2.11.tar.gz',
            'openssl': 'https://www.openssl.org/source/openssl-1.1.0i.tar.gz'
        }
        for package, url in packages.items():
            download_and_unpack(url, Path('.', package))

        sudo('apt-get update && apt-get upgrade -y')
        sudo('apt-get build-dep -y --no-install-recommends '
             '--no-install-suggests nginx')

        with cd('nginx'):
            run("./configure --prefix={nginx_dir} "
                "--user='{user}' --group='{user}' --with-pcre=../pcre "
                "--with-pcre-jit --with-zlib=../zlib "
                "--with-openssl=../openssl --with-http_ssl_module "
                "--with-http_v2_module --with-threads "
                "--with-file-aio".format(
                    nginx_dir='app',
                    user='nginx'
                ))
            run('make')
            run('make install')
