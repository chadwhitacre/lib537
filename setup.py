from distutils.core import setup


classifiers = [
    'Development Status :: 3 - Alpha'
  , 'Environment :: Console'
  , 'Intended Audience :: Developers'
  , 'License :: OSI Approved :: MIT License'
  , 'Natural Language :: English'
  , 'Operating System :: MacOS :: MacOS X'
  , 'Operating System :: Microsoft :: Windows'
  , 'Operating System :: POSIX'
  , 'Programming Language :: Python'
  , 'Topic :: Internet :: WWW/HTTP :: WSGI'
  , 'Topic :: Software Development :: Libraries :: Python Modules'
   ]

setup( name = 'lib537'
     , version = '1.0a1'
     , package_dir = {'':'src'}
     , packages = ['lib537']
     , description = 'lib537 is a Python library.'
     , long_description = """\
lib537 is a Python library bundling the following modules:

  httpy -- smooth over WSGI's worst warts
  mode -- manage the application life-cycle from debugging to production
  restarter -- automatically restart your program when module files change
"""
     , author = 'Chad Whitacre'
     , author_email = 'chad@zetaweb.com'
     , url = 'http://www.zetadev.com/software/lib537/'
     , classifiers = classifiers
      )
