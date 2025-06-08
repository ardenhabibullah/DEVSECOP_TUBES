pipeline {
    agent any

    environment {
        VENV_PATH = "/tmp/jenkins_venv"
        FLASK_APP = "app"
        FLASK_ENV = "development"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo '📦 Setup virtual environment and install dependencies'
                sh '''
                    set -e
                    python3 -m venv $VENV_PATH
                    $VENV_PATH/bin/pip install --upgrade pip
                    $VENV_PATH/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo '🧪 Run pytest unit tests'
                sh '''
                    set -e
                    export PYTHONPATH=.
                    $VENV_PATH/bin/pytest tests/ --junitxml=report.xml
                '''
            }
        }

        stage('Publish Test Report') {
            steps {
                echo '📊 Publish JUnit test report'
                junit 'report.xml'
            }
        }

        stage('SAST Scan') {
            steps {
                echo '🔒 Run Bandit security scan'
                sh '''
                    set -e
                    $VENV_PATH/bin/bandit -r app/ -ll -iii
                '''
            }
        }

        stage('Deploy to Test Environment') {
            steps {
                echo '🚀 Run Flask app in background'
                sh '''
                    set -e
                    pkill -f flask run || true
                    sleep 10
                    $VENV_PATH/bin/flask run --host=0.0.0.0 &
                '''
            }
        }

        stage('DAST Scan') {
            steps {
                echo '🛡️ Run OWASP ZAP scan'
                sh '''
                    set -e
                    docker rm -f zap || true
                    echo "🐳 Start ZAP container"
                    docker run --name zap -u root \
                        -v $(pwd):/zap/wrk/:rw \
                        -d -p 8091:8090 \
                        ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -port 8090 -host 0.0.0.0 -config api.disablekey=true

                    echo "🔍 Run ZAP active scan"
                    sleep 20  # wait ZAP to be ready
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 status -t 60
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 open-url http://host.docker.internal:5000
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 active-scan --scanners all http://host.docker.internal:5000
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 report -o zap_report.html -f html
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'zap_report.html', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed. Check logs for details.'
        }
    }
}
