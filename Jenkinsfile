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
                    // Publish test results to Jenkins UI
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
                    // Generate report in HTML format
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
                    // Run the app in the background so the pipeline can continue
                    nohup $VENV_DIR/bin/flask run --host=0.0.0.0 > flask.log 2>&1 &
                    sleep 10
                '''
            }
        }

        stage('DAST Scan') {
            steps {
                echo '🛡️ Run OWASP ZAP scan and generate reports'
                sh '''
                    set -e
                    # Use host.docker.internal to allow the ZAP container to access the Flask app running on the host
                    TARGET_URL_FOR_ZAP="http://host.docker.internal:5000"
                    
                    docker rm -f zap || true
                    docker run --name zap -u root -v $(pwd):/zap/wrk/:rw --add-host=host.docker.internal:host-gateway \
                        -d -p 8091:8090 ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -port 8090 -host 0.0.0.0 \
                        -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true
                    
                    # Wait for ZAP to start
                    sleep 15

                    echo "Starting ZAP Scan on ${TARGET_URL_FOR_ZAP}"
                    // Run ZAP baseline scan and generate reports in multiple formats
                    docker exec zap zap-baseline.py -t ${TARGET_URL_FOR_ZAP} -r zap-report.html -w zap-report.md -J zap-report.json

                    echo "ZAP Scan finished, reports generated in the workspace."
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
            sh '''
                pkill -f "flask run" || true
                docker rm -f zap || true
                
                # Create a directory for ZAP reports and copy them from the workspace
                mkdir -p reports/zap
                cp zap-report.html zap-report.md zap-report.json reports/zap/ || true
            '''
            // Archive all files in the reports directory
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