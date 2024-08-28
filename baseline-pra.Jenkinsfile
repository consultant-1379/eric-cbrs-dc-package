#!/usr/bin/env groovy

def defaultBobImage = 'armdocker.rnd.ericsson.se/proj-adp-cicd-drop/bob.2.0:latest'
def bob = new BobCommand()
        .bobImage(defaultBobImage)
        .envVars([
                ARM_API_TOKEN  : '${ARM_API_TOKEN}',
                HOME           : '${HOME}',
                CHART_NAME     : '${CHART_NAME}',
                CHART_REPO     : '${CHART_REPO}',
                USER           : '${USER}',
                GERRIT_USERNAME: '${GERRIT_USERNAME}',
                GERRIT_PASSWORD: '${GERRIT_PASSWORD}',
                SELI_USER      : '${SELI_USER}',
                SELI_PASSWORD  : '${SELI_PASSWORD}',
                SERO_USER      : '${SERO_USER}',
                SERO_PASSWORD  : '${SERO_PASSWORD}',
                SPRINT_TAG     : '${SPRINT_END}',
                SPRINT_END     : '${SPRINT_PREFIX}',
                CBRS_SSH       : '${CBRS_SSH}',
                R_STATE        : '${R_STATE}'
        ])
        .needDockerSocket(true)
        .toString()

pipeline {
    agent {
        node {
            label 'GE7_Docker'
        }
    }
    environment {
        SPRINT_PREFIX = "point_fix_${SPRINT_END}"
    }
    parameters {
        string(name: 'SPRINT_END', description: '"Sprint End e.g: Sprint number(20.17)"')
        string(name: 'R_STATE', description: '"R-State e.g: R-State(R1U)"')
    }
    stages {
        stage('Init') {
            steps {
                sh 'echo Init'
            }
        }
        stage('Package-Helm-Chart & Create new-pointfix-branch') {
            steps {
                withCredentials([
                        usernamePassword(credentialsId: 'Gerrit HTTP', usernameVariable: 'GERRIT_USERNAME', passwordVariable: 'GERRIT_PASSWORD'),
                        usernamePassword(credentialsId: 'SELI_Artifactory', usernameVariable: 'SELI_USER', passwordVariable: 'SELI_PASSWORD'),
                        usernamePassword(credentialsId: 'SERO_Artifactory', usernameVariable: 'SERO_USER', passwordVariable: 'SERO_PASSWORD'),
                        file(credentialsId: 'cbrsciadm_ssh_key', variable: 'CBRS_SSH'),
                        string(credentialsId: 'CBRSCIADM', variable: 'ARM_API_TOKEN')]) {
                    sh "${bob} -r ruleset2.0.pra.yaml package-helm-chart"
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'artifact.properties'
                }
            }
        }
    }
    post {
        always {
            deleteDir()
        }
    }
}

// More about @Builder: http://mrhaki.blogspot.com/2014/05/groovy-goodness-use-builder-ast.html
import groovy.transform.builder.Builder
import groovy.transform.builder.SimpleStrategy

@Builder(builderStrategy = SimpleStrategy, prefix = '')
class BobCommand {

    def bobImage = 'bob.2.0:latest'
    def envVars = [:]

    def needDockerSocket = false

    String toString() {
        def env = envVars
                .collect({ entry -> "-e ${entry.key}=\"${entry.value}\"" })
                .join(' ')

        def cmd = """\
            |docker run
            |--init
            |--rm
            |--workdir \${PWD}
            |--user \$(id -u):\$(id -g)
            |-v \${PWD}:\${PWD}
            |-v /etc/group:/etc/group:ro
            |-v /etc/passwd:/etc/passwd:ro
            |-v \${HOME}:\${HOME}
            |${needDockerSocket ? '-v /var/run/docker.sock:/var/run/docker.sock' : ''}
            |${env}
            |\$(for group in \$(id -G); do printf ' --group-add %s' "\$group"; done)
            |--group-add \$(stat -c '%g' /var/run/docker.sock)
            |${bobImage}
            |"""
        return cmd
                .stripMargin()           // remove indentation
                .replace('\n', ' ')      // join lines
                .replaceAll(/[ ]+/, ' ') // replace multiple spaces by one
    }
}