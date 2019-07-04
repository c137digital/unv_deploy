from pathlib import Path

from unv.utils.tasks import register

from ...tasks import DeployComponentTasks
from ...settings import DeployComponentSettings

from ..systemd import SystemdTasksMixin


class RedisSettings(DeployComponentSettings):
    NAME = 'redis'
    SCHEMA = {
        'systemd': SystemdTasksMixin.SCHEMA,
        'config': {
            'type': 'dict',
            'schema': {
                'template': {'type': 'string', 'required': True},
                'name': {'type': 'string', 'required': True}
            }
        },
        'workdir': {'type': 'string', 'required': True},
        'port': {'type': 'integer', 'required': True},
        'maxmemory': {'type': 'string', 'required': True},
        'databases': {'type': 'integer', 'required': True},
        'root': {'type': 'string', 'required': True},
        'packages': {
            'type': 'dict',
            'schema': {
                'redis': {'type': 'string', 'required': True},
            },
            'required': True
        },
        'iptables': {
            'type': 'dict',
            'schema': {
                'v4': {'type': 'string', 'required': True},
            },
            'required': True
        },
    }
    DEFAULT = {
        'systemd': {
            'template': 'server.service',
            'name': 'redis.service',
            'boot': True,
            'instances': {'count': 1}
        },
        'config': {
            # http://download.redis.io/redis-stable/redis.conf
            'template': 'server.conf',
            'name': 'redis.conf'
        },

        # TODO: move to base config (base package for this type of components)
        'workdir': '.',
        'port': 6379,
        'maxmemory': '128mb',
        'databases': 16,
        'root': 'app',
        'packages': {
            'redis': 'http://download.redis.io/releases/redis-5.0.5.tar.gz'
        },
        'iptables': {
            'v4': 'ipv4.rules'
        }
    }

    @property
    def build_dir(self):
        return self.home_abs / 'build'

    @property
    def bin(self):
        return self.root_abs / 'bin' / 'redis-server'

    @property
    def packages(self):
        return self._data['packages']

    @property
    def config_template(self):
        template = self._data['config']['template']
        if not template.startswith('/'):
            template = (self.local_root / template).resolve()
        return Path(template)

    @property
    def config_path(self):
        return self.root_abs / self._data['config']['name']

    @property
    def workdir(self):
        return self.root_abs / self._data['workdir']

    @property
    def port(self):
        return self._data['port']

    @property
    def maxmemory(self):
        return self._data['maxmemory']

    @property
    def databases(self):
        return self._data['databases']

    @property
    def iptables_v4_rules(self):
        return (self.local_root / self._data['iptables']['v4']).read_text()


SETTINGS = RedisSettings()


class RedisTasks(DeployComponentTasks, SystemdTasksMixin):
    SETTINGS = SETTINGS

    # TODO: add packages
    # TODO: add kernel systemd tasks to run settings on boot
    # # /proc/sys/net/core/somaxconn to 5000 (need command)
    async def get_iptables_template(self):
        return self.settings.iptables_v4_rules

    @register
    async def build(self):
        await self._create_user()

        async with self._cd(self.settings.build_dir, temporary=True):
            for package, url in self.settings.packages.items():
                await self._download_and_unpack(url, Path('.', package))

            async with self._cd('redis'):
                await self._run('make distclean')
                await self._run("make -j$(nproc) MALLOC=jemalloc")
                await self._run(
                    f"make PREFIX={self.settings.root_abs} install")

    @register
    async def sync(self):
        await self._upload_template(
            self.settings.config_template, self.settings.config_path)
        await self._sync_systemd_units()

    @register
    async def setup(self):
        await self.build()
        await self.sync()
        await self.start()
