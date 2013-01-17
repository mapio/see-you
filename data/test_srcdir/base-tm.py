SECRET_KEY = 'a very long secret'

MAX_CONTENT_LENGTH = 16 * 1024 * 1024

LANG = 'it'

EEG_HOME = '/tmp/vulcano_test/home'
UPLOAD_DIR = '/tmp/vulcano_test/uploads'

ENVIRONMENT_SETUP = """
export PATH="{0}/bin":\$PATH
export MAKEFILES="{0}/Makefile"
"""
