#------------------------------------------------------------------------------
# Name:        shell
# Purpose:
#
# Author:      Arnold
#
# Created:     15/01/2011
# Copyright:   (c) Arnold 2011
# Licence:     Apache License, 2.0 (TODO)
#------------------------------------------------------------------------------
#!/usr/bin/env python
import abc
import collections
import os.path
import itertools

class ShellSyntax(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def setvar(self, name, value):
        '''Returns a shell command to set `name` variable to `value`'''
        raise NotImplementedError('setvar')
    
    @abc.abstractmethod
    def delvar(self, name):
        '''Returns a shell command to delete the `name` variable'''
        raise NotImplementedError('delvar')
    
    @abc.abstractmethod
    def echo(self, msg):
        '''Returns a shell command to print `msg`'''
        raise NotImplementedError('echo')

    def settrace(self, enable):
        return ''
    
    def comment(self, text):
        return ''


class Win32CmdSyntax(ShellSyntax):
    def setvar(self, name, value):
        return self.__escape('SET {0}={1}'.format(name,value))
    
    def delvar(self, name):
        return self.__escape('SET {0}='.format(name))
    
    def echo(self, msg):
        if len(msg) == 0:
            return 'ECHO.'
        elif msg.upper() in {'ON','OFF'}:
            msg = '_'+msg
        return self.__escape('ECHO {0}'.format(msg))
    
    def settrace(self, enable):
        return '@ECHO ON' if enable else '@ECHO OFF'
        
    def comment(self, text):
        return self.__escape('REM {0}'.format(text))
                    
    def __escape(self, s):
        return s.translate(str.maketrans({x: ('^' + x) for x in '^<>|&%'}))
    
class BashSyntax(ShellSyntax):
    
    @staticmethod
    def __quote_literal(s):
        return "'" + s.replace("'","'\\''") + "'"
        
    def setvar(self, name, value):
        return 'export {0}={1}'.format(name,self.__quote_literal(value))
    
    def delvar(self, name):
        return 'export -n {0} ; unset {1}'.format(name,name)
    
    def echo(self, msg):
        return 'echo {0}'.format(self.__quote_literal(msg))
    
    def settrace(self, enable):
        ## Not supported for now.  We're going to source the script so we'll need a way to save and restore
        ## http://fvue.nl/wiki/Bash:_Backup_and_restore_settings
        ##'set -x' if enable else 'set + x'
        return ''
        
    def comment(self, text):
        return '# {0}'.format(text)
                    
    
class ShellWriter(object):
    
    def __init__(self, syntax, out):
        super().__init__()
        self.__out = out
        self.__syntax = syntax
    
    def line(self, *s):
        '''\
Writes a line to the writer's output.

The positional arguments are converted to strings, concatenated, and
written to the output object.  The a newline is written to the output.

'''
        print(*s, sep='',file=self.__out)

    def echo(self, msg=''):
        msg = str(msg)
        self.line(self.__syntax.echo(msg))

    def setvar(self, name, val):
        name,val = str(name),str(val)
        self.line(self.__syntax.setvar(name,val))

    def delvar(self, name):
        name = str(name)
        self.line(self.__syntax.delvar(name))
        
    def comment(self, text):
        text = str(text)
        self.line(self.__syntax.comment(text))
        
    def settrace(self, enable):
        enable = bool(enable)
        self.line(self.__syntax.settrace(enable))

def _find_index(matchfn, seq, *deflt):
    if len(deflt) > 1: 
        raise TypeError('_find_index takes 2 or 3 arguments ({0} given)'
                        .format(2+len(deflt)))
    for indx, val in enumerate(seq):
        if matchfn(val):
            return indx
    if not deflt:
        raise ValueError('No match found for {0}'.format(str(matchfn)))
    return deflt[0]

def _remove_last_match(matchfn, mutableseq):
    for indx in range(len(mutableseq)-1,-1,-1):
        if matchfn(mutableseq[indx]):
            del mutableseq[indx]
            return True
    return False
    


class EnvironmentBuilder(object):

    __os_ignore_case = os.path.normcase('MiXeD') != 'MiXeD'
    default_path_sep = os.pathsep
    default_path_ignore_case = __os_ignore_case
    
        
    def __init__(self):
        super().__init__()
        self.__env_vars = collections.OrderedDict()
        self.__protected = set()

    def set(self, name, value):
        '''Set the <name> variable to <value>'''
        name,value = self.__normalize(name,value)
        if name in self.__env_vars:
            del self.__env_vars[name]
        self.__env_vars[name] = value

    def path_add(self, name, value, separator=None):
        if separator is None:
            separator = self.default_path_sep
        name,value,separator = self.__normalize(name,value,separator)
        
        existing = self.__env_vars.get(name,'')
        if not existing:
            self.__env_vars[name] = value
        else:
            self.__env_vars[name] = existing+separator+value
    
    def path_remove(self, name, value, separator=None, ignore_case=None):
        if separator is None:
            separator = self.default_path_sep
        if ignore_case is None:
            ignore_case = self.default_path_ignore_case
        name,value,separator = self.__normalize(name,value,separator)
        if name not in self.__env_vars:
            self.__env_vars[name] = None            
        existing = self.__env_vars[name]
        if not existing:
            return False
        
        existing_list = list(existing.split(separator))
        normcase = str.upper if ignore_case else lambda x : x
        normval = normcase(value)
        changed = _remove_last_match(lambda x : normval == normcase(x),
                                     existing_list)
        if changed:
            self.__env_vars[name] = (
                separator.join(existing_list) if existing_list else None)
        return changed
        
    def remove(self, name):
        name = str(name).upper()
        #Remove then reinsert None to move var to the end of the dict
        self.__env_vars.pop(name, None)
        self.__env_vars[name] = None

    def __str__(self):
        return str(self.__env_vars)

    def write(self, shell_writer):
        for k, v in self.__env_vars.items():
            if k in self.__protected:
                continue
            if v is None:
                shell_writer.delvar(k)
            else:
                shell_writer.setvar(k, v)

    def protect(self, name):
        self.__protected.add(str(name).upper())

    def unprotect(self, name):
        self.__protected.discard(str(name).upper())
        
    def getprotected(self):
        return frozenset(self.__protected)
   
    def normalize_env_name(self, name):
        '''Normalize the name - may be overridden'''
        return name.upper() if self.__os_ignore_case else name
    
    def __normalize(self,name,*values):
        name = self.normalize_env_name(str(name))
        if not values:
            return name
        return tuple(itertools.chain((name,),map(str,values)))
    

def main():
    print('Testing the shell module:')
    import shenv.test.shell_test
    shenv.test.shell_test.main()

if __name__ == '__main__':
    main()
