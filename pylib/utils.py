import os
import errno
import shutil

def hardlink_or_copy(src, dst):
    try:
        os.link(src, dst)
    except OSError, e:
        if e[0] != errno.EXDEV:
            raise
        shutil.copyfile(src, dst)

def makedirs(path, mode=None):
    try:
        if mode is None:
            os.makedirs(path)
        else:
            os.makedirs(path, mode)

    except OSError, e:
        if e[0] != errno.EEXIST:
            raise
        
