from distutils.core import setup
setup(name='arch-frontend',
      version='0.0.1',
      py_modules=['frontend', 'frontends.base', 'frontends.Softhddevice',
                  'frontends.xbmc', 'frontends.xineliboutput', 'frontends.xine',
                  'tools.lirc_socket']
      )
