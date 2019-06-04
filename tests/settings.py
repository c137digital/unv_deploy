from unv.app.settings import ComponentSettings

SETTINGS = ComponentSettings.create({
    'deploy': {
        'tasks': [
            'unv.deploy.components.nginx:NginxComponentTasks',
            'unv.deploy.components.pyapp:PyAppComponentTasks',
            'unv.deploy.components.vagrant:VagrantTasks',
            'unv.deploy.components.iptables:IPtablesDeployTasks'
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
                    'instances': {'count': 0, 'cpu_count_percent': 50}
                }
            }
        }
    }
})
