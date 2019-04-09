from pathlib import Path

from unv.utils.tasks import register

from ..helpers import as_root


class SystemdTasksMixin:
    @property
    def _systemd_services(self):
        systemd = self._settings.systemd
        for template, original in systemd['services'].items():
            name = original.get('name', template)
            instances = original.get('instances', 1)
            for instance in range(1, instances + 1):
                service = original.copy()
                service['name'] = name.format(instance=instance)
                service['instance'] = instance
                service['template'] = template
                yield service

    @as_root
    async def _sync_systemd_units(self):
        for service in self._systemd_services:
            service_path = Path('/etc', 'systemd', 'system', service['name'])
            context = {
                'instance': service['instance'],
                'settings': self._settings
            }.copy()
            context.update(service.get('context', {}))
            path = service['template']
            if not str(path).startswith('/'):
                path = (self._settings.local_root / service['template'])
                path = path.resolve()
            await self._upload_template(path, service_path, context)
            print(await self._run(f"cat {service_path}"))

        await self._run('systemctl daemon-reload')

        for service in self._systemd_services:
            if service['boot']:
                await self._run(f'systemctl enable {service["name"]}')

    async def _systemctl(self, command: str, display=False):
        results = {}
        for service in self._systemd_services:
            if 'manage' in service and not service['manage']:
                continue

            result = await self._sudo(f'systemctl {command} {service["name"]}')
            results[service['name']] = result
        return results

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
        results = await self._systemctl('status')
        for service, result in results.items():
            print(f'Service: [{service}] ->')
            print(result)
