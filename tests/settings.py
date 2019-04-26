from pathlib import Path

TEST_NGINX_CONFIG = str((Path(__file__).parent / 'testnginx.conf').resolve())

SETTINGS = {
    'deploy': {
        'hosts': {
            'vagrant': {
                'public': '10.51.21.11',
                'private': '0.0.0.0',
                'components': ['test', 'nginx', 'app']
            }
        },
        'components': {
            'app': {
                'user': 'app',
                'systemd': {
                    'instances': {'count': 0, 'cpu_count_percent': 50}
                }
            },
            'nginx': {
                'user': 'nginx',
                'configs': {
                    TEST_NGINX_CONFIG: 'apps/test.conf'
                }
            },
            'test': {
                'user': 'someuser6'
            }
        }
    }
}
