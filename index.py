from flask import Flask, request, render_template, jsonify, url_for
import pandas as pd
import os
import json
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Sample database with email addresses and names
users_db = {
    "gouravsaha@deloitte.com": "Gourav Saha",
    "sushiagarwal@deloitte.com": "Sushil Agarwal",
    "roupaul@deloitte.com": "Mr.Rounik Paul",
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
        "question": "Office Rent : Shyam Metalics Energy. Ltd. is renting office space in a commercial building in New Delhi from Mr. Suresh, who is an individual, for a monthly rent of ₹1,00,000. The total rent paid for the financial year 2023-24 amounts to ₹12,00,000. What is the amount of TDS to be deducted on 1st payment and 3rd payment?",
        "options": ["A. Section 194I, 10%, INR 10,000 and 10%, INR 10,000", "B. Section 194I, 10%, INR 12000 and 10%, INR 10,000", "C. Section 194I(a), 10% INR 12000 and 10%, INR 12,000", "D. Section 194I(b) ,10% INR 12000 10%, INR 12,000"]
    },
    3: {
        "question": "How many digits are there in TAN No?",
        "options": ["A. 8", "B. 9", "C. 6", "D. 10"]
    },
    4: {
        "question": "Which forms are applicable in for quarterly and case of TDS return for payment other than salaries?",
        "options": ["A. 27EQ", "B. 26Q", "C. 27Q", "D. 24Q"]
    },
    5: {
        "question": "Which is the due date for TDS return for quarter ending 1st January to 31st March 2025?",
        "options": ["A. 7th of April 2025", "B. 30th of April 2025", "C. 31st May 2025", "D. 7th of May 2025"]
    },
    6: {
        "question": "Shyam Metalics & Energy Ltd. is engaged in a transaction involving the purchase of both goods and immovable property. The total value of the transaction includes the purchase of goods as well as immovable property. Goods worth INR 80 lacs (assume no transactions took place in the FY 2024-25). Lands Worth INR 1.3 Cr (assume no transactions took place in the FY 2024-25). What is amount of TDS to be deducted?",
        "options": ["A. 3000 for goods 1.3 lakhs for Land", "B. 3000 for goods 13 lacs for land", "C. NIL", "D. 8000 for goods and NIL for land as exempt under TDS"]
    },
    7: {
        "question": "Shyam Metalics pays interest on a loan of Rs. 10,00,000 to Mr. X, an individual resident, at an annual rate of 10%. TDS to be deducted-",
        "options": ["A. 194A 1,00,000", "B. 193 10,000", "C. 194L 1,000", "D. 194A 10,000"]
    },
    8: {
        "question": "Shyam Metalics & Energy Ltd. makes a payment of Rs. 29,000 to a contractor for the construction of a factory building during the financial year. The contractor is an individual and is registered under GST. The work contract does not involve any transfer of goods. What is the TDS liability under Section 194C of the Income Tax Act?",
        "options": ["A. TDS is required to be deducted at 1% for individual contractors.", "B. NIL", "C. TDS is not required to be deducted as the payment is below Rs. 30,00,000.", "D. TDS is not applicable, as the contractor is registered under GST."]
    },
    9: {
        "question": "Shyam Metalics & Energy Ltd, a manufacturing company, issues ₹10,00,000 worth of debentures to its investors. The interest on these debentures is payable at an annual rate of 8%. The company has to pay ₹80,000 as interest to its debenture holders during the financial year.",
        "options": ["A. TDS 193 is required to be deducted at 1% i.e INR 800", "B. NIL", "C. TDS 193 is required to be deducted at 10% i.e INR 8000", "D. TDS 193 is required to be deducted at 5% i.e INR 4000."]
    },
    10: {
        "question": "Shyam Metalics & Energy Ltd company in India that regularly pays interest to its debenture holders. Mr. B, an individual investor, holds ₹3,000 worth of debentures, and the company has to pay him ₹150 as interest during the financial year.",
        "options": ["A. TDS 193 is required to be deducted at 1% i.e INR 800", "B. NIL", "C. TDS 193 is required to be deducted at 10% i.e INR 300", "D. TDS 194A is required to be deducted at 10% i.e INR 300"]
    },
    11: {
        "question": "Shyam Metalics Ltd., a steel manufacturing company, enters into an agreement with XYZ Construction Pvt. Ltd., a contractor, for the installation of machinery in its new plant. The total contract value for the installation work is ₹2,40,000. The payment will be made in three installments: ₹80,000 each. Assume first installment being paid. What is the TDS rate and Section will be applicable?",
        "options": ["A. TDS 194C is required to be deducted at 1% i.e INR 800", "B. NIL as does not exceed 2,40,000 in a FY.", "C. TDS 194J is required to be deducted at 10% i.e INR 8000", "D. TDS 194C is required to be deducted at 2% i.e INR 1600"]
    },
    12: {
        "question": "Shyam Metalics Ltd., a steel manufacturing company, enters into an agreement with XYZ Construction Pvt. Ltd., a contractor, for the installation of machinery in its new plant. The total contract value for the installation work is ₹2,40,000. The payment will be made in three installments: ₹80,000 each. Assume first installment being paid. And the assessee does not furnished PAN.",
        "options": ["A. TDS 194C is required to be deducted at 2% i.e INR 1600", "B. NIL as does not exceed 2,40,000 in a FY.", "C. TDS 194J is required to be deducted at 10% i.e INR 8000", "D. TDS 194C is required to be deducted at 5% i.e INR 1600"]
    },
    13: {
        "question": "Shyam Metalics Ltd took sub lease a building from Ms. Rupa with effect from 1.7.2024 on a rent of Rs 20,000 per month. It also took on rent of plant & machinery machinery from Ms. Rupa with effect from 1.10.2024 on hire charges of 15,000 per month. Shyam metalics entered into two separate agreements with Ms Rupa for sub lease of building and hiring of machinery. Which of the following statement is correct? (assume calculation based on p.a) (Assuming one month’s rent was received as security deposit, which is refundable at the end of the lease period)",
        "options": ["A. No tax needs to be deducted at source since rent for building does not exceed Rs 2,40,000 p.a and rent for machinery also does not exceed Rs 2,40,000 p.a. Security deposit refundable at the end of the lease term is not rent for the purpose of TDS", "B. Tax has to be deducted @10% on Rs. 2,00,000 and @2% on Rs 1,05,000 (i.e rent including security deposit)", "C. NIL for building rent and @2% of INR 1800", "D. Tax has to deducted@10% on Rs 2,00,000 (i.e rent including security deposit). However no tax has to be deducted on Rent of Rs. 1,05,000 (i.e Rent including security deposit) for machinery, since the same does not exceed Rs. 1,80,000."]
    },
    14: {
        "question": "Shyam Metalics, a company, is making a payment of ₹1,00,000 to Indian Railways for transportation of goods provided during the financial year. According to Section 194C of the Income Tax Act, what is the correct TDS treatment for this payment?",
        "options": ["A. No TDS is applicable.", "B. TDS is required, and the rate of TDS will be 1% INR 1000", "C. TDS is required, and the rate of TDS will be 2% INR 2000", "D. TDS is required, and the rate of TDS will be 10% INR 10,000"]
        
    },
    15: {
        "question": "Shyam Metalics, a company, makes a payment of ₹60,000 to a transporter Fast transport Pvt Ltd, who owns 12 vehicles for the transportation of goods during the financial year. what is the correct TDS treatment for this payment?",
        "options": ["A. TDS to be deducted @10% INR 6,000 as per 194J.", "B. TDS to be deducted @1% INR 600 as per 194C.", "C. TDS to be deducted @2% INR 1,200 as per 194C", "D. No TDS is applicable since the transporter doesn’t own more than 15 vehicle."]
        
    },
    16: {
        "question": "During the winter season Shyam Metalics, has organized a sports event where it has made a payment of ₹110,000 to an event manager an individual for organizing a sports activity. what is the correct TDS treatment for this payment?",
        "options": ["A. No TDS is applicable.", "B. TDS is required as per 194C, and the rate of TDS will be 1% INR 1100", "C. TDS is required as per 194J, and the rate of TDS will be 10% INR 11,000", "D. TDS is required as per 194C, and the rate of TDS will be 2% INR 2200"]
        
    },
    17: {
        "question": "Shyam Metalics, a manufacturing company, has made a payment of ₹5,00,000 on 31st Oct’24 to a distributor for selling its products in the market during the financial year. The distributor is an individual and has provided a service agreement with a fixed commission structure. which of the following is the correct TDS treatment for this payment?",
        "options": ["A. 194C @1% INR 5,000", "B. 194I @10% INR 50,000", "C. TDS is applicable 194H at the rate of 10% as the payment is for commission on sales INR 50,000", "D. TDS is applicable 194H at the rate of 2% as the payment is for commission on sales INR 10,000"]
        
    },
    18: {
        "question": "Shyam Metalics, a company, has paid ₹12,00,000 on 31st December’24 as commission to an agent for promoting its products. The agent is an individual. The payment is made in installments, and the total commission paid in the financial year exceeds ₹15,000. The agent has not provided a PAN. According to Section 194H of the Income Tax Act, what is the correct TDS treatment for this payment?",
        "options": ["A. TDS is applicable at the rate of 10% as PAN is irrelevant under this case.", "B. TDS is applicable at the rate of 5% due to non-furnishing of PAN", "C. TDS is applicable at the rate of 20% due to non-furnishing of PAN", "D. TDS is not applicable if the payment is made in installments."]
        
    },
    19: {
        "question": "Shyam Metalics, a company, has paid ₹2,50,000 as rent for office premises to a landlord who is an individual during the financial year 24-25. The landlord is a resident individual and has provided a valid PAN. what is the correct TDS treatment for this payment?",
        "options": ["A. TDS is applicable at the rate of 1% as PAN is irrelevant under this case.", "B. TDS is applicable at the rate of 2% since payment is made to individual.", "C. TDS is applicable at the rate of 10% since payment made to individual.", "D. TDS is not applicable since exceeds 2,40,000."]
        
    },
    20: {
        "question": "Shyam Metalics, a manufacturing company, has paid ₹8,50,000 as rent for the use of machinery during the financial year. The payment is made to a private limited company, which is the owner of the machinery. The total rent paid for plant and machinery during the year exceeds ₹2,40,000. The machinery is used for the company's production process. The company has provided a valid PAN. According to Section 194I of the Income Tax Act, what is the correct TDS treatment for this payment?",
        "options": ["A. TDS is applicable at the rate of 10% for rent on plant and machinery", "B. TDS is applicable at the rate of 2% for rent on plant and machinery", "C. TDS is applicable at the rate of 10% for rent on machinery paid to a company", "D. TDS is not applicable as the rent is paid to a private limited company"]
        
    },
    21: {
        "question": "Shyam Metalics, a manufacturing company, has entered into a lease agreement for land with a landlord, where the company is required to pay a lease premium of ₹15,00,000 during the financial year. The lease agreement specifies that this payment is a one-time lease premium for the lease of land and not periodic rent. The landlord is a resident individual and has provided a valid PAN. According to Section 194I of the Income Tax Act, what is the correct TDS treatment for this lease premium payment?",
        "options": ["A. TDS is applicable at the rate of 10% as the lease premium is treated as rent", "B. TDS is applicable at the rate of 20% due to the non-periodic nature of the lease premium", "C. TDS is applicable at the rate of 2% for lease premium paid for land", "D. No TDS is applicable, as the payment is considered a capital expenditure"]
        
    },
    22: {
        "question": "Shyam Metalics a manufacturing company, has entered into rent agreement which is owned by three co-owners(Mr. Narayan, John & Hariprasad) at the ratio of 5:3:2. The total rent paid is 10,75,000 on 31st Oct’24. what is the correct TDS treatment in case of payment made to three people?",
        "options": ["A. 194C @1% Mr Naryan INR 5,375, Mr. John INR 3,225, Mr Hariprasad INR 2150", "B. 194I @10% Mr Naryan INR 53,750, Mr. John INR 32,250, Mr Hariprasad NIL", "C. 194IA @10% Mr Naryan INR 53,750, Mr. John INR 32,250, Mr Hariprasad 21,500", "D. 194I @10% Mr Naryan INR 53,750, Mr. John INR 32,250, Mr Hariprasad 21,500"]
        
    },
    23: {
        "question": "Shyam Metalics Ltd., a company based in Kolkata, is purchasing a commercial property from Mr. Ramesh, a resident individual. The sale consideration for the property is ₹1,00,00,000(SDV 1,20,00,000). The transaction is scheduled for February 10, 2025. As per the agreement, Shyam Metalics is required to deduct TDS under Section 194IA. The company has verified that the sale consideration exceeds ₹50 lakh, and Mr. Ramesh has provided his PAN details. Shyam Metalics plans to make the payment via cheque and deduct the TDS from the payment amount before transferring the balance to Mr. Ramesh. what is the correct TDS treatment?",
        "options": ["A. 194IB @1% 1,20,000", "B. 194I @10% 10,00,000", "C. 194IA @1% 1,20,000", "D. 194IB @10% 12,00,000"]
        
    },
    24: {
        "question": "Shyam Metalics Ltd., a manufacturing company, purchases raw materials (steel and metals) worth ₹80,00,000 from Steel Traders Pvt. Ltd. during the November’24 (First transaction). The transaction is part of an ongoing business relationship. As per the terms of the agreement, the payment is made after 45 days from the date of invoice. After receiving the goods, Shyam Metalics Ltd. returns a portion of the purchased goods worth ₹10,00,000 to Steel Traders Pvt. Ltd. due to quality issues. What will be the TDS treatment?",
        "options": ["A. 194C @2% INR 1,40,000", "B. 194Q @1% INR 70,000", "C. 194Q @0.1% INR 8,000", "D. 194Q @0.1% INR 2,000"]
        
    },
    25: {
        "question": "Combo Ltd., a newly established business in the month Dec’24 with small operation, has started selling raw materials (steel) to Shyam Metalics, a manufacturing company. Steel Traders Pvt. Ltd. made its first sale to ABC Enterprises worth ₹70,00,000. The purchase was made on October 15, 2025, and the payment terms are 45 days from the date of invoice. (assume buyers turnover does not exceed 10 Cr). What will be the TDS treatment?",
        "options": ["A. 194C @2% INR 1,40,000", "B. 194Q @1% INR 70,000", "C. 194Q @0.1% INR 2,000", "D. NIL"]
        
    },

   
}

