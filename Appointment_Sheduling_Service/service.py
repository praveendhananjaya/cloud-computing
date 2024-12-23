from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)

# MongoDB connection setup
MONGO_URI = os.getenv("MONGO_URI",
                      "mongodb+srv://healthsync.qntlu.mongodb.net/?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=HealthSync")
MONGO_CERT_PATH = os.getenv("MONGO_CERT_PATH", "X509-cert-8433791428290760769.pem")
DB_NAME = os.getenv("DB_NAME", "MediTrack")
COLLECTION_NAME = "appointments"

# Ensure the PEM file exists
if not os.path.exists(MONGO_CERT_PATH):
    raise FileNotFoundError(f"PEM file not found at {MONGO_CERT_PATH}")

client = MongoClient(MONGO_URI, tls=True, tlsCertificateKeyFile=MONGO_CERT_PATH)
db = client[DB_NAME]
patients_collection = db[COLLECTION_NAME]

from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)


class AppointmentSchedulingService:
    def __init__(self, mongo_uri='mongodb://localhost:27017/', db_name='appointment_system'):
        # Initialize the MongoDB client
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

        # Define the collections
        self.doctors_collection = self.db['doctors']
        self.appointments_collection = self.db['appointments']

    def add_doctor(self, doctor_id, name, specialty, availability_slots):
        """Add a new doctor with available time slots"""
        doctor = {
            'doctor_id': doctor_id,
            'name': name,
            'specialty': specialty,
            'availability_slots': availability_slots  # List of datetime objects
        }
        result = self.doctors_collection.insert_one(doctor)
        return result.inserted_id

    def get_doctor_availability(self, doctor_id):
        """Get available time slots for a specific doctor"""
        doctor = self.doctors_collection.find_one({'doctor_id': doctor_id})
        if doctor:
            return doctor['availability_slots']
        return None

    def book_appointment(self, patient_name, doctor_id, slot):
        """Book an appointment if the slot is available"""
        doctor = self.doctors_collection.find_one({'doctor_id': doctor_id})
        if not doctor:
            return 'Doctor not found'

        # Check if the requested slot is available
        if slot in doctor['availability_slots']:
            # Book the appointment by creating a record in the appointments collection
            appointment = {
                'patient_name': patient_name,
                'doctor_id': doctor_id,
                'slot': slot,
                'created_at': datetime.now()
            }
            self.appointments_collection.insert_one(appointment)

            # Remove the booked slot from the doctor's availability
            self.doctors_collection.update_one(
                {'doctor_id': doctor_id},
                {'$pull': {'availability_slots': slot}}
            )
            return 'Appointment booked successfully'
        return 'Slot not available'

    def cancel_appointment(self, appointment_id):
        """Cancel an existing appointment and free the slot"""
        appointment = self.appointments_collection.find_one({'_id': appointment_id})
        if not appointment:
            return 'Appointment not found'

        # Find the doctor and add the slot back to their availability
        doctor = self.doctors_collection.find_one({'doctor_id': appointment['doctor_id']})
        if doctor:
            self.doctors_collection.update_one(
                {'doctor_id': appointment['doctor_id']},
                {'$push': {'availability_slots': appointment['slot']}}
            )

        # Delete the appointment record
        self.appointments_collection.delete_one({'_id': appointment_id})
        return 'Appointment canceled successfully'

    def get_appointments(self, patient_name=None):
        """Get all appointments or filter by patient name"""
        query = {}
        if patient_name:
            query['patient_name'] = patient_name

        appointments = self.appointments_collection.find(query)
        return list(appointments)


# Instantiate the service
appointment_service = AppointmentSchedulingService(mongo_uri= MONGO_URI, db_name= DB_NAME)


@app.route('/doctors', methods=['POST'])
def add_doctor():
    data = request.get_json()
    doctor_id = data['doctor_id']
    name = data['name']
    specialty = data['specialty']
    availability_slots = [datetime.strptime(slot, '%Y-%m-%d %H:%M:%S') for slot in data['availability_slots']]

    doctor_id = appointment_service.add_doctor(doctor_id, name, specialty, availability_slots)
    return jsonify({'message': 'Doctor added successfully', 'doctor_id': doctor_id}), 201


@app.route('/doctors/<int:doctor_id>/availability', methods=['GET'])
def get_doctor_availability(doctor_id):
    availability = appointment_service.get_doctor_availability(doctor_id)
    if availability is None:
        return jsonify({'message': 'Doctor not found'}), 404

    availability_slots = [slot.strftime('%Y-%m-%d %H:%M:%S') for slot in availability]
    return jsonify({'availability_slots': availability_slots})


@app.route('/appointments', methods=['POST'])
def book_appointment():
    data = request.get_json()
    patient_name = data['patient_name']
    doctor_id = data['doctor_id']
    slot = datetime.strptime(data['slot'], '%Y-%m-%d %H:%M:%S')

    result = appointment_service.book_appointment(patient_name, doctor_id, slot)
    if result == 'Appointment booked successfully':
        return jsonify({'message': result}), 201
    return jsonify({'message': result}), 400


@app.route('/appointments', methods=['GET'])
def get_appointments():
    patient_name = request.args.get('patient_name')
    appointments = appointment_service.get_appointments(patient_name)

    if not appointments:
        return jsonify({'message': 'No appointments found'}), 404

    appointments_data = []
    for appointment in appointments:
        appointment_data = {
            'appointment_id': str(appointment['_id']),
            'patient_name': appointment['patient_name'],
            'doctor_id': appointment['doctor_id'],
            'slot': appointment['slot'].strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': appointment['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        }
        appointments_data.append(appointment_data)

    return jsonify({'appointments': appointments_data})


@app.route('/appointments/<appointment_id>', methods=['DELETE'])
def cancel_appointment(appointment_id):
    appointment_id = appointment_id.strip()
    result = appointment_service.cancel_appointment(appointment_id)
    if result == 'Appointment canceled successfully':
        return jsonify({'message': result})
    return jsonify({'message': result}), 400


if __name__ == '__main__':
    app.run(debug=True)
