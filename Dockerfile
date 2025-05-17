# Use an official Python runtime as the base image
FROM python:3.9

# Set environment variables for Python
#ENV PYTHONDONTWRITEBYTECODE=1  # Prevent Python from writing .pyc files
#ENV PYTHONUNBUFFERED=1         # Ensure Python output is sent straight to terminal

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1  
ENV PYTHONUNBUFFERED=1        



# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5001

# Set the environment variable for Flask
ENV FLASK_APP=grafana_lark_api.py

# Run the Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]