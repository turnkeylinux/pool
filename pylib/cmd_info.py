#!/usr/bin/python
"""Prints list of registered stocks"""
import sys
import pool

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    try:
        pool.Pool().print_info()
    except pool.Error, e:
        fatal(e)

if __name__ == "__main__":
    main()
