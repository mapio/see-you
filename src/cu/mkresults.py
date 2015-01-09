from xml.dom import minidom
from operator import itemgetter

from tm.mkresults import TristoMietitoreScanner, main

class SeeYouScanner( TristoMietitoreScanner ):

	SHORT_NAME = 'cu'
	SOURCE_PATTERN = r'(?P<uid>.*)/latest/(?P<exercise>.*)/(?P<source>.*\.(c|h|java))$'
	CASES_PATTERN = r'(?P<uid>.*)/latest/TEST-(?P=uid)\.(?P<exercise>.*)\.xml$'

	def cases_reader( self, path ):
		get_cdata = lambda elements: elements[ 0 ].childNodes[ 0 ].nodeValue
		xmldoc = minidom.parse( path )
		cases = []
		for tc in xmldoc.getElementsByTagName( 'testcase' ):
			case = {}
			case[ 'name' ] = tc.getAttribute( 'name' )
			case[ 'type' ] = 'ok'
			stdout = tc.getElementsByTagName( 'system-out' )
			case[ 'stdout' ] = get_cdata( stdout ) if stdout else None
			stderr = tc.getElementsByTagName( 'system-err' )
			case[ 'stderr' ] = get_cdata( stderr ) if stderr else None
			error = tc.getElementsByTagName( 'error' )
			if error:
				case[ 'error' ] = get_cdata( error )
				case[ 'type' ] = error[ 0 ].getAttribute( 'type' )
				case[ 'failure' ] = None
			else:
				failure = tc.getElementsByTagName( 'failure' )
				if failure:
					case[ 'failure' ] = get_cdata( failure )
					case[ 'type' ] = failure[ 0 ].getAttribute( 'type' )
					case[ 'error' ] = None
			cases.append( case )
		return cases

	def sort( self ):
		for res in self.results:
			res[ 'exercises' ].sort( key = itemgetter( 'name' ) )
			for exercise in res[ 'exercises' ]:
				if exercise[ 'cases' ]:
					first = exercise[ 'cases' ].pop( 0 )
					exercise[ 'cases' ].sort( key = itemgetter( 'name' ) )
					exercise[ 'cases' ].insert( 0, first )
				exercise[ 'sources' ].sort( key = itemgetter( 'name' ) )
		self.results.sort( key = lambda _: _[ 'signature' ][ 'uid' ] )
		return self
