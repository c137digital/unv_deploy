from fabric.api import env, task


@task
def dev():
    """Shortcut for load:app.deploy.development + hosts"""
    pass


@task
def prod():
    """Shortcut for load:secure.deploy.production + hosts"""
    pass


@task
def host(host_filter=''):
    env.user = env.DEPLOY['user']
    env.hosts = [
        '{}:{}'.format(host_['public'], host_.get('ssh', 22))
        for name, host_ in env.HOSTS.items()
        if not host_filter or name.startswith(host_filter)
    ]
    env.key_filename = str(env.KEYS['private'])
