import os
import requests
from dotenv import load_dotenv

load_dotenv()

sid = os.getenv('TWILIO_ACCOUNT_SID', 'your_account_sid_here')
token = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token_here')
from_num = os.getenv('TWILIO_PHONE_NUMBER', '+1234567890')
to_num = os.getenv('TARGET_PHONE_NUMBER', '+1234567890')

twiml = (
    '<Response>'
    '<Say voice="Polly.Aditi">Hello! This is your CampusLife AI student voice companion calling your phone. '
    'I am actively monitoring your workload and wellness. I noticed your exam is approaching in three days, '
    'and your sleep dropped below 6 hours. Remember to take regular study breaks and focus on high-yield revision topics! '
    'Your study plan has been prioritized in your portal. Goodbye!</Say>'
    '<Pause length="2"/>'
    '<Hangup/>'
    '</Response>'
)

url = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json'
data = {
    'To': to_num,
    'From': from_num,
    'Url': 'http://demo.twilio.com/docs/voice.xml'
}
r = requests.post(url, auth=(sid, token), data=data)

print('STATUS CODE:', r.status_code)
print('CALL SID:', r.json().get('sid'))
print('CALL STATUS:', r.json().get('status'))
print('FULL RESPONSE:', r.json())