# Correct answers
correct_answers = {
    1: "B. Section 194H, 2%, INR 20,000",
    2: "A. Section 194I, 10%, INR 10,000 and 10%, INR 10,000",
    3: "D.",
    4: "B.",
    5: "C.",
    6: "A.",
    7: "D.",
    8: "B.",
    9: "C.",
    10: "B.",
    11: "D.",
    12: "A.",
    13: "C.",
    14: "A.",
    15: "C.",
    16: "B.",
    17: "D.",
    18: "C.",
    19: "C.",
    20: "B.",
    21: "D.",
    22: "B.",
    23: "C.",
    24: "D.",
    25: "D.",
    
}

# Load credentials from environment variable
credentials_json = os.getenv('GOOGLE_SHEET_CREDENTIALS')
credentials_dict = json.loads(credentials_json)
credentials = service_account.Credentials.from_service_account_info(credentials_dict)

# Build the service
service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()

# Function to append data to Google Sheets
def append_to_google_sheet(spreadsheet_id, range_name, values):
    # Check if the sheet is empty and add headers if necessary
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
    print(f"{result.get('updates').get('updatedCells')} cells appended.")

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
    # Return all questions
    numbered_questions = {i+1: questions[q_id] for i, q_id in enumerate(questions)}
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

    # Append data to Google Sheets
    spreadsheet_id = '1UkiWz4V-3FhdW6iVxDxGNiZu1rmQJGppUjhO1NJOGkE'
    range_name = 'Sheet1!A1:E1'  # Specify the range to include 5 columns
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

# if __name__ == '__main__':
#     app.debug = True
#     app.run()

# Ensure compatibility with Vercel by exposing 'app'
if __name__ != '__main__':
    app = app  # For Vercel compatibility
