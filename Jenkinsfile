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
                    $VENV_DIR/bin/pytest tests/ --junitxml=report.xml
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
                echo '🛡️ Run OWASP ZAP scan'
                sh '''
                    set -e
                    docker rm -f zap || true

                    echo "🐳 Start ZAP container"
                    docker run --name zap -u root -v $(pwd):/zap/wrk/:rw -d -p 8091:8090 ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -port 8090 -host 0.0.0.0

                    echo "⌛ Waiting for ZAP to initialize..."
                    sleep 15

                    echo "🌐 Running scan on ${TEST_URL}"
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 status -t 60
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 open-url ${TEST_URL}
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 spider ${TEST_URL}
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 active-scan ${TEST_URL}

                    echo "📝 Generate ZAP HTML report"
                    docker exec zap zap-cli --zap-url http://localhost -p 8090 report -o /zap/wrk/zap_report.html -f html
                '''
            }
        }

        stage('Archive ZAP Report') {
            steps {
                echo '📁 Archive ZAP scan result'
                archiveArtifacts artifacts: 'zap_report.html', fingerprint: true
            }
        }

        stage('Deploy to Staging') {
            steps {
                echo '📦 Build Docker image'
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
            echo '🧹 Cleanup Flask process'
            sh 'pkill -f "flask run" || true'
        }

        failure {
            echo '❌ Build failed! Check logs.'
        }
    }
}
