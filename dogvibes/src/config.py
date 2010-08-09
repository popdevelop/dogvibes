import logging
import os

# -- Loads a config file, creates and returns a dictionary
def load(filename):

    defaults = {
        'MASTER_SERVER': 'dogvib.es',
        'ENABLE_SPOTIFY_SOURCE': '1',
        'ENABLE_LASTFM_SOURCE': '1',
        'ENABLE_FILE_SOURCE': '1',
        'DOGVIBES_USER': 'user',
        'DOGVIBES_PASS': 'pass',
        'SPOTIFY_USER': 'user',
        'SPOTIFY_PASS': 'pass',
        'LASTFM_USER': 'user',
        'LASTFM_PASS': 'pass',
        'HTTP_PORT': 2000,
        'WS_PORT': 9999,
        'FILE_SOURCE_ROOT': '/home/user/music'
        }

    try:
        execfile(filename, {}, defaults)
    except Exception, e:
        print "Found error in config, use defaults ", e
        pass

    for d in defaults:
        if d in os.environ:
            defaults[d] = os.environ[d]

    logging.debug(defaults)

    # return the fully-loaded dictionary object
    return defaults
