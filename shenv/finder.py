'''
Created on Sep 8, 2012

@author: arnold
'''
import re
import os.path

def _constantly(retval):
    return lambda *pos,**kw: retval

def _and(pred1, pred2):
    return lambda *pos,**kw: pred1(*pos, **kw) and pred2(*pos, **kw)

def _remove_punctuation(name):
    return name.replace(".","").replace("_","").replace("-","")

def _base26(num):
    result = ''
    while (num >= 1):
        result = chr(97 + (num % 26)) + result
        num = num / 26
    return result if result else 'a'

_number_pattern = re.compile(r'^\d+$')
_mixed_ver_splitter = re.compile(r'[^\d]')

class _VerComponent:
    
    @staticmethod
    
    
    def __init__(self, comp):
        self.__comp = tuple(comp)
        isnum = _number_pattern.match(comp)
        if isnum and len(comp) < 8:
            self.__sortkey = (0,int(comp))
        elif not isnum:
            self.__sortkey = (1,)
        raise Exception()

def _ver_component_sortkey(vercomponent):
    isnum = _number_pattern.match(vercomponent)
    if isnum and len(vercomponent) < 8:
        return (0, int(vercomponent))
    
    

def has_child_matcher(relpath):
    """ Returns a path matcher that selects directories that contain a file named by relpath """
    return lambda d: os.path.isfile(os.path.join(d, relpath))

class _NameMapper:
    def __init__(self):
        self.name_to_mapped = {}
        self.mapped_to_name = {}

    def add(self, name, mapped):
        if name in self.name_to_mapped:
            return
        
        if mapped not in self.mapped_to_name:
            self.__setnr(name, mapped)
            return
        
        conflict = self.mapped_to_name[mapped]
        if conflict is not None:
            self.__setnr(conflict, self.__uniqify_mapped(mapped))
            self.mapped_to_name[mapped] = None
        
        self.__setnr(name, self.__uniqify_mapped(mapped))
        
    def __setnr(self, name, reduced):
        self.name_to_mapped[name] = reduced
        self.mapped_to_name[reduced] = name
        
    def __uniqify_mapped(self, reduced):
        cnt = 0
        while True:
            chk = reduced + _base26(cnt)
            if chk not in self.mapped_to_name:
                return chk
            cnt = cnt + 1   
            
    def mappedNames(self):
        return self.name_to_mapped.values()
    
    def mapped(self, name):
        return self.name_to_mapped[name]

def _gennames(vers):
    nvers = tuple(("".join(v[0]),) + v for v in vers)
    mapper = _NameMapper()
    for indx, nv in enumerate(nvers):
        mapper.add(indx, nv[0])
    for indx, nv in enumerate(nvers):
        yield (mapper.mapped(indx), ) + nv[1:]


class _VerTrie:
    
    def __init__(self):
        self.leafcount = 0
        self.leaf = False
        self.__children = {}
    
    def add(self, item, startpos):
        if len(item) <= startpos:
            if self.leaf:
                return False
            else:
                self.leaf = True
                self.leafcount = self.leafcount + 1
                return True
        else:
            if self.__child(item[startpos]).add(item,startpos + 1):
                self.leafcount = self.leafcount + 1
                return True
            else:
                return False
        
    def __child(self, key):
        if key not in self.__children:
            self.__children[key] = _VerTrie()
        return self.__children[key]
   
    def uninteresting_prefix(self, count = 0):
        if len(self.__children) != 1:
            return (count, self)
        for k, ch in self.__children.items():
            if _number_pattern.match(k):
                return (count, self)
            return ch.uninteresting_prefix(count + 1)
        
    def min_unique(self, item, pos = 0):
        if len(item) <= pos:
            return pos
        if self.leafcount < 2:
            return pos
        itematpos = item[pos]
        if itematpos not in self.__children:
            return pos + 1
        return self.__children[itematpos].min_unique(item, pos + 1)

def _minify(vers):
    vers = tuple(vers)
    trie = _VerTrie()
    for v in vers:
        trie.add(v[0], 0)
    spos, strie = trie.uninteresting_prefix()
    for v in vers:
        vs = v[0]
        vend = strie.min_unique(vs, spos)
        vs = vs if spos >= vend else vs[spos:vend]
        yield( (vs, ) + v)

class VersionFinder:
    
    def __init__(self):
        self.version_splitter(r'[\_\-\.]+')
        self.name_matcher(_constantly(True))
        self.path_matcher(_constantly(True))
        pass
    
    def version_splitter(self, splitter):
        if hasattr(splitter, "split") and hasattr(splitter, "pattern"):
            self.__component_fn = lambda x: tuple(filter(None, splitter.split(x)))
        elif hasattr(splitter, "__call__"):
            self.__component_fn = lambda x: tuple(filter(None, splitter(x)))
        else:
            regex = re.compile(splitter)
            self.__component_fn = lambda x: tuple(filter(None, regex.split(x)))
        return self
    
    def name_matcher(self, matcher):
        if hasattr(matcher,"match") and hasattr(matcher, "pattern"):
            self.__name_pred = lambda x: bool(matcher.match(x))
        elif hasattr(matcher,"__call__"):
            self.__name_pred = lambda x: bool(matcher(x))
        else:
            regex = re.compile(matcher)
            self.__name_pred = lambda x: bool(regex.match(x))
        return self
    
    def path_matcher(self, matcher):
        if hasattr(matcher,"match") and hasattr(matcher, "pattern"):
            self.__path_pred = lambda x: bool(matcher.match(x))
        elif hasattr(matcher,"__call__"):
            self.__path_pred = lambda x: bool(matcher(x))
        else:
            regex = re.compile(matcher)
            self.__path_pred = lambda x: bool(regex.match(x))
        return self
    
    def versions(self, dirs):
        for d in dirs:
            if not os.path.isdir(d):
                continue
            if not self.__path_pred(d):
                continue
            name = os.path.basename(d)
            if not self.__name_pred(name):
                continue
            comps = self.__component_fn(name)
            if not comps:
                continue
            yield (comps, d)
    
    def find(self, path):
        return self.select(os.path.join(path, n) for n in os.listdir(path))
        
    def select(self, dirs):
        vs = tuple(self.versions(dirs))
        mvs = tuple(_minify(vs))
        nmvs = tuple(_gennames(mvs))
        return tuple(nmvs)

def _main():
    print('Testing the finder module:')
    
    vf = VersionFinder().path_matcher(has_child_matcher("bin/scala"))
    
    basepath = "/Users/arnold/devtools/langs/scala"
    res = vf.find(basepath)
    for item in res:
        print(item)
        
    
    ds = [os.path.join(basepath, d) for d in os.listdir("/Users/arnold/devtools/langs/scala")]
    ds.extend(list(ds))
    res = vf.select(ds)
    for item in res:
        print(item)
    


if __name__ == '__main__':
    _main()