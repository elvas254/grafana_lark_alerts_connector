
## **1. Introduction**
This project implements an API that receives alerts from Grafana and forwards them to Lark using interactive messages. The API processes alert data, formats it into a structured message, and sends it to multiple Lark webhook endpoints.

### **Key Features**
- Receives alerts from Grafana in JSON format
- Converts timestamps to East Africa Time (EAT, UTC+3)
- Formats alerts with color-coded statuses (🔴 Firing, 🟢 Resolved)
- Sends alerts to multiple Lark webhook URLs
- Logs request processing and errors for easy debugging
---

## **2. Project Structure**
The project is organized as follows:

```
grafana_lark_alerts_connector/
├── grafana_lark_api.py
├── tests/
│   ├── __init__.py
│   ├── test_integration_grafana_lark_api.py
│   └── test_unit_grafana_lark_api.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── .gitignore         
```

---

## **3. Setup and Installation**
## Tech Stack
- Python (Flask for API)
- Docker/Docker compose (Containerized deployment)
- Lark Webhooks (For sending notifications)
- Grafana (Source of alerts)
- .env Configuration (For managing environment variables)

### **Prerequisites**
- Python 3.9 or higher
- Docker (optional for containerization)
- Grafana instance with alerting configured
- Lark bot token and webhook URL


### **Environment Setup**
1. Clone the repository:
   ```bash
   git clone http://app.sasakonnect.net:20207/otienokevin/grafana_lark_alerts_connector
   cd grafana_lark_alerts_connector
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file and add your Lark webhook URL:
   ```
   LARK_WEBHOOK_URL=https://open.larksuite.com/open-apis/bot/v2/hook/YOUR_BOT_TOKEN
   ```
### **Running the Application**
1. Start the Flask application:
   ```bash
   python app/main.py
   ```

2. The application will be available at `http://localhost:5001`.

---

## **4. Configuration**
The application can be configured using the `.env` file or environment variables.

### **Environment Variables**
- `LARK_WEBHOOK_URL`: The webhook URL for sending notifications to Lark.
- `FLASK_ENV`: Set to `development` or `production`.

---

## **5. Usage**

### **API Endpoint**
Endpoint: POST /callback

Request Body Example
```json
{
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "QWETU Pop Power Monitoring",
        "name": "Qwetu PoP (Host: G45-FIBER)",
        "host": "server-01",
        "url": "172.16.0.243"
      },
      "annotations": {
        "description": "Power outage at QWETU Pop"
      },
      "startsAt": "2025-03-06T10:15:30Z"
    }
  ]
}
```

Success Response Status Code: 200 OK
```json
{
  "message": "Alert processed and sent to Lark"
}
```

Status Code: 400 Bad Request
```json
{
  "error": "Invalid request format"
}
```
Status Code: 500 Internal Server Error
```json
{
  "error": "Failed to send message to Lark"
}
```

### **Lark Notifications**
- When an alert is received, the application sends a notification to Lark with the following details:
  - Alert title
  - Alert status
  - Description
  - Dashboard and panel URLs
  - Metric values

---

## **6. Testing**
Here’s a simple and clear **documentation for testing** your project. This documentation explains how to set up, run, and interpret the unit and integration tests for your Flask application.

---

# **Testing Documentation**

This document provides instructions for running and understanding the unit and integration tests for the **Grafana Lark Alerts Connector** project.

---
## **Prerequisites**
Before running the tests, ensure the following:
1. **Python 3.x** is installed. Verify with:
   ```bash
   python3 --version
   ```
2. **Dependencies** are installed. Run:
   ```bash
   pip install -r requirements.txt
   ```
3. The **Flask app** (`grafana_lark_api.py`) is in the project root directory.

---

## **Running Unit Tests**
Unit tests verify the functionality of individual components in isolation.

### **Steps**
1. Navigate to the project root directory:
   ```bash
   cd /path/to/grafana_lark_alerts_connector
   ```
2. Run the unit tests:
   ```bash
   python3 -m pytest tests/test_unit_grafana_lark_api.py
   ```

### **Expected Output**
If all tests pass, you’ll see:
```
============================= test session starts =============================
collected 4 items

tests/test_unit_grafana_lark_api.py ....                                 [100%]

============================== 4 passed in 0.05s ==============================
```

