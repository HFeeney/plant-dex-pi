import email
import os
import pyzmail
import json
from pathvalidate import sanitize_filename


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
            # Text part of the email. Only attempt to interpret one text file.
            if name == None and part.filename and part.filename.lower().endswith('.txt'):
                text = part.get_payload().decode(part.charset)
                lines = text.splitlines()
                
                # Fail if there aren't enough lines or the keyword is missing.
                if len(lines) < 2 or lines[0].lower() != 'plant':
                    return None

                name = lines[1].lower()
                info = '' if len(lines) == 2 else ' '.join(lines[2:])


            # Image part of the email. Only attempt to store one image.
            if img_data == None and part.filename and part.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                img_data = part.get_payload()
                img_name = msgid + part.filename[part.filename.rfind('.'):]


        # Fail if either the text or image attachment was missing.
        if name == None or img_data == None:
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
