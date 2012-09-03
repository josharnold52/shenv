#-------------------------------------------------------------------------------
# Name:        decl_test
# Purpose:
#
# Author:      Arnold
#
# Created:     17/01/2011
# Copyright:   (c) Arnold 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import sys
import unittest
import itertools
from shenv import core

context = core.Context()
universe = context.universe
category = context.category
version = context.version


class HandlesCallbacks:
    def __append(self,name,univ,cat,ver,state):
        t = lambda x: type(x) if x is not None else None
        selft,univ,cat,ver = map(t,(self,univ,cat,ver))
        state.append((selft,name,univ,cat,ver))
    def install(self,univ,cat,ver,state):
        self.__append('install',univ,cat,ver,state)
    def remove(self,univ,cat,ver,state):
        self.__append('remove',univ,cat,ver,state)
    def clean(self,univ,cat,state):
        self.__append('clean',univ,cat,None,state)

@universe()
class Universe(HandlesCallbacks):
    description = 'The Test Universe'

@category()
class Python(HandlesCallbacks):
    name = 'python', 'py'

@version(Python)
class Python27(HandlesCallbacks):
    name = '27'

@version(Python)
class Python31:
    name = '31'

@category()
class Java(HandlesCallbacks):
    name = 'java'
    autoenable = True

@version(Java)
class Java14Sun(object):
    name = '14','4','sun14','sun4'

@version(Java)
class Java5Sun(object):
    name = '15','5','sun15','sun5'

@version(Java)
class Java6Sun(object):
    name = '16','6','sun16','sun6'
    default = True

@category()
class Ruby:
    name = 'ruby'

@version(Ruby)
class Ruby19(object):
    name = '19'

@category()
class Common:
    name = 'common'
    autoenable = True

@version(Common)
class CommonStd(HandlesCallbacks):
    name = 'std'
    default = True

expected_cleans = (
    (Python,'clean',Universe,Python,None),
    (Java,'clean',Universe,Java,None),
    (Universe,'clean',Universe,Ruby,None),
    (Universe,'clean',Universe,Common,None),
    )

class ContextTestCase(unittest.TestCase):
    def assertSameTarget(self,ctx1,ctx2,msg=None):
        self.assertIs(ctx1.target,ctx2.target,msg)

