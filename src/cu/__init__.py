from base64 import decodestring
from datetime import datetime
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

UIDS_RE = recompile( r'.*/(.*)/.*\.tar' )
TIMESTAMPS_RE = recompile( r'.*/([0-9]+)\.tar' )

all_uids = lambda : set( UIDS_RE.match( _ ).group( 1 ) for _ in glob( join( UPLOAD_DIR, '*', '[0-9]*.tar' ) ) )
all_timestamps = lambda uid: set( TIMESTAMPS_RE.match( _ ).group( 1 ) for _ in glob( join( UPLOAD_DIR, uid, '[0-9]*.tar' ) ) )
isots = lambda timestamp: datetime.fromtimestamp( int( timestamp ) / 1000 ).isoformat()
