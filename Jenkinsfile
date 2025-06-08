pipeline {
    agent any

    environment {
        APP_NAME = "todo-app"
        TEST_URL = "http://localhost:5000"
        VENV_DIR = "/tmp/jenkins_venv"
    }

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                git 'https://github.com/Alfikriangelo/todoapp.git'
            }
        }
        
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
                echo '🧪 Run pytest unit tests with JUnit XML report'
                sh '''
                    set -e
                    export PYTHONPATH=.
                    $VENV_DIR/bin/pytest tests/ --junitxml=pytest-report.xml
                '''
            }
            post {
                always {
                    junit 'pytest-report.xml'
                }
            }
        }


        stage('SAST Scan') {
            steps {
                echo '🔒 Run Bandit security scan with XML output'
                sh '''
                    set -e
                    $VENV_DIR/bin/bandit -r app/ -ll -iii -f xml -o bandit-report.xml
                '''
            }
            post {
                always {
                    // Anda bisa simpan file xml ini, dan gunakan plugin seperti Warnings Next Generation di Jenkins untuk parse laporan
                    archiveArtifacts artifacts: 'bandit-report.xml', allowEmptyArchive: true
                }
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
                echo '🛡️ Run OWASP ZAP baseline scan and generate HTML report'
                sh '''
                    set -e
                    docker run --rm --network=host \
                        -v $WORKSPACE:/zap/wrk/:rw \
                        ghcr.io/zaproxy/zaproxy:stable \
                        zap-baseline.py -t $TEST_URL -r zap-report.html
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        allowMissing: true,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: '.',
                        reportFiles: 'zap-report.html',
                        reportName: 'OWASP ZAP Report'
                    ])
                }
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