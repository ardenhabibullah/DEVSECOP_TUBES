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
                docker run -u root -d --name zap -p 8090:8090 -i owasp/zap2docker-stable zap.sh -daemon -port 8090 -host 0.0.0.0 -config api.disablekey=true
                sleep 15  # tunggu ZAP siap
                docker exec zap zap-cli quick-scan --self-contained --start-options "-config api.disablekey=true" http://host.docker.internal:5000
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
