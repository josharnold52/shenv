###############################
## shenv configuration script
##
## For normal operation, place this in %USERPROFILE%\.shenv\shenv_cfg.py
##
###############################
import sys
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
    description = 'The JDK including JRE' 
    homevar = 'JAVA_HOME'
    pathitems = ('bin','jre/bin')
    autoenable = True
    
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('java -version')

@version(Java)
class JavaSun6:
    name = ('sun6','6')
    description = 'Sun JDK 6' 
    home = '/System/Library/Java/JavaVirtualMachines/1.6.0.jdk/Contents/Home'

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
class Scala292:
    name = '292'
    description = 'Scala 2.9.2' 
    home = '/Users/arnold/devtools/langs/scala/scala-2.9.2'
    dependencies = (Java,)

############################# Maven ################################

@category()
class Maven(BasicCategory):
    name = 'mvn'
    description = 'Maven' 
    homevar = 'M2_HOME'
    pathitems = ('bin',)
    autoenable = True
    
    def install(self,univ,cat,ver,builder):
        super(Maven, self).install(univ,cat,ver,builder)
        builder.env.set('MAVEN_HOME', ver.home)

    def remove(self,univ,cat,ver,builder):
        super(Maven, self).remove(univ,cat,ver,builder)
        if ver is not None:
            builder.env.remove('MAVEN_HOME')
            
    def clean(self,univ,cat,builder):
        super(Maven, self).clean(univ,cat,builder)
        builder.env.remove('MAVEN_HOME')

    def query_version(self,univ,cat,ver,builder):
        builder.script.line('mvn --version')

@version(Maven)
class Maven30:
    name = '30'
    description = 'Maven 3.0.x' 
    home = '/Users/arnold/devtools/tools/maven/apache-maven-3.0.3'
    dependencies = (Java,)


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
    
    pathitems = ('opt/local/bin',
            '/opt/local/sbin',
            '/Users/arnold/bin',
            '/usr/bin',
            '/bin',
            '/usr/sbin',
            '/sbin',
            '/usr/local/bin',
            '/usr/X11/bin',
            '/usr/local/git/bin',
            )

