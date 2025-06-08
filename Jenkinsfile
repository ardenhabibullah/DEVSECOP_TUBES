pipeline {
    agent any

    environment {
        APP_NAME = "todo-app"
        TEST_URL = "http://localhost:5000"
        VENV_DIR = "/tmp/jenkins_venv"
    }

    stages {

        stage('Build') {
            steps {
                echo '📦 Setup virtual environment and install dependencies'
                sh '''
                    set -e
                    python3 -m venv $VENV_DIR
                    $VENV_DIR/bin/pip install --upgrade pip
                    $VENV_DIR/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo '🧪 Run pytest unit tests'
                sh '''
                    set -e
                    export PYTHONPATH=.
                    $VENV_DIR/bin/pytest tests/
                '''
            }
        }

        stage('SAST Scan') {
            steps {
                echo '🔒 Run Bandit security scan'
                sh '''
                    set -e
                    $VENV_DIR/bin/bandit -r app/ -ll -iii
                '''
            }
        }

        stage('Deploy to Test Environment') {
            steps {
                echo '🚀 Run Flask app in background'
                sh '''
                    set -e
                    pkill -f "flask run" || true
                    $VENV_DIR/bin/flask run --host=0.0.0.0 > flask.log 2>&1 &
                    sleep 10
                '''
            }
        }

        
        stage('DAST Scan') {
            steps {
                echo "🛡️ Run OWASP ZAP scan"
                sh '''
                    # Start ZAP container
                    docker run --name zap -u root -v /var/lib/jenkins/workspace/flask-todo-app:/zap/wrk/:rw -d -p 8091:8090 ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -port 8090 -host 0.0.0.0

                    # Tunggu container siap
                    sleep 15

                    # Install pip dan zap-cli di dalam container
                    docker exec zap apt-get update
                    docker exec zap apt-get install -y python3-pip
                    docker exec zap pip3 install zap-cli

                    # Jalankan DAST scan
                    docker exec zap zap-cli quick-scan --self-contained --start-options -config api.disablekey=true http://host.docker.internal:5000

                    # Cleanup container
                    docker stop zap
                    docker rm zap
                '''
            }
        }


        stage('Deploy to Staging') {
            steps {
                echo '📦 Deploy to staging (example: docker build and push)'
                sh '''
                    set -e
                    docker build -t ${APP_NAME}:latest .
                    # docker push yourregistry/${APP_NAME}:latest
                '''
            }
        }
    }

    post {
        always {
            echo '🧹 Cleanup: stop flask app'
            sh 'pkill -f "flask run" || true'
        }

        failure {
            echo '❌ Build failed! Please check logs.'
        }
    }
}
