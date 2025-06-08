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
                    mkdir -p reports
                '''
            }
        }

        stage('Test') {
            steps {
                echo '🧪 Run pytest unit tests'
                sh '''
                    set -e
                    export PYTHONPATH=.
                    $VENV_DIR/bin/pytest tests/ --junitxml=reports/unit-test-report.xml
                '''
            }
        }

        stage('SAST Scan') {
            steps {
                echo '🔒 Run Bandit security scan'
                sh '''
                    set -e
                    $VENV_DIR/bin/bandit -r app/ -f html -o reports/bandit-report.html -ll -iii
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
                echo '🛡️ Run OWASP ZAP scan'
                sh '''
                    set -e
                    docker rm -f zap || true
                    docker run --name zap -u root -v $(pwd)/reports:/zap/wrk/:rw -d -p 8091:8090 \
                        ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -port 8090 -host 0.0.0.0
                    sleep 30
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 status -t 60
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 open-url ${TEST_URL}
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 spider ${TEST_URL}
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 active-scan ${TEST_URL}
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 report -o /zap/wrk/zap-report.html -f html
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

            junit 'reports/unit-test-report.xml'

            publishHTML(target: [
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'bandit-report.html',
                reportName: 'Bandit SAST Report'
            ])

            publishHTML(target: [
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: 'zap-report.html',
                reportName: 'OWASP ZAP DAST Report'
            ])
        }

        failure {
            echo '❌ Build failed! Please check logs.'
        }
    }
}
