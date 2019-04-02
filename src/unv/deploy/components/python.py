# TODO: move to new tasks system, as nested subpackage?
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