class TestContext(ContextTestCase):
    longMessage = True
    empty_context = core.Context()
    
    class SomeUnrelatedClass: pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testuniverse(self):
        pass

    def testcategory(self):
        pass

    def testversion(self):
        pass

    def testtarget(self):
        self.assertTrue(isinstance(context.target, Universe))
        self.assertIsNot(None, self.empty_context.target)

    def testtarget_factory(self):
        self.assertIs(Universe, context.target_factory)
        self.assertIsNot(None, self.empty_context.target)

    def testdescription(self):
        self.assertEquals(Universe.description, context.description)
        self.assertEquals('context', self.empty_context.description)

    def testprocess_env_changes__defaults(self):
        callbacks = []
        result = context.process_env_changes('', '', callbacks)
        
        exp = list(expected_cleans)
        exp.append((Java,'install',Universe,Java,Java6Sun))
        exp.append((CommonStd,'install',Universe,Common,CommonStd))
        self.assertSequenceEqual(exp,callbacks)

        exp_res = 'python:~,java:~16,ruby:~,common:~std'
        self.assertEqual(exp_res,result)

    def testprocess_env_changes__empty(self):
        result = self.empty_context.process_env_changes('', '', [])
        self.assertEqual('',result)


    def testprocess_env_changes__callbacks_not_found(self):        
        c2 = core.Context()
        @c2.category()
        class Cat:
            name='cat'
        @c2.version(Cat)
        class Ver:
            name ='ver'

        result = c2.process_env_changes('', 'cat:ver', [])
        self.assertEqual('cat:ver',result)

    def testprocess_env_changes__explicits(self):
        callbacks = []
        result = context.process_env_changes('', 'ruby:*,java:sun4', callbacks)
        
        exp = list(expected_cleans)
        exp.append((Java,'install',Universe,Java,Java14Sun))
        exp.append((Universe,'install',Universe,Ruby,Ruby19))
        exp.append((CommonStd,'install',Universe,Common,CommonStd))
        self.assertSequenceEqual(exp,callbacks)

        exp_res = 'python:~,java:14,ruby:*19,common:~std'
        self.assertEqual(exp_res,result)

    def testprocess_env_changes__force_off(self):
        callbacks = []
        result = context.process_env_changes('', 'java:', callbacks)
        
        exp = list(expected_cleans)
        exp.append((CommonStd,'install',Universe,Common,CommonStd))
        self.assertSequenceEqual(exp,callbacks)

        exp_res = 'python:~,java:,ruby:~,common:~std'
        self.assertEqual(exp_res,result)
        
    def testprocess_env_changes__change(self):
        callbacks = []
        result = context.process_env_changes('python:27,java:14,ruby:19', 'python:31,java:~,ruby:~', callbacks)
        
        exp = []
        exp.append((Python27,'remove',Universe,Python,Python27))
        exp.append((Java,'remove',Universe,Java,Java14Sun))
        exp.append((Universe,'remove',Universe,Ruby,Ruby19))
        exp.extend(list(expected_cleans))
        exp.append((Python,'install',Universe,Python,Python31))
        exp.append((Java,'install',Universe,Java,Java6Sun))
        exp.append((CommonStd,'install',Universe,Common,CommonStd))
        self.assertSequenceEqual(exp,callbacks)

        exp_res = 'python:31,java:~16,ruby:~,common:~std'
        self.assertEqual(exp_res,result)

    def testgetcategory_context(self):
        cc = context.getcategory_context('java')
        self.assertTrue(isinstance(cc.target,Java))

        for c in ('java',Java,cc.target):
            self.assertSameTarget(cc,
                context.getcategory_context(c),str(c))

        cc = context.getcategory_context('python')
        self.assertTrue(isinstance(cc.target,Python))

        for c in('python','py',Python,cc.target):
            self.assertSameTarget(cc,
                context.getcategory_context(c),str(c))

        with self.assertRaises(LookupError):
            context.getcategory_context(None)
        with self.assertRaises(LookupError):
            context.getcategory_context('missing')
        with self.assertRaises(LookupError):
            context.getcategory_context(self.SomeUnrelatedClass)
        with self.assertRaises(LookupError):
            context.getcategory_context(self.SomeUnrelatedClass())
        with self.assertRaises(LookupError):
            context.getcategory_context(Java()) #Wrong instance

    def testgetversion_context(self):
        cc = context.getcategory_context('java')
        vc = context.getversion_context('java','6')
        self.assertTrue(isinstance(cc.target,Java))
        self.assertTrue(isinstance(vc.target,Java6Sun))

        for c,v in itertools.product(('java',Java,cc.target),
            ('6','16','sun6','sun16',Java6Sun,vc.target)):
                self.assertSameTarget(cc,
                    context.getcategory_context(c),str((c,v)))
                self.assertSameTarget(vc,
                    context.getversion_context(c,v),str((c,v)))

        cc = context.getcategory_context('python')
        vc = context.getversion_context('python','27')
        self.assertTrue(isinstance(cc.target,Python))
        self.assertTrue(isinstance(vc.target,Python27))

        for c,v in itertools.product(('python','py',Python,cc.target),
            ('27',Python27,vc.target)):
                self.assertSameTarget(cc,
                    context.getcategory_context(c),str((c,v)))
                self.assertSameTarget(vc,
                    context.getversion_context(c,v),str((c,v)))

        with self.assertRaises(LookupError):
            context.getversion_context(None,Java6Sun)
        with self.assertRaises(LookupError):
            context.getversion_context('missing',Java6Sun)
        with self.assertRaises(LookupError):
            context.getversion_context(self.SomeUnrelatedClass,Java6Sun)
        with self.assertRaises(LookupError):
            context.getversion_context(self.SomeUnrelatedClass(),Java6Sun)
        with self.assertRaises(LookupError):
            context.getversion_context(Java,None)
        with self.assertRaises(LookupError):
            context.getversion_context(Java,'missing')
        with self.assertRaises(LookupError):
            context.getversion_context(Java,self.SomeUnrelatedClass)
        with self.assertRaises(LookupError):
            context.getversion_context(Java,self.SomeUnrelatedClass())
        with self.assertRaises(LookupError):
            context.getversion_context(Java,Java6Sun()) #Wrong instance

    def testgetcategory_contexts(self):
        pass

    def testgetversion_contexts(self):
        pass

    def test__str__(self):
        pass

class TestCategoryContext(ContextTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testgetversion_context(self):
        pass

    def testgetversion_contexts(self):
        pass

    def testautoenable(self):
        pass

    def testprimary_name(self):
        pass

    def testnames(self):
        pass

    def testtarget(self):
        pass

    def testtarget_factory(self):
        pass

    def testdescription(self):
        pass

    def test__str__(self):
        pass

class TestVersionContext(ContextTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testdefault(self):
        pass

    def testprimary_name(self):
        pass

    def testnames(self):
        pass

    def testtarget(self):
        pass

    def testtarget_factory(self):
        pass

    def testdescription(self):
        pass

    def test__str__(self):
        pass

def runtests(argv=None):
    unittest.main(module='shenv.test.core_test',argv=argv)

def main():
    #print(context)
    runtests(sys.argv+['-v'])

if __name__ == '__main__':
    main()
