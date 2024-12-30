# aggregate.py
from pymongo import MongoClient
import ssl
import os

# MongoDB client setup
MONGO_URI = os.getenv("MONGO_URI",
                      "mongodb+srv://healthsync.qntlu.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=HealthSync")
MONGO_CERT_PATH = os.getenv("MONGO_CERT_PATH", "/X509-cert-8433791428290760769.pem")
DB_NAME = os.getenv("DB_NAME", "MediTrack")

# Ensure the PEM file exists
if not os.path.exists(MONGO_CERT_PATH):
    raise FileNotFoundError(f"PEM file not found at {MONGO_CERT_PATH}")

client = MongoClient(MONGO_URI, tls=True, tlsCertificateKeyFile=MONGO_CERT_PATH)
db = client[DB_NAME]


def aggregate_appointments_per_doctor():
    pipeline = [
        {"$group": {"_id": "$doctor_name", "appointment_count": {"$sum": 1}}},
        {"$out": "aggregated_appointments_per_doctor"}
    ]
    db.appointments.aggregate(pipeline)

def aggregate_appointments_over_time():
    pipeline = [
        {"$group": {
            "_id": {"year": {"$year": "$appointment_date"}, "month": {"$month": "$appointment_date"}},
            "appointment_count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}},
        {"$out": "aggregated_appointments_over_time"}
    ]
    db.appointments.aggregate(pipeline)

def aggregate_symptoms_by_specialty():
    pipeline = [
        {"$group": {"_id": "$specialty", "symptoms": {"$push": "$symptom"}}},
        {"$project": {"specialty": "$_id", "symptoms": 1, "_id": 0}},
        {"$out": "aggregated_symptoms_by_specialty"}
    ]
    db.appointments.aggregate(pipeline)

if __name__ == '__main__':
    aggregate_appointments_per_doctor()
    aggregate_appointments_over_time()
    aggregate_symptoms_by_specialty()
    print("Aggregation complete")

