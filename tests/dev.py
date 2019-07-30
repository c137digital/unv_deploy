from unv.app.settings import ComponentSettings

SETTINGS = ComponentSettings.create({
    'deploy': {
        'tasks': [
            'unv.deploy.components.nginx:NginxTasks',
            'unv.deploy.components.app:AppTasks',
            'unv.deploy.components.vagrant:VagrantTasks',
            'unv.deploy.components.iptables:IPtablesTasks',
            'unv.deploy.components.redis:RedisTasks'
        ],
        'hosts': {
            'test.1': {
                'public_ip': '10.10.30.10',
                'components': ['vagrant', 'nginx', 'iptables', 'redis'],
                'settings': {
                    'nginx': {'geoip2db': {'lang': 'ru'}}
                },
                'provider': 'vagrant'
            },
            'test.2': {
                'public_ip': '10.10.30.11',
                'components': ['vagrant', 'web', 'iptables', 'redis'],
                'provider': 'vagrant'
            },
            'test.3': {
                'public_ip': '10.10.30.12',
                'components': ['vagrant', 'app', 'nginx'],
                'settings': {
                    'nginx': {
                        'geoip2db': {'lang': 'en'},
                        'subproxy': True,
                    }
                },
                'provider': 'vagrant'
            },
        },
        'components': {
            'app': {
                'systemd': {
                    'instances': {'count': 0, 'percent': 50}
                }
            },
            'nginx': {
                'geoip2': True,
                'geoip2db': {
                    'lang': 'ru'
                }
            }
        }
    }
})
