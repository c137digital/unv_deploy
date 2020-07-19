from pathlib import Path

from unv.deploy.tasks import (
    DeployComponentSettings, DeployComponentTasks, register
)
from unv.deploy.components.systemd import SystemdTasksMixin


class PostgresSettings(DeployComponentSettings):
    NAME = 'postgres'
    SCHEMA = {
        'user': {'type': 'string', 'required': False},
        'systemd': SystemdTasksMixin.SCHEMA,
        'root': {'type': 'string', 'required': True},
        'password': {'type': 'string', 'required': True},
        'build_dir': {'type': 'string', 'required': True},
        'data_dir': {'type': 'string', 'required': True},
        'locale': {'type': 'string', 'required': True},
        'configs': {'type': 'list', 'schema': {'type': 'string'}},
        'sources': {
            'type': 'dict',
            'schema': {
                'postgres': {'type': 'string', 'required': True},
            },
            'required': True
        },
    }
    DEFAULT = {
        'systemd': {
            'template': 'server.service',
            'name': 'postgres.service',
            'boot': True,
            'instances': {'count': 1}
        },
        'root': 'app',
        'password': 'postgres',
        'build_dir': 'build',
        'data_dir': 'data',
        'locale': 'en_US.UTF-8',
        'sources': {
            'postgres': 'https://ftp.postgresql.org/pub/source'
                        '/v12.1/postgresql-12.1.tar.gz',
        },
        'configs': ['pg_hba.conf', 'postgresql.conf'],
        # 'databases': {
        #     'user_name': 'db1'
        # }
        # 'contrib': {
        #     # https://www.postgresql.org/docs/current/adminpack.html
        #     'adminpack': {'enabled': True},

        #     # https://www.postgresql.org/docs/current/amcheck.html
        #     'amcheck': {'enabled': True},

        #     # https://www.postgresql.org/docs/current/auth-delay.html
        #     'auth_delay': {'enabled': True},

        #     # https://www.postgresql.org/docs/current/auto-explain.html
        #     'auto_explain': {'enabled': True},

        #     # https://www.postgresql.org/docs/current/bloom.html
        #     'bloom': {'enabled': True},

        #     # btree_gin, https://www.postgresql.org/docs/current/btree-gin.html
        #     # btree_gist, citext, cube
        # }
    }

    @property
    def sources(self):
        return self._data['sources']

    @property
    def build_dir(self):
        return self._data['build_dir']

    @property
    def data_dir(self):
        return self.root_abs / self._data['data_dir']

    @property
    def configs(self):
        for config in self._data['configs']:
            yield config, self.local_root / config

    @property
    def locale(self):
        return self._data['locale']


class PostgresTasks(DeployComponentTasks, SystemdTasksMixin):
    SETTINGS = PostgresSettings()

    @register
    async def build(self):
        await self._create_user()

        await self._apt_install(
            'build-essential flex bison libreadline6-dev '
            'zlib1g-dev libossp-uuid-dev libsystemd-dev'
        )
        async with self._cd(self.settings.build_dir, temporary=True):
            for package, url in self.settings.sources.items():
                await self._download_and_unpack(url, Path('.', package))
            async with self._cd('postgres'):
                await self._run(
                    f'./configure --with-systemd '
                    f'--prefix={self.settings.root_abs}'
                )

                async with self._cd('contrib'):
                    await self._run('make')

                # TODO: add custom contrib packages configuration
                # for contrib in str(await self._run('ls contrib')).split():
                #     if contrib 
                #     async with self._cd(f'contrib/{contrib}'):
                #         await self._run('ls')

                await self._run('make -j$(nproc)')
                await self._run('make install')

    @register
    async def sync(self):
        for name, config_path in self.settings.configs:
            await self._upload_template(
                config_path, self.settings.data_dir / name)
        await self._sync_systemd_units()

    @register
    async def make_data_dir(self):
        init_db_bin = self.settings.root_abs / 'bin' / 'initdb'
        await self._run(
            f'{init_db_bin} -D {self.settings.data_dir} '
            f'--locale {self.settings.locale}'
        )

    @register
    async def psql(self, command: str = ''):
        if command:
            command = f' -c "{command}"'
        return await self._run(
            self.settings.root_abs / 'bin' / f'psql{command}',
            interactive=not bool(command)
        )

    @register
    async def create_user(self, name, password=''):
        password = password or ''
        await self.psql(
            f"CREATE USER {name} WITH ENCRYPTED PASSWORD '{name}';")

    @register
    async def create_database(self, name, user=''):
        user = user or name
        await self.psql(f'CREATE DATABASE {name};')
        await self.psql(f'GRANT ALL PRIVILEGES ON DATABASE {name} TO {user};')

    @register
    async def setup(self):
        await self.build()
        await self.make_data_dir()
        await self.sync()
        await self.start()

        # TODO: create user from settings
        # await self.create_user('project_user')
        # await self.create_database('project_db', 'project_user')
