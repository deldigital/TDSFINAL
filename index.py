import random
from flask import Flask, request, render_template, jsonify
import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Sample database with email addresses and names
users_db = {
    "gouravsaha@deloitte.com": "Gourav Saha",
    "sushiagarwal@deloitte.com": "Sushil Agarwal",
    "roupaul@deloitte.com": "Mr.Rounik Paul",
    "pochoudhury@deloitte.com": "Pooja Chodhury",
    "esmehta.ext@deloitte.com": "Esha Mehta",
    # ... Additional emails
}

# Questions and options
questions = {
    1: {"question": "Question 1?", "options": ["Option A", "Option B", "Option C", "Option D"]},
    2: {"question": "Question 2?", "options": ["Option A", "Option B", "Option C", "Option D"]},
    3: {"question": "Question 3?", "options": ["Option A", "Option B", "Option C", "Option D"]},
    # Add more questions...
}

# Correct answers
correct_answers = {
    1: "B. Option B",
    2: "A. Option A",
    3: "D. Option D",
    # Add more answers...
}

# Load credentials from environment variable
try:
    credentials_json = os.getenv('GOOGLE_SHEET_CREDENTIALS')
    credentials_dict = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
except Exception as e:
    logging.error(f"Failed to load Google Sheets credentials: {e}")
    sheet = None

# Google Sheets Helper Function
def append_to_google_sheet(spreadsheet_id, range_name, values):
    try:
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range='Sheet1!A1:E1').execute()
        if 'values' not in result:
            headers = [['FULL NAME', 'EMAIL', 'TOTAL SCORE', 'CORRECT ANSWER', 'INCORRECT ANSWER']]
            body = {'values': headers}
            sheet.values().append(
                spreadsheetId=spreadsheet_id,
                range='Sheet1!A1:E1',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

        body = {'values': values}
        result = sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        logging.info(f"{result.get('updates').get('updatedCells')} cells appended.")
    except Exception as e:
        logging.error(f"Error appending to Google Sheets: {e}")

# Routes
@app.route('/')
def first_page():
    return render_template('first_page.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/questions_page')
def questions_page():
    return render_template('questions.html')

@app.route('/questions', methods=['GET'])
def get_questions():
    selected_questions = dict(random.sample(list(questions.items()), k=3))
    numbered_questions = {i + 1: selected_questions[q_id] for i, q_id in enumerate(selected_questions)}
    return jsonify(numbered_questions)

@app.route('/submit_email', methods=['POST'])
def submit_email():
    try:
        data = request.get_json()
        email = data['email']
        if email in users_db:
            name = users_db[email]
            return jsonify({"message": f"Hello {name}", "name": name})
        else:
            return jsonify({"message": "Email not found"}), 404
    except Exception as e:
        logging.error(f"Error in submit_email: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    try:
        data = request.get_json()
        logging.info(f"Received data: {data}")
        answers = data.get('answers', {})
        email = data.get('email', '')
        full_name = data.get('full_name', '')

        if not answers or not email or not full_name:
            return jsonify({"message": "Invalid input data"}), 400

        score = calculate_score(answers)

        user_data = {
            'full_name': full_name,
            'email': email,
            'score': score['score'],
            'correct_count': score['correct_count'],
            'wrong_count': score['wrong_count'],
        }

        spreadsheet_id = os.getenv('SPREADSHEET_ID')
        range_name = 'Sheet1!A1:E1'
        values = [[user_data['full_name'], user_data['email'], user_data['score'], user_data['correct_count'], user_data['wrong_count']]]
        append_to_google_sheet(spreadsheet_id, range_name, values)

        return jsonify(user_data)
    except Exception as e:
        logging.error(f"Error in submit_exam: {e}")
        return jsonify({"message": "Internal Server Error"}), 500

def calculate_score(answers):
    score = {'score': 0, 'correct_count': 0, 'wrong_count': 0}
    try:
        for q_id, answer in answers.items():
            q_id = int(q_id)
            correct_answer = correct_answers.get(q_id)
            logging.info(f"Question ID: {q_id}, User Answer: {answer}, Correct Answer: {correct_answer}")
            if correct_answer and correct_answer.strip().upper() == answer.strip().upper():
                score['score'] += 2
                score['correct_count'] += 1
            else:
                score['wrong_count'] += 1
    except Exception as e:
        logging.error(f"Error in calculate_score: {e}")
    return score

# Ensure compatibility with Vercel
if __name__ != '__main__':
    app = app
