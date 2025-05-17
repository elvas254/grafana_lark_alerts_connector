import json
import logging
import requests
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load Lark webhook URLs
LARK_WEBHOOK_URLS = os.getenv("LARK_WEBHOOK_URLS", "").split(",")

class AlertFormatter:
    """Base class for formatting different types of alerts."""
    
    @staticmethod
    def convert_to_eat(utc_time):
        """Convert UTC time to East Africa Time (UTC+3)."""
        if not utc_time:
            return "N/A"
        utc_dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%SZ")
        eat_dt = utc_dt.replace(tzinfo=timezone.utc) + timedelta(hours=3)
        return eat_dt.strftime("%I:%M %p")

    @staticmethod
    def calculate_downtime(start_time, end_time=None):
        """Calculate downtime duration in human-readable format."""
        if not start_time:
            return "N/A"
        
        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        end_dt = datetime.utcnow().replace(tzinfo=timezone.utc) if not end_time else datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        
        downtime = end_dt - start_dt
        hours, remainder = divmod(int(downtime.total_seconds()), 3600)
        minutes = remainder // 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}hrs {minutes}mins"
        elif hours > 0:
            return f"{hours}hrs"
        else:
            return f"{minutes}mins"

    @classmethod
    def create_base_message(cls, title, status, color):
        """Create the base structure for a Lark message."""
        return {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": color
                },
                "elements": []
            }
        }

class StandardAlertFormatter(AlertFormatter):
    """Formatter for standard alerts."""
    
    @classmethod
    def format(cls, alert_data):
        is_firing = alert_data["status"].lower() == "firing"
        status_text = "FIRING" if is_firing else "RESOLVED"
        header_color = "red" if is_firing else "green"
        timestamp_key = "startsAt" if is_firing else "endsAt"
        timestamp_eat = cls.convert_to_eat(alert_data.get(timestamp_key))
        duration = cls.calculate_downtime(alert_data.get("startsAt"), alert_data.get("endsAt") if not is_firing else None)

        alert_description = alert_data["description"]
        if alert_data.get("url"):
            alert_description += f"\n\n🔗 **URL**: {alert_data['url']}"

        message = cls.create_base_message(
            title=f"[{status_text}] {alert_data['alertname']}",
            status=status_text,
            color=header_color
        )

        message["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"**<font color='blue'>📍 Location</font>**: {alert_data['name']} (Host: {alert_data['host']})\n\n"
                    f"**<font color='{header_color}'>⚠️ Issue</font>**: {alert_description}\n\n"
                    f"**<font color='gray'>🕒 {'Started' if is_firing else 'Resolved At'}</font>**: {timestamp_eat}\n\n"
                    f"**<font color='gray'>⏳ Duration</font>**: {duration}"
                )
            }
        })

        return message

class OLTAlertFormatter(AlertFormatter):
    """Formatter for OLT offline alerts."""
    
    @classmethod
    def format(cls, alert_data):
        is_firing = alert_data["status"].lower() == "firing"
        header_color = "orange" if is_firing else "green"
        status_text = f" {alert_data['olt_name']} IS OFFLINE, PLS CHECK" if is_firing else f" {alert_data['olt_name']} IS BACK ONLINE"
        timestamp_key = "startsAt" if is_firing else "endsAt"
        timestamp_eat = cls.convert_to_eat(alert_data.get(timestamp_key))
        duration = cls.calculate_downtime(alert_data.get("startsAt"), alert_data.get("endsAt") if not is_firing else None)

        message = cls.create_base_message(
            title=f"GPON OLT Monitoring {alert_data['url']}",
            status=status_text,
            color=header_color
        )

        message["card"]["elements"].extend([
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**🌍 Region**: {alert_data['region']}\n\n"
                        f"**⚠️ Status**: {status_text}\n\n"
                        f"**🕒 Started**: {timestamp_eat}\n\n"
                        f"**⏳ Duration**: {duration}"
                    )
                }
            },
            {"tag": "hr"}
        ])

        return message

