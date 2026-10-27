import firebase_admin
from firebase_admin import credentials, messaging
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
# Note: You should place your serviceAccountKey.json in a secure location and point to it via settings or env var
firebase_initialized = False

def initialize_firebase():
    global firebase_initialized
    if not firebase_initialized:
        try:
            cred_path = getattr(settings, 'FIREBASE_SERVICE_ACCOUNT_KEY', os.path.join(settings.BASE_DIR, 'serviceAccountKey.json'))
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                firebase_initialized = True
                logger.info("Firebase Admin SDK initialized successfully.")
            else:
                logger.warning(f"Firebase service account key not found at {cred_path}. Push notifications will not be sent.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")

def send_push_notification(token, title, body, data=None):
    """
    Sends a bush notification to a specific FCM device token.
    """
    initialize_firebase()
    if not firebase_initialized:
        return False

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
            data=data or {},
        )
        response = messaging.send(message)
        logger.info(f"Successfully sent message: {response}")
        return True
    except Exception as e:
        logger.error(f"Error sending push notification: {e}")
        return False
