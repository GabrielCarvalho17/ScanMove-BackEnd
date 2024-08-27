pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'api_aplicacoes_internas:v0.0.1'
        CLUSTER = 'administrador@192.168.0.7'
        IMAGE_TAR = 'api_aplicacoes_internas.tar'
        COMPOSE = 'Docker-compose.yml'
        SENHA = '@@king&joe##' 
        SERVICO = 'app_api_aplicacoes_internas'
    }

    stages {

        stage("Build da imagem docker ") {
            steps {
                sh "docker build -t ${DOCKER_IMAGE} ."
            }
        }
        
        stage("Cluster 1 - Verificar e apagar serviço no docker swarm - Cluster 1") {
            steps {
                script {
                    def serviceExists = sh(script: "docker service ls --filter name=${SERVICO} --format '{{.Name}}'", returnStdout: true).trim()
                    echo "Serviço existente no Cluster 1: '${serviceExists}'"
                    if (serviceExists == "${SERVICO}") {
                        sh "docker service rm ${SERVICO}"
                    } else {
                        echo "O serviço ${SERVICO} não existe no Cluster 1. Ignorando a remoção."
                    }
                }
            }
        }

        stage("Cluster 1 - Subindo serviço / container - Cluster 1") {
            steps {
                sh 'docker stack deploy -c Docker-compose.yml app'
            }
        }

        /*
        stage('Salvar imagem no Docker') {
            steps {
                script {
                    // Save the Docker image to a tar file
                    sh "docker save -o ${IMAGE_TAR} ${DOCKER_IMAGE}"
                }
            }
        }

        stage('Cluster 2 - Transferir imagem Docker e arquivo de composição') {
            steps {
                script {
                    // Transfer the tar file and docker-compose.yml to the remote host
                    sh "sshpass -p '${SENHA}' scp -o StrictHostKeyChecking=no ${IMAGE_TAR} ${CLUSTER}:/tmp/${IMAGE_TAR}"
                    sh "sshpass -p '${SENHA}' scp -o StrictHostKeyChecking=no ${COMPOSE} ${CLUSTER}:/tmp/${COMPOSE}"
                }
            }
        }

        stage('Cluster 2 - Verificar e apagar serviço no Docker Swarm') {
            steps {
                script {
                    def serviceExists = sh(script: "sshpass -p '${SENHA}' ssh ${CLUSTER} docker service ls --filter name=${SERVICO} --format '{{.Name}}'", returnStdout: true).trim()
                    echo "Serviço existente no Cluster 2: '${serviceExists}'"
                    if (serviceExists == "${SERVICO}") {
                        sh "sshpass -p '${SENHA}' ssh ${CLUSTER} docker service rm ${SERVICO}"
                    } else {
                        echo "O serviço ${SERVICO} não existe no Cluster 2. Ignorando a remoção."
                    }
                }
            }
        }

        stage('Cluster 2 - Carregar imagem Docker e implantar pilha') {
            steps {
                script {
                    // SSH into the remote host, load the Docker image, and deploy the stack
                    sh """
                    sshpass -p '${SENHA}' ssh -o StrictHostKeyChecking=no ${CLUSTER} << EOF
                    docker load -i /tmp/${IMAGE_TAR}
                    docker stack deploy -c /tmp/${COMPOSE} app
                    """
                }
            }
        }
          */
    }
}
