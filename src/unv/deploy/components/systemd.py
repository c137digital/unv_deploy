from pathlib import Path

from unv.utils.tasks import register

from ..helpers import as_root


class SystemdTasksMixin:
    async def _get_systemd_services(self):
        systemd = self.settings.systemd
        name = systemd['name']
        count = await self._calc_instances_count(**systemd['instances'])
        for instance in range(1, count + 1):
            service = systemd.copy()
            service['name'] = name.format(instance=instance)
            service['instance'] = instance
            yield service

    @as_root
    async def _sync_systemd_units(self):
        services = [service async for service in self._get_systemd_services()]
        for service in services:
            service_path = Path('/etc', 'systemd', 'system', service['name'])
            context = {'instance': service['instance']}.copy()
            context.update(service.get('context', {}))
            path = service['template']
            if not str(path).startswith('/'):
                path = (self.settings.local_root / service['template'])
                path = path.resolve()
            await self._upload_template(path, service_path, context)

        await self._run('systemctl daemon-reload')

        for service in services:
            if service['boot']:
                await self._run(f'systemctl enable {service["name"]}')

    async def _systemctl(self, command: str, display=False):
        results = {}
        async for service in self._get_systemd_services():
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
            print(result)
