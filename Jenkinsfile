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
                echo '🧪 Run pytest unit tests and generate report'
                sh '''
                    set -e
                    export PYTHONPATH=.
                    mkdir -p reports
                    $VENV_DIR/bin/pytest tests/ --junitxml=reports/test-results.xml
                '''
            }
            post {
                always {
                    junit 'reports/test-results.xml'
                }
            }
        }

        stage('SAST Scan') {
            steps {
                echo '🔒 Run Bandit security scan and generate report'
                sh '''
                    set -e
                    mkdir -p reports
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
                    # Jalankan di background (&) dan simpan output ke flask.log
                    nohup $VENV_DIR/bin/flask run --host=0.0.0.0 > flask.log 2>&1 &
                    sleep 10
                '''
            }
        }

        stage('DAST Scan') {
            steps {
                echo '🛡️ Run OWASP ZAP scan and generate reports (max 5 minutes)'
                sh '''
                    set -e
                    # Saat menggunakan --network="host", kontainer bisa mengakses host melalui 127.0.0.1
                    TARGET_URL_FOR_ZAP="http://127.0.0.1:5000"
                    
                    docker rm -f zap || true
                    # Gunakan jaringan host secara langsung, ini lebih andal di Linux
                    docker run --name zap -u root -v $(pwd):/zap/wrk/:rw --network="host" \
                        -d ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -port 8090 -host 0.0.0.0 \
                        -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true
                    
                    sleep 15

                    echo "Starting ZAP Scan on ${TARGET_URL_FOR_ZAP}"
                    docker exec zap zap-baseline.py -t ${TARGET_URL_FOR_ZAP} -m 5 -r zap-report.html -w zap-report.md -J zap-report.json

                    echo "ZAP Scan finished."
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
            echo '🧹 Cleanup and archive reports'
            sh script: '''
                pkill -f "flask run" || true
                docker rm -f zap || true
                
                mkdir -p reports/zap
                cp zap-report.html zap-report.md zap-report.json reports/zap/ || true
            '''
            archiveArtifacts artifacts: 'reports/**/*', fingerprint: true
        }
        success {
            echo '✅ Build successful!'
        }
        failure {
            echo '❌ Build failed! Please check logs.'
        }
    }
}