#!/usr/bin/env groovy

/* IMPORTANT:
 *
 * In order to make this pipeline work, the following configuration on Jenkins is required:
 * - slave with a specific label (see pipeline.agent.label below)
 * - credentials plugin should be installed and have the secrets with the following names:
 *   + cbrsciadm credentials (token to access Artifactory)
 */

def defaultBobImage = 'armdocker.rnd.ericsson.se/proj-adp-cicd-drop/bob.2.0:latest'
def bob = new BobCommand()
        .bobImage(defaultBobImage)
        .envVars([
                HOME                 : '${HOME}',
                PWD                  : '${PWD}',
                HELM_REPO_TOKEN      : '${HELM_REPO_TOKEN}',
                KUBECONFIG           : '${KUBECONFIG}',
                USER                 : '${USER}',
                SELI_USER            : '${SELI_USER}',
                SELI_PASSWORD        : '${SELI_PASSWORD}',
                SERO_USER            : '${SERO_USER}',
                SERO_PASSWORD        : '${SERO_PASSWORD}',
                GERRIT_USERNAME      : '${GERRIT_USERNAME}',
                GERRIT_PASSWORD      : '${GERRIT_PASSWORD}',
                GERRIT_REFSPEC       : '${GERRIT_REFSPEC}',
                ARM_API_TOKEN        : '${ARM_API_TOKEN}',
                ENVIRONMENT_NAME     : '${ENVIRONMENT_NAME}',
                NAMESPACE            : '${NAMESPACE}',
                INT_CHART_VERSION    : '${INT_CHART_VERSION}',
                CSAR_VERSION         : '${CSAR_VERSION}',
                ENM_ENROLL           : 'true',
                TEST_SPEC_TAG        : '${TEST_SPEC_TAG}',
                CERTM_CONFIG_CONTENT : '${CERTM_CONFIG_CONTENT}'
        ])
        .needDockerSocket(true)
        .toString()
pipeline {
    agent {
        node {
             label 'GE7_Docker'
        }
    }
    options {
        lock(params.ENVIRONMENT_NAME + "-" + params.NAMESPACE + "-deployment-resource") // Prevent parallel builds against the same namespace on the same deployment ID
    }
    environment{
        KUBECONFIG = "${WORKSPACE}/.kube/config"
    }
    parameters {
        string(name: 'ENVIRONMENT_NAME', description: 'Provide environment name using this page: https://atvdit.athtem.eei.ericsson.se/deployments')
        string(name: 'NAMESPACE', description: '(Optional) Provide namespace for rollback', defaultValue: 'cbrs')
    }
    stages {
        stage('Inject Credential Files') {
            steps {
                withCredentials([file(credentialsId: 'cbrsciadm_docker_config', variable: 'dockerConfig')]) {
                    sh "cp ${dockerConfig} ${HOME}/.docker/config.json"
                }
            }
        }
        stage ('Init') {
            steps {
                script {
                    currentBuild.description = ''
                    if (params.ENVIRONMENT_NAME != null && params.ENVIRONMENT_NAME != "") {
                        currentBuild.description += 'environment: ' + params.ENVIRONMENT_NAME + '<br>'
                    } else {
                        error("Build failed because of no deployment ID provided")
                    }
                    if (params.NAMESPACE != null && params.NAMESPACE != "") {
                        currentBuild.description += 'namespace: ' + params.NAMESPACE + '<br>'
                    }
                    if (params.CSAR_VERSION != null && params.CSAR_VERSION != "") {
                        currentBuild.description += 'eric-cbrs-dc-csar: ' + params.CSAR_VERSION + '<br>'
                    }
                }
                sh "${bob} init"
            }
        }
        stage('Execute') {
            steps {
                sh "${bob} rollback-cdl"
            }
        }
    }
    post {
        always {
        withCredentials([usernamePassword(credentialsId: 'SERO_Artifactory', usernameVariable: 'SERO_USER', passwordVariable: 'SERO_PASSWORD')]) {
             sh "${bob} collect-logs || true"
        }
        archiveArtifacts allowEmptyArchive: true, artifacts: 'k8s-test/target/logs/**/*.*'
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