import sys

from unv.deploy.tasks import DeployTasksManager
from unv.deploy.components.nginx import NginxComponentTasks
from unv.deploy.components.app import AppComponentTasks
from unv.deploy.components.vagrant import VagrantTasks
from unv.deploy.components.iptables import IPtablesDeployTasks


if __name__ == '__main__':
    manager = DeployTasksManager()
    manager.register(AppComponentTasks)
    manager.register(NginxComponentTasks)
    manager.register(VagrantTasks)
    manager.register(IPtablesDeployTasks)
    manager.run(' '.join(sys.argv[1:]))
