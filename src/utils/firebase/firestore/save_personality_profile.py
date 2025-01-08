import json
import datetime
from firebase_admin import firestore
from src.utils.firebase.firebase_init import firestore_client
from src.utils.constants import PersonalityProfile

# Load personality profile from an external JSON file
JSON_FILE_PATH = "./src/utils/firebase/firestore/my_data.json"
USER_UID = "g" # TODO replace before using for any other user
SOURCE="understandmyself.com"

def load_personality_profile(file_path: str) -> PersonalityProfile:
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            # Ensure data matches the expected type
            if not isinstance(data, dict) or "metrics" not in data:
                raise ValueError("Invalid personality profile format.")
            return data
    except Exception as e:
        raise RuntimeError(f"Failed to load personality profile from {file_path}: {e}")

# Firestore collection and document setup
profiles_collection = firestore_client.collection("personality_profiles")

# Create or update user record with personality profile and timestamp
def store_user_profile(uid: str, profile_data: PersonalityProfile):
    try:
        # Add datetimeCreated with current timestamp
        datetime_created = datetime.datetime.now().isoformat()
        profile_data["datetimeCreated"] = datetime_created

        # Add the user UID for reference
        profile_data["for_user_UID"] = uid
        
        # Add the source of the personality profile
        profile_data["source"] = SOURCE

        # Set the user profile in the personality_profiles collection
        profiles_collection.document(uid).set(profile_data, merge=True)
        print(f"Personality profile for UID {uid} stored successfully in 'personality_profiles' collection.")
    except Exception as e:
        print(f"An error occurred while storing the user profile: {e}")

# Main execution
if __name__ == "__main__":
    try:
        personality_profile = load_personality_profile(JSON_FILE_PATH)
        store_user_profile(USER_UID, personality_profile)
    except Exception as e:
        print(f"An error occurred: {e}")