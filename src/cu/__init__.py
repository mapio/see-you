from base64 import decodestring
from glob import glob
from io import BytesIO
from os import environ
from os.path import abspath, expandvars, expanduser, join
from re import compile as recompile
from sys import exit

_config = {}
try:
	execfile( environ.get( 'CU_SETTINGS' ), _config, _config )
except:
	exit( 'Error loading CU_SETTINGS, is such variable defined?' )

TAR_DATA = BytesIO( decodestring( _config[ 'TAR_DATA' ] ) )
UPLOAD_DIR = abspath( expandvars( expanduser( _config[ 'UPLOAD_DIR' ] ) ) )

def all_uids():
	re = recompile( r'.*/(.*)/.*\.tar' )
	return set( re.match( _ ).group( 1 ) for _ in glob( join( UPLOAD_DIR, '*', '[0-9]*.tar' ) ) )
