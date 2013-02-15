from argparse import ArgumentParser
from os.path import join
from subprocess import Popen, PIPE

from . import UPLOAD_DIR, all_uids

JENKINS_JOB_TEMPLATE = """
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description>{description}</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>uid</name>
          <description></description>
          <defaultValue>unknown_uid</defaultValue>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>timestamp</name>
          <description></description>
          <defaultValue>unknown_timestamp</defaultValue>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>$CU_CMD test --clean --uid $uid --timestamp $timestamp --result_dir $WORKSPACE</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers>
    <hudson.tasks.junit.JUnitResultArchiver>
      <testResults>**/latest/TEST-*.xml</testResults>
      <keepLongStdio>false</keepLongStdio>
      <testDataPublishers/>
    </hudson.tasks.junit.JUnitResultArchiver>
  </publishers>
  <buildWrappers/>
</project>
"""

def main():
	parser = ArgumentParser( prog = 'cu test' )
	parser.add_argument( 'jenkins_cli', help = 'The local Jenkins cli script' )
	args = parser.parse_args()

	for uid in all_uids():
		print "Creating job for uid: {0}".format( uid )
		with ( open( join( UPLOAD_DIR, uid, 'SIGNATURE.tsv' ) ) ) as f: description = f.read().strip();
		p = Popen( [ args.jenkins_cli, 'create-job', uid ], stdin = PIPE, stdout = PIPE )
		p.communicate( JENKINS_JOB_TEMPLATE.format( description = description ) )
