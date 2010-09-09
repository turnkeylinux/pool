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
