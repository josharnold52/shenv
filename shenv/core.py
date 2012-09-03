#-------------------------------------------------------------------------------
# Name:        decl
# Purpose:
#
# Author:      Arnold
#
# Created:     16/01/2011
# Copyright:   (c) Arnold 2011
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import abc
import collections
import weakref
import io
import itertools
import re
from shenv._utils import _startswith
from shenv import proxies

# Terms:
#   Universe
#   Category
#   Version

CATEGORY_ENABLED = 0      
"""Category is explicitly enabled with a specific version."""

CATEGORY_ENABLED_ANY = 1  
"""Category is explicitly enabled but with no version specified."""
 
CATEGORY_DISABLED = 2
"""Category is explicitly disabled."""
 
CATEGORY_DERIVED = 3
"""Category is unspecified."""

VERSION_SENTINEL_ANY = '*'
VERSION_SENTINEL_UNSPECIFIED = '~'

class _Tree(object):
    """Underlying structure for univers->>category->>version relations.

    This data structure is essentially a multimap where the mapped values
    are the child nodes and are themselves instances of _Tree (or a subclass).
    With respect to python, _Tree is a container and supports the [key] syntax
    for accessing children.  _Tree also supports in/not in syntax for testing
    key membership.  However, _Tree is /not/ considered a Mapping and does
    not offer any other Mapping methods.

    The '_createchild' method is used to add entries.  This is the only way to
    add a new mapping to the tree.


    """

    def __init__(self, child_type = None):
        """
        Initializes the __Tree.

        The optional argument must be a factory callable (typically a subclass
        of _Tree) that takes 0 parameters and produces an empty node to be
        used as a child of this tree.  If the argument is None (the default),
        then the _Tree will not be able to create child nodes.

        """
        super().__init__()
        self.__child_dict = collections.OrderedDict()
        self.__child_type = child_type
        self.__mykeys = ()
        self.__parent = None

    def __newchild(self, childkeys):
        if self.__child_type==None:
            raise Exception("Child type not specified for _Tree: {0}"
                    .format(self.__class__))
        ch = self.__child_type()
        ch.__mykeys = tuple(childkeys)
        ch.__parent = weakref.ref(self)
        return ch

    def _createchild(self,key,*altkeys):
        ks = [key] + list(altkeys)
        ch = self.__newchild(ks)
        for k in ch._nodekeys:
            if k in self.__child_dict: raise KeyAlreadyExistsError(
                "{0} already exists in node".format(k))
        for k in ks:
            self.__child_dict[k]=ch
        return ch

    def __get_node(self,*path):
        if len(path)==0: return self
        return self.__child_dict[path[0]].__get_node(*path[1:])

    def _get_node(self,*path):
        try:
            return self.__get_node(*path)
        except KeyError as e:
            raise PathNotFoundError(*path) from e

    @property
    def _nodekeys(self):
        return self.__mykeys

    @property
    def _parent(self):
        return None if self.__parent is None else self.__parent()

    @property
    def _ancestors(self):
        '''\
        Returns iterable of ancestors (including self)
        
        The iterable starts with self and proceeds up the hierarchy.

        '''
        def gen(nd):
            while nd is not None:
                yield nd
                nd = nd._parent
        return gen(self)
            
    @property
    def _children(self):
        seen = set()
        for ch in self.__child_dict.values():
            if ch not in seen:
                seen.add(ch)
                yield ch

    def __contains__(self, item): return item in self.__child_dict

    def __getitem__(self, key): return self.__child_dict[key]


class _BaseNode(_Tree, metaclass=abc.ABCMeta):

    def __init__(self, child_class):
        super().__init__(child_class)
        self.__target = object()
        self.__target_factory = object
        self.__did_inittarget = False

    def _inittarget(self, target, target_factory):
        if self.__did_inittarget: 
            raise MultipleTargetDefinitionError('Target already initialized')
        self.__target = target
        self.__target_factory = target_factory
        self.__did_inittarget = True
        self._inittarget_post()

    @abc.abstractmethod
    def _inittarget_post(self): pass

    @property
    def target(self) : return self.__target

    @property
    def target_factory(self): return self.__target_factory

    @property
    def _did_inittarget(self) : return self.__did_inittarget

    @abc.abstractproperty
    def names(self): return ('')

    @property
    def primary_name(self):
        return _first(self.names)

    @property
    def alt_names(self): 
        pn = self.primary_name
        return tuple(n for n in self.names if n != pn)

    @property
    def description(self) :
        if (hasattr(self.target,'description')):
            return str(self.target.description)
        return self.primary_name
    
    @property
    def hierarchy(self):
        ancestors = reversed(list(self._ancestors))
        return tuple(map(_targetof,ancestors))
    
    def get_hierarchy_proxy(self, *default):
        #Don't use self.hierarchy because it's reversed
        return proxies.HierarchyProxy(map(_targetof,self._ancestors),*default)
    
    def get_target_proxy(self, *default):
        return proxies.BasicProxy(_targetof(self),*default)
    
    def get_iterating_proxy(self, *default):
        #Use self.hierarchy because we want the reversed behavior
        return proxies.IteratingProxy(self.hierarchy,*default)
    
    @property
    def _notifier(self):
        return self.get_hierarchy_proxy(_constantly(None))


