import os
import shutil
import errno

def hardlink_or_copy(src, dst):
    try:
        os.link(src, dst)
    except OSError, e:
        if e[0] != errno.EXDEV:
            raise
        shutil.copyfile(src, dst)

def mkdir(path):
    path = str(path)
    try:
        os.makedirs(path)
    except OSError, e:
        if e[0] != errno.EEXIST:
            raise