class CelcomAlertFormatter(AlertFormatter):
    """Formatter for Celcom data streaming alerts."""
    
    @classmethod
    def format(cls, alert_data):
        is_firing = alert_data["status"].lower() == "firing"
        status_text = "NO DATA STREAMING" if is_firing else "DATA STREAMING RESTORED"
        header_color = "red" if is_firing else "green"
        timestamp_key = "startsAt" if is_firing else "endsAt"
        timestamp_eat = cls.convert_to_eat(alert_data.get(timestamp_key))
        duration = cls.calculate_downtime(alert_data.get("startsAt"), alert_data.get("endsAt") if not is_firing else None)

        message = cls.create_base_message(
            title="Celcom Data Streaming Alert",
            status=status_text,
            color=header_color
        )

        message["card"]["elements"].append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"**🚨 Celcom Data Streaming Alert**\n\n"
                    f"**⚠️ Status**: {status_text.upper()}\n\n"
                    f"**📍 Endpoint**: Celcom SMS Ingestion Point\n\n"
                    f"**🕒 {'Started' if is_firing else 'Resolved At'}**: {timestamp_eat}\n\n"
                    f"**⏳ Duration**: {duration}\n\n"
                    f"{'**🧭 Action Needed**: Check SMS flow or Celcom Pipeline status.' if is_firing else '**✅ No action required — issue resolved.**'}"
                )
            }
        })

        return message


def send_to_lark(message):
    """Send formatted message to Lark webhook."""
    for url in LARK_WEBHOOK_URLS:
        try:
            response = requests.post(url, json=message)
            if response.status_code == 200:
                logging.info("Message sent successfully to Lark.")
                return True
            else:
                logging.error(f"Failed to send message to Lark. Response: {response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending message to Lark: {e}")
    return False

def process_alert(alert, formatter_class):
    """Generic alert processing function."""
    alert_data = {
        "status": alert.get('status', 'unknown').capitalize(),
        "url": alert['labels'].get('url', 'No URL Provided'),
        "startsAt": alert.get("startsAt"),
        "endsAt": alert.get("endsAt")
    }
    
    # Add formatter-specific fields
    if formatter_class == StandardAlertFormatter:
        alert_data.update({
            "alertname": alert['labels'].get('alertname', 'Unknown Alert'),
            "name": alert['labels'].get('name', 'Unknown Location'),
            "host": alert['labels'].get('host', 'Unknown Host'),
            "description": alert.get('annotations', {}).get('description', 'No description provided')
        })
    elif formatter_class == OLTAlertFormatter:
        alert_data.update({
            "region": alert['labels'].get('host', 'Unknown Region'),
            "olt_name": alert['labels'].get('name', 'Unknown OLT')
        })
    elif formatter_class == CelcomAlertFormatter:
        alert_data.update({
            "interface": alert['labels'].get('interface', 'Unknown Interface')
        })
    
    formatted_message = formatter_class.format(alert_data)
    logging.info("Formatted Message: %s", json.dumps(formatted_message, ensure_ascii=False))
    return formatted_message

@app.route('/callback', methods=['POST'])
def callback():
    """API endpoint to receive standard alerts from Grafana."""
    client_ip = request.remote_addr
    logging.info(f"Client IP: {client_ip}")

    data = request.json
    logging.info(f"Incoming JSON Payload: {json.dumps(data, indent=2)}")

    if not data or 'alerts' not in data:
        logging.error("Invalid request format")
        return jsonify({"error": "Invalid request format"}), 400

    formatted_message = process_alert(data['alerts'][0], StandardAlertFormatter)
    success = send_to_lark(formatted_message)
    
    if success:
        return jsonify({"message": "Alert processed and sent to Lark"}), 200
    else:
        return jsonify({"error": "Failed to send message to Lark"}), 500

@app.route('/olt_offline', methods=['POST'])
def olt_offline_callback():
    """API endpoint to receive OLT offline alerts."""
    data = request.json
    if not data or 'alerts' not in data:
        return jsonify({"error": "Invalid request format"}), 400

    formatted_message = process_alert(data['alerts'][0], OLTAlertFormatter)
    success = send_to_lark(formatted_message)
    
    if success:
        return jsonify({"message": "OLT offline alert processed and sent to Lark"}), 200
    else:
        return jsonify({"error": "Failed to send message to Lark"}), 500

@app.route('/celcom_alert', methods=['POST'])
def celcom_alert_callback():
    """API endpoint to receive Celcom no-data streaming alerts."""
    data = request.json
    if not data or 'alerts' not in data:
        logging.error("Invalid request format for Celcom alert")
        return jsonify({"error": "Invalid request format"}), 400

    formatted_message = process_alert(data['alerts'][0], CelcomAlertFormatter)
    success = send_to_lark(formatted_message)
    
    if success:
        return jsonify({"message": "Celcom alert processed and sent to Lark"}), 200
    else:
        return jsonify({"error": "Failed to send Celcom alert to Lark"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)