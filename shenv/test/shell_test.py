#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Arnold
#
# Created:     15/01/2011
# Copyright:   (c) Arnold 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import io
import sys
import unittest

from shenv import shell
from shenv.shell import Win32CmdSyntax

class TestWin32CmdSyntax(unittest.TestCase):
    longMessage = True
    syntax = shell.Win32CmdSyntax()

    def _assert_echo(self, arg, expect):
        self.assertEqual(expect,self.syntax.echo(arg)
            ,'testing echo of {0}'.format(repr(arg)))
        
    def testecho(self):
        self._assert_echo('','ECHO.')
        self._assert_echo('a6d hje9','ECHO a6d hje9')
        self._assert_echo('^<>|&%','ECHO ^^^<^>^|^&^%')
        self._assert_echo('^^^<>>>|&%','ECHO ^^^^^^^<^>^>^>^|^&^%')
        self._assert_echo('^^^<>>> abc|&%','ECHO ^^^^^^^<^>^>^> abc^|^&^%')
        pass

    def _assert_setvar(self, name, value, expect):
        self.assertEqual(expect,self.syntax.setvar(name,value)
            ,'testing setvar of {0},{1}'.format(repr(name),repr(value)))
        
    def testsetvar(self):
        self._assert_setvar('A','B','SET A=B')
        self._assert_setvar('ESC','>','SET ESC=^>')
        self._assert_setvar('^','>','SET ^^=^>')
        pass

    def _assert_delvar(self, name, expect):
        self.assertEqual(expect,self.syntax.delvar(name)
            ,'testing delvar of {0}'.format(repr(name)))
        
    def testdelvar(self):
        self._assert_delvar('A','SET A=')
        self._assert_delvar('^','SET ^^=')
        pass

class TestShellWriter(unittest.TestCase):

    def setUp(self):
        self.out = io.StringIO()
        self.sw = shell.ShellWriter(Win32CmdSyntax(),self.out)

    def tearDown(self):
        self.sw = None
        self.out.close()
        self.out = None

    def _assertOutput(self, expected):
        self.assertEqual(expected,self.out.getvalue())

    def testline(self):
        self.sw.line('line',1)
        self.sw.line('l','i','n','e',2)
        self.sw.line('line3',' ','no more')
        self._assertOutput("""\
line1
line2
line3 no more
""")

    def testecho(self):
        self.sw.echo()
        self.sw.echo('')
        self.sw.echo('no escapes needed')
        self.sw.echo('with && escapes')
        self._assertOutput("""\
ECHO.
ECHO.
ECHO no escapes needed
ECHO with ^&^& escapes
""")

    def testsetvar(self):
        self.sw.setvar('name1','value')
        self.sw.setvar('name2','<value>')
        self._assertOutput("""\
SET name1=value
SET name2=^<value^>
""")

    def testdelvar(self):
        self.sw.delvar('name')
        self._assertOutput("""\
SET name=
""")



class TestEnvironmentBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = shell.EnvironmentBuilder()
        self.builder.default_path_sep = ';'
        self.builder.default_path_ignore_case  = True
        self.builder.normalize_env_name = str.upper

    def tearDown(self):
        self.builder = None

    def _assert_shell(self, *expect):
        class MockSW:
            def __init__(self):
                self.calls =[]
            def setvar(self,name,val):
                self.calls.append(('setvar',name,val))
            def delvar(self,name):
                self.calls.append(('delvar',name))
        msw = MockSW()
        self.builder.write(msw)
        self.assertSequenceEqual(expect,msw.calls)

    def testset(self):
        self.builder.set("somevar","Value")
        self.builder.set("otherVar","CAPS")
        self.builder.set("LASTVAR","lowers")
        self._assert_shell(
            ('setvar','SOMEVAR',"Value")
            ,('setvar','OTHERVAR',"CAPS")
            ,('setvar','LASTVAR',"lowers")
        )

    def testset_overwrites(self):
        self.builder.set("aaa","vala")
        self.builder.set("bbb","valb")
        self.builder.set("AaA","NEWvala")
        self._assert_shell(
            ('setvar','BBB',"valb")
            ,('setvar','AAA',"NEWvala")
        )

    def testremove(self):
        self.builder.remove('java_home')
        self._assert_shell(
            ('delvar','JAVA_HOME')
        )

    def testremove_overwrite(self):
        self.builder.set('JAVA_HOME','/jdk')
        self.builder.set('PATH','/weee')
        self.builder.remove('java_home')
        self._assert_shell(
            ('setvar','PATH','/weee')
            ,('delvar','JAVA_HOME')
        )

    def testpath_add(self):
        self.builder.path_add('path','c:/dir1')
        self._assert_shell(
            ('setvar','PATH','c:/dir1')
        )
    def testpath_add2(self):
        self.builder.path_add('path','c:/dir1')
        self.builder.path_add('pATH','d:/dir2')
        self._assert_shell(
            ('setvar','PATH','c:/dir1;d:/dir2')
        )
    def testpath_add3(self):
        self.builder.path_add('path','c:/dir1')
        self.builder.path_add('pATH','d:/dir2')
        self.builder.path_add('pATH','c:/something/else')
        self._assert_shell(
            ('setvar','PATH','c:/dir1;d:/dir2;c:/something/else')
        )
    def testpath_add_altsep(self):
        self.builder.set('myvar','val1')
        self.builder.path_add('myvar','val2')
        self.builder.path_add('myvar','val3',separator=':')
        self._assert_shell(
            ('setvar','MYVAR','val1;val2:val3')
        )
        
    def testpath_remove_empty(self):
        #Remove from a variable that hasn't been touched
        res = self.builder.path_remove('REM1', 'VAL')
        self.assertFalse(res)
        
        #Remove from a deleted variable
        self.builder.remove('REM2')
        res = self.builder.path_remove('REM2', 'VAL')
        self.assertFalse(res)

        #Remove the last path component from a variable
        self.builder.set('REM3', 'Entry')
        res = self.builder.path_remove('REM3', 'Entry')
        self.assertTrue(res)
        
        #All of the above should result in a variable being deleted
        self._assert_shell(
            ('delvar','REM1'),
            ('delvar','REM2'),
            ('delvar','REM3')
        )
        
    def testpath_remove(self):
        self.builder.set('name', 'a;b;c;d;e;d;c;b;a')
        
        res = self.builder.path_remove('name', 'c')
        self.assertTrue(res)
        self._assert_shell(('setvar','NAME','a;b;c;d;e;d;b;a'))

        res = self.builder.path_remove('name', 'c')
        self.assertTrue(res)
        self._assert_shell(('setvar','NAME','a;b;d;e;d;b;a'))

        res = self.builder.path_remove('name', 'c')
        self.assertFalse(res)
        self._assert_shell(('setvar','NAME','a;b;d;e;d;b;a'))
        
    def testpath_remove_ingore_case(self):
        self.builder.set('name', 'Piece1;Piece2;Piece3')
        
        res = self.builder.path_remove('name', 'PIECE1')
        self.assertTrue(res)
        self._assert_shell(('setvar','NAME','Piece2;Piece3'))
        
    def testpath_case_sensitive(self):
        self.builder.set('name', 'Piece1;Piece2;Piece3')
        
        res = self.builder.path_remove('name', 'PIECE1', ignore_case = False)
        self.assertFalse(res)
        self._assert_shell(('setvar','NAME','Piece1;Piece2;Piece3'))

        res = self.builder.path_remove('name', 'Piece1', ignore_case = False)
        self.assertTrue(res)
        self._assert_shell(('setvar','NAME','Piece2;Piece3'))

def runtests(argv=None):
    unittest.main(module='shenv.test.shell_test',argv=argv)

def main():
    runtests(sys.argv+['-v'])

if __name__ == '__main__':
    main()
