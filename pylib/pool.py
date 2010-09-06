import os
from os.path import *

import shutil

from paths import Paths

class Error(Exception):
    pass

class PoolPaths(Paths):
    def __init__(self, path=None):
        if path is None:
            path = os.getenv("POOL_DIR", os.getcwd())
            
        path = join(realpath(path), ".pool")
        Paths.__init__(self, path,
                       ['pkgcache',
                        'stock',
                        'build'])

        self.build = Paths(self.build,
                           ['root',
                            'logs'])

def mkdir(p):
    os.makedirs(str(p))

class Pool:
    @classmethod
    def init_create(cls, buildroot, path=None):
        paths = PoolPaths(path)

        if not isdir(buildroot):
            raise Error("buildroot `%s' is not a directory" % buildroot)
        
        mkdir(paths.stock)
        mkdir(paths.pkgcache)
        mkdir(paths.build)
        mkdir(paths.build.logs)
        os.symlink(buildroot, paths.build.root)

        return cls(path)
    
    def __init__(self, path=None):
        self.paths = PoolPaths(path)
        if not exists(self.paths.path):
            raise Error("no pool found (POOL_DIR=%s)" % dirname(self.paths.path))

    def register(self, dir):
        if not isdir(dir):
            raise Error("not a directory `%s'" % dir)
        
        stock_name = basename(abspath(dir))
        stock_path = join(self.paths.stock, stock_name, "path")
        
        if lexists(stock_path):
            raise Error("stock already registered under name `%s'" % stock_name)
        
        mkdir(dirname(stock_path))
        os.symlink(realpath(dir), stock_path)
        
    def unregister(self, dir):
        stock_name = basename(abspath(dir))
        stock_path = join(self.paths.stock, stock_name, "path")

        if not lexists(stock_path) or os.readlink(stock_path) != realpath(dir):
            raise Error("no matches for unregister")

        shutil.rmtree(dirname(stock_path))

    def print_info(self):
        for d in os.listdir(self.paths.stock):
            print os.readlink(join(self.paths.stock, d, "path"))
        

