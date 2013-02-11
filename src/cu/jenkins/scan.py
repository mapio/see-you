from argparse import ArgumentParser
from os.path import join, isdir
from subprocess import check_call

from .. import all_uids, all_timestamps, isots
from . import JENKINS_CLI, JENKINS_HOME

def build( uid, timestamp = None ):
	if not timestamp: timestamp = max( all_timestamps( uid ) )
	dest_dir = join( JENKINS_HOME, 'workspace', uid, uid, timestamp )
	if isdir( dest_dir ):
		return 'skipped (time {0})'.format( isots( timestamp ) )
	cmd = [ JENKINS_CLI, 'build', uid, '-p', 'timestamp={0}'.format( timestamp ), '-p', 'uid={0}'.format( uid ) ]
	print ' '.join( cmd )
	check_call( cmd )
	return 'scheduled (time {0})'.format( isots( timestamp ) )

def main():

	parser = ArgumentParser( prog = 'cu jenkins.scan' )
	parser.add_argument( '--uid', help = 'The UID to test (default: all)' )
	parser.add_argument( '--timestamp', help = 'The timestamp of the upload to test (default: latest)' )
	args = parser.parse_args()

	for uid in [ args.uid ] if args.uid else all_uids():
		print 'Build for {0}: {1}'.format( uid, build( uid, args.timestamp ) )
