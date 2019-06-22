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
        'root': {'type': 'string', 'required': True},
        'packages': {
            'type': 'dict',
            'schema': {
                'redis': {'type': 'string', 'required': True},
            },
            'required': True
        },
        'port': {'type': 'integer', 'required': True}
    }
    DEFAULT = {
        'systemd': {
            'template': 'server.service',
            'name': 'nginx.service',
            'boot': True,
            'instances': {'count': 1}
        },
        'config': {
            'template': 'server.conf',
            'name': 'redis.conf'
        },
        'root': 'app',
        'packages': {
            'redis': 'http://download.redis.io/releases/redis-5.0.5.tar.gz'
        },
        'port': 5673
    }

    @property
    def build_dir(self):
        return self.root / 'build'

    @property
    def packages(self):
        return self._data['packages']

    @property
    def config_template(self):
        pass

    @property
    def port(self):
        return self._data['port']

    @property
    def iptables_v4_rules(self):
        return (self.local_root / self._data['iptables']['v4']).read_text()


class RedisTasks(DeployComponentTasks, SystemdTasksMixin):
    SETTINGS = RedisSettings()

    # TODO: add packages
    # async def get_iptables_template(self):
    #     return self.settings.iptables_v4_rules

    @register
    async def build(self):
        await self._create_user()

        # TODO: move fix packages
        await self._sudo('apt-get update')
        await self._sudo('apt-get build-dep redis -y')

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
        # await self.start()
