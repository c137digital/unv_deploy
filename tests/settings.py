from pathlib import Path

TEST_NGINX_CONFIG = str((Path(__file__).parent / 'testnginx.conf').resolve())

SETTINGS = {
    'deploy': {
        'hosts': {
            'vagrant': {
                'public_ip': '10.51.21.11',
                'private_ip': '0.0.0.0',
                'port': 22,
                'components': ['test', 'nginx', 'app', 'iptables']
            }
        },
        'components': {
            'app': {
                'systemd': {
                    'instances': {'count': 0, 'cpu_count_percent': 50}
                }
            },
            'test': {
                'user': 'someuser6'
            }
        }
    }
}
