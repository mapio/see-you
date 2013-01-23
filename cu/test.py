from argparse import ArgumentParser
from glob import glob
from os import symlink, unlink
from os.path import join, islink, isdir
from re import compile as recompile
from shutil import rmtree

from . import UPLOAD_DIR
from .testrunner import TestRunner, isots

def test( uid, timestamp = None, result_dir = None, clean = None ):
	if not result_dir: result_dir = UPLOAD_DIR
	if not timestamp:
		re = recompile( r'.*/([0-9]+)\.tar' )
		timestamp = max( re.match( _ ).group( 1 ) for _ in glob( join( UPLOAD_DIR, uid, '*.tar' ) ) )
	dest_dir = join( result_dir, uid, timestamp )
	if isdir( dest_dir ):
		if clean: rmtree( dest_dir )
		else: return 'skipped ({0} already exists, corresponding to time {1})'.format( dest_dir, isots( timestamp ) )
	tr = TestRunner( uid, timestamp )
	tr.toxml()
	tr.saveto( dest_dir )
	latest = join( result_dir, uid, 'latest' )
	if islink( latest ): unlink( latest )
	symlink( timestamp, latest )
	return 'saved in {0} by {1}'.format( dest_dir, tr )

if __name__ == '__main__':

	parser = ArgumentParser()
	parser.add_argument( '--uid', help = 'The UID to test (default: all)' )
	parser.add_argument( '--result_dir', help = 'The destination directory where to copy the results directory (default: UPLOAD_DIR)' )
	parser.add_argument( '--timestamp', help = 'The timestamp of the upload to test (default: latest)' )
	parser.add_argument( '--clean', action='store_true', help = 'Whether to clean the destination result directory first' )
	args = parser.parse_args()

	if not args.uid: re = recompile( r'.*/(.*)/.*\.tar' )
	for uid in [ args.uid ] if args.uid else set( re.match( _ ).group( 1 ) for _ in glob( join( UPLOAD_DIR, '*', '*.tar' ) ) ):
		print 'Test for {0}: {1}'.format( uid, test( uid, args.timestamp, args.result_dir, args.clean ) )
