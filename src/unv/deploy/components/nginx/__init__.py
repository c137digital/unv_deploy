from pathlib import Path

from unv.utils.tasks import register

from ...tasks import DeployComponentTasksBase
from ...helpers import ComponentSettingsBase

from ..systemd import SystemdTasksMixin


class NginxComponentSettings(ComponentSettingsBase):
    NAME = 'nginx'
    DEFAULT = {
        'systemd': {
            'template': 'server.service',
            'name': 'nginx.service',
            'boot': True,
            'instances': {'count': 1}
        },
        'master': True,
        'root': 'app',
        'packages': {
            'nginx': 'http://nginx.org/download/nginx-1.16.0.tar.gz',
            'pcre': 'https://ftp.pcre.org/pub/pcre/pcre-8.42.tar.gz',
            'zlib': 'http://www.zlib.net/zlib-1.2.11.tar.gz',
            'openssl': 'https://www.openssl.org/source/openssl-1.1.1a.tar.gz'
        },
        'configs': {'server.conf': 'nginx.conf'},
        'connections': 1000,
        'workers': 1,
        'aio': 'on',
        'sendfile': 'on',
        'tcp_nopush': 'on',
        'tcp_nodelay': 'on',
        'keepalive_timeout': 60,
        'include': 'conf/apps/*.conf',
        'access_log': 'logs/access.log',
        'error_log': 'logs/error.log',
        'default_type': 'application/octet-stream',
    }

    @property
    def build(self):
        return self.root / 'build'

    @property
    def packages(self):
        return self._data['packages']

    @property
    def configs(self):
        for template, name in self._data['configs'].items():
            if not template.startswith('/'):
                template = (self.local_root / template).resolve()
            yield Path(template), self.root / 'conf' / name

    @property
    def include(self):
        return self.root_abs / self._data['include']

    @property
    def access_log(self):
        return self.root_abs / self._data['access_log']

    @property
    def error_log(self):
        return self.root_abs / self._data['error_log']

    @property
    def default_type(self):
        return self._data['default_type']

    @property
    def aio(self):
        return self._data['aio']

    @property
    def sendfile(self):
        return self._data['sendfile']

    @property
    def tcp_nopush(self):
        return self._data['tcp_nopush']

    @property
    def tcp_nodelay(self):
        return self._data['tcp_nodelay']

    @property
    def keepalive_timeout(self):
        return self._data['keepalive_timeout']

    @property
    def workers(self):
        return self._data['workers']

    @property
    def connections(self):
        return self._data['connections']

    @property
    def master(self):
        return self._data['master']


class NginxComponentTasks(DeployComponentTasksBase, SystemdTasksMixin):
    NAMESPACE = 'nginx'
    SETTINGS = NginxComponentSettings()

    @register
    async def build(self):
        if not self._settings.master:
            print('Nginx already builded on this host, just use nginx.sync')
            return

        await self._create_user()
        await self._mkdir(self._settings.include.parent)
        await self._apt_install(
            'build-essential', 'autotools-dev', 'libexpat-dev',
            'libgd-dev', 'libgeoip-dev', 'libluajit-5.1-dev',
            'libmhash-dev', 'libpam0g-dev', 'libperl-dev',
            'libxslt1-dev'
        )

        async with self._cd(self._settings.build, temporary=True):
            for package, url in self._settings.packages.items():
                await self._download_and_unpack(url, Path('.', package))

            async with self._cd('nginx'):
                await self._run(
                    f"./configure --prefix={self._settings.root_abs} "
                    f"--user='{self._user}' --group='{self._user}' "
                    "--with-pcre=../pcre "
                    "--with-pcre-jit --with-zlib=../zlib "
                    "--with-openssl=../openssl --with-http_ssl_module "
                    "--with-http_v2_module --with-threads "
                    "--with-file-aio"
                )
                await self._run('make')
                await self._run('make install')

    @register
    async def sync(self):
        for template, path in self._settings.configs:
            await self._upload_template(
                template, path, {'settings': self._settings})
            print(await self._run(f'cat {path}'))
        await self._sync_systemd_units()
