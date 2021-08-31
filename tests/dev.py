import json
import pathlib
# from unv.utils.collections import update_dict_recur

# TODO: add support for auto task assign per namespace -> we can replace any
# TODO: after postgres rebuild copy data folder (stop postgres -> copy folder) -> build new version
# TODO: fix geoip build for nginx (?) do we need this (?) -> probably no
# TODO: we need to mount media folder of all (backend - nginx - nfs (?))
# TODO: migrate data from one server to other

VAGRANT_VM = 'parallels'
SETTINGS = {'deploy': {
    'env': 'dev',
    'services': {
        'backend': [{
            'hosts': [
                {
                    'name': 'django',
                    'count': 1,
                    'provider': 'vagrant',
                    'cpus': 1,
                    'ram': 512,
                    'vm': VAGRANT_VM
                }
            ],
            'components': {
                'app': {
                    'systemd': {
                        'instances': {'count': 2}
                    }
                },
                'python': {},
                'iptables': {
                    'allow': ['nginx'],
                }
            },
        }],
        'frontend': [{
            'hosts': [
                {
                    'name': 'nginx',
                    'provider': 'vagrant',
                    'cpus': 1,
                    'ram': 512,
                    'vm': VAGRANT_VM
                }
            ],
            'components': {
                'nginx': {},
                'iptables': {}
            },
        }],
        'db': [
            {
                'hosts': [
                    {
                        'name': 'postgres',
                        'count': 1,
                        'provider': 'vagrant',
                        'vm': VAGRANT_VM
                    }
                ],
                'components': {
                    'postgres': {},
                    'iptables': {
                        'allow': ['app']
                    }
                }
            },
            {
                'hosts': [
                    {
                        'name': 'redis',
                        'count': 1,
                        'provider': 'vagrant',
                        'vm': VAGRANT_VM
                    }
                ],
                'components': {
                    'redis': {'listen_private_ip': True},
                    'iptables': {
                        'allow': ['app']
                    }
                }
            }
        ]
    }
}}
