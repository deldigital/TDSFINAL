import random
from flask import Flask, request, render_template, jsonify, url_for
import pandas as pd
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Sample database with email addresses and names
users_db = {
    "gouravsaha@deloitte.com": "Gourav Saha",
    "sushiagarwal@deloitte.com": "Sushil Agarwal",
    "roupaul@deloitte.com": "Mr. Rounik Paul",
    "pochoudhury@deloitte.com": "Pooja Chodhury",
    "esmehta.ext@deloitte.com": "Esha Mehta",
    "shilagrawal@deloitte.com": "Shilpee Agrawal",
    "soburman@deloitte.com": "Somnath Burman",
    "stores_smel@shyamgroup.com": "Sumit Bag",
    "binit@shyammetalics.com": "Binit Jha",
    "smelpi@shyamgroup.com": "Dipak Yadav",
    "ssplpi@shyammetalics.com": "Bijay Singh",
    "sushant.jana@shyammetalics.com": "Sushant Jana",
    "wbmiro@shyamgroup.com": "Puja Shaw",
    "ambar.mukherjee@shyamgroup.com": "Ambar Mukherjee",
    "ravi.chaubey@shyammetalics.com": "Ravi Prakash Choubey",
    "accounts.trinity@shyammetalics.com": "Sayan Sen",
    "orisamiro@shyamgroup.com": "Deep Purokayastha",
    "storemiro@shyammetalics.com": "Rajeshwar Prasad Gupta",
    "amit.prasad@shyammetalics.com": "Amit Prasad",
    "sspl.plantfund@shyamgroup.com": "Raja Singh",
    "plantfundsmel@shyamgroup.com": "Soumen Pual",
    "shaw.abhijit@shyammetalics.com": "Abhijit Shaw",
    "sayantani.dutta@shyamgroup.com": "Sayantani Dutta",
    "hoaccounts.ril@shyammetalics.com": "Sarbani Baidya",
    "lc@shyammetalics.com": "Neha Srivastav",
    "atanughosh@shyammetalics.com": "Atanu Ghosh",
}

# Questions and options
questions = {
    1: {
        "question": "Shyam Metalics and Energy Ltd paid Mr. Raj, a commission agent, a commission of ₹10,00,000 for the sales generated through him during the month November’2024. Mr. Raj acts as an intermediary between Shyam Metalics and Energy Ltd and the final consumers, selling electronic goods on behalf of the company?",
        "options": ["A. Section 194H, 5%, INR 50,000", "B. Section 194H, 2%, INR 20,000", "C. Section 194J 10% INR 10,000", "D. Section 194C 1% 10,000"]
    },
    2: {
        "question": "Office Rent: Shyam Metalics Energy. Ltd. is renting office space in a commercial building in New Delhi from Mr. Suresh, who is an individual, for a monthly rent of ₹1,00,000. The total rent paid for the financial year 2023-24 amounts to ₹12,00,000. What is the amount of TDS to be deducted on 1st payment and 3rd payment?",
        "options": ["A. Section 194I, 10%, INR 10,000 and 10%, INR 10,000", "B. Section 194I, 10%, INR 12,000 and 10%, INR 10,000", "C. Section 194I(a), 10% INR 12,000 and 10%, INR 12,000", "D. Section 194I(b), 10% INR 12,000 10%, INR 12,000"]
    },
    3: {
        "question": "How many digits are there in TAN No?",
        "options": ["A. 8", "B. 9", "C. 6", "D. 10"]
    },
    4: {
        "question": "Which forms are applicable for quarterly TDS returns for payments other than salaries?",
        "options": ["A. 27EQ", "B. 26Q", "C. 27Q", "D. 24Q"]
    },
    5: {
        "question": "What is the due date for TDS return for the quarter ending 1st January to 31st March 2025?",
        "options": ["A. 7th of April 2025", "B. 30th of April 2025", "C. 31st May 2025", "D. 7th of May 2025"]
    },
}

# Correct answers
correct_answers = {
    1: "B",
    2: "A",
    3: "D",
    4: "B",
    5: "C",
}

# Load credentials for Google Sheets
credentials_json = os.getenv('GOOGLE_SHEET_CREDENTIALS')
credentials_dict = json.loads(credentials_json)
credentials = service_account.Credentials.from_service_account_info(credentials_dict)

# Build the Google Sheets API service
service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()

def append_to_google_sheet(spreadsheet_id, range_name, values):
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
    sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()

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
    numbered_questions = {i+1: selected_questions[q_id] for i, q_id in enumerate(selected_questions)}
    return jsonify(numbered_questions)

@app.route('/submit_email', methods=['POST'])
def submit_email():
    data = request.get_json()
    email = data['email']
    if email in users_db:
        name = users_db[email]
        return jsonify({"message": f"Hello {name}", "name": name})
    else:
        return jsonify({"message": "Email not found"}), 404

@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    data = request.get_json()
    answers = data['answers']
    email = data['email']
    full_name = data['full_name']

    score = calculate_score(answers)

    user_data = {
        'full_name': full_name,
        'email': email,
        'score': score['score'],
        'correct_count': score['correct_count'],
        'wrong_count': score['wrong_count'],
    }

    spreadsheet_id = '1UkiWz4V-3FhdW6iVxDxGNiZu1rmQJGppUjhO1NJOGkE'
    range_name = 'Sheet1!A1:E1'
    values = [
        [user_data['full_name'], user_data['email'], user_data['score'], user_data['correct_count'], user_data['wrong_count']]
    ]
    append_to_google_sheet(spreadsheet_id, range_name, values)

    return jsonify(user_data)
    def calculate_score(answers):
    score = {'score': 0, 'correct_count': 0, 'wrong_count': 0}
    for q_id, answer in answers.items():
        q_id = int(q_id)
        if answer.strip() == correct_answers[q_id]:
            score['score'] += 2
            score['correct_count'] += 1
        else:
            score['wrong_count'] += 1
    return score

if __name__ != '__main__':
    app = app
