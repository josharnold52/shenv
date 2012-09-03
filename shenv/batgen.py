#batgen.py

from os import path
from shenv import _utils, shell
import sys
import string



def printall(iterable, file):
    for line in iterable:
        assert line.find('\r') == -1
        assert line.find('\n') == -1
        print(line,file=file)

def main(argv):
    exedir, exefile = path.split(path.abspath(sys.executable))
    syntax = shell.Win32CmdSyntax() #TODO support other syntax
    
    #TODO: Encodings?
    tmpltext = _utils._get_text_resource('data/shenv.bat.tmpl')
    template = string.Template(tmpltext)
    
    
    tmpltext = template.substitute({
                'set_shenv_python_dir' : syntax.setvar('__EMGR_PYTHON_DIR__', exedir),
                'set_shenv_python_file' : syntax.setvar('__EMGR_PYTHON_FILE__', exefile),
                    })

    lines = list(_utils._linesof(tmpltext))
    
    class App(_utils._TemplateApp):
        def perform(self,out,prepare_data):
            printall(lines,out)
            
    App().run('shenv.batgen', 'shenv batch script')
    return 0


if __name__ == '__main__':
    ec = main(sys.argv)
    sys.exit(ec)
