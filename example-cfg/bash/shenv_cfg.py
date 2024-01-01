###############################
## shenv configuration script
##
## For normal operation, place this in %USERPROFILE%\.shenv\shenv_cfg.py
##
###############################
import sys
import os
from shenv.app import universe, category, version
from shenv.app import BasicCategory

#print(globals().keys(),file=sys.stderr)

#Normally universe, category, version are injected.  If not present, add them
#in case we are running directly as a script.
#if 'universe' not in globals():
#    app = App()
#    universe, category, version = app.universe, app.category, app.version
#    del app


@universe()
class Universe:
    pass


############################# Java ################################

@category()
class Java(BasicCategory):
    name = 'java'
    description = 'Java JDK' 
    homevar = 'JAVA_HOME'
    pathitems = ('bin',)
    autoenable = True
    
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('java -version')

@version(Java)
class JavaDefault:
    name = ('default',)
    description = 'OS Default Java' 
    home = '/usr/lib/jvm/default'

############################# Scala ################################

@category()
class Scala(BasicCategory):
    name = 'scala'
    description = 'Scala development environment' 
    homevar = 'SCALA_HOME'
    pathitems = ('bin',)
    autoenable = True
    
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('scala -version')

@version(Scala)
class Scala33:
    name = '3.3'
    description = 'Scala 3.3' 
    home = '/usr/local/devtools/scala/scala3-3.3.0'
    dependencies = (Java,)

############################# gcloud ################################

@category()
class Gcloud(BasicCategory):
    name = 'gcloud'
    description = 'gcloud' 
    homevar = 'GCLOUD_HOME'
    pathitems = ('bin',)
    autoenable = False
    
    def install(self,univ,cat,ver,builder):
        super(Gcloud, self).install(univ,cat,ver,builder)
        builder.env.add_post_var_command(f"source '{self.homevar}'/completion.bash.inc")

    def remove(self,univ,cat,ver,builder):
        super(Gcloud, self).remove(univ,cat,ver,builder)

        if ver is not None:
            builder.env.add_pre_var_command(f"complete -r bq gsutil")
            
    def clean(self,univ,cat,builder):
        super(Gcloud, self).clean(univ,cat,builder)
        builder.env.add_pre_var_command('complete -r bq gsutil 2>/dev/null')

    def query_version(self,univ,cat,ver,builder):
        builder.script.line("gcloud version | perl -pe 's/\n/; /' ; echo")

@version(Gcloud)
class GcloudStd:
    name = 'std'
    description = 'Gcloud standard install' 
    home = '/home/arnold/devtools/google-cloud-sdk'


############################# Common ################################

@category()
class Common(BasicCategory):
    name = 'common'
    autoenable = True
    description = 'Settings common to all environments' 
    
    
@version(Common)
class StandardCommon:
    name = 'std','standard'
    description = 'Standard settings common to all environments' 
    pathitems = tuple() if '_SHENV_INITPATH' not in os.environ else tuple(
            os.environ['_SHENV_INITPATH'].split(':')
            )

