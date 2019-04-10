from unv.utils.tasks import register

from ..tasks import DeployComponentTasksBase
from ..helpers import ComponentSettingsBase


class PythonComponentSettings(ComponentSettingsBase):
    NAME = 'python'
    DEFAULT = {
        'root': 'python',
        'version': '3.7.3',
        'build': {
            'fast': True,
            'path': '/tmp/python'
        }
    }

    @property
    def version(self):
        return self._data['version']

    @property
    def fast_build(self):
        return self._data['build']['fast']

    @property
    def build_path(self):
        return self._data['build']['path']


class PythonComponentTasks(DeployComponentTasksBase):
    SETTINGS = PythonComponentSettings()

    async def pip(self, command: str):
        return await self.bin(f'pip3 {command}')

    async def run(self, command: str):
        return await self.bin(f'python3 {command}')

    async def bin(self, command: str):
        return await self._run(str(self._settings.root_abs / 'bin' / command))

    async def shell(self):
        return await self._run(
            str(self._settings.root_abs / 'bin' / 'python3'),
            interactive=True
        )

    @register
    async def build(self):
        version = self._settings.version
        fast_build = self._settings.fast_build
        build_path = self._settings.build_path

        await self._apt_install(
            'make', 'build-essential', 'libssl-dev', 'zlib1g-dev',
            'libbz2-dev', 'libreadline-dev', 'libsqlite3-dev', 'wget', 'curl',
            'llvm', 'libncurses5-dev', 'libncursesw5-dev', 'xz-utils',
            'tk-dev', 'tcl-dev', 'libffi-dev', 'wget'
        )

        await self._mkdir(self._settings.root, delete=True)

        async with self._cd(build_path, temporary=True):
            url = 'https://www.python.org/ftp/' \
                f'python/{version}/Python-{version}.tar.xz'
            await self._download_and_unpack(url)

            await self._run(
                './configure --prefix={0} '
                '--enable-loadable-sqlite-extensions --enable-shared '
                '--with-system-expat --enable-optimizations '
                'LDFLAGS="-L{0}/extlib/lib -Wl,--rpath={0}/lib '
                '-Wl,--rpath={0}/extlib/lib" '
                'CPPFLAGS="-I{0}/extlib/include"'.format(
                    self._settings.root_abs
                )
            )
            await self._run('make -j$(nproc) {}'.format(
                'build_all' if fast_build else 'build'))
            await self._run('make install > /dev/null')

        await self.pip('install wheel')
        await self.pip('install -U pip')
        await self.pip('install -U setuptools')
