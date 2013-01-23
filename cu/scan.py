from argparse import ArgumentParser
from collections import defaultdict
from glob import glob
from os.path import basename, join, split, splitext

from . import UPLOAD_DIR
from .test import test

def scan( result_dir = None, clean = False ):
	uid2tars = defaultdict( list )
	for tar in glob( join( UPLOAD_DIR, '*', '*.tar' ) ):
		base, tarext = split( tar )
		uid = basename( base )
		ts, _ = splitext( tarext )
		uid2tars[ uid ].append( ts )
	for uid, tss in uid2tars.items():
		hrts, dest_dir = test( uid, max( tss ), result_dir, clean, False )
		print ( 'Results for time {1} stored in {0}' if hrts else 'Results alreay present in {0} (use --clean to force re-testing)' ).format( dest_dir, hrts )


if __name__ == '__main__':

	parser = ArgumentParser()
	parser.add_argument( 'result_dir', help = 'The destination directory where to copy the results directory (default: UPLOAD_DIR)', nargs = '?' )
	parser.add_argument( '--clean', '-v', default = False, action='store_true', help = 'Whether to clean the destination result directory first' )
	args = parser.parse_args()

	scan( args.result_dir, args.clean )
