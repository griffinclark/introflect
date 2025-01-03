import os
from firebase_admin import credentials, firestore, initialize_app

# Path to the service account key
SERVICE_KEY_PATH = os.path.join("src", "resources", "firebase", "secrets", "service_key.json")

# Initialize Firebase app with service account credentials
cred = credentials.Certificate(SERVICE_KEY_PATH)
firebase_app = initialize_app(cred)

# Export Firestore client
firestore_client = firestore.client()
