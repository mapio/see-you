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
MakeResult = namedtuple( 'MakeResult', 'elapsed stdout stderr' )
Exercise = namedtuple( 'Exercise', 'path cases' )

DEBUG = 1

# exercise_num -> MakeResult
def make( cases_map, makefile ):
	def _make( path ):
		try:
			cmd = [ 'make', '-f', makefile, '-C', path, 'pulisci', 'test', 'exit_on_fail=false', 'blue=echo', 'red=echo', 'reset=echo' ]
			if DEBUG: print ' '.join( cmd )
			start = time()
			stdout = check_output( cmd, stderr = STDOUT )
			stderr = None
		except CalledProcessError as e:
			stdout = None
			stderr = e.stdout
		finally:
			elapsed = int( ( time() - start ) * 100 ) / 100
		return MakeResult( elapsed, stdout, stderr )
	res = {}
	for exercise_num, path_cases in cases_map.items():
		res[ exercise_num ] = _make( path_cases[ 0 ] )
	return res

# exercise_num -> Exercise
def cases( base_dir ):
	re = recompile( r'.*/esercizio-([0-9]+)/(input-(.*)\.txt)?' )
	res = {}
	for path in glob( join( base_dir, 'esercizio-*/' ) ):
		res[ re.match( path ).group( 1 ) ] = Exercise( path, (
			re.match( input_file_path ).group( 3 ) for input_file_path in glob( join( path, 'input-*.txt' ) )
		) )
	return res

def collect( temp_dir, uid, timestamp ):
	timestamp = isots( timestamp )
	cases_map = cases( temp_dir )
	make_map = make( cases_map, join( temp_dir, 'bin', 'Makefile' ) )
	for exercise_num, exercise in cases_map.items():
		mr = make_map[ exercise_num ]
		ts = [ TestCase( 'COMPILE', '0', None, mr.stderr ) ]
		classname = '{0}.esercizio-{1}'.format( uid, exercise_num )
		for case_num in exercise.cases:
			case = 'case-{0}'.format( case_num )
			with open( join( exercise.path, '.errors-{0}'.format( case_num ) ) ) as f: stderr = f.read()
			if stderr:
				ts.append( TestCase( case, '0', None,  stderr ) )
			else:
				with open( join( exercise.path, 'diffs-{0}.txt'.format( case_num ) ) ) as f: diffs = f.read()
				ts.append( TestCase( case, '0', diffs if diffs else None, None ) )
		tests = len( ts )
		failures = sum( 1 for _ in ts if _.failure )
		errors = sum( 1 for _ in ts if _.error )
		with open( join( temp_dir, 'TEST-{0}.xml'.format( classname ) ), 'w' ) as out:
			out.write( '<?xml version="1.0" encoding="UTF-8" ?>\n' )
			out.write( '<testsuite failures="{0}" time="{1}" errors="{2}" skipped="0" tests="{3}" name="{4}" timestamp="{5}" hostname="localhost">\n'.format(
				failures, mr.elapsed, errors, tests, classname, timestamp ) )
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

def test( uid, timestamp = None, result_dir = None, clean = None ):
	if not result_dir: result_dir = UPLOAD_DIR
	if not timestamp:
		p = recompile( r'.*/([0-9]+)\.tar' )
		timestamp = max( p.match( _ ).group( 1 ) for _ in glob( join( UPLOAD_DIR, uid, '*.tar' ) ) )
	dest_dir = join( result_dir, uid, timestamp )
	if isdir( dest_dir ):
		if clean: rmtree( dest_dir )
		else: return None, dest_dir
	td = setup( uid, timestamp )
	collect( td, uid, timestamp )
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
