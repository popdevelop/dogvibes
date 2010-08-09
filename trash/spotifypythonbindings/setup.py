from distutils.core import setup, Extension

module1 = Extension('spotifydogvibes',
                    include_dirs = ['/usr/local/include/spotify'],
                    libraries = ['spotify'],
                    library_dirs = ['/usr/local/lib'],
                    sources = ['spotify.c'])


setup (name = 'Spotify bindings for Dogvibes',
       version = '1.0',
       description = 'Spotify bindings for the Dogvibes audio server',
       author = 'Johan Gyllenspetz',
       author_email = 'johan.gyllenspetz@gmail.com',
       url = 'http://code.google.com/p/dogvibes',
       ext_modules = [module1])
