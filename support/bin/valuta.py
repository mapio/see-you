from collections import namedtuple
from datetime import datetime
from glob import glob
from os.path import join
from re import compile as recompile
from subprocess import check_output, STDOUT, CalledProcessError
from time import time
from sys import argv

uid, timestamp = argv[ 1: ]
timestamp = datetime.fromtimestamp( int( timestamp ) / 1000 ).isoformat()

p = recompile( r'esercizio-([0-9]+)/(input-(.*)\.txt)?' )

TestCase = namedtuple( 'TestCase', 'name time failure error' )

for ex in glob( 'esercizio-*/' ):
	exn = p.match( ex ).group( 1 )
	classname = '{0}.esercizio-{1}'.format( uid, exn )
	try:
		cmd = [ 'make', '-f', '../Makefile', '-C', ex, 'pulisci', 'test', 'exit_on_fail=false', 'blue=echo', 'red=echo', 'reset=echo' ]
		start = time()
		outerr = check_output( cmd, stderr = STDOUT )
	except CalledProcessError as e:
		ts = [ TestCase( 'COMPILE', '0', None, e.output ) ]
	else:
		ts = []
	finally:
		elapsed = int( ( time() - start ) * 100 ) / 100
	if not ts:
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
	with open( 'TEST-{0}.xml'.format( classname ), 'w' ) as out:
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