class Context(_BaseNode):

    def __init__(self):
        super().__init__(CategoryContext)
        self.__target_factory = _DefaultUniverse
        self.__target = _DefaultUniverse()

    def _inittarget_post(self):
        pass

    @property
    def names(self):
        names = _get_name_tuple(self.__target)
        return names if names else ('context',)
        
    def _parse_state_string(self, state_str):
        state_dict = collections.OrderedDict()
        if not state_str: return state_dict
        for cs,_,csts in map(lambda x: x.partition(':'),state_str.split(',')):
            c = self[cs]
            cst = _VersionSelection.from_string(csts, lambda x : c[x]) 
            if not c in state_dict: state_dict[c] = cst
            else: raise ValueError(state_str,"duplicate category: "+cs)
        return state_dict
    
    def _normalize_state_dict(self, state_dict):
        res = collections.OrderedDict()
        for cat in self._children:
            if cat in state_dict: res[cat] = state_dict[cat]
            else: res[cat] = _VersionSelection(None, CATEGORY_DERIVED)
        return res

    @staticmethod
    def _generate_state_string(state_dict):
        def cnm(x): 
            return x.primary_name if x else ''
        def itm(c,cst): 
            return cnm(c) + ':' + str(cst)
        return ','.join(itm(c,cst) for c,cst in state_dict.items())

    __invalid_character = re.compile('[^\\w.\\-]')

    @staticmethod
    def validname(name):
        """Returns true iff a string is a valid version or category name."""
        return len(name)>0 and (
            Context.__invalid_character.search(name) is None)

    def __named(self,cls,ctx_factory,*path):
        target = cls()
        #Get the names of the managed object
        names = _get_name_tuple(target)
        if len(names)==0:
            raise ValueError(target,'empty names',cls,ctx_factory,names)
        if not all(map(self.validname,names)):
            raise ValueError(target,'invalid name',cls,ctx_factory,names,
                    tuple(map(self.validname,names)))
        parnode = self._get_node(*path)
        node = parnode._createchild(*tuple((target,cls)+ names))
        node._inittarget(target,cls)
        
        #Install a getcontext function on the target that returns
        target.getcontext = _compose(ctx_factory, weakref.ref(node))
        return cls

    def universe(self):
        """Class decorator for universe"""
        def doit(cls):
            if self._did_inittarget:
                raise MultipleTargetDefinitionError("Universe already defined")
            target = cls()
            self._inittarget(target,cls)
            target.getcontext = _compose(lambda x: x, weakref.ref(self))
            return cls
        return doit

    def category(self):
        """Class decorator for categories"""
        return lambda cls : self.__named(cls, CategoryContext)

    def version(self, category):
        """Class decorator for versions"""
        return lambda cls : self.__named(cls, VersionContext, category)

    def get_version_selection(self, category, state_string):
        """
Get the version selection for a `category` given a `state_string`.

Returns a tuple where the first item is the VersionContext or None
and the second item is one of:

`CATEGORY_ENABLED` - The category is enabled with an explicit version
`CATEGORY_ENABLED_ANY` - The category is enabled with a default version
`CATEGORY_DISABLED` - The category is disabled
`CATEGORY_DERIVED` - The category state is not specified by the state_string.

"""
        catnode = self[category]

        envd = self._parse_state_string(state_string)
        envd = self._normalize_state_dict(envd)
        state = envd[catnode]
        return state.version,state.classifier
    
    def process_env_changes(self, initial_state, changes, callback_param):
        """\
Process changes to the environment.

Params:
  `initial_state` - State string describing the initial environment
  `changes` - State string describing updates to the environemnt
  `callback_param` - Passed into the callback functions.

Returns:
  an updated state string
  
Callbacks:
  remove(u,c,v,`callback_param`) - for all initially enabled versions
  clean(u,c,`callback_param`) - for all categories
  install(u,c,v,`callback_param`) - for all subsequent enabled versions

"""

        envd = self._parse_state_string(initial_state)
        envd = self._normalize_state_dict(envd)
        
        cd = self._parse_state_string(changes)

        
        cats = list(self._children)
        def envditems(): return ((x, envd[x]) for x in cats)

        #Remove all preexisting versions
        for cat,state in envditems():
            if state.version is not None:
                state.version._notifier.remove(
                    _targetof(self),
                    _targetof(cat),
                    _targetof(state.version),
                    callback_param)

        #Clean all categories
        for cat in cats:
            cat._notifier.clean(
                _targetof(self),
                _targetof(cat),
                callback_param)

        #Update envd using changes in cd
        for cat,state in cd.items():
            envd[cat] = state
            
        #Handle CATEGORY_DERIVED and _ENABLE_ANY items.
        #Future: process dependencies and constraints?
        for cat, state in envditems():
            if state.classifier == CATEGORY_DERIVED:
                if cat.autoenable:
                    envd[cat] = _VersionSelection(cat.default_version, CATEGORY_DERIVED)
                else:
                    envd[cat] = _VersionSelection(None,CATEGORY_DERIVED)
            elif state.classifier == CATEGORY_ENABLED_ANY:
                envd[cat] = _VersionSelection(cat.default_version, CATEGORY_ENABLED_ANY)
        
        #Dependencies
        deps = [cat for cat, state in envditems() if state.version is not None]
        while deps:
            alldeps = (dep for cat in deps
                           for dep in envd[cat].version._dependency_contexts
                           if envd[dep].version is None
                           if envd[dep].classifier == CATEGORY_DERIVED)
            alldeps_set = set()            
            for dep in alldeps:
                envd[dep] = _VersionSelection(dep.default_version, CATEGORY_DERIVED)
                alldeps_set.add(dep)
            #Reorder itmes in alldeps_set to the canonical order for our next pass
            deps = [cat for cat, state in envditems() if cat in alldeps_set]
            
        
        #Trigger install events
        for cat,state in envd.items():
            if state.version is not None:
                state.version._notifier.install(
                    _targetof(self),
                    _targetof(cat),
                    _targetof(state.version),
                    callback_param)
        
        return self._generate_state_string(envd)

    def getcategory_context(self,category):
        """
        Returns the CategoryContext for the specified category.

        A category may be specified using:

        1) Any of its names
        2) Its factory
        3) Its instance

        A LookupError (or subtype thereof) is raised if no such category exists.

        """
        return self[category]

    def getversion_context(self,category, version):
        """
        Returns the VersionContext for the specified category and version.

        A category (version) may be specified using:

        1) Any of its names
        2) Its factory
        3) Its instance

        A LookupError (or subtype thereof) is raised if no such category
        (version) exists.

        """
        return self[category][version]

    def getcategory_contexts(self):
        return self._children

    def getversion_contexts(self):
        return itertools.chain.from_iterable(
            x._children for x in self._children)


    def _describeto(self, out, indent):
        spaces = ''.ljust(indent)
        s = str(self.target) if self._did_inittarget else ''
        print(spaces,s,file=out)
        for c in self._children:
            c._describeto(out,indent+4)

    def __str__(self):
        with io.StringIO as out:
            out.write('Context: ')
            self._describeto(out,0)
            return out.getvalue()

    

