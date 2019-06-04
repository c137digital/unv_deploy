from unv.app.settings import ComponentSettings

SETTINGS = ComponentSettings.create({
    'deploy': {
        'tasks': {
            'nginx': 'unv.deploy.components.nginx:NginxComponentTasks',
            'app': 'unv.deploy.components.app:AppComponentTasks',
            'vagrant': 'unv.deploy.components.vagrant:VagrantTasks',
            'iptables': 'unv.deploy.components.iptables:IPtablesDeployTasks'
        },
        'hosts': {
            'vagrant': {
                'public_ip': '10.10.10.10',
                'components': ['app', 'nginx', 'iptables']
            }
        },
        'components': {
            'app': {
                'systemd': {
                    'instances': {'count': 0, 'percent': 50}
                }
            }
        }
    }
})
