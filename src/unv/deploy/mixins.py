from pathlib import Path

from unv.utils.tasks import register

from .helpers import as_root


class SystemdTasksMixin:
    @property
    def _systemd_services(self):
        systemd = self._settings.systemd
        for template, original in systemd['services'].items():
            name = original['name']
            instances = original.get('instances', 1)
            for instance in range(1, instances + 1):
                service = original.copy()
                service['name'] = name.format(instance=instance)
                service['instance'] = instance
                service['template'] = template
                yield service

    @as_root
    async def _setup_systemd_units(self):
        for service in self._systemd_services:
            service_path = Path('/etc', 'systemd', 'system', service['name'])
            await self._upload_template(
                (self._settings.local_root / service['template']).resolve(),
                service_path,
                {'instance': service['instance'], 'settings': self._settings}
            )
            print(await self._run(f"cat {service_path}"))

        await self._run('systemctl daemon-reload')

        for service in self._systemd_services:
            if service['boot']:
                await self._run(f'systemctl enable {service["name"]}')

    async def _systemctl(self, command: str):
        for service in self._systemd_services:
            if 'manage' in service and not service['manage']:
                continue

            await self._sudo(f'systemctl {command} {service["name"]}')

    @register
    async def start(self):
        await self._systemctl('start')

    @register
    async def stop(self):
        await self._systemctl('stop')

    @register
    async def restart(self):
        await self._systemctl('restart')

    @register
    async def status(self):
        print(await self._systemctl('status'))
