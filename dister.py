'''
Created on Jan 24, 2011

@author: Arnold
'''

from distutils.command.bdist_msi import bdist_msi
from distutils.core import Distribution, run_setup

def main():
    run_setup()

if __name__ == '__main__':
    main()