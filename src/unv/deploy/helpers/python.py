from fabric.api import env

from .core import apt_install


# CONCEPT: python building flow from source
# TODO: sources for python code
# config params as args in func?
# def build(bin_dir):
#     apt_install(
#         'make', 'build-essential', 'libssl-dev', 'zlib1g-dev',
#         'libbz2-dev', 'libreadline-dev', 'libsqlite3-dev', 'wget', 'curl',
#         'llvm', 'libncurses5-dev', 'libncursesw5-dev', 'xz-utils',
#         'tk-dev', 'tcl-dev', 'libffi-dev',
#     )
#     with cd_temp_dir(build_dir):
#         # sources path
#         # put(str('sources' / 'python.tar.gz'), '.')
#         run(
#             './configure --prefix={0} '
#             '--enable-loadable-sqlite-extensions --enable-shared '
#             '--with-system-expat --enable-optimizations '
#             'LDFLAGS="-L{0}/extlib/lib -Wl,--rpath={0}/lib '
#             '-Wl,--rpath={0}/extlib/lib" '
#             'CPPFLAGS="-I{0}/extlib/include"'.format(bin_dir)
#         )
#         run('make -j$(nproc) build_all')
#         run('make install > /dev/null')

#     run('{} install wheel'.format(ENV.DEPLOY['python']['pip']))
#     run('{} install -U pip'.format(ENV.DEPLOY['python']['pip']))
#     run('{} install -U setuptools'.format(ENV.DEPLOY['python']['pip']))
#     update_pip()

#     run('rm -rf {}'.format(ENV.DEPLOY['build']))
