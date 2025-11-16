from flask import Flask, request, jsonify
import logging
import json
from datetime import datetime
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook_receiver():
    try:
        data = request.get_json()
        
        if not data:
            logger.warning("No data received in webhook")
            return jsonify({"error": "No data received"}), 400
        
        # Log the alert
        logger.info(f"📢 Received alert: {json.dumps(data, indent=2)}")
        
        # Process alerts
        if data.get('status') == 'firing':
            for alert in data.get('alerts', []):
                labels = alert.get('labels', {})
                annotations = alert.get('annotations', {})
                
                logger.info(f"🚨 FIRING ALERT: {labels.get('alertname')}")
                logger.info(f"   Severity: {labels.get('severity')}")
                logger.info(f"   Summary: {annotations.get('summary')}")
                logger.info(f"   Description: {annotations.get('description')}")
                logger.info(f"   Timestamp: {alert.get('startsAt')}")
                
        elif data.get('status') == 'resolved':
            for alert in data.get('alerts', []):
                logger.info(f"✅ RESOLVED ALERT: {alert.get('labels', {}).get('alertname')}")
        
        return jsonify({"status": "success", "message": "Alert processed"}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "service": "webhook-receiver"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
