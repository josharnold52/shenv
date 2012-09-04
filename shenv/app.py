'''
Created on Jan 21, 2011

@author: Arnold
'''

import shenv.shell
import shenv.core
import shenv.cfggen
import os.path
import io
import sys
import abc
import runpy

#Fake abc reference to suppress bogus warning in pydev, which otherwise thinks
#abc is unused, probably because it doesn't understand the new python 3 metaclass
#syntax
abc.ABCMeta

_MODULES_VAR = '_SHELL_MODULES'

def _constantly(retval):
    return lambda *pos,**kw: retval

def _str_concat(*items):
    return ''.join(map(str,items))

class _Win32Platform:
    def __init__(self):
        self.environ = os.environ
        self.syntax = shenv.shell.Win32CmdSyntax()
        self.pathvar = 'PATH'

class _BashPlatform:
    def __init__(self):
        self.environ = os.environ
        self.syntax = shenv.shell.BashSyntax()
        self.pathvar = 'PATH'

_platforms = {'win32cmd' : _Win32Platform(), 'bash' : _BashPlatform() } 

class ProcessorError(Exception): pass
class UnknownCategoryError(ProcessorError): pass
class UnknownVersionError(ProcessorError): pass
class ShowUsageSignal(Exception): pass

class _Processor:
    
    list_format = '{0:<12}{1:<20}{2}'
    
    def __init__(self, context, platform):
        self.context = context
        self.platform = platform
        
    def __catctx(self, cat):
        try:
            return self.context.getcategory_context(cat)
        except Exception as err:
            raise UnknownCategoryError(cat) from err
        
    def __verctx(self, cat, ver):
        try:
            return self.context.getversion_context(cat, ver)
        except Exception as err:
            raise UnknownVersionError(cat, ver) from err
    
    def __validate(self, cat, ver = None):
        try:
            self.context.getcategory_context(cat)
        except Exception as e:
            raise UnknownCategoryError(cat) from e
        if ver:
            try:
                self.context.getversion_context(cat,ver)
            except Exception as e:
                raise UnknownVersionError(cat,ver) from e
        
    
    def get_initial_state(self):
        return self.platform.environ.get(_MODULES_VAR,'')

    @staticmethod
    def _set_final_state(state_str,builder):
        builder.env.set(_MODULES_VAR, state_str)
        

    def __echo_version(self,category,state_string,builder,verbose=True):
        cctx = self.context.getcategory_context(category)
        vctx, classifier = self.context.get_version_selection(category, state_string)
        #TODO: Give some indication of classifier?
        if classifier == shenv.core.CATEGORY_ENABLED:
            builder.script.echo('{0:<12} is enabled and set to version \'{1}\''
                                .format(cctx.primary_name,vctx.primary_name))
        elif classifier == shenv.core.CATEGORY_ENABLED_ANY:
            builder.script.echo('{0:<12} is enabled and set to its default version of \'{1}\''
                                .format(cctx.primary_name,vctx.primary_name))
        elif classifier == shenv.core.CATEGORY_DISABLED:
            builder.script.echo('{0:<12} is disabled'
                                .format(cctx.primary_name))
        elif vctx is not None:
            builder.script.echo('{0:<12} is unspecified but is enabled by default to version \'{1}\''
                                .format(cctx.primary_name,vctx.primary_name))
        else:
            builder.script.echo('{0:<12} is unspecified and is disabled by default'
                                .format(cctx.primary_name))
        if not verbose:
            return
        builder.script.echo('')
        if vctx is not None:
            hier = vctx.hierarchy
            proxy = vctx.get_hierarchy_proxy(_constantly(None))
            proxy.query_version(*(hier + (builder,)))
            
    def show_version(self,category, builder):
        self.__echo_version(category, self.get_initial_state(),builder)
    
    def show_all_versions(self, builder):
        statestr = self.get_initial_state()
        for catctx in self.context.getcategory_contexts():
            self.__echo_version(catctx.primary_name, statestr, builder, False)
            
    def __change_env(self, cat, ver, flags, builder):
        ver = ver if ver else ''
        self.__validate(cat, ver)
        initial = self.get_initial_state()
        final = self.context.process_env_changes(initial, 
                    _str_concat(cat,':',flags,ver), builder)
        self._set_final_state(final, builder)
        self.__echo_version(cat, final, builder)
    
    def setup(self, builder):
        initial = self.get_initial_state()
        final = self.context.process_env_changes(initial, 
                    '', builder)
        self._set_final_state(final, builder)
        for catctx in self.context.getcategory_contexts():
            self.__echo_version(catctx.primary_name, final, builder, False)
    
    def enable_category(self, cat, ver, builder):
        flags = '' if ver else shenv.core.VERSION_SENTINEL_ANY
        self.__change_env(cat, ver, flags, builder)

    def disable_category(self, cat, builder):
        self.__change_env(cat, None, '', builder)
        
    def unspecify_category(self, cat, builder):
        self.__change_env(cat, None, shenv.core.VERSION_SENTINEL_UNSPECIFIED, builder)

    def spit_categories(self,builder):
        for catctx in self.context.getcategory_contexts():
            allnames = [catctx.primary_name] + list(catctx.alt_names)
            for name in allnames:
                builder.script.echo(name)
                
    def spit_versions(self,cat,builder):
        try:
            catctx = self.context.getcategory_context(cat)
        except Exception:
            return
        for verctx in catctx.getversion_contexts():
            allnames = [verctx.primary_name] + list(verctx.alt_names)
            for name in allnames:
                builder.script.echo(name)

    def list_categories(self,builder):
        msg = self.list_format.format('category','aliases','description')
        builder.script.echo(msg)
        builder.script.echo(''.ljust(len(msg),'-'))
        for catctx in self.context.getcategory_contexts():
            alts = tuple(catctx.alt_names)
            msg = self.list_format.format(catctx.primary_name,
                    ', '.join(alts) if alts else '',
                    catctx.description)
            builder.script.echo(msg)
    
    def list_versions(self,cat,builder):
        self.__validate(cat)
        msg = self.list_format.format('version','aliases','description')
        builder.script.echo(msg)
        builder.script.echo(''.ljust(len(msg),'-'))
        catctx = self.context.getcategory_context(cat)
        for verctx in catctx.getversion_contexts():
            alts = tuple(verctx.alt_names)
            msg = self.list_format.format(verctx.primary_name,
                    ', '.join(alts) if alts else '',
                    verctx.description)
            builder.script.echo(msg)
            
    def create_builder(self):
        return ScriptBuilder(self.platform)
        
