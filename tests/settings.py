from pathlib import Path

TEST_NGINX_CONFIG = str((Path(__file__).parent / 'testnginx.conf').resolve())

SETTINGS = {
    'deploy': {
        'hosts': {
            'vagrant': {
                '1': {
                    'public': '10.50.25.10',
                    'private': '0.0.0.0',
                    'components': ['test', 'nginx']
                },
                # '2': {
                #     'public': '10.50.25.10',
                #     'private': '0.0.0.0',
                #     'components': ['test']
                # },
            }
        },
        'components': {
            'nginx': {
                'user': 'someuser10',
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
