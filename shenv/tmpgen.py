'''
Created on Jan 25, 2011

@author: Arnold
'''
import sys
import os
import random
from os import path

_MASK_TEMP_DIR_BAD = 0x10000000;
_MASK_PRINTF_ERROR = 0x20000000;
_MASK_FILE_CREATION_FAILED = 0x30000000;
_MASK_STRCOPY_ERROR = 0x40000000;
_MASK_BAD_ARGS = 0x50000000;

def randfnum():
    return random.randint(0x1000,0xFFFFFFF)

def trycreate(filename):
    filename = path.abspath(filename)
    try:
        fd = os.open(filename, os.O_CREAT | os.O_EXCL)
    except os.error:
        return False
    os.close(fd)
    return True
    
def gentemp(pr,sf,dir):
    dir = os.path.abspath(dir)
    for _ in range(0,1000):
        num = randfnum()
        fname = "{0}{1}{2}".format(pr,num,sf)
        fpath = os.path.join(dir,fname)
        path = os.path.normpath(fpath)
        if trycreate(path):
            print(fpath,file=sys.stdout)
            return num
    print('Unable to generate file in {0}'.format(dir),file=sys.stderr)
    return _MASK_FILE_CREATION_FAILED
    
    
def main(argv):
    if (len(argv)!=4):
        print('Usage: python <script> <prefix> <suffix> <dir>')
        print()
        print('Arguments were: ',tuple(argv))
        return _MASK_BAD_ARGS | randfnum()
    
    random.seed(None)
    _,pr,sf,dir = sys.argv
    
    return gentemp(pr, sf, dir)
    
if __name__ == '__main__':
    ec = main(sys.argv)
    sys.exit(ec)