class ScriptBuilder:
    def __init__(self, platform):
        self.__env = shenv.shell.EnvironmentBuilder()        
        self.__out = io.StringIO()
        self.__wri = shenv.shell.ShellWriter(platform.syntax,self.__out)
        self.__platform = platform
        
    @property
    def script(self):
        return self.__wri
    
    @property
    def env(self):
        return self.__env
    
    @property
    def pathvar(self):
        return self.__platform.pathvar
    
    def generate(self):
        out = io.StringIO()
        wri = shenv.shell.ShellWriter(self.__platform.syntax, out)
        wri.settrace(False)
        wri.comment('=== Environment ===')
        self.env.write(wri)
        wri.comment('===================')
        wri.line()
        wri.line()
        out.write(self.__out.getvalue())
        wri.line()
        return out.getvalue()
        
class BasicCategory(metaclass=abc.ABCMeta):
    
    def install(self,univ,cat,ver,builder):
        hv = self.__get_homevar(cat)
        h = self.__get_home(ver)
        if h and hv:
            builder.env.set(hv,h)
        for pi in self.__get_pathitems(cat, ver):
            builder.env.path_add(builder.pathvar, pi)

    def remove(self,univ,cat,ver,builder):
        hv = self.__get_homevar(cat)
        h = self.__get_home(ver)
        if h and hv:
            builder.env.remove(hv)
        for pi in self.__get_pathitems(cat, ver):
            builder.env.path_remove(builder.pathvar, pi)


    def clean(self,univ,cat,builder):
        hv = self.__get_homevar(cat)
        if hv:
            builder.env.remove(hv)
    
    @staticmethod
    def __get_homevar(cat):
        return getattr(cat,'homevar', None)

    @staticmethod
    def __get_home(ver):
        h = getattr(ver,'home', '')
        return os.path.abspath(h) if h else None
        
    @classmethod 
    def __get_pathitems(cls, cat, ver):
        pi = getattr(ver, 'pathitems', ()) if ver is not None else ()
        if not pi:
            pi = getattr(cat, 'pathitems', ())
        home = cls.__get_home(ver)
        if home:
            return (os.path.abspath(os.path.join(home, x)) for x in pi)
        return (os.path.abspath(x) for x in pi)

    


