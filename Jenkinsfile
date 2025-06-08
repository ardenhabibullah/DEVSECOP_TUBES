pipeline {
    agent any

    environment {
        APP_NAME = "todo-app"
        TEST_URL = "http://localhost:5000"
        VENV_DIR = "/tmp/jenkins_venv"
        REPORT_DIR = "reports"
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
                    mkdir -p $REPORT_DIR
                '''
            }
        }

        stage('Test') {
            steps {
                echo '🧪 Run pytest unit tests and generate report'
                sh '''
                    set -e
                    export PYTHONPATH=.
                    $VENV_DIR/bin/pip install pytest pytest-html
                    $VENV_DIR/bin/pytest tests/ --html=$REPORT_DIR/pytest-report.html --self-contained-html
                '''
            }
        }

        stage('SAST Scan') {
            steps {
                echo '🔒 Run Bandit security scan and generate report'
                sh '''
                    set -e
                    $VENV_DIR/bin/pip install bandit
                    $VENV_DIR/bin/bandit -r app/ -f html -o $REPORT_DIR/bandit-report.html
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
                echo '🛡️ Run OWASP ZAP scan and generate report'
                sh '''
                    set -e
                    docker rm -f zap || true
                    mkdir -p $REPORT_DIR
                    docker run --name zap -u root -v $(pwd):/zap/wrk/:rw \
                        -d -p 8091:8090 ghcr.io/zaproxy/zaproxy:stable \
                        zap.sh -daemon -port 8090 -host 0.0.0.0

                    sleep 15  # Wait for ZAP to initialize
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 status -t 120
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 open-url ${TEST_URL}
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 spider ${TEST_URL}
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 active-scan ${TEST_URL}
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 report -o /zap/wrk/$REPORT_DIR/zap-report.html -f html
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
            echo '🧹 Cleanup: stop flask app and archive reports'
            sh '''
                pkill -f "flask run" || true
            '''
            archiveArtifacts artifacts: 'reports/*.html', allowEmptyArchive: true
            publishHTML([ 
                reportDir: 'reports', 
                reportFiles: 'pytest-report.html,bandit-report.html,zap-report.html', 
                reportName: 'Test & Security Reports' 
            ])
        }

        failure {
            echo '❌ Build failed! Please check logs.'
        }
    }
}
