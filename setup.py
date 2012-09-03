'''
Created on Jan 24, 2011

@author: Arnold
'''

from distutils.core import setup
from distutils.command.bdist_msi import bdist_msi, PyDialog

from msilib import add_data

class my_bdist_msi(bdist_msi):
    
    def finalize_options(self):
        super().finalize_options()
        self.versions = [v for v in self.versions if v[0:1]=='3']
    
    def add_scripts(self):
        super().add_scripts()
        start = 6850
        for ver in self.versions + [self.other_version]:
            install_action = "post_batgen." + ver
            exe_prop = "PYTHON" + ver
            add_data(self.db, "CustomAction",
                    [(install_action, 50, exe_prop, '-m shenv.batgen --overwrite -f \"[EmgrBatDir]\\shenv.bat\"')])
            add_data(self.db, "InstallExecuteSequence",
                    [(install_action, "&Python%s=3" % ver, start)])
            start += 1
    
    def add_ui(self):
        super().add_ui();
        
        db = self.db
        x = y = 50
        w = 370
        h = 300
        title = "[ProductName] Setup"

        # see "Dialog Style Bits"
        modal = 3      # visible | modal
        modeless = 1   # visible

        add_data(db, "Property",
             # See "DefaultUIFont Property"
             [("EmgrBatDir", "c:\\utility"),
             ])


        add_data(db, "InstallUISequence", [
                 ("SelectBatDest", "Not Installed", 1231),
                 ])
        
        #####################################################################
        # Feature (Python directory) selection
        seldlg = PyDialog(db, "SelectBatDest", x, y, w, h, modal, title,
                        "Next", "Next", "Cancel")
        seldlg.title("Select the destination for the shenv.bat file")

        seldlg.text("Hint", 15, 30, 300, 20, 3,
                    "Select the directory where the shenv.bat file is installed."
                    )
        
        seldlg.back("< Back", None, active=1)
        c = seldlg.next("Next >", "Cancel")
        order = 1
        c.event("SpawnWaitDialog", "WaitForCostingDlg", ordering=order + 1)
        c.event("EndDialog", "Return", ordering=order + 2)
        c = seldlg.cancel("Cancel", "PathEdit")  #TODO : next cointrol
        c.event("SpawnDialog", "CancelDlg")

        c = seldlg.control("PathEdit", "PathEdit", 15, 60, 300, 16, 3,
                   "EmgrBatDir", "YoMan", "Next", None)


def main():
    setup(
        name='shenv',
        version='0.1',
        description='Utilities for managing the shell environment',
        author='Joshua Arnold',
        packages=['shenv','shenv.test'],
        package_data={'shenv': ['data/*.tmpl']},
        scripts=[],
        classifiers = [
            'Development Status :: 2 - Pre-Alpha',
            'Environment :: Win32 (MS Windows)',
            'Intended Audience :: Developers',
        ],
        cmdclass = {
            'bdist_msi' : my_bdist_msi
        },
        options = {
            'bdist_msi' : {
            },
        },
    )
    
if __name__ == '__main__':
    main()