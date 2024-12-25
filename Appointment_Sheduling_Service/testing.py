# tests/test_app.py
import unittest
from unittest.mock import patch, MagicMock
from service import app, is_valid_datetime

class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_is_valid_datetime(self):
        self.assertTrue(is_valid_datetime("2024-12-25 15:30:00"))
        self.assertFalse(is_valid_datetime("2024-12-25"))

    @patch("app.doctors_collection")
    def test_add_doctor_availability(self, mock_doctors_collection):
        mock_doctors_collection.insert_one = MagicMock()

        response = self.client.post(
            "/doctor/availability",
            json={
                "doctor_name": "Dr. Smith",
                "available_slots": ["2024-12-25 15:30:00", "2024-12-26 10:00:00"]
            }
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("Availability for Dr. Smith added successfully.", response.get_json()["message"])
        mock_doctors_collection.insert_one.assert_called_once()

    @patch("app.doctors_collection")
    @patch("app.appointments_collection")
    def test_book_appointment(self, mock_appointments_collection, mock_doctors_collection):
        mock_doctors_collection.find_one.return_value = {
            "doctor_name": "Dr. Smith",
            "available_slots": [datetime(2024, 12, 25, 15, 30)]
        }
        mock_doctors_collection.update_one = MagicMock()
        mock_appointments_collection.insert_one = MagicMock()

        response = self.client.post(
            "/appointment/book",
            json={
                "patient_name": "John Doe",
                "doctor_name": "Dr. Smith",
                "appointment_time": "2024-12-25 15:30:00"
            }
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn("Appointment booked successfully", response.get_json()["message"])
        mock_appointments_collection.insert_one.assert_called_once()
        mock_doctors_collection.update_one.assert_called_once()

    @patch("app.doctors_collection")
    def test_get_doctor_availability(self, mock_doctors_collection):
        mock_doctors_collection.find.return_value = [
            {"doctor_name": "Dr. Smith", "available_slots": [datetime(2024, 12, 25, 15, 30)]},
            {"doctor_name": "Dr. Smith", "available_slots": [datetime(2024, 12, 26, 10, 0)]}
        ]

        response = self.client.get("/doctor/availability/Dr. Smith")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["available_slots"]), 2)
        self.assertIn("2024-12-25 15:30:00", response.get_json()["available_slots"])

if __name__ == "__main__":
    unittest.main()
