#cfggen.py

from os import path, environ
from shenv import _utils
import sys
import string

def printall(iterable, file):
    for line in iterable:
        assert line.find('\r') == -1
        assert line.find('\n') == -1
        print(line,file=file)

def winpathitems():
    srchpath = environ.get('PATH','')
    windir = environ.get('WINDIR','')
    if not (srchpath and windir):
        return ()
    windir = path.normcase(windir)
    return (p for p in srchpath.split(path.pathsep) if 
              _utils._startswith(path.normcase(p), windir))

def pathitems():
    srchpath = environ.get('PATH','')
    return srchpath.split(path.pathsep)
    
def get_template_lines():
    exedir, _ = path.split(path.abspath(sys.executable))

    tmpltext = _utils._get_text_resource('data/shenv_cfg.py.tmpl')

    template = string.Template(tmpltext)
    tmpltext = template.substitute({
                'pyver' : '31',
                'pyhome' : exedir,
                'windirs' : repr(tuple(winpathitems())),
                'pathdirs' : repr(tuple(pathitems()))
                    })

    return list(_utils._linesof(tmpltext))

def main(argv):
    lines = get_template_lines()
    
    class App(_utils._TemplateApp):
        def perform(self,out,prepare_data):
            printall(lines,out)
            
    App().run('shenv.cfggen', 'shenv configuration')
    return 0


if __name__ == '__main__':
    ec = main(sys.argv)
    sys.exit(ec)
