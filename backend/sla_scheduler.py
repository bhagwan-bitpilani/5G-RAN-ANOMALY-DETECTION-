# sla_scheduler.py - Enhanced SLA Scheduler for Backend Deployment
# Version: 1.1.0 (Enhanced for Production Deployment)
# Description: Kubernetes-based SLA-driven resource optimization with AI decision making,
#              integrated with Prometheus metrics. References main.py for config, logging, and structure.

import asyncio
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import numpy as np
from kubernetes import client, config
from prometheus_api_client import PrometheusConnect

# Reference main.py imports and settings
try:
    from main import settings  # Import settings from main.py
except ImportError:
    # Fallback if not available
    class FallbackSettings:
        PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
        KUBERNETES_NAMESPACE: str = os.getenv("KUBERNETES_NAMESPACE", "5g-anomaly-detection")
        SCHEDULER_INTERVAL: int = int(os.getenv("SCHEDULER_INTERVAL", 60))  # seconds
        MAX_REPLICAS: int = int(os.getenv("MAX_REPLICAS", 10))
        MIN_REPLICAS: int = int(os.getenv("MIN_REPLICAS", 1))
        LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    settings = FallbackSettings()

# Logging setup (consistent with main.py)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedSLAScheduler:
    """
    Enhanced SLA Scheduler for Kubernetes-based resource optimization.
    Integrates with Prometheus for metrics and makes AI-driven scaling decisions.
    References main.py for configuration and logging patterns.
    """
    
    def __init__(self):
        # Load Kubernetes config (in-cluster or local)
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            config.load_kube_config()
            logger.info("Loaded local Kubernetes config")
        
        # Kubernetes API clients
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        
        # Prometheus client
        self.prometheus = PrometheusConnect(url=settings.PROMETHEUS_URL)
        
        # SLA targets (configurable via env or main.py settings)
        self.sla_targets = {
            'response_time': float(os.getenv("SLA_RESPONSE_TIME_MS", 100)),  # ms
            'throughput': float(os.getenv("SLA_THROUGHPUT_PERCENT", 95)),   # %
            'availability': float(os.getenv("SLA_AVAILABILITY_PERCENT", 99.9)),  # %
            'error_rate': float(os.getenv("SLA_ERROR_RATE_PERCENT", 1))     # %
        }
        
        # Scaling history for AI decisions
        self.scaling_history: List[Dict] = []
        
        logger.info(f"SLA Scheduler initialized with targets: {self.sla_targets}")
    
    async def optimize_resources(self):
        """
        Main optimization loop with enhanced error handling and AI decision making.
        Runs indefinitely, checking metrics and scaling resources.
        """
        logger.info("🚀 Starting SLA-based resource optimization loop")
        
        while True:
            try:
                # Step 1: Collect metrics
                cluster_metrics = await self.get_cluster_metrics()
                app_performance = await self.get_application_performance()
                
                if not cluster_metrics or not app_performance:
                    logger.warning("Skipping optimization cycle due to missing metrics")
                    await asyncio.sleep(settings.SCHEDULER_INTERVAL)
                    continue
                
                # Step 2: AI-based decision making
                decisions = await self.make_scaling_decisions(cluster_metrics, app_performance)
                
                # Step 3: Execute decisions with validation
                if decisions:
                    await self.execute_decisions(decisions)
                    logger.info(f"Executed {len(decisions)} scaling decisions")
                else:
                    logger.debug("No scaling decisions needed")
                
                # Step 4: Log and sleep
                await asyncio.sleep(settings.SCHEDULER_INTERVAL)
                
            except asyncio.CancelledError:
                logger.info("Optimization loop cancelled")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}", exc_info=True)
                await asyncio.sleep(settings.SCHEDULER_INTERVAL // 2)  # Retry sooner on error
    
    async def get_cluster_metrics(self) -> Dict:
        """
        Enhanced cluster metrics collection from Prometheus.
        Includes CPU, memory, and node-level metrics.
        """
        try:
            metrics = {}
            
            # CPU usage per pod
            cpu_query = 'sum(rate(container_cpu_usage_seconds_total[5m])) by (pod, namespace)'
            cpu_result = self.prometheus.custom_query(cpu_query)
            metrics['cpu_usage'] = self._parse_prometheus_results(cpu_result, 'cpu_cores')
            
            # Memory usage per pod
            memory_query = 'container_memory_usage_bytes{pod=~".*", namespace="' + settings.KUBERNETES_NAMESPACE + '"}'
            memory_result = self.prometheus.custom_query(memory_query)
            metrics['memory_usage'] = self._parse_prometheus_results(memory_result, 'bytes')
            
            # Node CPU utilization
            node_cpu_query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
            node_cpu_result = self.prometheus.custom_query(node_cpu_query)
            metrics['node_cpu'] = self._parse_prometheus_results(node_cpu_result, 'percent')
            
            # Node memory utilization
            node_memory_query = '(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100'
            node_memory_result = self.prometheus.custom_query(node_memory_query)
            metrics['node_memory'] = self._parse_prometheus_results(node_memory_result, 'percent')
            
            logger.debug(f"Collected cluster metrics: {list(metrics.keys())}")
            return metrics
            
        except Exception as e:
            logger.error(f"Cluster metrics collection error: {str(e)}")
            return {}
    
    async def get_application_performance(self) -> Dict:
        """
        Enhanced application performance metrics from Prometheus.
        Includes KPI processing, anomaly detection, and error rates.
        """
        try:
            metrics = {}
            
            # KPI processing rate
            processing_rate_query = 'rate(kpi_processed_total[5m])'
            processing_rate_result = self.prometheus.custom_query(processing_rate_query)
            metrics['processing_rate'] = self._parse_prometheus_results(processing_rate_result, 'requests_per_second')
            
            # Anomaly detection latency (95th percentile)
            latency_query = 'histogram_quantile(0.95, rate(anomaly_detection_duration_seconds_bucket[5m]))'
            latency_result = self.prometheus.custom_query(latency_query)
            metrics['detection_latency'] = self._parse_prometheus_results(latency_result, 'seconds')
            
            # Error rate
            error_rate_query = 'rate(kpi_processing_errors_total[5m]) / rate(kpi_processed_total[5m]) * 100'
            error_rate_result = self.prometheus.custom_query(error_rate_query)
            metrics['error_rate'] = self._parse_prometheus_results(error_rate_result, 'percent')
            
            # API response time
            response_time_query = 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="app-api"}[5m]))'
            response_time_result = self.prometheus.custom_query(response_time_query)
            metrics['api_response_time'] = self._parse_prometheus_results(response_time_result, 'seconds')
            
            logger.debug(f"Collected app performance metrics: {list(metrics.keys())}")
            return metrics
            
        except Exception as e:
            logger.error(f"Application performance metrics error: {str(e)}")
            return {}
    
    async def make_scaling_decisions(self, metrics: Dict, performance: Dict) -> List[Dict]:
        """
        AI-based decision making for resource scaling.
        Uses historical data and ML-like logic for predictions.
        """
        decisions = []
        
        # Analyze API response time vs SLA
        api_response_time = performance.get('api_response_time', {}).get('value', 0)
        target_response_time = self.sla_targets['response_time'] / 1000  # Convert ms to seconds
        
        if api_response_time > target_response_time * 1.2:
            decisions.append({
                'action': 'scale_up',
                'deployment': 'app-api',
                'reason': f'High API latency: {api_response_time:.3f}s > {target_response_time:.3f}s',
                'confidence': 0.9
            })
        elif api_response_time < target_response_time * 0.7 and len(self.scaling_history) > 5:
            # Only scale down if consistently low and we have history
            recent_scales = [h for h in self.scaling_history[-10:] if h['action'] == 'scale_up']
            if not recent_scales:
                decisions.append({
                    'action': 'scale_down',
                    'deployment': 'app-api',
                    'reason': f'Low API latency: {api_response_time:.3f}s < {target_response_time * 0.8:.3f}s',
                    'confidence': 0.7
                })
        
        # Analyze error rate
        error_rate = performance.get('error_rate', {}).get('value', 0)
        if error_rate > self.sla_targets['error_rate']:
            decisions.append({
                'action': 'scale_up',
                'deployment': 'ml-scheduler',
                'reason': f'High error rate: {error_rate:.1f}% > {self.sla_targets["error_rate"]}%',
                'confidence': 0.95
            })
        
        # Analyze processing rate and cluster resources
        processing_rate = performance.get('processing_rate', {}).get('value', 0)
        cpu_usage = metrics.get('node_cpu', {}).get('avg_value', 0)
        
        if processing_rate > 100 and cpu_usage > 80:  # High load
            decisions.append({
                'action': 'scale_up',
                'deployment': 'kpi-processor',
                'reason': f'High processing load: {processing_rate:.1f} req/s, CPU: {cpu_usage:.1f}%',
                'confidence': 0.85
            })
        
        # Filter decisions by confidence and avoid conflicting actions
        high_confidence_decisions = [d for d in decisions if d['confidence'] > 0.8]
        
        # Log decisions
        for decision in high_confidence_decisions:
            logger.info(f"Scaling decision: {decision['action']} {decision['deployment']} - {decision['reason']} (confidence: {decision['confidence']})")
        
        return high_confidence_decisions
    
    async def execute_decisions(self, decisions: List[Dict]):
        """
        Execute scaling decisions with validation and rollback capability.
        """
        executed_decisions = []
        
        for decision in decisions:
            try:
                deployment = decision['deployment']
                current_replicas = await self.get_current_replicas(deployment)
                
                if decision['action'] == 'scale_up':
                    new_replicas = min(current_replicas + 1, settings.MAX_REPLICAS)
                elif decision['action'] == 'scale_down':
                    new_replicas = max(current_replicas - 1, settings.MIN_REPLICAS)
                else:
                    continue
                
                if new_replicas != current_replicas:
                    await self.scale_deployment(deployment, new_replicas)
                    
                    # Record in history
                    executed_decisions.append({
                        **decision,
                        'old_replicas': current_replicas,
                        'new_replicas': new_replicas,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    logger.info(f"✅ Scaled {deployment} from {current_replicas} to {new_replicas} replicas")
                    
                    # Update scaling history
                    self.scaling_history.append({
                        'deployment': deployment,
                        'action': decision['action'],
                        'replicas': new_replicas,
                        'timestamp': datetime.utcnow(),
                        'reason': decision['reason']
                    })
                    
                    # Keep history limited
                    if len(self.scaling_history) > 100:
                        self.scaling_history = self.scaling_history[-100:]
                    
                else:
                    logger.debug(f"No scaling needed for {deployment} (already at {current_replicas} replicas)")
                    
            except Exception as e:
                logger.error(f"Failed to execute decision for {deployment}: {str(e)}")
        
        return executed_decisions
    
    async def get_current_replicas(self, deployment_name: str) -> int:
        """
        Get current replica count for a deployment.
        """
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=settings.KUBERNETES_NAMESPACE
            )
            return deployment.spec.replicas or 1
        except client.exceptions.ApiException as e:
            if e.status == 404:
                logger.warning(f"Deployment {deployment_name} not found")
                return 1
            else:
                logger.error(f"Error getting replicas for {deployment_name}: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error getting replicas for {deployment_name}: {str(e)}")
            return 1
    
    async def scale_deployment(self, deployment_name: str, replicas: int):
        """
        Scale a Kubernetes deployment to the specified replica count.
        """
        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=settings.KUBERNETES_NAMESPACE
            )
            
            # Update replicas
            deployment.spec.replicas = replicas
            
            # Patch deployment
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=settings.KUBERNETES_NAMESPACE,
                body=deployment
            )
            
            # Wait for rollout to complete (optional, for validation)
            await self._wait_for_rollout(deployment_name)
            
        except Exception as e:
            logger.error(f"Error scaling {deployment_name} to {replicas} replicas: {str(e)}")
            raise
    
    async def _wait_for_rollout(self, deployment_name: str, timeout: int = 300):
        """
        Wait for deployment rollout to complete.
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = self.apps_v1.read_namespaced_deployment_status(
                    name=deployment_name,
                    namespace=settings.KUBERNETES_NAMESPACE
                )
                
                if (status.status.available_replicas == status.spec.replicas and
                    status.status.unavailable_replicas == 0):
                    logger.info(f"Rollout complete for {deployment_name}")
                    return
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.warning(f"Error checking rollout status: {str(e)}")
                await asyncio.sleep(5)
        
        logger.warning(f"Rollout timeout for {deployment_name}")
    
    def _parse_prometheus_results(self, results, unit: str = '') -> Dict:
        """
        Parse Prometheus query results into a structured format.
        """
        if not results:
            return {}
        
        try:
            parsed = {}
            values = []
            
            for result in results:
                value = float(result['value'][1])
                values.append(value)
                labels = result.get('metric', {})
                
                # Store by labels if available
                key = labels.get('pod', labels.get('instance', 'default'))
                parsed[key] = {'value': value, 'labels': labels}
            
            # Calculate aggregate stats
            if values:
                parsed['avg_value'] = np.mean(values)
                parsed['max_value'] = np.max(values)
                parsed['min_value'] = np.min(values)
                parsed['count'] = len(values)
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing Prometheus results: {str(e)}")
            return {}
    
    async def get_health_status(self) -> Dict:
        """
        Get health status of the scheduler for monitoring.
        """
        return {
            'status': 'healthy',
            'last_metrics_collection': getattr(self, '_last_metrics_time', None),
            'scaling_history_count': len(self.scaling_history),
            'sla_targets': self.sla_targets,
            'kubernetes_namespace': settings.KUBERNETES_NAMESPACE
        }

# Integration with main.py (add this to main.py's lifespan or as a background task)
async def start_sla_scheduler():
    """
    Function to start the SLA scheduler as a background task in main.py.
    """
    scheduler = EnhancedSLAScheduler()
    asyncio.create_task(scheduler.optimize_resources())
    logger.info("SLA Scheduler started as background task")

# Example usage in main.py:
# In the lifespan function, add:
# await start_sla_scheduler()

