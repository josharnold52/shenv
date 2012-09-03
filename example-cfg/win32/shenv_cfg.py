
from shenv.app import BasicCategory



#Normally universe, category, version are injected.  If not present, add them
#in case we are running directly as a script.
if 'universe' not in globals():
    from shenv.app import App
    app = App()
    universe, category, version = app.universe, app.category, app.version
    del app

@universe()
class Universe:
    pass 

################################# JAVA ##########################################

@category()
class Java(BasicCategory):
    name = 'java'
    description = 'The JDK including JRE' 
    homevar = 'JAVA_HOME'
    pathitems = ('bin','jre/bin')
    
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('java -version')

@version(Java)
class JavaSun6:
    name = ('sun6','6')
    description = 'Sun JDK 6' 
    home = 'C:/devtools/JDK/sun/jdk1.6.0_21'
    
@version(Java)
class JavaSun5:
    name = ('sun5','5')
    description = 'Sun JDK 5' 
    home = 'C:/devtools/JDK/sun/jdk1.5.0_22'

@version(Java)
class JavaSun4:
    name = ('sun4','4')
    description = 'Sun J2SDK 1.4' 
    home = 'C:/devtools/JDK/sun/j2sdk1.4.2_19'

################################# SCALA ###########################################
@category()
class Scala(BasicCategory):
    name = 'scala'
    description = 'Scala runtime environment' 
    homevar = 'SCALA_HOME'
    pathitems = ('bin',)
    
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('scala -version')

@version(Scala)
class Scala28:
    name = '28'
    description = 'Scala 2.8' 
    home = 'C:/devtools/scala/scala-2.8.1.final'
    dependencies = (Java,)


################################ GROOVY ###########################################

@category()
class Groovy(BasicCategory):
    name = 'groovy'
    description = 'Groovy runtime environment' 
    homevar = 'GROOVY_HOME'
    pathitems = ('bin',)
    
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('groovy -version')

@version(Groovy)
class Groovy17:
    name = '17'
    description = 'Groovy 1.7' 
    home = 'C:/devtools/groovy/groovy-1.7.6'
    dependencies = (Java,)

################################ MAVEN ###########################################

@category()
class Maven(BasicCategory):
    name = ('maven', 'mvn')
    description = 'Maven build tool' 
    homevar = 'MAVEN_HOME'
    pathitems = ('bin',)
    
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('mvn -v')

@version(Maven)
class Maven30:
    name = '30'
    description = 'Maven 3.0' 
    home = 'C:/devtools/maven/apache-maven-3.0.2'
    dependencies = (Java,)

@version(Maven)
class Maven22:
    name = '22'
    description = 'Maven 2.2' 
    home = 'C:/devtools/maven/apache-maven-2.2.1'
    dependencies = (Java,)

@version(Maven)
class Maven20:
    name = '20'
    description = 'Maven 2.0' 
    home = 'C:/devtools/maven/apache-maven-2.0.11'
    dependencies = (Java,)
    
    
################################# ANT #############################################

@category()
class Ant(BasicCategory):
    name = 'ant'
    description = 'Ant build tool' 
    homevar = 'ANT_HOME'
    pathitems = ('bin',)
    
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('ant -version')

@version(Ant)
class Ant18:
    name = '18'
    description = 'Ant 1.8'  
    home = 'C:/devtools/ant/apache-ant-1.8.1'
    dependencies = (Java,)
    
    
################################ ASPECTJ ##########################################

@category()
class AspectJ(BasicCategory):
    name = ('aspectj','aj')
    description = 'AspectJ'
    homevar = 'ASPECTJ_HOME'
    pathitems = ('bin',)
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('ajc -version')
    
@version(AspectJ)
class AspectJ16:
    name = '16'
    description = 'AspectJ 1.6'
    home='C:/devtools/aspectj/aspectj1.6'
    dependencies = (Java,)
    
################################# PYTHON ##########################################

@category()
class Python(BasicCategory):
    name = ('python','py')
    description = 'A python runtime environment'
    homevar = 'PYTHONHOME'
    pathitems = ('',)

    def query_version(self,univ,cat,ver,builder):
        builder.script.line('python --version')

@version(Python)
class CPython31:
    name = ('C31','31')
    description = 'CPython version 31'
    home = 'C:/devtools/Python/31'

@version(Python)
class CPython27:
    name = ('C27','27')
    description = 'CPython version 27'
    home = 'C:/devtools/Python/27'

@version(Python)
class CPython25:
    name = ('C25','25')
    description = 'CPython version 25'
    home = 'C:/devtools/Python/25'

@version(Python)
class CPython32:
    name = ('C32','32')
    description = 'CPython version 32'
    home = 'C:/devtools/Python/32'

################################# RUBY ##########################################

@category()
class Ruby(BasicCategory):
    name = ('ruby',)
    description = 'A ruby runtime environment'
    homevar = 'RUBY_HOME'
    pathitems = ('bin',)

    def query_version(self,univ,cat,ver,builder):
        builder.script.line('ruby --version')

@version(Ruby)
class Ruby19:
    name = ('19',)
    description = 'Ruby version 1.9'
    home = 'C:/devtools/ruby/ruby1.9'
    
@version(Ruby)
class Ruby18:
    name = ('18',)
    description = 'Ruby version 1.8'
    home = 'C:/devtools/ruby/ruby1.8'
    

################################# HASKELL ##########################################

@category()
class Haskell(BasicCategory):
    name = ('haskell',)
    description = 'A haskell runtime environment'

@version(Haskell)
class GHCI:
    name = ('ghc',)
    description = 'Haskell ghc environment'
    home = 'C:/devtools/haskell/haskell-platform/2010.2.0.0'
    pathitems = ('bin',)

    def install(self,univ,cat,ver,builder):
        import os.path
        builder.env.set('GHC_HOME',os.path.abspath(self.home))
        cat.install(univ,cat,ver,builder)
        
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('ghc --version')
        

################################# PERL ##########################################

@category()
class Perl(BasicCategory):
    name = ('perl',)
    description = 'A perl runtime environment'
    homevar = 'PERL_HOME'
        
    def query_version(self,univ,cat,ver,builder):
        builder.script.line('perl -v')
        
@version(Perl)
class Straw512:
    name = ('512','straw512')
    description = 'Strawberry Perl 5.12'
    home = 'C:/devtools/perl/strawberry/5.12'
    pathitems = ('c/bin','perl/site/bin','perl/bin')

    def install(self,univ,cat,ver,builder):
        import os.path
        builder.env.set('TERM','dumb')
        cat.install(univ,cat,ver,builder)

        
                

############################# COMMON ##################################

@category()
class Common(BasicCategory):
    name = 'common'
    autoenable = True
    description = 'Settings common to all environments' 
    
    
    
@version(Common)
class StandardCommon:
    name = 'std','standard'
    description = 'Standard settings common to all environments' 
    
    pathitems = ('c:/windows/system32',
                 'c:/windows',
                 'c:/windows/system32/wbem',
                 'c:/utility')
