from pathlib import Path

TEST_NGINX_CONFIG = str((Path(__file__).parent / 'testnginx.conf').resolve())

SETTINGS = {
    'deploy': {
        'hosts': {
            # 'vagrant.app.1': {
            #     'public_ip': '10.10.10.11',
            #     'private_ip': '10.10.10.11',
            #     'port': 22,
            #     'components': ['app', 'iptables']
            # },
            # 'vagrant.app.2': {
            #     'public_ip': '10.10.10.12',
            #     'private_ip': '10.10.10.12',
            #     'port': 22,
            #     'components': ['app', 'iptables']
            # },
            'vagrant': {
                'public_ip': '10.10.10.10',
                'private_ip': '10.10.10.10',
                'port': 22,
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
}
