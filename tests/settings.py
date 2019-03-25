SETTINGS = {
    'deploy': {
        'hosts': {
            'vagrant': {
                '1': {
                    'public': '10.50.25.11',
                    'private': '0.0.0.0',
                    'components': ['test']
                },
                '2': {
                    'public': '10.50.25.10',
                    'private': '0.0.0.0',
                    'components': ['test']
                },
            }
        },
        'components': {
            'test': {
                'user': 'vagrant'
            }
        }
    }
}
