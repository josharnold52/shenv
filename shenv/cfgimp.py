'''
Created on Sep 8, 2012

@author: arnold
'''

# fallback import needed for python 3.1 compatibility.  See importlib doc
try:
    from importlib.abc import SourceLoader
except ImportError:
    from importlib.abc import PyLoader as SourceLoader
    
import imp

_imported = False
_config = imp.new_module("shenv._runtime_config")

def ximport_configuration(cfgfile):
    if _imported:
        return _config
    
    
def import_configuration(cfgfile):
    if _imported:
        return _config

    class CustomLoader(SourceLoader):
        def get_filename(self, fullname):
            return cfgfile

        def source_path(self, fullname):
            return cfgfile
    
        def is_package(self, fullname):
            return False
        
        def get_data(self, path):
            with open(path, "rb") as f:
                return f.read()

        def module_repr(self, module):
            return str(module)

    _config = CustomLoader().load_module("shenv._runtime_config")
    return _config

def get_configuration():
    return _config
