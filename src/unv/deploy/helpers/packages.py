from pathlib import Path

from .core import apt_install, mkdir, rmrf, run, cd


def build_python(
        root_dir: Path,
        version='3.7.2', fast_build=True, build_dir=Path('/tmp/python')):
    apt_install(
        'make', 'build-essential', 'libssl-dev', 'zlib1g-dev',
        'libbz2-dev', 'libreadline-dev', 'libsqlite3-dev', 'wget', 'curl',
        'llvm', 'libncurses5-dev', 'libncursesw5-dev', 'xz-utils',
        'tk-dev', 'tcl-dev', 'libffi-dev', 'wget'
    )

    mkdir(build_dir, remove_exist=True)
    mkdir(root_dir, remove_exist=True)

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
            'CPPFLAGS="-I{0}/extlib/include"'.format(root_dir)
        )
        run('make -j$(nproc) {}'.format(
            'build_all' if fast_build else 'build'))
        run('make install > /dev/null')
    rmrf(build_dir)

    with cd(root_dir / 'bin'):
        run('./pip3 install wheel')
        run('./pip3 install -U pip')
        run('./pip3 install -U setuptools')
