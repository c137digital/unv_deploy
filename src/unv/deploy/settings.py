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
                'public': {'type': 'string'},
                'private': {'type': 'string'},
                'components': {'type': 'list', 'schema': {'type': 'string'}}
            }
        }
    },
    'components': {'allow_unknown': True}
}

SETTINGS = create_component_settings('deploy', DEFAULT, SCHEMA)
