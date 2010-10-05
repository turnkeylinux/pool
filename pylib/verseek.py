from subprocess import *

class Error(Exception):
    pass

def list(srcpath):
    command = ["verseek", "-l", srcpath]
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    output = p.communicate()[0]

    if p.returncode != 0:
        raise Error("failed command: " + " ".join(command))

    return output.strip().split("\n")

def seek(srcpath, version=None):
    command = ["verseek", srcpath]
    if version:
        command += [ version ]
    error = call(command)
    if error:
        raise Error("failed command: " + " ".join(command))

