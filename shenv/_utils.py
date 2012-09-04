#_utils.py
import os
import errno
from os import path
import sys
import re
import abc
import optparse

_linebreak = re.compile('\\r\\n?|\\n')

class reiterable:
    def __init__(self,iterfn,*posn,**kwds):
        self.__fn = lambda : iterfn(*posn,**kwds)

    def __iter__(self):
        return self.__fn()
    

def _startswith(s, chk):
    return s[0:len(chk)]==chk


def _linesof(s):
    return _linebreak.split(s)

class _FileExistsError(Exception): pass

def _open_if_not_exist(filename, flags):
    try:
        fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except EnvironmentError as enverr:
        if enverr.errno == errno.EEXIST:
            raise _FileExistsError(filename) from enverr
        raise
    try:
        res = os.fdopen(fd,flags)
        fd = None
        return res
    finally:
        if fd is not None:
            os.close(fd)
            

def _get_text_resource(name):
    fullname = path.join(path.dirname(__file__),name)
    loader = globals().get('__loader__',None)
    if loader is not None:
        txt = loader.get_data(fullname)
    else:        
        with open(fullname) as inp:
            txt = inp.read()
    
    #I'm unclear as to whether loaders return bytes or strings
    if isinstance(txt, bytes):
        txt = txt.encode()
    return txt

class _TemplateApp(metaclass=abc.ABCMeta):
    
    def run(self,modpath,file_description, args=None):
        args = sys.argv[1:] if args is None else list(args)
        parser = optparse.OptionParser(
                    prog=modpath,
                    usage="python -m %prog [options]",
                    description="{0} file generator".format(file_description),
                    version="0.1",
                    add_help_option='True',
                )
        parser.add_option('-f','--file', metavar="FILE", dest='file', 
                          help="write output to FILE",default=None)
        parser.add_option("--overwrite", action='store_true', dest='overwrite',
                          default=False,help="""\
Overwrite the output file if it already exists.  By default, the program fails
if the output file already exists.  This option overrides that behavior.  If
the -f option is not in use then this option has no effect.""")
        parser.add_option("--quiet", action='store_true', dest='quiet',
                          default=False,help='Suppress non-syntax error messages')
        
        options, posargs = parser.parse_args(args)
        if len(posargs) > 0:
            parser.error('Invalid arguments: '+' '.join(posargs))
        
        self._doit(parser, options)
        
    def _doit(self, parser, options):
        prepare_data = self.prepare()
        if not options.file:
            self.perform(sys.stdout, prepare_data)
            return
        self.__ensuredir(options.file)
        ofn = open if options.overwrite else _open_if_not_exist
        try:
            with ofn(options.file, 'w') as out:
                self.perform(out, prepare_data)
        except _FileExistsError:
            if not options.quiet:
                print('File already exists.  Use the --overwrite option to force overwrite',
                      file=sys.stderr)
            sys.exit(3)
          
    def __ensuredir(self,file):
        dirnm = path.dirname(file)
        try:
            os.makedirs(dirnm) #TODO add mode
        except os.error:
            return False
        return True
            
    def prepare(self):
        pass
    
    @abc.abstractmethod
    def perform(self,out,prepare_data):
        pass