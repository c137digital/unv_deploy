import os
import pwd

from fabric.api import task, runs_once

task = runs_once(task)()


def get_local_username():
    return pwd.getpwuid(os.getuid())[0]
