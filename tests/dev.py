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
            'vagrant': {
                'public_ip': '10.10.10.10',
                'components': ['app', 'nginx', 'iptables', 'redis']
            }
        },
        'components': {
            'app': {
                'systemd': {
                    'instances': {'count': 0, 'percent': 50}
                }
            },
            'nginx': {
                'geoip2db': {
                    'lang': 'ru'
                }
            }
        },
        'tags': {
            'test_tag': {
                'app': {
                    # TODO: updated per host config globally (settings patched)
                    # even deploy settings, so ve can mark tags to deploy
                    'components': [],
                    'deploy': {
                        'nginx': {
                            'geoip2db': {
                                'lang': 'en'
                            }
                        }
                    }
                }
            }
        }
    }
})
