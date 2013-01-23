from collections import namedtuple
from datetime import datetime
from glob import glob
from os import chmod
from os.path import join
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

DEBUG = 1

class TestRunner( object ):

	# cases_map := exercise_name -> ( case_num, )
	# makes_map := exercise_name -> MakeResult
	# suites_map := exercise_name -> ( TestCase, )

	def __init__( self, uid, timestamp ):
		temp_dir = mkdtemp( prefix = 'cu-', dir = '/tmp' )
		if DEBUG: print temp_dir
		TAR_DATA.seek( 0 )
		with TarFile.open( mode = 'r', fileobj = TAR_DATA ) as tf: tf.extractall( temp_dir )
		with TarFile.open( join( UPLOAD_DIR, uid, timestamp + '.tar' ), mode = 'r' ) as tf: tf.extractall( temp_dir )
		re = recompile( r'.*/(esercizio-[0-9]+)/(input-(.*)\.txt)?' )
		cases_map = {}
		for path in glob( join( temp_dir, 'esercizio-*/' ) ):
			cases_map[ re.match( path ).group( 1 ) ] = (
				re.match( input_file_path ).group( 3 ) for input_file_path in glob( join( path, 'input-*.txt' ) )
			)
		self.uid = uid
		self.timestamp = timestamp
		self.temp_dir = temp_dir
		self.cases_map = cases_map
		self.makes_map = None
		self.suites_map = None

	def make( self ):
		def _make( exercise ):
			try:
				cmd = [ 'make',
					'-f', join( self.temp_dir, 'bin', 'Makefile' ),
					'-C', join( self.temp_dir, exercise ),
					'pulisci', 'test', 'exit_on_fail=false', 'blue=echo', 'red=echo', 'reset=echo'
				]
				if DEBUG: print ' '.join( cmd )
				start = time()
				stdout = check_output( cmd, stderr = STDOUT )
				stderr = None
			except CalledProcessError as e:
				stdout = None
				stderr = e.stdout
			finally:
				elapsed = int( ( time() - start ) * 1000 ) / 1000.0
			return MakeResult( elapsed, stdout, stderr )
		self.makes_map = dict( ( name, _make( name ) ) for name in self.cases_map.keys() )

	def collect( self ):
		if not self.makes_map: self.make()
		suites_map = {}
		for exercise, cases in self.cases_map.items():
			mr = self.makes_map[ exercise ]
			ts = [ TestCase( 'COMPILE', mr.elapsed, None, mr.stderr ) ]
			for case_num in cases:
				case = 'case-{0}'.format( case_num )
				with open( join( self.temp_dir, exercise, '.errors-{0}'.format( case_num ) ) ) as f: stderr = f.read()
				if stderr:
					ts.append( TestCase( case, '0', None,  stderr ) )
				else:
					with open( join( self.temp_dir, exercise, 'diffs-{0}.txt'.format( case_num ) ) ) as f: diffs = f.read()
					ts.append( TestCase( case, '0', diffs if diffs else None, None ) )
			suites_map[ exercise ] = tuple( ts )
		self.suites_map = suites_map

	def toxml( self ):
		if not self.suites_map: self.collect()
		for exercise, results in self.suites_map.items():
			classname = '{0}.{1}'.format( self.uid, exercise )
			tests = len( results )
			failures = sum( 1 for _ in results if _.failure )
			errors = sum( 1 for _ in results if _.error )
			elapsed = results[ 0 ].time
			with open( join( self.temp_dir, 'TEST-{0}.xml'.format( classname ) ), 'w' ) as out:
				out.write( '<?xml version="1.0" encoding="UTF-8" ?>\n' )
				out.write( '<testsuite failures="{0}" time="{1}" errors="{2}" skipped="0" tests="{3}" name="{4}" timestamp="{5}" hostname="localhost">\n'.format(
					failures, elapsed, errors, tests, classname, isots( self.timestamp ) ) )
				for tc in results:
					if tc.error:
						content = '<error><![CDATA[\n{0}\n\t]]></error>'.format( tc.error )
					elif tc.failure:
						content = '<failure><![CDATA[\n{0}\n\t]]></failure>'.format( tc.failure )
					else:
						content = ''
					out.write( '\t<testcase time="0" classname="{0}" name="{1}">{2}</testcase>\n'.format(
						classname, tc.name, content ) )
				out.write( '</testsuite>\n' )

	def saveto( self, dest_dir ):
		if not self.temp_dir: raise AttributeError( 'Working directory already deleted' )
		copytree( self.temp_dir, dest_dir )
		chmod( dest_dir, 0700 )

	def delete( self ):
		if self.temp_dir:
			rmtree( self.temp_dir )
			self.temp_dir = None
