import sys
import os
import pty
import time

master, slave = pty.openpty()
pid = os.fork()
if pid == 0:
    os.close(slave)
    while True:
        print "child"
        os.write(master, "ping")
        buf = os.read(master, 4)
        if not buf:
            break
        print "master read: " + buf

    sys.exit(0)
        
else:
    os.close(master)
    buf = os.read(slave, 4)
    if buf:
        print "slave read: " + buf
        os.write(slave, "pong")
        os.close(slave)
    time.sleep(5)
        
        

    
