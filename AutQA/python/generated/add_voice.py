from pathlib import Path
import sys, os
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from client import post
import json

def main():
    path = '/onboarding/enrollment/addVoice'
    payload = {
        'enrollmentToken': os.getenv('ETOKEN',''),
        'livenessData': {
            'voice': {
                'voiceSamples': [ {'data': os.getenv('VOICE','')} ],
                'workflow': 'alfa4',
                'meta_data': {
                    'client_device_brand': 'Samsung',
                    'client_device_model': 'SM-A526U',
                    'client_os_version': '14',
                    'client_version': 'AwareID_version:3.2.703',
                    'localization': 'en-US',
                    'programming_language_version': 'Java',
                    'username': os.getenv('USERNAME','')
                }
            }
        }
    }
    resp = post(path, json=payload)
    print('Status:', resp.status_code)
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)

if __name__ == '__main__':
    main()