---

## **Running Integration Tests**
Integration tests verify the end-to-end functionality of the application, including interactions with external systems.

### **Steps**
1. Ensure no other application is using port `5001`. Check with:
   ```bash
   sudo lsof -i :5001
   ```
2. Run the integration tests:
   ```bash
   python3 tests/test_integration_grafana_lark_api.py
   ```

### **Expected Output**
If all tests pass, you’ll see:
```
....
----------------------------------------------------------------------
Ran 4 tests in 2.005s

OK
```

---

## **Interpreting Test Results**
- **`.` (Dot)**: A passing test.
- **`F`**: A failing test.
- **`E`**: An error in the test setup or execution.

### **Example Output**
```
.FE.
======================================================================
ERROR: test_callback_endpoint_server_error (__main__.TestGrafanaLarkAPIIntegration)
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AssertionError: 500 != 200

======================================================================
FAIL: test_callback_endpoint_invalid_format (__main__.TestGrafanaLarkAPIIntegration)
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AssertionError: 400 != 200

----------------------------------------------------------------------
Ran 4 tests in 2.005s

FAILED (failures=1, errors=1)
```

---

## **Troubleshooting**
### **1. Flask App Fails to Start**
- **Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'python'`
- **Solution**: Use `python3` instead of `python` in the `subprocess.Popen` command.

### **2. Port 5001 Already in Use**
- **Error**: `Address already in use`
- **Solution**: Stop the application using port `5001`:
  ```bash
  sudo kill $(sudo lsof -t -i:5001)
  ```

### **3. Tests Fail with `404 Not Found`**
- **Error**: The `/callback` endpoint is not reachable.
- **Solution**:
  - Ensure the Flask app is running.
  - Verify the route is correctly defined in `grafana_lark_api.py`.

### **4. Tests Fail with `500 Internal Server Error`**
- **Error**: The app encounters an error while processing the request.
- **Solution**:
  - Check the Flask app logs for errors.
  - Ensure the payload format matches the expected structure.

---

## **Running Tests in CI/CD**
To run tests in your CI/CD pipeline, add the following to your `.gitlab-ci.yml`:
```yaml
unit_tests:
  stage: test
  script:
    - pip install -r requirements.txt
    - python3 -m pytest tests/test_unit_grafana_lark_api.py

integration_tests:
  stage: test
  script:
    - pip install -r requirements.txt
    - python3 tests/test_integration_grafana_lark_api.py
```

---
## **7. Deployment**

### **Docker**
1. Build the Docker image:
   ```bash
   docker build -t grafana-lark-connector .
   ```

2. Run the container:
   ```bash
   docker run -p 5001:5001 --env-file .env grafana-lark-connector
   ```

### **Kubernetes (advaced concept)**
- For future enhancements the project can implement kubernetes for the following reasos
    - Deployment: Automate the deployment of the Flask application.
    - Scaling: Scale the application based on demand.
    - High Availability: Ensure the application is always running.
    - Configuration: Manage environment variables and secrets securely.
    - Monitoring: Integrate with monitoring and logging tools.


1. Create a Kubernetes deployment:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: grafana-lark-connector
   spec:
     replicas: 1
     template:
       spec:
         containers:
         - name: grafana-lark-connector
           image: grafana-lark-connector:latest
           ports:
           - containerPort: 5001
           envFrom:
           - secretRef:
               name: grafana-lark-secrets
   ```

2. Apply the deployment:
   ```bash
   kubectl apply -f deployment.yaml
   ```

---

## **8. Maintenance**

### **Logging**
The application logs:
- Incoming alert data
- Formatted Lark messages
- Errors when sending alerts

### **Error Handling**
- The application handles errors gracefully and logs them for debugging.
- Failed Lark notifications are retried automatically.


### **API Security**
API Key Authentication:
Added a check for the X-API-Key header in the /callback endpoint.
If the API key is missing or incorrect, the API returns a 401 Unauthorized response.
IP Whitelisting:
Added a check for the client's IP address (request.remote_addr).
If the IP is not in the ALLOWED_IPS list, the API returns a 403 Forbidden response.

 API_KEY and ALLOWED_IPS are stored in the .env file:



---

## **9. Contributing**
Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a detailed description of your changes.

---
