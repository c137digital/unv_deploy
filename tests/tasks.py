import sys

from unv.utils.tasks import register
from unv.deploy.tasks import DeployTasksBase, DeployTasksManager, parallel


class AppTasks(DeployTasksBase):
    @register
    @parallel
    async def benchmark(self):
        response = await self.run('expr 2 + 2')
        print(self.host, 'before sleep')
        await self.run('sleep 3')
        response = await self.run(f'expr {response} + 2')
        print(self.host, response)
        return response


if __name__ == '__main__':
    manager = DeployTasksManager()
    manager.register(AppTasks)
    manager.select_component('test')
    manager.run(' '.join(sys.argv[1:]))
