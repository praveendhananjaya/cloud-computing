from flask import Flask, jsonify, request
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

app = Flask(__name__)

# SendGrid API Key (set this environment variable)
SENDGRID_API_KEY = os.getenv('aa','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')

# Initialize SendGrid client
sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

# NotificationService to handle sending email
class NotificationService:
    @staticmethod
    def send_email(to_email, subject, body):
        from_email = Email("noreply@yourdomain.com")  # Replace with your email address
        to_email = To(to_email)
        content = Content("text/plain", body)
        mail = Mail(from_email, to_email, subject, content)

        try:
            response = sg.send(mail)
            # Return response details
            return {
                'status_code': response.status_code,
                'body': response.body.decode('utf-8'),
                'headers': response.headers
            }
        except Exception as e:
            return {'error': str(e)}

# Route to send emails with POST method
@app.route('/send-email', methods=['POST'])
def send_email():
    try:
        # Get data from the POST request
        data = request.get_json()

        # Extract necessary details
        to_email = data.get('to_email')
        subject = data.get('subject')
        body = data.get('body')

        if not to_email or not subject or not body:
            return jsonify({"error": "Missing required fields: to_email, subject, body"}), 400

        # Send email using NotificationService
        response = NotificationService.send_email(to_email, subject, body)

        if 'error' in response:
            return jsonify({"error": response['error']}), 500

        # Return success message
        if response['status_code'] == 202:
            return jsonify({"message": "Email sent successfully!"}), 200
        else:
            return jsonify({"error": f"Failed to send email: {response['body']}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002)
