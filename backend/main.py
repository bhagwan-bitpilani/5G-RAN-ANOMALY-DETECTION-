#!/usr/bin/env python3
"""
ML Scheduler for 5G KPI Anomaly Detection
"""
import asyncio
import logging
from fastapi import FastAPI
from kubernetes import client, config
from prometheus_client import start_http_server, Counter, Histogram
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
MODEL_TRAINING_COUNT = Counter('ml_model_training_total', 'Total model training operations')
ANOMALY_PREDICTION_COUNT = Counter('ml_anomaly_predictions_total', 'Total anomaly predictions')
PREDICTION_DURATION = Histogram('ml_prediction_duration_seconds', 'Prediction duration in seconds')

app = FastAPI(title="ML Scheduler", version="2.0.0")

class MLScheduler:
    def __init__(self):
        self.k8s_client = None
        self.initialize_kubernetes()
    
    def initialize_kubernetes(self):
        """Initialize Kubernetes client"""
        try:
            if os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/namespace'):
                config.load_incluster_config()
            else:
                config.load_kube_config()
            
            self.k8s_client = client.BatchV1Api()
            logger.info("Kubernetes client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
    
    async def schedule_model_training(self, model_type: str, data_range: dict):
        """Schedule ML model training job"""
        try:
            job_manifest = {
                "apiVersion": "batch/v1",
                "kind": "Job",
                "metadata": {
                    "name": f"model-train-{model_type}-{int(asyncio.get_event_loop().time())}",
                    "namespace": "5g-anomaly-detection"
                },
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [{
                                "name": "model-trainer",
                                "image": "registry.example.com/5g-anomaly/model-trainer:latest",
                                "env": [
                                    {"name": "MODEL_TYPE", "value": model_type},
                                    {"name": "DATA_RANGE", "value": str(data_range)}
                                ],
                                "resources": {
                                    "requests": {"memory": "1Gi", "cpu": "500m"},
                                    "limits": {"memory": "2Gi", "cpu": "1000m"}
                                }
                            }],
                            "restartPolicy": "Never"
                        }
                    },
                    "backoffLimit": 3
                }
            }
            
            if self.k8s_client:
                self.k8s_client.create_namespaced_job(
                    namespace="5g-anomaly-detection",
                    body=job_manifest
                )
                MODEL_TRAINING_COUNT.inc()
                logger.info(f"Scheduled training job for {model_type}")
            
        except Exception as e:
            logger.error(f"Failed to schedule training job: {e}")

# Global scheduler instance
ml_scheduler = MLScheduler()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ml-scheduler"}

@app.get("/ready")
async def readiness_check():
    return {"status": "ready", "kubernetes": ml_scheduler.k8s_client is not None}

@app.post("/schedule/training/{model_type}")
async def schedule_training(model_type: str):
    """Schedule a model training job"""
    data_range = {
        "start": "2024-01-01",
        "end": "2024-01-31"
    }
    await ml_scheduler.schedule_model_training(model_type, data_range)
    return {"message": f"Training scheduled for {model_type}", "status": "scheduled"}

async def main():
    """Main application entry point"""
    # Start Prometheus metrics server
    start_http_server(9090)
    logger.info("ML Scheduler started on port 8000, metrics on 9090")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
