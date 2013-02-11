from os import environ
from sys import exit

try:
	JENKINS_HOME = environ[ 'JENKINS_HOME' ]
except KeyError:
	exit( 'Please define JENKINS_HOME environment variable' )

try:
	JENKINS_CLI = environ[ 'JENKINS_CLI' ]
except KeyError:
	exit( 'Please define JENKINS_CLI environment variable' )
