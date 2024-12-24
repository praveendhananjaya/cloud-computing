# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make sure the PEM certificate file is available in the container
# Copy the certificate file into the container
COPY ../Aggregator%20Service/X509-cert-8433791428290760769.pem /app/X509-cert-8433791428290760769.pem

# Expose the port that the Flask app will run on
EXPOSE 5000

# Set environment variables for MongoDB connection
ENV MONGO_URI="mongodb+srv://healthsync.qntlu.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=HealthSync"
ENV MONGO_CERT_PATH="/app/X509-cert-8433791428290760769.pem"
ENV DB_NAME="MediTrack"

# Define the command to run the application
CMD ["python", "service.py"]
