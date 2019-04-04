from pathlib import Path

TEST_NGINX_CONFIG = str((Path(__file__).parent / 'testnginx.conf').resolve())

SETTINGS = {
    'deploy': {
        'hosts': {
            'vagrant': {
                '1': {
                    'public': '10.51.21.11',
                    'private': '0.0.0.0',
                    'components': ['test', 'nginx']
                }
            }
        },
        'components': {
            'nginx': {
                'user': 'nginx',
                'configs': {
                    TEST_NGINX_CONFIG: 'conf/apps/test.conf'
                }
            },
            'test': {
                'user': 'someuser6'
            }
        }
    }
}
