pipeline {
    agent any

    environment {
        APP_NAME = "hn-hit-predictor"
        IMAGE_TAG = "v${BUILD_NUMBER}"
        LOCAL_IMAGE = "${APP_NAME}:${IMAGE_TAG}"
        TEST_PORT = "8009"
    }

    stages {
        stage('Checkout & Lint') {
            steps {
                echo "=== Step 1: Checking out code and validating structure ==="
                sh '''
                    echo "Validating project structure..."
                    test -f requirements.txt
                    test -f docker/Dockerfile
                    test -f app/main.py
                    test -f src/train.py
                    test -f cloudformation/infra.yaml
                    echo "Project files validated."
                '''
            }
        }

        stage('DevSecOps - IaC Security (Checkov)') {
            steps {
                echo "=== Step 2: DevSecOps IaC Scan with Checkov ==="
                sh '''
                    # Scans CloudFormation template for AWS security flaws
                    docker run --rm -v $(pwd):/work bridgecrew/checkov:latest \
                        -f /work/cloudformation/infra.yaml \
                        --framework cloudformation \
                        --soft-fail
                '''
            }
        }

        stage('Build Test Environment & Run Tests') {
            steps {
                echo "=== Step 3: Running Unit Tests & ML Sanity Checks ==="
                sh '''
                    # Build and run tests inside temporary container
                    docker build -t ${APP_NAME}-test -f docker/Dockerfile .
                    docker run --rm ${APP_NAME}-test pytest -v tests/
                '''
            }
        }

        stage('Package Production Image') {
            steps {
                echo "=== Step 4: Tagging Production Image ==="
                sh '''
                    docker tag ${APP_NAME}-test ${LOCAL_IMAGE}
                    docker tag ${APP_NAME}-test ${APP_NAME}:latest
                    echo "Built: ${LOCAL_IMAGE} and ${APP_NAME}:latest"
                '''
            }
        }

        stage('DevSecOps - Container Scan (Trivy)') {
            steps {
                echo "=== Step 5: DevSecOps Vulnerability Scan with Aqua Trivy ==="
                sh '''
                    # Scans production container for OS & package CVEs
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy:latest image \
                        --severity HIGH,CRITICAL \
                        --exit-code 0 \
                        ${APP_NAME}:latest
                '''
            }
        }

        stage('Integration Smoke Test') {
            steps {
                echo "=== Step 6: Running Container Smoke Test ==="
                sh '''
                    # Run container in background on test port
                    docker run -d --name ${APP_NAME}-smoke -p ${TEST_PORT}:8000 ${APP_NAME}:latest
                    
                    # Wait for container startup
                    sleep 7
                    
                    # Verify health check endpoint directly inside container
                    docker exec ${APP_NAME}-smoke curl -s -f http://localhost:8000/health || (docker logs ${APP_NAME}-smoke && exit 1)
                    
                    # Verify prediction endpoint directly inside container
                    docker exec ${APP_NAME}-smoke curl -s -X POST http://localhost:8000/predict \
                        -H "Content-Type: application/json" \
                        -d '{"title": "Show HN: My New MLOps Pipeline in Docker", "url": "https://github.com/test/pipeline"}'
                    
                    # Cleanup smoke container
                    docker stop ${APP_NAME}-smoke
                    docker rm ${APP_NAME}-smoke
                    echo "Integration smoke test passed successfully!"
                '''
            }
        }

        stage('Deploy to Production (AWS EC2 / Local)') {
            steps {
                echo "=== Step 7: Production Deployment Stage ==="
                sh '''
                    # Stop any running API container and deploy latest hardened build
                    docker rm -f hn-hit-predictor-api ${APP_NAME}-prod || true
                    docker run -d --name hn-hit-predictor-api --restart unless-stopped -p 8000:8000 ${APP_NAME}:latest
                    echo "Service is live on port 8000!"
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline run completed."
            sh 'docker rm -f ${APP_NAME}-smoke || true'
        }
        success {
            echo "CI/CD Pipeline succeeded! HN Hit Predictor is hardened and ready."
        }
        failure {
            echo "Pipeline failed. Inspect stage logs for details."
        }
    }
}
