from pathlib import Path

from unv.deploy.helpers import ComponentSettingsBase, get_components, get_hosts
from unv.deploy.tasks import DeployComponentTasksBase, register
from unv.deploy.components.systemd import SystemdTasksMixin


class IPtablesComponentSettings(ComponentSettingsBase):
    NAME = 'iptables'
    DEFAULT = {
        'bin': '/sbin/iptables-restore',
        'user': 'root',
        'rules': {
            'template': 'ipv4.rules',
            'name': 'ipv4.rules'
        },
        'systemd': {
            'template': 'app.service',
            'name': 'iptables.service',
            'boot': True,
            'instances': {'count': 1}
        }
    }

    @property
    def rules_template(self):
        return self.local_root / self._data['rules']['template']

    @property
    def rules(self):
        return Path('/etc') / self._data['rules']['name']

    @property
    def bin(self):
        return f"{self._data['bin']} {self.rules}"


class IPtablesDeployTasks(DeployComponentTasksBase, SystemdTasksMixin):
    NAMESPACE = 'iptables'
    SETTINGS = IPtablesComponentSettings()

    @register
    async def sync(self):
        await self._upload_template(
            self._settings.rules_template, self._settings.rules,
            {
                'get_hosts': get_hosts,
                'components': get_components(self._public_ip)
            }
        )
        await self._sync_systemd_units()
