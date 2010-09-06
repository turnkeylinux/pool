"""register a package stock into the pool"""
import sys
import help
import pool

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <dir>" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    args = sys.argv[1:]
    
    if len(args) != 1:
        usage("bad number of arguments")

    dir = args[0]
    try:
        pool.Pool().register(dir)
    except pool.Error, e:
        fatal(e)
        
if __name__=="__main__":
    main()

