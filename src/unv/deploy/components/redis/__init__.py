from pathlib import Path

from unv.utils.tasks import register

from ...tasks import DeployComponentTasks
from ...settings import DeployComponentSettings

from ..systemd import SystemdTasksMixin


class RedisSettings(DeployComponentSettings):
    NAME = 'redis'
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
                'openssl': {'type': 'string', 'required': True}
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
            'nginx': 'http://nginx.org/download/nginx-1.17.0.tar.gz',
            'pcre': 'https://ftp.pcre.org/pub/pcre/pcre-8.42.tar.gz',
            'zlib': 'http://www.zlib.net/zlib-1.2.11.tar.gz',
            'openssl': 'https://www.openssl.org/source/openssl-1.1.1a.tar.gz'
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
        'iptables': {
            'v4': 'ipv4.rules'
        }
    }

    @property
    def build(self):
        return self.root / 'build'

    @property
    def packages(self):
        return self._data['packages']

    @property
    def iptables_v4_rules(self):
        return (self.local_root / self._data['iptables']['v4']).read_text()


class RedisTasks(DeployComponentTasks, SystemdTasksMixin):
    SETTINGS = RedisSettings()

    async def get_iptables_template(self):
        return self.settings.iptables_v4_rules

    @register
    async def build(self):
        await self._create_user()
        await self._sudo('apt-get update')
        await self._sudo('apt-get build-dep redis -y')

        async with self._cd(self.settings.build, temporary=True):
            for package, url in self.settings.packages.items():
                await self._download_and_unpack(url, Path('.', package))

            async with self._cd('redis'):
                await self._run('make distclean')
                # NOTE: ARCH='' used for fixing bug in
                # hiredis only for arm builds
                await self._run("make -j$(nproc) ARCH='' MALLOC=jemalloc")
                await self._run(
                    f"make PREFIX={self.settings.root_abs} install")

    @register
    async def sync(self):
        pass
        # for template, path in self.settings.configs:
        #     await self._upload_template(template, path)

        # for task in self.get_all_deploy_tasks():
        #     get_configs = getattr(task, 'get_nginx_include_configs', None)
        #     if get_configs is not None:
        #         configs = await get_configs()
        #         for template, path in configs:
        #             await self._upload_template(
        #                 template,
        #                 self.settings.root / self.settings.include.parent
        #                 / path, {'deploy': task, 'nginx_deploy': self}
        #             )

        # await self._sync_systemd_units()

    @register
    async def setup(self):
        await self.build()
        await self.sync()
        await self.start()
