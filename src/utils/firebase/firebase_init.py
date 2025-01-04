import os
from firebase_admin import credentials, firestore, initialize_app

# Path to the service account key
SERVICE_KEY_PATH = os.path.join("secrets", "service_key.json")

# Ensure the service key exists
if not os.path.exists(SERVICE_KEY_PATH):
    raise FileNotFoundError(f"Service account key not found at {SERVICE_KEY_PATH}")

# Initialize Firebase app with service account credentials
try:
    cred = credentials.Certificate(SERVICE_KEY_PATH)
    firebase_app = initialize_app(cred)
except Exception as e:
    raise RuntimeError(f"Failed to initialize Firebase app: {e}")

# Export Firestore client
try:
    firestore_client = firestore.client()

except Exception as e:
    raise RuntimeError(f"Failed to initialize Firestore client: {e}")
