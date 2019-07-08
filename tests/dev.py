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
            'vagrant.1': {
                'public_ip': '10.10.20.10',
                'components': ['app', 'nginx', 'iptables', 'redis'],
                # 'tags': ['app_settings_1'],
                'provider': 'vagrant'
            },
            'vagrant.2': {
                'public_ip': '10.10.20.11',
                'components': ['app', 'nginx', 'iptables', 'redis'],
                # 'tags': ['app_settings_2'],
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
                'geoip2db': {
                    'lang': 'ru'
                }
            }
        }
        # 'tags': {
        #     'test_tag': {
        #         'app': {
        #             # TODO: updated per host config globally (settings patched)
        #             # even deploy settings, so ve can mark tags to deploy
        #             'components': [],
        #             'deploy': {
        #                 'nginx': {
        #                     'geoip2db': {
        #                         'lang': 'en'
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # }
    }
})
