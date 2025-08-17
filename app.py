import os
from flask import Flask, request, send_file, jsonify
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    try:
        file = request.files['file']
        transcript = file.read().decode('utf-8')
        custom_prompt = request.form.get('prompt', '')
        
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
        full_prompt = f"{custom_prompt}\n\nTranscript:\n{transcript}"
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": full_prompt}],
            model="llama-3.1-8b-instant",
        )
        
        summary = chat_completion.choices[0].message.content
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': f"Error generating summary: {str(e)}"}), 500

@app.route('/share', methods=['POST'])
def share():
    try:
        data = request.json
        summary = data.get('summary', '')
        recipients = data.get('recipients', '').split(',')
        
        if not summary or not recipients:
            return jsonify({'error': 'Missing summary or recipients'}), 400
        
        sender = os.environ.get('EMAIL_SENDER')
        password = os.environ.get('EMAIL_PASSWORD')
        
        if not sender or not password:
            return jsonify({'error': 'Email configuration missing'}), 500
        
        msg = MIMEText(summary)
        msg['Subject'] = 'Meeting Summary'
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
        
        return jsonify({'status': 'sent'})
    except Exception as e:
        return jsonify({'error': f"Error sending email: {str(e)}"}), 500

if __name__ == '__main__':
    # Bind to 0.0.0.0 and PORT for Render.com
    port = int(os.environ.get('PORT', 5000))  
    app.run(host='0.0.0.0', port=port, debug=False)  