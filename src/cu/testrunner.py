from collections import namedtuple
from glob import glob
from os import chmod, unlink
from os.path import join, dirname
from re import compile as recompile
from shutil import copytree, rmtree
from subprocess import check_output, STDOUT, CalledProcessError
from tarfile import TarFile
from tempfile import mkdtemp
from time import time

from . import TAR_DATA, UPLOAD_DIR, isots

CDATA_ALLOWED = frozenset( '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \t\n\r' )

asciify = lambda s: ''.join( map( lambda c: c if c in CDATA_ALLOWED else r'\x{0:0x}'.format( ord( c ) ), s ) )

MakeResult = namedtuple( 'MakeResult', 'elapsed output error' )

def rmrotree( path ):
	def _oe( f, p, e ):
		if p == path: return
		pp = dirname( p )
		chmod( pp, 0700 )
		chmod( p, 0700 )
		unlink( p )
	rmtree( path, onerror = _oe )

class TestCase( object ):

	COMPILE, EXECUTION, DIFF = 'compile', 'execution', 'diff'

	def __init__( self, name, type_, time = 0, failure = None, error = None, stdout = None, stderr = None ):
		self.name = name
		self.type = type_
		self.time = time
		self.failure = failure
		self.error = error
		self.stdout = stdout
		self.stderr = stderr

	def toxml( self, classname ):
		def _wrap( elem, cont, type_ = None ):
			return '<{0}{1}><![CDATA[\n{2}\n\t]]></{0}>'.format(
				elem, ' type="{0}" message="{0}"'.format( type_ ) if type_ else '', asciify( cont )
			)
		content = []
		if self.error:
			content.append( _wrap( 'error', self.error, self.type ) )
		elif self.failure:
			content. append( _wrap( 'failure', self.failure, self.type ) )
		if self.stdout:
			content.append( _wrap( 'system-out', self.stdout ) )
		if self.stderr:
			content.append( _wrap( 'system-err', self.stderr ) )
		return '\t<testcase time="{0}" classname="{1}" name="{2}"'.format( self.time, classname, self.name ) + (
			'>{0}</testcase>'.format( '\n\t'.join( content ) ) if content else '/>' )

class TestRunner( object ):

	# cases_map := exercise_name -> ( case_num, )
	# makes_map := exercise_name -> MakeResult
	# suites_map := exercise_name -> test_suite; test_suite := ( TestCase, )

	def __init__( self, uid, timestamp ):
		temp_dir = mkdtemp( prefix = 'cu-', dir = '/tmp' )
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

	def __str__( self ):
		return 'TestRunner< "{0}", "{1}", "{2}" >'.format( self.uid, isots( self.timestamp ), self.temp_dir )

	def __enter__( self ):
		return self

	def __exit__( self, exc_type, exc_value, traceback ):
		self.delete()
		return False  # pass the exceptions upwards

	def make( self ):
		def _make( exercise ):
			try:
				cmd = [ 'make',
					'-f', join( self.temp_dir, 'bin', 'Makefile' ),
					'-C', join( self.temp_dir, exercise ),
					'pulisci', 'LC_ALL=C'
				]
				stdout = unicode( check_output( cmd, stderr = STDOUT ), errors = 'replace' )
				cmd = [ 'make',
					'-f', join( self.temp_dir, 'bin', 'Makefile' ),
					'-C', join( self.temp_dir, exercise ),
					'test', 'exit_on_fail=false', 'blue=echo', 'red=echo', 'reset=echo', 'LC_ALL=C'
				]
				start = time()
				stdout = unicode( check_output( cmd, stderr = STDOUT ), errors = 'replace' )
			except CalledProcessError as e:
				stdout = None
				stderr = unicode( e.output, errors = 'replace' )
			else:
				stderr = None
			finally:
				elapsed = int( ( time() - start ) * 1000 ) / 1000.0
			return MakeResult( elapsed, stdout, stderr )
		self.makes_map = dict( ( name, _make( name ) ) for name in self.cases_map.keys() )

	def getres( self, exercise, case_num ):
		def _r( exercise, path, case_num ):
			with open( join( self.temp_dir, exercise, path.format( case_num ) ) ) as f: data = unicode( f.read(), errors = 'replace' )
			return data
		stderr = _r( exercise, '.errors-{0}', case_num )
		if stderr:
			actual = diffs = None
		else:
			actual = _r( exercise, 'actual-{0}.txt', case_num )
			diffs = _r( exercise, 'diffs-{0}.txt', case_num )
		return stderr, actual, diffs

	def collect( self ):
		if not self.makes_map: self.make()
		suites_map = {}
		for exercise, cases in self.cases_map.items():
			mr = self.makes_map[ exercise ]
			ts = [ TestCase(
				'make', TestCase.COMPILE, mr.elapsed, error = mr.error, stderr = mr.error, stdout = mr.output
			) ]
			if not mr.error:
				for case_num in cases:
					case = '{0}'.format( case_num )
					stderr, actual, diffs = self.getres( exercise, case_num )
					if stderr:
						ts.append( TestCase( case, TestCase.EXECUTION, error = stderr ) )
					else:
						if diffs:
							ts.append( TestCase( case, TestCase.DIFF, failure = diffs, stdout = actual ) )
						else:
							ts.append( TestCase( case, TestCase.DIFF ) )
			suites_map[ exercise ] = tuple( ts )
		self.suites_map = suites_map

	# based on http://windyroad.org/dl/Open%20Source/JUnit.xsd
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
				for tc in results: out.write( tc.toxml( classname ) + '\n' )
				out.write( '</testsuite>\n' )

	def saveto( self, dest_dir ):
		if not self.temp_dir: raise AttributeError( 'Working directory already deleted' )
		copytree( self.temp_dir, dest_dir )
		chmod( dest_dir, 0700 )

	def delete( self ):
		if self.temp_dir:
			rmrotree( self.temp_dir )
			self.temp_dir = None