class CategoryContext(_BaseNode):
    def __init__(self):
        super().__init__(VersionContext)

    def _inittarget_post(self):
        pass

    @property
    def names(self): 
        #By convention, the first key of the node must be its target
        #The second key of the node must be its factory
        #The third key is its primary name
        #Subsequent keys are alternate names
        return self._nodekeys[2:]
    
    def getversion_context(self, cat, ver):
        return self[ver]
    
    def getuniverse_context(self):
        return self._parent

    def getversion_contexts(self):
        return tuple(self._children)

    @property
    def default_version(self):
        v = next((c for c in self._children if c.default), None)
        if v is None:
            v = next(self._children, None)
            if v is None: raise ValueError("No children have been defined")
        return v

    @property
    def autoenable(self):
        if hasattr(self.target,'autoenable'):
            return bool(self.target.autoenable)
        return False

    def _describeto(self, out, indent):
        spaces = ''.ljust(indent)
        s = '{0}{1}: autoenable={2}'.format(spaces,
            list(self.names), self.autoenable)
        print(s,file=out)
        for c in self._children:
            c._describeto(out,indent+4)
                    
    def __str__(self):
        with io.StringIO as out:
            self._describeto(out,0)
            return out.getvalue()

class VersionContext(_BaseNode):
    def __init__(self,):
        super().__init__(None)

    def _inittarget_post(self):
        pass

    @property
    def names(self): 
        #By convention, the first key of the node must be its target
        #The second key of the node must be its factory
        #The third key is its primary name
        #Subsequent keys are alternate names
        return self._nodekeys[2:]

    @property
    def default(self):
        if hasattr(self.target,'default'):
            return bool(self.target.default)
        return False
    
    def getuniverse_context(self):
        return self._parent._parent

    def getcategory_context(self):
        return self._parent

    def _describeto(self, out, indent):
        spaces = ''.ljust(indent)
        s = '{0}{1}: default={2}'.format(spaces,
            list(self.names), self.default)
        print(s,file=out)
        
    def __str__(self):
        with io.StringIO as out:
            self._describeto(out,0)
            return out.getvalue()

    @property
    def _dependency_contexts(self):
        proxy = proxies.HierarchyProxy((self.target,self._parent.target), ())
        deps = proxy.dependencies
        univ = self.getuniverse_context()
        return tuple(univ[x] for x in deps)
        
