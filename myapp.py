from flask import Flask, render_template, request, session, jsonify
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# Configure Google Generative AI
import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Set a secret key for session management

# Function to get Gemini AI response
def get_gemini_response(input_text):
    model = genai.GenerativeModel("gemini-1.5-flash",
                                  generation_config={"response_mime_type": "application/json"}
                                  )
    response = model.generate_content(input_text)
    return response.text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    email = request.form.get('email')
    quiz_for = request.form.get('quiz_for')
    subject = request.form.get('subject')
    schooling_level = request.form.get('schooling_level')
    num_questions = request.form.get('numQuestions')
    level = request.form.get("level")
    language = request.form.get("language")
    

    prompt = f"""
    Using the following JSON schema,
    Please list {num_questions} quiz questions in {language} on {subject} for {schooling_level} and difficulty level of the quiz should be {level}.
    Recipe = {{
        "question": "str",
        "options": "list",
        "answer": "str"
    }} 
    Return: list[Recipe]

    example:
    [
        {{
            "question": "What is the largest ocean in the world?",
            "options": ["Atlantic Ocean", "Indian Ocean", "Pacific Ocean", "Arctic Ocean"],
            "answer": "Pacific Ocean"
        }},
        {{
            "question": "Who is the author of the Harry Potter series?",
            "options": ["J.K. Rowling", "Roald Dahl", "Dr. Seuss", "Rick Riordan"],
            "answer": "J.K. Rowling"
        }},
        {{
            "question": "Which programing langauge is better for Data Science?",
            "options": ["Java", "R", "SQL", "Python"],
            "answer": "Python"
        }},
                {{
            "question": "Who is the value of Pi?",
            "options": ["22/7", "4.6", "No One", "1 and 2 both"],
            "answer": "J.K. Rowling"
        }}
    ]
    """
    #print(f"Received form data: email={email}, quiz_for={quiz_for}, subject={subject}, schooling_level={schooling_level}, num_questions={num_questions}, level={level}")

    # Return the constructed prompt
    print(prompt)
    raw_response = get_gemini_response(prompt)
    print(raw_response)

    try:
        data = json.loads(raw_response)
        session['questions'] = data
        return render_template('quiz.html', questions=data)
        
    except json.JSONDecodeError:
        return "Error decoding JSON from response", 400
    
        
@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    try:
        # Retrieve the questions from the session
        questions = session.get('questions')
        if not questions:
            return "Questions not found in session", 400

        user_answers = {}
        # Loop through each question and extract the selected option from the form
        for idx, question in enumerate(questions, start=1):
            # The name attribute of each radio button group is 'group_<index>'
            group_name = f'group_{idx}'
            selected_option = request.form.get(group_name)
            user_answers[idx] = selected_option

        score = 0
        results = []

        # Calculate the score and prepare the results
        for idx, question in enumerate(questions, start=1):
            correct_answer = question['answer']
            user_answer = user_answers.get(idx)
            is_correct = user_answer == correct_answer
            if is_correct:
                score += 1
            results.append({
                'question': question['question'],
                'correct_answer': correct_answer,
                'user_answer': user_answer,
                'is_correct': is_correct
            })

        # Render the results template with the score and results
        return render_template('quiz.html', results=results, score=score, total=len(questions))
    except Exception as e:
        return str(e), 400
if __name__ == '__main__':
    app.run(debug=True)
