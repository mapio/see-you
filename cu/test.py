from argparse import ArgumentParser
from datetime import datetime
from glob import glob
from os import symlink, unlink
from os.path import join, islink, isdir
from re import compile as recompile
from shutil import rmtree

from . import UPLOAD_DIR
from .testrunner import TestRunner

def test( uid, timestamp = None, result_dir = None, clean = None ):
	if not result_dir: result_dir = UPLOAD_DIR
	if not timestamp:
		p = recompile( r'.*/([0-9]+)\.tar' )
		timestamp = max( p.match( _ ).group( 1 ) for _ in glob( join( UPLOAD_DIR, uid, '*.tar' ) ) )
	dest_dir = join( result_dir, uid, timestamp )
	if isdir( dest_dir ):
		if clean: rmtree( dest_dir )
		else: return None, dest_dir
	tr = TestRunner( uid, timestamp )
	tr.toxml()
	tr.saveto( dest_dir )
	latest = join( result_dir, uid, 'latest' )
	if islink( latest ): unlink( latest )
	symlink( timestamp, latest )
	ht_timestamp = datetime.fromtimestamp( int( timestamp ) / 1000 ).isoformat()
	return ht_timestamp, dest_dir

if __name__ == '__main__':

	parser = ArgumentParser()
	parser.add_argument( 'uid', help = 'The UID to test' )
	parser.add_argument( 'result_dir', help = 'The destination directory where to copy the results directory (default: UPLOAD_DIR)', nargs = '?' )
	parser.add_argument( 'timestamp', help = 'The timestamp of the upload to test (default: latest)', nargs = '?' )
	parser.add_argument( '--clean', '-v', default = False, action='store_true', help = 'Whether to clean the destination result directory first' )
	args = parser.parse_args()

	hrts, dest_dir = test( args.uid, args.timestamp, args.result_dir, args.clean )
	print ( 'Results for time {1} stored in {0}' if hrts else 'Results alreay present in {0} (use --clean to force re-testing)' ).format( dest_dir, hrts )
