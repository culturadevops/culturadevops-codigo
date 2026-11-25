<?xml version='1.1' encoding='UTF-8'?>
<project>
  <description>Demo: error fetching remote repo 'origin'</description>
  <scm class="hudson.plugins.git.GitSCM">
    <configVersion>2</configVersion>
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
        <url>__URL__</url>__CREDS__
      </hudson.plugins.git.UserRemoteConfig>
    </userRemoteConfigs>
    <branches>
      <hudson.plugins.git.BranchSpec><name>*/main</name></hudson.plugins.git.BranchSpec>
    </branches>
  </scm>
  <builders/>
</project>
