from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from bson import ObjectId
from datetime import datetime  # Import datetime module

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS

# MongoDB setup
mongo_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongo_uri)
db_name = os.getenv("MONGODB_DB_NAME")
db = client[db_name]
inquiries_collection = db.inquiries

# Email setup
email_user = os.getenv("EMAIL_USER")
email_password = os.getenv("EMAIL_PASSWORD")
email_smtp_server = "smtp.office365.com"
email_smtp_port = 587
email_recipient = "Inquery.developement@outlook.com"

def send_email(data):
    msg = MIMEMultipart()
    msg['From'] = email_user
    msg['To'] = email_recipient
    msg['Subject'] = "New Inquiry"

    body = f"""
    New Inquiry Received:
    Name: {data['name']}
    Email: {data['email']}
    Phone: {data['phone']}
    Organization Name: {data['organization']}
    Organization Type: {data['option']}
    Message:
    {data['message']}
    """

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(email_smtp_server, email_smtp_port)
    server.starttls()
    server.login(email_user, email_password)
    text = msg.as_string()
    server.sendmail(email_user, email_recipient, text)
    server.quit()

@app.route('/submit', methods=['POST'])
def submit_form():
    data = request.get_json()
    
    # Set default flag to 'new'
    data['flag'] = 'new'
    
    # Add current date as date_registered
    data['date_registered'] = datetime.now()
    
    inquiries_collection.insert_one(data)
    send_email(data)
    return jsonify({"message": "Inquiry submitted successfully"}), 201

@app.route('/inq', methods=['GET'])
def get_inquiries():
    inquiries = list(inquiries_collection.find())
    for inquiry in inquiries:
        inquiry['_id'] = str(inquiry['_id'])
    return jsonify(inquiries), 200

@app.route('/inq/<id>', methods=['DELETE'])
def delete_inquiry(id):
    result = inquiries_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return jsonify({"message": "Inquiry deleted successfully"}), 200
    else:
        return jsonify({"message": "Inquiry not found"}), 404

@app.route('/inq/<string:inquiry_id>', methods=['PUT'])
def update_inquiry_flag(inquiry_id):
    data = request.get_json()
    flag = data.get('flag')
    inquiries_collection.update_one(
        {'_id': ObjectId(inquiry_id)},
        {'$set': {'flag': flag}}
    )
    return jsonify({"message": "Flag updated successfully"}), 200

if __name__ == "__main__":
    app.run(debug=False,host="0.0.0.0")
