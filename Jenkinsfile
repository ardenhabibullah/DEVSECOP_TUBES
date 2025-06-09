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
        
        // --- TAHAP YANG DIPERBAIKI ---
        // Menggabungkan Deploy ke Test dan DAST Scan menjadi satu stage
        stage('Deploy for Test & DAST Scan') {
            steps {
                echo '🚀 Deploying app for testing and running DAST scan'
                sh '''
                    set -e
                    
                    # 1. Hentikan proses flask lama jika ada
                    pkill -f "flask run" || true
                    
                    # 2. Jalankan aplikasi Flask di background
                    echo "Starting Flask app in background..."
                    nohup $VENV_DIR/bin/flask run --host=0.0.0.0 > flask.log 2>&1 &
                    
                    # Beri waktu beberapa detik agar aplikasi siap
                    echo "Waiting for application to start..."
                    sleep 15

                    # (Opsional tapi direkomendasikan) Verifikasi apakah aplikasi berjalan
                    echo "Verifying application is accessible at ${TEST_URL}"
                    curl -s --head --request GET ${TEST_URL} | grep "200 OK" || (echo "Application failed to start!" && exit 1)
                    
                    # 3. Jalankan ZAP Scan sementara aplikasi berjalan
                    echo "🛡️ Starting OWASP ZAP scan..."
                    TARGET_URL_FOR_ZAP="http://127.0.0.1:5000"
                    
                    docker rm -f zap || true
                    
                    docker run --name zap -u root -v $(pwd):/zap/wrk/:rw --network="host" \\
                        -d ghcr.io/zaproxy/zaproxy:stable zap.sh -daemon -port 8090 -host 0.0.0.0 \\
                        -config api.addrs.addr.name=.* -config api.addrs.addr.regex=true
                    
                    # Beri waktu agar ZAP siap
                    sleep 15

                    echo "Executing ZAP baseline scan on ${TARGET_URL_FOR_ZAP}..."
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
                set +e  # Jangan hentikan pipeline jika cleanup gagal
                echo "Stopping Flask application..."
                pkill -f "flask run"
                
                echo "Removing ZAP container..."
                docker rm -f zap

                echo "Copying ZAP reports..."
                mkdir -p reports/zap
                # Gunakan '|| true' untuk mencegah error jika file tidak ada (misal, jika stage scan di-skip)
                cp zap-report.html zap-report.md zap-report.json reports/zap/ || true
                set -e
            '''
            archiveArtifacts artifacts: 'reports/**/*', fingerprint: true
        }
        success {
            echo '✅ Build successful!'
        }
        failure {
            echo '❌ Build failed. Please check logs.'
        }
    }
}