class _DefaultUniverse:
    pass

class _VersionSelection:
    
    def __init__(self,version,classifier):
        self.__version = version
        self.__classifier = classifier
        if classifier not in set((CATEGORY_ENABLED,CATEGORY_ENABLED_ANY,CATEGORY_DISABLED,CATEGORY_DERIVED)):
            raise ValueError(version,classifier)
        if classifier == CATEGORY_DISABLED and version is not None:
            raise ValueError(version,classifier)
        if classifier == CATEGORY_ENABLED and version is None:
            raise ValueError(version,classifier)
            

    @staticmethod
    def from_string(state_str, finder):
        if _startswith(state_str, VERSION_SENTINEL_ANY):
            classifier = CATEGORY_ENABLED_ANY
            rest = state_str[len(VERSION_SENTINEL_ANY):]
        elif _startswith(state_str, VERSION_SENTINEL_UNSPECIFIED):
            classifier = CATEGORY_DERIVED
            rest = state_str[len(VERSION_SENTINEL_UNSPECIFIED):]
        else:
            classifier = CATEGORY_ENABLED if state_str else CATEGORY_DISABLED
            rest = state_str
        
        version = finder(rest) if rest else None
        
        return _VersionSelection(version, classifier)
        
    @property
    def version(self): return self.__version

    @property
    def classifier(self): return self.__classifier

    def __repr__(self):
        return '_VersionSelection({0},{1})'.format(self.version,self.classifier)

    def __str__(self):
        if self.classifier == CATEGORY_DERIVED: 
            prefix = VERSION_SENTINEL_UNSPECIFIED
        elif self.classifier == CATEGORY_ENABLED_ANY: 
            prefix = VERSION_SENTINEL_ANY
        else: 
            prefix = ''
        
        ver = self.version
        vername = ver.primary_name if ver is not None else ''
        return prefix+vername



def _first(iterable):
    try:
        return next(iter(iterable))
    except StopIteration as si:
        raise ValueError('Empty iterable',iterable) from si

def _constantly(retval):
    return lambda *pos,**kw: retval

def _none_to_none(f, *val):
    '''\
Maps None to None otherwise applies f
    
The first argument must be a function accepting a single parameter.

If there is a second argument, the return value is the function applied
to the second argument if the latter is not None, otherwise None is
returned.

If there is no second argument, this function acts as a decorator,
returning a function that returns None if its argument is None and
otherwise applies f to its argument.'''
    if len(val) == 0:
        return lambda x : None if x is None else f(x)
    if len(val) == 1:
        return None if val[0] is None else f(val[0])
    raise TypeError('1 or 2 params, please')
    
def _targetof(node):
    """Returns the target of a node or None if no such target exists."""
    if node is None: return None
    return node.target

def _compose(outer, inner):
    def f(*posn,**kwds):
        return outer(inner(*posn,**kwds))

def _get_name_tuple(target):
    try:
        names = getattr(target, 'name')
    except AttributeError:
        return ()
    if isinstance(names, str):
        return (names,)
    return tuple(map(str,names))




class LeakedExceptionError(Exception): pass
class KeyAlreadyExistsError(Exception): pass
class PathNotFoundError(KeyError): pass
class MultipleTargetDefinitionError(Exception): pass

def main():
    print('Testing the shenv.core module:')
    import shenv.test.core_test
    shenv.test.core_test.main()

if __name__ == '__main__':
    main()
