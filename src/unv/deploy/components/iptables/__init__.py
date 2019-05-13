import jinja2

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
        context = {
            'get_hosts': get_hosts,
            'components': get_components(self._public_ip)
        }
        rendered = []
        for task in self.get_all_deploy_tasks():
            get_template = getattr(task, 'get_iptables_template', None)
            if get_template is not None:
                template = jinja2.Template(await get_template())
                context['deploy'] = task
                rendered.append(template.render(context))
                context.pop('deploy')
        context['components_templates'] = "\n".join([
            line.strip() for line in rendered
        ])

        await self._upload_template(
            self.settings.rules_template, self.settings.rules, context)
        await self._sync_systemd_units()
