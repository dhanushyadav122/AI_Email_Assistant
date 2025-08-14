from flask import Flask, render_template, request
import requests
import json
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Read credentials from environment
YOUR_EMAIL = os.getenv("YOUR_EMAIL")
YOUR_APP_PASSWORD = os.getenv("YOUR_APP_PASSWORD")
app_key = os.getenv("OPENROUTER_API_KEY")

# History file
HISTORY_FILE = "emails.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_to_history(entry):
    history = load_history()
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    email_to = ""
    email_subject = ""
    send_status = ""
    suggestion = ""
    tone = ""
    language = ""
    mail_type = ""

    if request.method == "POST":
        email_to = request.form['email_to']
        email_subject = request.form['subject']
        body_idea = request.form['body']
        tone = request.form.get('tone', 'friendly')
        language = request.form.get('language', 'english')
        mail_type = request.form.get('mail_type', 'personal')
        send_email = request.form.get('send_email')

        # AI Prompt
        prompt = f"""Write a {tone} {mail_type} email in {language} to {email_to}.
Subject: {email_subject}
Content: {body_idea}"""

        # Call AI API
        headers = {
            "Authorization": f"Bearer {app_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [
                {"role": "system", "content": "You are a helpful email assistant."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                     headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            suggestion = response.json()['choices'][0]['message']['content']
        except Exception as e:
            suggestion = f"❌ AI request failed: {str(e)}"

        # Save to history if AI suggestion is generated
        if suggestion and not suggestion.startswith("❌"):
            save_to_history({
                "to": email_to,
                "subject": email_subject,
                "body": suggestion,
                "tone": tone,
                "language": language,
                "mail_type": mail_type
            })

        # Send email if user checked the box
        if send_email and suggestion and not suggestion.startswith("❌"):
            try:
                msg = MIMEText(suggestion)
                msg['Subject'] = email_subject
                msg['From'] = YOUR_EMAIL
                msg['To'] = email_to

                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(YOUR_EMAIL, YOUR_APP_PASSWORD)
                server.sendmail(YOUR_EMAIL, email_to, msg.as_string())
                server.quit()
                send_status = "✅ Email sent successfully!"
            except Exception as e:
                send_status = f"❌ Failed to send email: {str(e)}"

    return render_template("index.html",
                           suggestion=suggestion,
                           email_to=email_to,
                           email_subject=email_subject,
                           send_status=send_status,
                           tone=tone,
                           language=language,
                           mail_type=mail_type)

@app.route("/auto_reply", methods=["POST"])
def auto_reply():
    incoming_email = request.form.get("incoming_email")
    tone = request.form.get("tone")

    # Call AI API for auto-reply
    prompt = f"Write an auto-reply in {tone} tone to this email:\n\n{incoming_email}"

    headers = {
        "Authorization": f"Bearer {app_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [
            {"role": "system", "content": "You are a helpful email auto-reply assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        generated_reply = response.json()['choices'][0]['message']['content']
    except Exception as e:
        generated_reply = f"❌ AI request failed: {str(e)}"

    return render_template("index.html", auto_reply=generated_reply)

@app.route("/history", methods=["GET"])
def view_history():
    return render_template("history.html", history_data=load_history())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
