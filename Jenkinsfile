pipeline {
    agent any

    environment {
        APP_NAME = "todo-app"
        TEST_URL = "http://localhost:5000"
    }

    stages {

        stage('Build') {
            steps {
                echo '📦 Setup virtual environment and install dependencies'
                sh '''
                    set -e
                    python3 -m venv venv
                    chmod -R +x venv/bin
                    venv/bin/pip install --upgrade pip
                    venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo '🧪 Run pytest unit tests'
                sh '''
                    set -e
                    export PYTHONPATH=.
                    ./venv/bin/pytest tests/
                '''
            }
        }

        stage('SAST Scan') {
            steps {
                echo '🔒 Run Bandit security scan'
                sh '''
                    set -e
                    ./venv/bin/bandit -r app/ -ll -iii
                '''
            }
        }

        stage('Deploy to Test Environment') {
            steps {
                echo '🚀 Run Flask app in background'
                sh '''
                    set -e
                    pkill -f "flask run" || true
                    ./venv/bin/flask run --host=0.0.0.0 > flask.log 2>&1 &
                    sleep 10
                '''
            }
        }

        stage('DAST Scan') {
            steps {
                echo '🛡️ Run OWASP ZAP scan'
                sh '''
                    set -e
                    zap-cli start --start-options '-config api.disablekey=true'
                    zap-cli quick-scan --self-contained --spider --scanners all $TEST_URL
                    zap-cli shutdown
                '''
            }
        }

        stage('Deploy to Staging') {
            steps {
                echo '📦 Deploy to staging (example: docker build and push)'
                sh '''
                    set -e
                    docker build -t ${APP_NAME}:latest .
                    # Uncomment this line to push to your Docker registry:
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
