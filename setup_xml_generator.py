# -*- coding: utf-8 -*-

# A simple setup script to create an executable using PyQt4. This also
# demonstrates the method for creating a Windows executable that does not have
# an associated console.
#
# PyQt4app.py is a very simple type of PyQt4 application
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application

from cx_Freeze import setup, Executable

includes = ['atexit', 'lxml']
excludes = ['collections.abc', 'tkinter']	
packages = ['lxml']
	
options = {
    'build_exe': {
        'includes': includes,
		"excludes": excludes,
		'packages': packages
    }
}

executables = [
    Executable('iTunes_Xml_Generator_0630A.py', base='Win32GUI')
]

setup(name='iTunes Xml Generator',
      version='1.0',
      description='Generates xmls for iTunes',
      options=options,
      executables=executables
      )