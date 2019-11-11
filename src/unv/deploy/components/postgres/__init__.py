from pathlib import Path

from unv.deploy.tasks import (
    DeployComponentSettings, DeployComponentTasks, register
)


class PostgresSettings(DeployComponentSettings):
    NAME = 'postgres'
    SCHEMA = {
        'user': {'type': 'string', 'required': True},
        'work_dir': {'type': 'string', 'required': True},
        'build_dir': {'type': 'string', 'required': True},
        'sources': {
            'type': 'dict',
            'schema': {
                'postgres': {'type': 'string', 'required': True},
            },
            'required': True
        },
    }
    DEFAULT = {
        'user': 'postgres',
        'work_dir': '',
        'build_dir': 'build',
        'sources': {
            'postgres': 'https://ftp.postgresql.org/pub/source'
                        '/v12.0/postgresql-12.0.tar.gz',
        },
        'contrib': {
            # https://www.postgresql.org/docs/current/adminpack.html
            'adminpack': {'enabled': True},

            # https://www.postgresql.org/docs/current/amcheck.html
            'amcheck': {'enabled': True},

            # https://www.postgresql.org/docs/current/auth-delay.html
            'auth_delay': {'enabled': True},

            # https://www.postgresql.org/docs/current/auto-explain.html
            'auto_explain': {'enabled': True},

            # https://www.postgresql.org/docs/current/bloom.html
            'bloom': {'enabled': True},

            # btree_gin, https://www.postgresql.org/docs/current/btree-gin.html
            # btree_gist, citext, cube
        }
    }

    @property
    def sources(self):
        return self._data['sources']

    @property
    def work_dir(self):
        return self._data['work_dir']

    @property
    def build_dir(self):
        return self._data['build_dir']


class PostgresTasks(DeployComponentTasks):
    SETTINGS = PostgresSettings()

    @register
    async def build(self):
        await self._create_user()

        # await self._apt_install(
        #     'build-essential flex bison libreadline6-dev '
        #     'zlib1g-dev libossp-uuid-dev'
        # )
        # await self._mkdir(self.settings.build_dir, delete=True)
        async with self._cd(self.settings.build_dir):
            # for package, url in self.settings.sources.items():
            #     await self._download_and_unpack(url, Path('.', package))
            async with self._cd('postgres'):
                async with self._cd('contrib'):
                    await self._run('make')
                # for contrib in str(await self._run('ls contrib')).split():
                #     if contrib 
                #     async with self._cd(f'contrib/{contrib}'):
                #         await self._run('ls')
                await self._run('./configure --prefix=/home/postgres/app')
                await self._run('make')
                await self._run('make install')
