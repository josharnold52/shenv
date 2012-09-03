shenv
=====

Shell environment manager

### Bash Installation

(todo)

### Win32 cmd Installation

To install from source, first create a MSI via:

```
python setup.py dist_msi
```

Then run installer (in dist)

### Win32 cmd Alternate Installation

Alternatively, install python packages via something like:

```
python setup.py install
```
 
Then generate the batch file with:
    
```
python -m shenv.batgen --overwrite -f \path\to\shenv.bat
```   

(or just run "python -m shenv.batgen" and capture stdout)

