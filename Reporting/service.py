from flask import Flask, jsonify
from pymongo import MongoClient
import ssl
import os

app = Flask(__name__)

# MongoDB client setup
MONGO_URI = os.getenv("MONGO_URI",
                      "mongodb+srv://healthsync.qntlu.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=HealthSync")
MONGO_CERT_PATH = os.getenv("MONGO_CERT_PATH", "X509-cert-8433791428290760769.pem")
DB_NAME = os.getenv("DB_NAME", "MediTrack")

if not os.path.exists(MONGO_CERT_PATH):
    raise FileNotFoundError(f"PEM file not found at {MONGO_CERT_PATH}")

client = MongoClient(MONGO_URI, tls=True, tlsCertificateKeyFile=MONGO_CERT_PATH)
db = client[DB_NAME]

@app.route('/report/appointments_per_doctor', methods=['GET'])
def appointments_per_doctor():
    result = db.aggregated_appointments_per_doctor.find()
    return jsonify([doc for doc in result])

@app.route('/report/appointments_over_time', methods=['GET'])
def appointments_over_time():
    result = db.aggregated_appointments_over_time.find()
    return jsonify([doc for doc in result])

@app.route('/report/symptoms_by_specialty', methods=['GET'])
def symptoms_by_specialty():
    result = db.aggregated_symptoms_by_specialty.find()
    return jsonify([doc for doc in result])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
