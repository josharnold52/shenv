'''
Created on Jan 26, 2011

@author: Arnold
'''

from shenv import _utils
import itertools

class BasicProxy:
    def __init__(self,target,*default):
        if len(default)>1:
            raise TypeError('1 or 2 args, please!')
        self.__target = target
        self.__default = tuple(default)
            
    
    def __getattr__(self,name):
        return getattr(self.__target,name,*self.__default)

class HierarchyProxy:
    def __init__(self,targets,*default):
        if len(default)>1:
            raise TypeError('1 or 2 args, please!')
        self.__targets = tuple(targets)
        self.__default = tuple(default)
            
    
    def __getattr__(self,name):
        for t in self.__targets:
            try:
                return getattr(t,name)
            except AttributeError:
                pass
        if self.__default:
            return self.__default[0]
        raise AttributeError(name, self.__targets)


class IteratingProxy:

    def __init__(self,targets,*default):
        if len(default)>1:
            raise TypeError('1 or 2 args, please!')
        self.__targets = tuple(targets)
        self.__default = tuple(default)
            
    
    def __getattr__(self,name):
        return _utils.reiterable(
                    map,
                    lambda t: getattr(t,name,*self.__default),
                    self.__targets)


class AggregatingProxy:
    def __init__(self,targets):
        self.__inner = IteratingProxy(targets,())
    
    def __getattr__(self,name):
        return _utils.reiterable(
                    itertools.chain,
                    getattr(self.__inner,name))
    
    