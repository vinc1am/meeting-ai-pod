import os
from flask import Flask, render_template, request, session, jsonify
from werkzeug.utils import secure_filename
import time
from script.azure_speech_service import *
from script.llm_transcription_analysis import *
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# System Value
app.secret_key = 'SECRET_KEY'

# Azure OpenAI configuration 
app.config['OPENAI_MODEL_ENGINE'] = os.getenv('OPENAI_MODEL_ENGINE')
app.config['OPENAI_API_TYPE'] = os.getenv('OPENAI_API_TYPE')
app.config['OPENAI_API_BASE'] = os.getenv('OPENAI_API_BASE')
app.config['OPENAI_API_VERSION'] = os.getenv('OPENAI_API_VERSION')
app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
openai_config = {
    'openai_model_engine': app.config['OPENAI_MODEL_ENGINE'],
    'openai_api_type': app.config['OPENAI_API_TYPE'],
    'openai_api_base': app.config['OPENAI_API_BASE'],
    'openai_api_version': app.config['OPENAI_API_VERSION'],
    'openai_api_key': app.config['OPENAI_API_KEY']
}

# Azure Speech Recognition
app.config['WHISPER_MODEL_REFERENCE'] = os.getenv('WHISPER_MODEL_REFERENCE')
app.config['SPEECH_SERVICE_SUBSCRIPTION_KEY'] = os.getenv('SPEECH_SERVICE_SUBSCRIPTION_KEY')
app.config['SPEECH_SERVICE_REGION'] = os.getenv('SPEECH_SERVICE_REGION')
SPEECH_SERVICE_SUBSCRIPTION_KEY = app.config['SPEECH_SERVICE_SUBSCRIPTION_KEY']
SPEECH_SERVICE_REGION = app.config['SPEECH_SERVICE_REGION']
WHISPER_MODEL_REFERENCE = app.config['WHISPER_MODEL_REFERENCE']



chat_messages = [{'speaker': 'Assistant', 'message': 'Good Morning! Please ask me any question regarding to the meeting minutes.'}]
transcription_list = None
meeting_summary = None
minutes_result = None
transcription_str = None


@app.route("/")
def home():
    return render_template('main.html')

@app.route('/load_audio_master_list', methods=['GET'])
def load_audio_master_list():

    file_path = 'audio/audio_list.json'

    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        audio_list = []
        for item in data:
            audio_list.append({
                'audio': item['audio'],
                'path': item['path'],
                'link': item['link']
            })
        return jsonify(audio_list), 200
    else:
        return '', 404





@app.route('/start_transcription', methods=['POST'])
def start_transcription():
    try:
        audio_link = request.json['audio_link']
        
        # Step 1: Transcribe
        transcription_list = transcribe(audio_link, WHISPER_MODEL_REFERENCE, SPEECH_SERVICE_SUBSCRIPTION_KEY, SPEECH_SERVICE_REGION, debug=False)
        
        # Step 2: Summarize
        transcription_str = json.dumps(transcription_list)
        meeting_summary = get_summary(transcription_str, openai_config)
        
        # Step 3: Get Meeting Minutes
        minutes_result = get_meeting_minutes(transcription_str, openai_config)
        
        # Prepare the response data
        response_data = {
            'transcription': transcription_list,
            'summary': meeting_summary,
            'minutes': minutes_result
        }

        # Clear the chat message list
        global chat_messages
        chat_messages.clear()
        chat_messages.append({'speaker': 'Assistant', 'message': 'Good Morning! Please ask me any question regarding to the meeting minutes.'})

        return jsonify(response_data), 200

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500






@app.route('/sendMessage', methods=['POST'])
def send_message():
    message_data = request.get_json()

    # Get user message from the request
    user_message = message_data.get('message')    # Returns None if 'message' does not exist in message_data
    transcription_list = message_data.get('transcription_list')  # Get the transcription list from the request

    # If user_message is None or an empty string, return success without processing the message
    if not user_message or not user_message.strip():
        return jsonify(success=True), 200

    global chat_messages
    print(message_data)
    chat_messages.append(message_data)

    # Convert transcription list to string
    transcription_str = json.dumps(transcription_list)

    # Generate assistant response
    assistant_response = get_assistant_response(transcription_str, user_message, openai_config, debug=False)
    assistant_response = {'speaker': 'Assistant', 'message': assistant_response}
    print(assistant_response)
    chat_messages.append(assistant_response)

    return jsonify(success=True), 200



@app.route('/getChatHistory', methods=['GET'])
def get_chat_history():
    return jsonify(chat_messages), 200


if __name__ == "__main__":
    app.run(debug=True)






