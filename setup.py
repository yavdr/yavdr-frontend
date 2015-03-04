from distutils.core import setup
setup(name='arch-frontend',
      version='0.0.1',
      package_dir={'yavdr-frontend': ''},
      py_modules=['frontend', 'frontends.base', 'frontends.Softhddevice',
                  'frontends.kodi', 'frontends.xineliboutput', 'frontends.xine',
                  'tools.lirc_socket']
      )
