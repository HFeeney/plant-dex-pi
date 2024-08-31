import imaplib
import email
import os
import pyzmail
import plant_record
from credentials import *

# Configuration
REC_SAVE_DIR = os.path.join(os.path.dirname(__file__), 'records') 
IMG_SAVE_DIR = os.path.join(os.path.dirname(__file__), 'images')


# Ensure the save directory exists
if not os.path.exists(IMG_SAVE_DIR):
    os.makedirs(IMG_SAVE_DIR)

# Ensure the save directory exists
if not os.path.exists(REC_SAVE_DIR):
    os.makedirs(REC_SAVE_DIR)

def record_new_plants():
    # Connect to the server
    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail:
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')

        # Search for all emails from my phone.
        status, data = mail.search(None, f'(HEADER FROM "{SOURCE}")')
        email_ids = data[0].split()

        for email_id in email_ids:
            # Fetch the email by ID
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            msg = pyzmail.PyzMessage.factory(msg_data[0][1])

            record = plant_record.Record.from_email(msg)

            # Mark this message for deletion.
            mail.store(email_id, '+FLAGS', '\\Deleted')

        # Delete all messages from my phone.
        mail.expunge()
        
if __name__ == "__main__":
    record_new_plants()
