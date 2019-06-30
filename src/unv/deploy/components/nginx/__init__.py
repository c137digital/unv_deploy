from pathlib import Path

from unv.utils.tasks import register

from ...tasks import DeployComponentTasks, as_root
from ...settings import DeployComponentSettings

from ..systemd import SystemdTasksMixin


class NginxSettings(DeployComponentSettings):
    NAME = 'nginx'
    SCHEMA = {
        'systemd': SystemdTasksMixin.SCHEMA,
        'master': {'type': 'boolean', 'required': True},
        'root': {'type': 'string', 'required': True},
        'packages': {
            'type': 'dict',
            'schema': {
                'nginx': {'type': 'string', 'required': True},
                'pcre': {'type': 'string', 'required': True},
                'zlib': {'type': 'string', 'required': True},
                'openssl': {'type': 'string', 'required': True},
                'geoip2': {'type': 'string', 'required': True},
                'libmaxminddb': {'type': 'string', 'required': True}
            },
            'required': True
        },
        'packages_dir': {
            'type': 'dict',
            'required': False
        },
        'geoip2db': {
            'type': 'dict',
            'schema': {
                'city': {'type': 'string', 'required': True},
                'country': {'type': 'string', 'required': True},
                'lang': {
                    'type': 'string',
                    'required': True,
                    'allowed': ['en', 'ru']
                }
            },
            'required': True
        },
        'configs': {'type': 'dict'},
        'connections': {'type': 'integer', 'required': True},
        'workers': {'type': 'integer', 'required': True},
        'aio': {'type': 'boolean', 'required': True},
        'sendfile': {'type': 'boolean', 'required': True},
        'tcp_nopush': {'type': 'boolean', 'required': True},
        'tcp_nodelay': {'type': 'boolean', 'required': True},
        'keepalive_timeout': {'type': 'integer', 'required': True},
        'include': {'type': 'string', 'required': True},
        'access_log': {'type': 'string', 'required': True},
        'error_log': {'type': 'string', 'required': True},
        'default_type': {'type': 'string', 'required': True},
        'geoip2': {'type': 'boolean', 'required': True},
        'iptables': {
            'type': 'dict',
            'schema': {
                'v4': {'type': 'string', 'required': True}
            },
            'required': True
        }
    }
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
            'nginx': 'http://nginx.org/download/nginx-1.17.1.tar.gz',
            'pcre': 'https://ftp.pcre.org/pub/pcre/pcre-8.42.tar.gz',
            'zlib': 'http://www.zlib.net/zlib-1.2.11.tar.gz',
            'openssl': 'https://www.openssl.org/source/openssl-1.1.1a.tar.gz',
            'geoip2': 'https://github.com/leev/ngx_http_geoip2_'
                'module/archive/master.tar.gz',
            'libmaxminddb': 'https://github.com/maxmind/libmaxminddb/releases'
                '/download/1.3.2/libmaxminddb-1.3.2.tar.gz',
        },
        'packages_dir': {
            'geoip2': 'ngx_http_geoip2_module-master',
        },
        'geoip2db': {
            'city': 'https://geolite.maxmind.com/download/geoip/database/'
                'GeoLite2-City.tar.gz',
            'country': 'https://geolite.maxmind.com/download/geoip/database/'
                'GeoLite2-Country.tar.gz',
            'lang': 'en'
        },
        'configs': {'server.conf': 'nginx.conf'},
        'connections': 1000,
        'workers': 1,
        'aio': True,
        'sendfile': True,
        'tcp_nopush': True,
        'tcp_nodelay': True,
        'keepalive_timeout': 60,
        'include': 'conf/apps/*.conf',
        'access_log': 'logs/access.log',
        'error_log': 'logs/error.log',
        'default_type': 'application/octet-stream',
        'geoip2': False,
        'iptables': {'v4': 'ipv4.rules'}
    }

    @property
    def build(self):
        return self.root / 'build'

    @property
    def packages(self):
        return self._data['packages']

    @property
    def packages_dir(self):
        return self._data.get('packages_dir', {})

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
        return 'on' if self._data['aio'] else 'off'

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

    @property
    def geoip2(self):
        return self._data['geoip2']

    @property
    def geoip2_city_path(self):
        return self.root_abs / 'geoip2' / 'GeoLite2-City.mmdb'

    @property
    def geoip2_country_path(self):
        return self.root_abs / 'geoip2' / 'GeoLite2-Country.mmdb'

    @property
    def geoip2_lang(self):
        return self._data['geoip2db']['lang']

    @property
    def geoip2db_city_url(self):
        return self._data['geoip2db']['city']

    @property
    def geoip2db_country_url(self):
        return self._data['geoip2db']['country']

    @property
    def iptables_v4_rules(self):
        return (self.local_root / self._data['iptables']['v4']).read_text()


