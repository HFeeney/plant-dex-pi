import email
import os
import pyzmail
import json
import requests
from pathvalidate import sanitize_filename
from credentials import API_KEY

IDENTIFICATION_THRESHOLD = 0.5

REC_SAVE_DIR = os.path.join(os.path.dirname(__file__), 'records')
IMG_SAVE_DIR = os.path.join(os.path.dirname(__file__), 'images')

class Record:
    def __init__(self, name, img, info, msgid):
        self.name = name
        self.img = img
        self.info = info
        self.msgid = msgid

    # Builds a plant record from an email message. Returns the record upon
    # success, or None otherwise. The message must contain at least a txt
    # file and an image.
    # In the txt file, the first line must be the keyword 'plant',
    # and there must be a second line to be interpreted as the name. All
    # remaining lines are the information about the plant.
    # Saves the record and image files associated with the plant.
    @classmethod
    def from_email(cls, msg):
        # Track the attributes of the record to be saved.
        name = None
        img_name = None
        img_data = None
        info = None
        msgid = msg.__getitem__('Message-ID')

        # Fail if there is no message id.
        if msgid == None:
            return None

        # Read the parts (attachments) of the email.
        for part in msg.mailparts:
            # Image part of the email. Only attempt to store one image.
            if part.filename and part.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_data = part.get_payload()
                img_name = msgid + part.filename[part.filename.rfind('.'):]
                break


        # Fail if the image attachment was missing.
        if img_data == None:
            return None

        # Attempt to identify the plant using Pl@ntNet
        api_url = 'https://my-api.plantnet.org/v2/identify/all'
        params = {'nb-results': '1', 'type': 'kt', 'api-key': API_KEY}
        images = [('images', img_data)]
        r = requests.post(api_url, params=params, files=images)

        # Fail if identification failed
        if r.status_code != 200:
            return None

        # Attempt json conversion
        try:
            result_json = r.json()
            print(result_json)

            if len(result_json['results']) == 0:
                return None

            # Fail if the identification result is too low 
            results_first = result_json['results'][0]
            if results_first['score'] < IDENTIFICATION_THRESHOLD:
                return None

            result_plant = results_first['species']
            info = result_plant['scientificName']
            if len(result_plant['commonNames']) == 0:
                return None

            name = result_plant['commonNames'][0]

        except requests.exceptions.JSONDecodeError:
            return None

        # The email contained valid data for a plant record.
        # Sanitize both the image name and record name, then save both.
        img_name = sanitize_filename(img_name)
        name = sanitize_filename(name)

        ret_val = cls(name, img_name, info, msgid)

        img_path = os.path.join(IMG_SAVE_DIR, img_name)
        with open(img_path, 'wb') as f:
            f.write(img_data)
        
        json_path = os.path.join(REC_SAVE_DIR, name + msgid + '.json')
        with open(json_path, 'w') as sf:
            json.dump(ret_val.__dict__, sf)

        return ret_val
