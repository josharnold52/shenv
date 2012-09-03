#-------------------------------------------------------------------------------
# Name:        test
# Purpose:
#
# Author:      Arnold
#
# Created:     15/01/2011
# Copyright:   (c) Arnold 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import sys
import unittest

from shenv.test import shell_test
from shenv.test import core_test

def main():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    suite.addTest(loader.loadTestsFromModule(shell_test))
    suite.addTest(loader.loadTestsFromModule(core_test))

    ttr = unittest.TextTestRunner()
    ttr.verbosity = 2
    ttr.run(suite)

    pass

if __name__ == '__main__':
    main()
