'''
Created on Sep 8, 2012

@author: arnold
'''




_imported = False
_config = None
    
def import_configuration(cfgfile):
    global _imported
    global _config
    if _imported:
        return _config

    import importlib.util
    import sys
    module_name = "shenv._runtime_config"

    spec = importlib.util.spec_from_file_location(module_name, cfgfile)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    _config = module
    _imported = True
    return _config


def get_configuration():
    return _config

