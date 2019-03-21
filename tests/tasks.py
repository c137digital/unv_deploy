import sys

from unv.utils.tasks import TasksManager, register
from unv.deploy.tasks import DeployTasksBase


class AppTasks(DeployTasksBase):
    @register
    async def some(self):
        result = await self.ssh('10.50.25.11', '22', 'root', 'ls -la')
        print('res', result)

    @register(parallel=True)
    async def benchmark(self):
        response = await self.run('expr 2 + 2')
        return await self.run(f'expr {response} + 2')

if __name__ == '__main__':
    manager = TasksManager()
    manager.register(AppTasks)
    manager.run(' '.join(sys.argv[1:]))