class NginxTasks(DeployComponentTasks, SystemdTasksMixin):
    SETTINGS = NginxSettings()

    async def get_iptables_template(self):
        return self.settings.iptables_v4_rules

    @as_root
    async def _install_libmaxminddb(self):
        # TODO: move to other package?
        package = 'libmaxminddb'
        url = self.settings.packages[package]

        async with self._cd('build', temporary=True):
            await self._download_and_unpack(url, Path('.', package))

            async with self._cd('libmaxminddb'):
                await self._run('./configure')
                await self._run('make')
                await self._run('make check')
                await self._run('make install')
                await self._run('ldconfig')

    @register
    async def build(self):
        if not self.settings.master:
            print('Nginx already builded on this host, just use nginx.sync')
            return

        await self._create_user()
        await self._mkdir(self.settings.include.parent)
        await self._apt_install(
            'build-essential', 'autotools-dev', 'libexpat-dev',
            'libgd-dev', 'libgeoip-dev', 'liblua5.1-0-dev',
            'libmhash-dev', 'libpam0g-dev', 'libperl-dev',
            'libxslt1-dev'
        )

        if self.settings.geoip2:
            await self._install_libmaxminddb()

            async with self._cd(self.settings.root):
                await self._mkdir('geoip2')
                async with self._cd('geoip2'):
                    await self._download_and_unpack(
                        self.settings.geoip2db_city_url,
                        archive_dir_name='GeoLite2-City_*'
                    )
                    await self._download_and_unpack(
                        self.settings.geoip2db_country_url,
                        archive_dir_name='GeoLite2-Country_*'
                    )
                    await self._run('rm *.txt')

        async with self._cd(self.settings.build, temporary=True):
            for package, url in self.settings.packages.items():
                if package == 'libmaxminddb':
                    continue
                if package == 'geoip2' and not self.settings.geoip2:
                    continue

                await self._download_and_unpack(
                    url, Path('.', package),
                    archive_dir_name=self.settings.packages_dir.get(package)
                )

            async with self._cd('nginx'):
                build_command = (
                    f"./configure --prefix={self.settings.root_abs} "
                    f"--user='{self.user}' --group='{self.user}' "
                    "--with-pcre=../pcre "
                    "--with-pcre-jit --with-zlib=../zlib "
                    "--with-openssl=../openssl --with-http_ssl_module "
                    "--with-http_v2_module --with-threads "
                    "--with-file-aio "
                )
                if self.settings.geoip2:
                    build_command += '--add-module=../geoip2 '
                await self._run(build_command)
                await self._run('make')
                await self._run('make install')

    @register
    async def sync(self):
        for template, path in self.settings.configs:
            await self._upload_template(template, path)

        for task in self.get_all_deploy_tasks():
            get_configs = getattr(task, 'get_nginx_include_configs', None)
            if get_configs is not None:
                configs = await get_configs()
                for template, path in configs:
                    await self._upload_template(
                        template,
                        self.settings.root / self.settings.include.parent
                        / path, {'deploy': task, 'nginx_deploy': self}
                    )

        await self._sync_systemd_units()

    @register
    async def setup(self):
        await self.build()
        await self.sync()
        await self.start()
