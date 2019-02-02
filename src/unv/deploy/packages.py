from pathlib import Path

from .helpers import apt_install, mkdir, rmrf, run, cd


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
            run(f'wget https://www.python.org/ftp/'
                f'python/{version}/Python-{version}.tar.xz')
            run(f'tar xf Python-{version}.tar.xz')
            run(f'mv ./Python-{version}/* ./')
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
        run("echo 'building")
