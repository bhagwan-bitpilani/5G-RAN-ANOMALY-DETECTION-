"""
Enhanced ML Service Client for communicating with ML service
"""
import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import time
import hashlib
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, Gauge

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics for ML client
ml_request_counter = Counter('ml_client_requests_total', 'Total ML service requests', ['method', 'status'])
ml_request_duration = Histogram('ml_client_request_duration_seconds', 'ML request duration')
ml_client_errors = Counter('ml_client_errors_total', 'ML client errors', ['error_type'])
ml_service_health = Gauge('ml_service_health', 'ML service health status (1=healthy, 0=unhealthy)')

@dataclass
class MLRequestResult:
    """Result container for ML service requests"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    model_used: Optional[str] = None
    response_time: float = 0.0
    is_fallback: bool = False

class MLClient:
    """Enhanced client for ML service communication with retries, caching, and fallbacks"""
    
    def __init__(
        self, 
        base_url: str = "http://ml-service:8001",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        cache_ttl: int = 300  # 5 minutes
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.cache_ttl = cache_ttl
        
        # Cache for model info and health status
        self._cache = {}
        self._health_status = False
        self._last_health_check = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Circuit breaker state
        self._circuit_open = False
        self._circuit_open_until = None
        self._failure_count = 0
        self._success_count = 0
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'fallback_used': 0,
            'avg_response_time': 0.0
        }

    async def ensure_session(self) -> aiohttp.ClientSession:
        """Ensure we have an active session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': '5G-KPI-app/2.0.0',
                    'Content-Type': 'application/json'
                }
            )
        return self._session

    async def close(self):
        """Close the client session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @asynccontextmanager
    async def session_context(self):
        """Context manager for session handling"""
        session = await self.ensure_session()
        try:
            yield session
        finally:
            # Don't close session here to allow connection reuse
            pass

    def _get_cache_key(self, endpoint: str, data: Dict = None) -> str:
        """Generate cache key for requests"""
        key_data = f"{endpoint}:{json.dumps(data, sort_keys=True) if data else ''}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self._cache:
            return False
        
        cached_time, _ = self._cache[key]
        return (datetime.utcnow() - cached_time).total_seconds() < self.cache_ttl

    def _get_cached_response(self, key: str) -> Optional[Any]:
        """Get cached response if valid"""
        if self._is_cache_valid(key):
            _, data = self._cache[key]
            return data
        return None

    def _set_cached_response(self, key: str, data: Any):
        """Set cached response"""
        self._cache[key] = (datetime.utcnow(), data)

    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> MLRequestResult:
        """Make HTTP request to ML service with retry logic"""
        
        # Check circuit breaker
        if self._circuit_open:
            if self._circuit_open_until and datetime.utcnow() < self._circuit_open_until:
                logger.warning("Circuit breaker is OPEN, using fallback")
                ml_client_errors.labels(error_type='circuit_breaker').inc()
                return MLRequestResult(
                    success=False, 
                    error="Circuit breaker is open",
                    is_fallback=True
                )
            else:
                # Reset circuit after timeout
                self._circuit_open = False
                self._failure_count = 0

        start_time = time.time()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session_context() as session:
                if method.upper() == 'GET':
                    async with session.get(url) as response:
                        return await self._handle_response(response, start_time)
                elif method.upper() == 'POST':
                    async with session.post(url, json=data) as response:
                        return await self._handle_response(response, start_time)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                    
        except asyncio.TimeoutError:
            error_msg = f"ML service timeout after {self.timeout}s"
            logger.warning(error_msg)
            ml_client_errors.labels(error_type='timeout').inc()
            return await self._handle_request_error(error_msg, start_time, retry_count)
            
        except aiohttp.ClientError as e:
            error_msg = f"ML service connection error: {str(e)}"
            logger.warning(error_msg)
            ml_client_errors.labels(error_type='connection').inc()
            return await self._handle_request_error(error_msg, start_time, retry_count)
            
        except Exception as e:
            error_msg = f"Unexpected error calling ML service: {str(e)}"
            logger.error(error_msg)
            ml_client_errors.labels(error_type='unexpected').inc()
            return await self._handle_request_error(error_msg, start_time, retry_count)

    async def _handle_response(self, response: aiohttp.ClientResponse, start_time: float) -> MLRequestResult:
        """Handle HTTP response from ML service"""
        response_time = time.time() - start_time
        ml_request_duration.observe(response_time)
        
        try:
            response_data = await response.json()
        except Exception as e:
            response_data = {"error": f"Failed to parse response: {str(e)}"}

        if response.status == 200:
            self._record_success()
            ml_request_counter.labels(method=response.method, status='success').inc()
            
            return MLRequestResult(
                success=True,
                data=response_data,
                model_used=response_data.get('model_used', 'unknown'),
                response_time=response_time
            )
        else:
            error_msg = f"ML service returned {response.status}: {response_data.get('error', 'Unknown error')}"
            logger.warning(error_msg)
            ml_request_counter.labels(method=response.method, status='error').inc()
            
            return MLRequestResult(
                success=False,
                error=error_msg,
                response_time=response_time
            )

    async def _handle_request_error(self, error_msg: str, start_time: float, retry_count: int) -> MLRequestResult:
        """Handle request errors and implement retry logic"""
        response_time = time.time() - start_time
        self._record_failure()
        
        # Retry logic
        if retry_count < self.max_retries:
            logger.info(f"Retrying request ({retry_count + 1}/{self.max_retries}) after {self.retry_delay}s")
            await asyncio.sleep(self.retry_delay)
            return await self._make_request('POST', '/api/ml/detect', {}, retry_count + 1)
        
        return MLRequestResult(
            success=False,
            error=error_msg,
            response_time=response_time,
            is_fallback=True
        )

    def _record_success(self):
        """Record successful request for circuit breaker"""
        self._success_count += 1
        self._failure_count = max(0, self._failure_count - 1)  # Decay failures
        
        if self._circuit_open:
            logger.info("Circuit breaker transitioning to HALF-OPEN")
            self._circuit_open = False

    def _record_failure(self):
        """Record failed request for circuit breaker"""
        self._failure_count += 1
        self.stats['failed_requests'] += 1
        
        # Open circuit if failure threshold reached
        if self._failure_count >= 5 and not self._circuit_open:
            logger.warning("Circuit breaker OPENING due to consecutive failures")
            self._circuit_open = True
            self._circuit_open_until = datetime.utcnow() + timedelta(minutes=1)

    async def detect_anomalies(self, kpi_data: Dict[str, Any]) -> MLRequestResult:
        """
        Detect anomalies using ML service with enhanced 5G KPI support
        
        Args:
            kpi_data: Dictionary containing KPI data with structure:
                {
                    'cell_id': 'NR2600_001',
                    'timestamp': '2024-01-01T00:00:00Z',
                    'downlink_ue_throughput': 750000000,
                    'downlink_prb_utilization': 65.5,
                    'data_session_setup_success_rate': 99.2,
                    ...
                }
        
        Returns:
            MLRequestResult with anomaly detection results
        """
        logger.info(f"Detecting anomalies for cell: {kpi_data.get('cell_id', 'unknown')}")
        
        # Try ML service first
        result = await self._make_request('POST', '/api/ml/detect', kpi_data)
        
        if result.success:
            return result
        
        # Fallback to local anomaly detection
        logger.warning("Using enhanced fallback anomaly detection")
        self.stats['fallback_used'] += 1
        
        fallback_result = await self._fallback_anomaly_detection(kpi_data)
        fallback_result.is_fallback = True
        return fallback_result

    async def _fallback_anomaly_detection(self, kpi_data: Dict[str, Any]) -> MLRequestResult:
        """Enhanced fallback anomaly detection using 3GPP thresholds"""
        
        # 3GPP-compliant thresholds for different KPIs
        threegpp_thresholds = {
            'downlink_ue_throughput': {'min': 50000000, 'max': 1000000000, 'weight': 0.3},
            'downlink_prb_utilization': {'min': 5, 'max': 85, 'weight': 0.2},
            'data_session_setup_success_rate': {'min': 98, 'max': 100, 'weight': 0.15},
            'endc_add_setup_success_rate': {'min': 95, 'max': 100, 'weight': 0.1},
            'inter_sgnb_change_success_rate': {'min': 90, 'max': 100, 'weight': 0.1},
            'maximum_active_endc_user': {'min': 1, 'max': 200, 'weight': 0.05},
            'downlink_latency': {'min': 1, 'max': 20, 'weight': 0.05},
            'downlink_payload': {'min': 0.1, 'max': 500, 'weight': 0.05}
        }

        anomalies_detected = []
        total_score = 0.0
        max_possible_score = sum(t['weight'] for t in threegpp_thresholds.values())
        
        for kpi_name, threshold in threegpp_thresholds.items():
            value = kpi_data.get(kpi_name)
            if value is None:
                continue
                
            min_val = threshold['min']
            max_val = threshold['max']
            weight = threshold['weight']
            
            if value < min_val or value > max_val:
                if value < min_val:
                    reason = f"Low {kpi_name}: {value} (3GPP min: {min_val})"
                    score_component = (min_val - value) / min_val
                else:
                    reason = f"High {kpi_name}: {value} (3GPP max: {max_val})"
                    score_component = (value - max_val) / max_val
                
                anomalies_detected.append(reason)
                total_score += min(score_component, 1.0) * weight
        
        normalized_score = total_score / max_possible_score if max_possible_score > 0 else 0
        is_anomaly = len(anomalies_detected) > 0
        
        # Determine severity
        severity = "low"
        if normalized_score > 0.7:
            severity = "critical"
        elif normalized_score > 0.5:
            severity = "high"
        elif normalized_score > 0.3:
            severity = "medium"

        return MLRequestResult(
            success=True,
            data={
                "is_anomaly": is_anomaly,
                "anomaly_score": round(normalized_score, 3),
                "severity": severity,
                "reasons": anomalies_detected,
                "model_used": "3gpp_threshold_fallback",
                "thresholds_checked": list(threegpp_thresholds.keys()),
                "compliance": "3GPP Release 16"
            },
            model_used="3gpp_threshold_fallback"
        )

    async def train_model(self, training_data: Dict[str, Any]) -> MLRequestResult:
        """Train ML model with new data"""
        logger.info("Requesting model training with new data")
        
        # Cache key for training requests (don't cache actual training)
        return await self._make_request('POST', '/api/ml/train', training_data)

    async def get_model_info(self) -> MLRequestResult:
        """Get information about loaded ML models with caching"""
        cache_key = self._get_cache_key('/api/ml/models')
        cached_response = self._get_cached_response(cache_key)
        
        if cached_response:
            logger.debug("Returning cached model info")
            return MLRequestResult(success=True, data=cached_response)
        
        result = await self._make_request('GET', '/api/ml/models')
        if result.success and result.data:
            self._set_cached_response(cache_key, result.data)
        
        return result

    async def get_model_performance(self) -> MLRequestResult:
        """Get model performance metrics"""
        cache_key = self._get_cache_key('/api/ml/performance')
        cached_response = self._get_cached_response(cache_key)
        
        if cached_response:
            return MLRequestResult(success=True, data=cached_response)
        
        result = await self._make_request('GET', '/api/ml/performance')
        if result.success and result.data:
            self._set_cached_response(cache_key, result.data)
        
        return result

    async def health_check(self) -> bool:
        """Enhanced health check with caching and metrics"""
        # Cache health checks for 30 seconds
        if (self._last_health_check and 
            (datetime.utcnow() - self._last_health_check).total_seconds() < 30):
            ml_service_health.set(1 if self._health_status else 0)
            return self._health_status
        
        try:
            async with self.session_context() as session:
                async with session.get(f"{self.base_url}/health", timeout=5) as response:
                    self._health_status = response.status == 200
                    self._last_health_check = datetime.utcnow()
                    
                    if self._health_status:
                        logger.debug("ML service health check: HEALTHY")
                    else:
                        logger.warning(f"ML service health check: UNHEALTHY (status: {response.status})")
                    
                    ml_service_health.set(1 if self._health_status else 0)
                    return self._health_status
                    
        except Exception as e:
            logger.warning(f"ML service health check failed: {str(e)}")
            self._health_status = False
            self._last_health_check = datetime.utcnow()
            ml_service_health.set(0)
            return False

    async def batch_detect_anomalies(self, kpi_batch: List[Dict[str, Any]]) -> MLRequestResult:
        """Detect anomalies for multiple KPI records in batch"""
        logger.info(f"Batch detecting anomalies for {len(kpi_batch)} records")
        
        batch_data = {
            "batch_size": len(kpi_batch),
            "records": kpi_batch,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self._make_request('POST', '/api/ml/detect-batch', batch_data)
        
        if not result.success:
            # Fallback: process each record individually with fallback
            logger.warning("Using fallback for batch anomaly detection")
            fallback_results = []
            
            for kpi_data in kpi_batch:
                fallback_result = await self._fallback_anomaly_detection(kpi_data)
                fallback_results.append(fallback_result.data)
            
            return MLRequestResult(
                success=True,
                data={
                    "batch_results": fallback_results,
                    "total_processed": len(fallback_results),
                    "model_used": "3gpp_threshold_fallback_batch"
                },
                model_used="3gpp_threshold_fallback_batch",
                is_fallback=True
            )
        
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        total_requests = self.stats['total_requests']
        success_rate = ((total_requests - self.stats['failed_requests']) / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'success_rate': round(success_rate, 2),
            'circuit_breaker_open': self._circuit_open,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'service_healthy': self._health_status,
            'cache_size': len(self._cache)
        }

    async def reset_circuit_breaker(self):
        """Reset circuit breaker manually"""
        self._circuit_open = False
        self._circuit_open_until = None
        self._failure_count = 0
        self._success_count = 0
        logger.info("Circuit breaker manually reset")

    async def clear_cache(self):
        """Clear all cached responses"""
        self._cache.clear()
        logger.info("ML client cache cleared")

# Global ML client instance with enhanced configuration
ml_client = MLClient(
    base_url="http://ml-service:8001",
    timeout=30,
    max_retries=3,
    retry_delay=1.0,
    cache_ttl=300  # 5 minutes
)

# Utility functions for working with the ML client
async def initialize_ml_client():
    """Initialize the global ML client"""
    try:
        # Test connection
        healthy = await ml_client.health_check()
        if healthy:
            logger.info("✅ ML client initialized successfully")
        else:
            logger.warning("⚠️ ML service is unavailable, fallback mode will be used")
        return healthy
    except Exception as e:
        logger.error(f"❌ ML client initialization failed: {e}")
        return False

async def shutdown_ml_client():
    """Shutdown the global ML client"""
    await ml_client.close()
    logger.info("ML client shutdown complete")

# Example usage and testing
async def example_usage():
    """Example of how to use the enhanced ML client"""
    
    # Initialize client
    await initialize_ml_client()
    
    try:
        # Example KPI data
        kpi_data = {
            'cell_id': 'NR2600_001',
            'timestamp': datetime.utcnow().isoformat(),
            'downlink_ue_throughput': 25000000,  # Low throughput (anomaly)
            'downlink_prb_utilization': 65.5,
            'data_session_setup_success_rate': 99.2,
            'endc_add_setup_success_rate': 97.8,
            'inter_sgnb_change_success_rate': 95.1,
            'maximum_active_endc_user': 145,
            'downlink_latency': 8.2,
            'downlink_payload': 187.3
        }
        
        # Detect anomalies
        result = await ml_client.detect_anomalies(kpi_data)
        
        if result.success:
            print(f"Anomaly detected: {result.data.get('is_anomaly')}")
            print(f"Score: {result.data.get('anomaly_score')}")
            print(f"Model used: {result.model_used}")
        else:
            print(f"Error: {result.error}")
        
        # Get statistics
        stats = ml_client.get_stats()
        print(f"Client stats: {stats}")
        
    finally:
        await shutdown_ml_client()

if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_usage())
