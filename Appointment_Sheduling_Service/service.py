from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)

# MongoDB connection setup
MONGO_URI = os.getenv("MONGO_URI",
                      "mongodb+srv://healthsync.qntlu.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=HealthSync")
MONGO_CERT_PATH = os.getenv("MONGO_CERT_PATH", "secrete/X509-cert-8433791428290760769.pem")
DB_NAME = os.getenv("DB_NAME", "MediTrack")
if not os.path.exists(MONGO_CERT_PATH):
    raise FileNotFoundError(f"PEM file not found at {MONGO_CERT_PATH}")

client = MongoClient(MONGO_URI, tls=True, tlsCertificateKeyFile=MONGO_CERT_PATH)
db = client[DB_NAME]
doctors_collection = db['doctor']
appointments_collection = db['appointments']


# Helper function to validate the datetime
def is_valid_datetime(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False


@app.route('/appointments/healthz', methods=['GET'])
def health_check():
    return 'OK', 200

# Endpoint to add doctor availability
@app.route('/doctor/availability', methods=['POST'])
def add_doctor_availability():
    data = request.get_json()

    doctor_name = data.get('doctor_name')
    available_slots = data.get('available_slots')  # List of datetime strings in "YYYY-MM-DD HH:MM:SS"

    if not doctor_name or not available_slots:
        return jsonify({"error": "Missing doctor name or availability slots"}), 400

    # Validate availability slots
    invalid_slots = [slot for slot in available_slots if not is_valid_datetime(slot)]
    if invalid_slots:
        return jsonify({"error": f"Invalid datetime format in slots: {', '.join(invalid_slots)}"}), 400

    doctor_data = {
        'doctor_name': doctor_name,
        'available_slots': [datetime.strptime(slot, "%Y-%m-%d %H:%M:%S") for slot in available_slots]
    }

    # Insert into MongoDB
    doctors_collection.insert_one(doctor_data)
    print(doctor_data)

    return jsonify({"message": f"Availability for {doctor_name} added successfully."}), 201


# Endpoint to book an appointment
@app.route('/appointment/book', methods=['POST'])
def book_appointment():
    data = request.get_json()

    patient_name = data.get('patient_name')
    doctor_name = data.get('doctor_name')
    appointment_time = data.get('appointment_time')  # datetime string in "YYYY-MM-DD HH:MM:SS"

    if not patient_name or not doctor_name or not appointment_time:
        return jsonify({"error": "Missing patient name, doctor name, or appointment time"}), 400

    if not is_valid_datetime(appointment_time):
        return jsonify({"error": "Invalid datetime format for appointment"}), 400

    appointment_time = datetime.strptime(appointment_time, "%Y-%m-%d %H:%M:%S")

    # Check if the doctor is available
    doctor = doctors_collection.find_one({"doctor_name": doctor_name, "available_slots": appointment_time})

    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    if appointment_time not in doctor['available_slots']:
        return jsonify({"error": "Selected time is not available"}), 400

    # Create the appointment
    appointment = {
        'patient_name': patient_name,
        'doctor_name': doctor_name,
        'appointment_time': appointment_time
    }

    # Insert into MongoDB
    appointments_collection.insert_one(appointment)

    # Remove the slot from doctor's availability after booking
    doctors_collection.update_one(
        {"doctor_name": doctor_name},
        {"$pull": {"available_slots": appointment_time}}
    )

    return jsonify({
                       "message": f"Appointment booked successfully for {patient_name} with Dr. {doctor_name} at {appointment_time}."}), 201


# Endpoint to check available slots for a doctor
@app.route('/doctor/availability/<doctor_name>', methods=['GET'])
def get_doctor_availability(doctor_name):
    # Query to find all entries for the doctor
    doctor_entries = doctors_collection.find({"doctor_name": doctor_name})

    # Check if any documents are found
    if not doctor_entries:
        return jsonify({"error": "Doctor not found"}), 404

    # Aggregate all available slots from multiple entries
    all_slots = []
    for entry in doctor_entries:
        available_slots = entry.get('available_slots', [])
        all_slots.extend(available_slots)

    # Remove duplicates and format slots as strings
    formatted_slots = sorted(
        {slot.strftime("%Y-%m-%d %H:%M:%S") if isinstance(slot, datetime) else slot for slot in all_slots}
    )

    return jsonify({
        "name": doctor_name,
        "available_slots": formatted_slots
    }), 200



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)