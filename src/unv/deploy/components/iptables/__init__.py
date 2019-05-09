from unv.deploy.helpers import ComponentSettingsBase
from unv.deploy.tasks import DeployTasksBase
from unv.deploy.components.systemd import SystemdTasksMixin


class IPtablesComponentSettings(ComponentSettingsBase):
    NAME = 'iptables'
    DEFAULT = {
        'bin': '/sbin/iptables-restore',
        'user': 'root',
        'rules': 'ipv4.rules',
        'systemd': {
            'template': 'app.service',
            'name': 'iptables_.service',
            'boot': True,
            'instances': {'count': 1}
        }
    }


class IPtablesDeployTasks(DeployTasksBase, SystemdTasksMixin):
    SETTINGS = IPtablesComponentSettings()
