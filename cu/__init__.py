from base64 import decodestring
from io import BytesIO
from os import environ
from os.path import abspath, expandvars, expanduser
from sys import exit

_config = {}
try:
	execfile( environ.get( 'TM_SETTINGS' ), _config, _config )
except:
	exit( 'Error loading TM_SETTINGS, is such variable defined?' )

TAR_DATA = BytesIO( decodestring( _config[ 'TAR_DATA' ] ) )
UPLOAD_DIR = abspath( expandvars( expanduser( _config[ 'UPLOAD_DIR' ] ) ) )
