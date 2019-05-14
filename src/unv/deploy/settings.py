from unv.app.core import create_component_settings


DEFAULT = {
    'hosts': {},
    'components': {},
}

SCHEMA = {
    'hosts': {
        'type': 'dict',
        'keyschema': {'type': 'string'},
        'valueschema': {
            'type': 'dict',
            'schema': {
                'public_ip': {'type': 'string'},
                'private_ip': {'type': 'string'},
                'port': {'type': 'integer', 'required': True},
                'components': {'type': 'list', 'schema': {'type': 'string'}}
            }
        }
    },
    'components': {'allow_unknown': True}
}

SETTINGS = create_component_settings('deploy', DEFAULT, SCHEMA)
