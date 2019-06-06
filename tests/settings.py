from unv.app.settings import ComponentSettings

SETTINGS = ComponentSettings.create({
    'deploy': {
        'tasks': [
            'unv.deploy.components.nginx:NginxTasks',
            'unv.deploy.components.app:AppTasks',
            'unv.deploy.components.vagrant:VagrantTasks',
            'unv.deploy.components.iptables:IPtablesTasks'
        ],
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
