from setuptools import setup, find_packages, Extension
setup(name='Mumoro',
      version='1.0',
      author= 'Tristram',
      author_email = 'tristramg@gmail.com',
      url = 'http://github.com/Tristramg/mumoro/',
      packages = ['lib', 'lib.core', 'web'],

      install_requires = ['cherrypy', 'genshi', 'simplejson', 'transitfeed', 'psycopg2', 'setuptools-git'],
      ext_modules = [
          Extension("lib.core._mumoro",
              sources=["lib/core/martins.cpp", "lib/core/graph_wrapper.cpp", "lib/core/mumoro_wrap.cpp"],
              swig_opts=['-c++'],
              include_dirs=['lib/core/'])
          ]

      )

