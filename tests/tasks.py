import sys
import pathlib

from unv.utils.tasks import register
from unv.deploy.tasks import DeployTasksBase, DeployTasksManager, parallel
from unv.deploy.packages import NginxTasks


class AppTasks(DeployTasksBase):
    # @register
    # @parallel
    # async def benchmark(self):
    #     response = await self.run('expr 2 + 2')
    #     print(self.host, 'before sleep')
    #     # await self.run('sleep 3')
    #     response = await self.run(f'expr {response} + 2')
    #     print(self.host, response)

    #     await self.put(pathlib.Path('tests/test.txt'), pathlib.Path('~/'))
    #     print(await self.run('ls -la'))
    #     return response

    @register
    async def setup(self):
        await self._create_user()
        await self._run('ls -la')
        await self._mkdir('build')

        with self._cd('build'):
            await self._download_and_unpack(
                'https://www.python.org/ftp/python/3.7.2/Python-3.7.2.tar.xz')
            print(await self._run('ls -la'))

        await self._upload_template(
            pathlib.Path('tests/test.conf'),
            pathlib.Path('test1.conf'),
            {'name': 'world'}
        )

        print(await self._run('ls -la'))

        await self._apt_install('redis-server')


if __name__ == '__main__':
    manager = DeployTasksManager()
    manager.register(AppTasks)
    manager.register(NginxTasks)
    manager.select_component('test')
    manager.run(' '.join(sys.argv[1:]))
