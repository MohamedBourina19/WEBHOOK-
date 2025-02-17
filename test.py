import requests
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder
from flask import Flask, request

class FacebookMessengerAPI:
    def __init__(self, page_access_token: str):
        # يتم تخزين التوكن مباشرة في المتغير
        self.PAGE_ACCESS_TOKEN = page_access_token

    @staticmethod
    def split_message(text, max_length=2000):
        return [text[i:i + max_length] for i in range(0, len(text), max_length)]

    def send_typing_indicator(self, recipient_id, action):
        url = f"https://graph.facebook.com/v21.0/me/messages?access_token={self.PAGE_ACCESS_TOKEN}"
        response = requests.post(url, json={
            "recipient": {"id": recipient_id},
            "sender_action": action
        })
        if response.status_code != 200:
            print(f"Failed to send typing indicator: {response.text}")

    def send_message(self, recipient_id, message):
        url = f"https://graph.facebook.com/v21.0/me/messages?access_token={self.PAGE_ACCESS_TOKEN}"

        try:
            self.send_typing_indicator(recipient_id, 'typing_on')

            if "filedata" in message:
                self._send_file_message(url, recipient_id, message)
            elif "text" in message:
                self._send_text_message(url, recipient_id, message["text"])

            print("Message sent successfully to ", recipient_id)

        except requests.exceptions.RequestException as e:
            print(f"Error sending message: {e}")
            self._send_error_message(url, recipient_id, str(e))

        finally:
            self.send_typing_indicator(recipient_id, 'typing_off')

    def _send_file_message(self, url, recipient_id, message):
        form_data = MultipartEncoder(
            fields={
                "recipient": json.dumps({"id": recipient_id}),
                "message": json.dumps({"attachment": message["attachment"]}),
                "filedata": (message["filedata"]["filename"], message["filedata"]["content"], message["filedata"]["content_type"])
            }
        )
        response = requests.post(url, data=form_data, headers={"Content-Type": form_data.content_type})
        response.raise_for_status()

    def _send_text_message(self, url, recipient_id, text):
        message_chunks = self.split_message(text)
        for chunk in message_chunks:
            data = {
                "recipient": {"id": recipient_id},
                "message": {"text": chunk}
            }
            response = requests.post(url, json=data)
            response.raise_for_status()

    def _send_error_message(self, url, recipient_id, error_message):
        requests.post(url, json={
            "recipient": {"id": recipient_id},
            "message": {"text": f"فشل في البرنامج ⚠️"}
        })

app = Flask(__name__)
VERIFY_TOKEN = "bougrina123"
processed_messages = set()

# هنا يتم تخزين التوكن مباشرة في متغير
PAGE_ACCESS_TOKEN = "EAAO52Vx4rI0BOyqEFtklEORPceKHn5G3iNT4hvZB2d6stZCZAlO7uyJGBCqZB6ifeMHZBGOalZBywmU9E0ej3PEoeXeaSUvQvPyOUpjyfXkSK6XQygwLQsCXZAHnZA3znJ6HHyUt4jZCKZCCZClhQLUJG7L6q6gQHvd9atfAPoZAZAzvDiF8bewE46wzRTZAZBG6GZBZBT0UaMgZDZD"
api = FacebookMessengerAPI(PAGE_ACCESS_TOKEN)

@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get("hub.verify_token")
    if request.args.get("hub.mode") == "subscribe" and token == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    body = request.json
    if body['object'] == 'page':
        process_entries(body['entry'])
        return "EVENT_RECEIVED", 200
    return "Not Found", 404

def process_entries(entries):
    for entry in entries:
        for event in entry.get('messaging', []):
            handle_event(event)

def handle_event(event):
    sender_id = event['sender']['id']
    message_id = event['message']['mid'] if 'message' in event else None
    if 'postback' in event and event['postback']['payload'] == "GET_STARTED":
        send_welcome_message(sender_id)
    else: pass
    if message_id in processed_messages:
        return 
    processed_messages.add(message_id)
    process_message(sender_id, event)

def send_welcome_message(sender_id):
    api.send_message(sender_id, {"text": "HELLO"})

def process_message(sender_id, event):
    if event.get('message') and 'text' in event['message']:
        message_text = event['message']['text'].strip()
        api.send_message(sender_id, {"text": "مرحبا"})
        image_url = "https://example.com/path/to/image.jpg"
        message = {"attachment": {"type": "image","payload": {"url":image_url,"is_reusable": True}}}
        api.send_message(sender_id, message)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port='5000', debug=True)
