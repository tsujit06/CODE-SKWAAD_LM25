from flask import Flask, request, jsonify, render_template
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from string import punctuation
import json
import pyttsx3
import speech_recognition as sr

app = Flask(__name__)

# File to store pairs
PAIRS_FILE = 'pairs.json'

# Password
ADMIN_PASSWORD = 'admin123'

# Initialize question and answer pairs
default_pairs = [
    ["What is your return policy?", ["Our return policy allows returns within 30 days of purchase with a receipt. Please visit our returns page for more details."]],
    ["What is your return product?", ["Which product?"]],
    ["Do you offer free shipping?", ["Yes, we offer free shipping on orders over $50 within the continental US."]],
    ["How can I track my order?", ["You can track your order by visiting the 'Track Order' page on our website and entering your order number."]],
    ["What payment methods do you accept?", ["We accept Visa, MasterCard, American Express, and PayPal."]],
    ["Can I cancel my order?", ["Orders can be canceled within 24 hours of placing them. Please contact our customer support for assistance."]],
    ["What are your business hours?", ["Our business hours are Monday to Friday, 9 AM to 5 PM. We are closed on weekends and holidays."]],
    ["How do I contact customer support?", ["You can reach our customer support team at support@example.com or by calling +123456789."]],
    ["Are your products eco-friendly?", ["Yes, we strive to offer eco-friendly products and use sustainable packaging materials."]],
    ["Do you offer bulk discounts?", ["Yes, we offer discounts on bulk orders. Please contact our sales team for more information."]],
    ["What is the warranty on your products?", ["Our products come with a 1-year warranty against manufacturing defects. Please see our warranty page for details."]],
    ["How long will it take for my order to arrive?", ["Delivery times vary depending on your location. Typically, orders arrive within 5-7 business days. You will receive a shipping confirmation with tracking details once your order ships."]],
    ["Can I customize my order?", ["Yes, we offer customization options on select products. Please contact our sales team to discuss your specific requirements."]],
    ["Are your products tested for safety?", ["Yes, all our products undergo rigorous safety testing to meet industry standards and ensure customer satisfaction."]],
    ["What is your privacy policy?", ["Our privacy policy outlines how we collect, use, and protect your personal information. You can view our full privacy policy on our website."]],
    ["Do you offer international shipping?", ["Yes, we offer international shipping to select countries. Shipping rates and delivery times may vary based on your location."]],
    ["How do I apply for a job at your company?", ["You can view and apply for current job openings on our careers page. We look forward to reviewing your application."]],
]

# Function to load pairs from file
@app.route('/')
def home():
    return render_template('index.html')

def load_pairs():
    try:
        with open(PAIRS_FILE, 'r') as file:
            pairs = json.load(file)
    except FileNotFoundError:
        pairs = default_pairs
        save_pairs(pairs)
    return pairs

# Function to save pairs to file
def save_pairs(pairs):
    with open(PAIRS_FILE, 'w') as file:
        json.dump(pairs, file, indent=4)

# Load pairs from file
pairs = load_pairs()

# Preprocess text
lemmatiser = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocessing(sent):
    rem_words = ['get', 'avail', 'where', 'what', 'why', 'when', 'i', 'can']
    sent = sent.translate(str.maketrans('', '', punctuation)).lower()
    words = sent.split()
    words = [word for word in words if word not in stop_words and word not in rem_words]
    words = [lemmatiser.lemmatize(word, pos="v") for word in words]
    return list(set(words))

# Text-to-speech engine
tts_engine = pyttsx3.init()
voices = tts_engine.getProperty('voices')
tts_engine.setProperty('voice', voices[1].id)

# Text to Speech
def speak(text):
    tts_engine.say(text)
    print(text)
    tts_engine.runAndWait()

# Speech recognizer
recognizer = sr.Recognizer()

def recognize_speech():
    with sr.Microphone() as source:
        print("Listening for 7 seconds...")
        audio = recognizer.listen(source, timeout=7)

    try:
        print("Recognizing...")
        response = recognizer.recognize_google(audio)
        print(f"You said: {response}")
    except sr.UnknownValueError:
        response = None
        speak("Sorry, I did not understand that.")
    except sr.RequestError:
        response = None
        speak("Sorry, my speech service is down.")
    except sr.WaitTimeoutError:
        response = None
        speak("Listening timed out.")
    
    return response

# Function to add new pairs
def add_new_pair(question, answer, admin_password):
    global pairs
    if admin_password == ADMIN_PASSWORD:
        pairs.append([question, [answer]])
        save_pairs(pairs)
        speak("New pair added successfully!")
        return True
    else:
        speak("Incorrect password. You are not authorized to add new pairs.")
        return False

# Function to get response for a given question
def get_response(question):
    global pairs
    list_response = preprocessing(question)
    chosen_index = -1
    max_matches = 0

    for i in range(len(pairs)):
        pair_question = pairs[i][0]
        list_pair = preprocessing(pair_question)

        # Count matches between user's question and pair's question + answer
        match_count = len(set(list_response) & set(list_pair))

        if match_count > max_matches:
            max_matches = match_count
            chosen_index = i
    
    if chosen_index != -1:
        return pairs[chosen_index][1][0]
    else:
        return "Unable to answer this question. Sorry for the inconvenience."

# Flask route to handle incoming messages
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    message = data['message']

    response = get_response(message)
    return jsonify({'message': response})

# Flask route for adding new pairs
@app.route('/add_pair', methods=['POST'])
def add_pair():
    data = request.get_json()
    question = data.get('question')
    answer = data.get('answer')
    admin_password = data.get('password')
    
    if add_new_pair(question, answer, admin_password):
        return jsonify({'status': 'success', 'message': 'New pair added successfully!'})
    else:
        return jsonify({'status': 'error', 'message': 'Incorrect password. Unauthorized access.'})

# Main method to run the Flask application
if __name__ == '__main__':
    app.run(port=5000, debug=True)