from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)

# MongoDB connection setup
MONGO_URI = os.getenv("MONGO_URI",
                      "mongodb+srv://healthsync.qntlu.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=HealthSync")
MONGO_CERT_PATH = os.getenv("MONGO_CERT_PATH", "/secrete/X509-cert-8433791428290760769.pem")
DB_NAME = os.getenv("DB_NAME", "MediTrack")
COLLECTION_NAME = "patient"

# Ensure the PEM file exists
if not os.path.exists(MONGO_CERT_PATH):
    raise FileNotFoundError(f"PEM file not found at {MONGO_CERT_PATH}")

client = MongoClient(MONGO_URI, tls=True, tlsCertificateKeyFile=MONGO_CERT_PATH)
db = client[DB_NAME]
patients_collection = db[COLLECTION_NAME]

@app.route('/', methods=['GET'])
def health_check():
    return 'OK', 200

@app.route('/healthz', methods=['GET'])
def health_check():
    return 'OK', 200

@app.route("/patients", methods=["POST"])
def save_patient():
    """Endpoint to save patient data."""
    data = request.get_json()
    # data['date'] = currect.date
    # Validate input data
    required_fields = [ "phone_number", "name", "age", "gender", "medical_details"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        # Insert data into MongoDB
        patient_id = patients_collection.insert_one(data).inserted_id
        return jsonify({"message": "Patient data saved successfully", "id": str(patient_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/patients/<phone_number>", methods=["GET"])
def get_patient(phone_number):
    """Endpoint to retrieve all patient records by phone number."""
    try:
        # Find all records with the given phone number
        patients = patients_collection.find({"phone_number": phone_number})

        # Convert the cursor to a list of dictionaries and ensure ObjectId is JSON serializable
        patient_list = []
        for patient in patients:
            patient["_id"] = str(patient["_id"])  # Convert ObjectId to string
            patient_list.append(patient)

        if patient_list:
            return jsonify(patient_list), 200
        else:
            return jsonify({"error": "No patients found for the given phone number"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