class App:
    
    def __init__(self, platform):
        self._platform = platform
        self._context = shenv.core.Context()
        self._processor = _Processor(self._context, self._platform)
        
    def universe(self):
        return self._context.universe()
    def category(self):
        return self._context.category()
    def version(self, category):
        return self._context.version(category)
    
    def main(self, args, out = None):
        if out is None:
            out = sys.stdout
        args = list(args)
        builder = self._processor.create_builder()
        #builder.script.echo()
        #print(':'.join(args),file=sys.stderr)
        cmd = '_handle_'+args[1] if len(args)>1 else ''
        if cmd and hasattr(self,cmd):
            try:
                getattr(self,cmd)(builder, *args[2:])
            except ShowUsageSignal:
                self.__show_usage(builder)
        else:
            self.__show_usage(builder)
        #builder.script.echo()
        out.write(builder.generate())

    def _handle_list(self, builder, *params):
        if (len(params)) not in {0,1}:
            raise ShowUsageSignal()
        if params:
            self._processor.list_versions(params[0], builder)
        else:
            self._processor.list_categories(builder)

    def _handle_spit(self, builder, *params):
        if (len(params)) not in {0,1}:
            raise ShowUsageSignal()
        if params:
            self._processor.spit_versions(params[0], builder)
        else:
            self._processor.spit_categories(builder)

    def _handle_show(self, builder, *params):
        if (len(params)) not in {0,1}:
            raise ShowUsageSignal()
        if params:
            self._processor.show_version(params[0], builder)
        else:
            self._processor.show_all_versions(builder)
            
    def _handle_set(self, builder, *params):
        if (len(params)) not in {1,2}:
            raise ShowUsageSignal()
        self._processor.enable_category(params[0], 
                params[1] if len(params)>1 else None, 
                builder)

    def _handle_unset(self, builder, *params):
        if len(params) != 1:
            raise ShowUsageSignal()
        self._processor.unspecify_category(params[0], builder)

    def _handle_disable(self, builder, *params):
        if len(params) != 1:
            raise ShowUsageSignal()
        self._processor.disable_category(params[0], builder)

    def _handle_init(self, builder, *params):
        if len(params) != 0:
            raise ShowUsageSignal()
        self._processor.setup(builder)
        
    def _handle_generate(self, builder, *params):
        if len(params) != 0:
            raise ShowUsageSignal()
        lines = shenv.cfggen.get_template_lines()
        for line in lines:
            builder.script.echo(line.rstrip())
        
    def __show_usage(self, builder):
        txt = self.usage_text
        for line in txt.splitlines():
            builder.script.echo(line.format(self.app_name)) 
        
    usage_text = """\
{0} - Utility to add or remove modules from shell environment

usage:

{0} set <cat>            -> enables <cat>, any version
{0} set <cat> <ver>      -> enables <cat>, <ver> 
{0} unset <cat>          -> unspecifies <cat>
{0} disable <cat>        -> forces <cat> to be disabled
{0} show <cat>           -> show current state for <cat>
{0} show                 -> show current state of all categories
{0} list <cat>           -> lists all versions for <cat>
{0} list                 -> lists all categories
{0} spit <cat>           -> list all versions for <cat> (unformatted)
{0} spit                 -> lists all categories (unformatted)
{0} init                 -> ensures a valid environment is installed
{0} generate             -> output a configuration file template
{0} [<anything-else>]    -> show help
"""
    app_name = 'shenv'

    

def _runpy(cfgscript, glos):
    cfgdir, cfgfile = os.path.split(os.path.abspath(cfgscript))
    cfgbase, _ = os.path.splitext(cfgfile)
    
    #TODO - testing (is this really any faster?)
    #import compileall 
    #compileall.compile_dir(cfgdir, maxlevels=0, quiet=True)
    
    save = type('tmp',(object,),{})()   #Make an empty object
    save.path, save.path_hooks = tuple(sys.path), tuple(sys.path_hooks)
    try:
        sys.path[:] = [cfgdir]
        sys.path_hooks[:] = []
        return runpy.run_module(cfgbase, init_globals=dict(glos), alter_sys=True)
    finally:
        sys.path[:], sys.path_hooks[:] = save.path, save.path_hooks
     
def main(argv):    
    shell = 'win32cmd'
    if len(argv) >=3 and argv[1] == '--shell':
        shell = argv[2]
        argv = argv[0:1] + argv[3:] 
    
    platform = _platforms.get(shell, _Win32Platform())
    
    if len(argv) < 3:
        print('usage: python -m shenv.app [--shell <shell>] <config-script> <generated-script> *args', 
              file=sys.stderr)
        print()
        print('args were: \"{0}\"'.format('\" \"'.join(argv)), file=sys.stderr)
        return 1
    
    configfile = os.path.abspath(argv[1])
    if not os.path.isfile(configfile):
        print('config script [{0}] does not exist or is not a file'
              .format(configfile),file=sys.stderr)
        return 2
    
    app = App(platform)
    glos = {'universe' : app.universe,
            'category' : app.category,
            'version' : app.version}
    _runpy(configfile, glos)
    
    
    innerargs = argv[0:1] + argv[3:]
    if argv[2] == '(stdout)':
        app.main(innerargs, sys.stdout)
    else:
        outputfile = os.path.abspath(argv[2])
        with open(outputfile,'w') as out:
            app.main(innerargs, out)
        
    return 0
    

if __name__ == '__main__':
    ec = main(sys.argv)
    sys.exit(ec)