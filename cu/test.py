from argparse import ArgumentParser
from collections import namedtuple
from datetime import datetime
from glob import glob
from os import symlink, unlink, chmod
from os.path import join, islink, isdir
from re import compile as recompile
from shutil import copytree, rmtree
from subprocess import check_output, STDOUT, CalledProcessError
from tarfile import TarFile
from tempfile import mkdtemp
from time import time

from . import TAR_DATA, UPLOAD_DIR

isots = lambda timestamp: datetime.fromtimestamp( int( timestamp ) / 1000 ).isoformat()

TestCase = namedtuple( 'TestCase', 'name time failure error' )

DEBUG = 1

def make( makefile, exercise ):
	try:
		cmd = [ 'make', '-f', makefile, '-C', exercise, 'pulisci', 'test', 'exit_on_fail=false', 'blue=echo', 'red=echo', 'reset=echo' ]
		if DEBUG: print ' '.join( cmd )
		start = time()
		check_output( cmd, stderr = STDOUT )
	except CalledProcessError as e:
		output = e.output
	else:
		output = None
	finally:
		elapsed = int( ( time() - start ) * 100 ) / 100
	return elapsed, output

def unitize( temp_dir, uid, timestamp ):
	timestamp = isots( timestamp )
	makefile = join( temp_dir, 'bin', 'Makefile' )
	p = recompile( r'.*/esercizio-([0-9]+)/(input-(.*)\.txt)?' )
	for ex in glob( join( temp_dir, 'esercizio-*/' ) ):
		exn = p.match( ex ).group( 1 )
		classname = '{0}.esercizio-{1}'.format( uid, exn )
		elapsed, output = make( makefile, ex )
		if output:
			ts = [ TestCase( 'COMPILE', '0', None, output ) ]
		else:
			ts = []
			for inf in glob( join( ex, 'input-*.txt' ) ):
				testn = p.match( inf ).group( 3 )
				case = 'case-{0}'.format( testn )
				with open( join( ex, '.errors-{0}'.format( testn ) ) ) as f: errors = f.read()
				if errors:
					ts.append( TestCase( case, '0', None,  errors ) )
				else:
					with open( join( ex, 'diffs-{0}.txt'.format( testn ) ) ) as f: diffs = f.read()
					ts.append( TestCase( case, '0', diffs if diffs else None, None ) )
		tests = len( ts )
		failures = sum( 1 for _ in ts if _.failure )
		errors = sum( 1 for _ in ts if _.error )
		with open( join( temp_dir, 'TEST-{0}.xml'.format( classname ) ), 'w' ) as out:
			out.write( '<?xml version="1.0" encoding="UTF-8" ?>\n' )
			out.write( '<testsuite failures="{0}" time="{1}" errors="{2}" skipped="0" tests="{3}" name="{4}" timestamp="{5}" hostname="localhost">\n'.format(
				failures, elapsed, errors, tests, classname, timestamp ) )
			for tc in ts:
				if tc.error:
					content = '<error><![CDATA[\n{0}\n\t]]></error>'.format( tc.error )
				elif tc.failure:
					content = '<failure><![CDATA[\n{0}\n\t]]></failure>'.format( tc.failure )
				else:
					content = ''
				out.write( '\t<testcase time="0" classname="{0}" name="{1}">{2}</testcase>\n'.format(
					classname, tc.name, content ) )
			out.write( '</testsuite>\n' )

def setup( uid, timestamp ):
	td = mkdtemp( prefix = 'cu-', dir = '/tmp' )
	if DEBUG: print td
	TAR_DATA.seek( 0 )
	with TarFile.open( mode = 'r', fileobj = TAR_DATA ) as tf: tf.extractall( td )
	with TarFile.open( join( UPLOAD_DIR, uid, timestamp + '.tar' ), mode = 'r' ) as tf: tf.extractall( td )
	return td

def test( uid, timestamp = None, result_dir = None, clean = None, raise_on_fail = True ):
	if not result_dir: result_dir = UPLOAD_DIR
	if not timestamp:
		p = recompile( r'.*/([0-9]+)\.tar' )
		timestamp = max( p.match( _ ).group( 1 ) for _ in glob( join( UPLOAD_DIR, uid, '*.tar' ) ) )
	dest_dir = join( result_dir, uid, timestamp )
	if isdir( dest_dir ):
		if clean: rmtree( dest_dir )
		else: return None, dest_dir
	td = setup( uid, timestamp )
	unitize( td, uid, timestamp )
	copytree( td, dest_dir )
	chmod( dest_dir, 0700 )
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
