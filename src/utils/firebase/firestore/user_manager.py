from src.utils.firebase.firebase_init import firestore_client
from typing import Optional, Union
from src.utils.constants import User
from dataclasses import asdict
def crud_user_secret(uid, key, action, value=None):
    try:
        # Query the users collection to find the document where UID matches the provided uid
        query = firestore_client.collection("users").where("UID", "==", uid).get()
        if not query:
            raise ValueError(f"No user document found with UID: {uid}.")
        
        user_doc = query[0]  # Assuming UID is unique
        user_doc_ref = user_doc.reference
        user_data = user_doc.to_dict()
        
        if action in ("create", "update"):
            if not value:
                raise ValueError("Value must be provided for 'create' or 'update' actions.")
            secrets = user_data.get("secrets", {})
            secrets[key] = value
            user_doc_ref.set({"secrets": secrets}, merge=True)
        elif action == "read":
            secrets = user_data.get("secrets", {})
            return secrets.get(key)
        elif action == "delete":
            secrets = user_data.get("secrets", {})
            if key not in secrets:
                raise ValueError(f"Secret '{key}' is missing for UID: {uid}.")
            del secrets[key]
            user_doc_ref.set({"secrets": secrets}, merge=True)
        else:
            raise ValueError(f"Invalid action '{action}'. Supported actions are: 'create', 'read', 'update', 'delete'.")
    except Exception as e:
        raise RuntimeError(f"Failed to perform '{action}' action on secret '{key}' for UID {uid}: {e}")

def save_user_to_firestore(user: Union[dict, 'User']):
    """
    Saves or updates a user in Firestore.

    Args:
        user (Union[dict, User]): The user data to save. Can be a dictionary or a User dataclass.
    """
    if not isinstance(user, dict):
        user_data = asdict(user)  # Convert dataclass to dictionary
    else:
        user_data = user  # Already a dictionary

    try:
        uid = user_data.get("UID")
        if not uid:
            raise ValueError("UID is required to save a user.")

        query = firestore_client.collection("users").where("UID", "==", uid).get()

        if query:
            # Update existing user
            user_doc = query[0].reference
            user_doc.set(user_data, merge=True)
        else:
            # Create new user
            firestore_client.collection("users").add(user_data)

        print("User saved successfully.")
    except Exception as e:
        print(f"Error saving user: {e}")


def validate_user(user_data: dict) -> bool:
    """
    Validates a user object against the User dataclass.

    Args:
        user_data (dict): The user data to validate.

    Returns:
        bool: True if the user is valid, raises an exception otherwise.
    """
    try:
        # Create a User instance to validate the data
        User(
            uid=user_data["UID"],
            name=user_data["name"],
            age=int(user_data["age"]),
            gender=user_data["gender"],
            location=user_data["location"],
            occupation=user_data["occupation"],
            favorite_books_and_movies=user_data.get("favorite_books_and_movies", {}),
            pets=user_data.get("pets", {}),
            languages_spoken=user_data.get("languages_spoken", []),
            cultural_religious_identity=user_data.get("cultural_religious_identity"),
            secrets=user_data.get("secrets", {}),
        )
        return True
    except Exception as e:
        print(f"Validation failed: {e}")
        return False
    
def load_user(uid: str):
    try:
        # Query the users collection to find the document where UID matches the provided uid
        query = firestore_client.collection("users").where("UID", "==", uid).get()
        if not query:
            print(f"No user found with UID: {uid}")
            return None
        user_doc = query[0]
        print(f"User found: {user_doc.to_dict()}")
        return user_doc.to_dict()
    except Exception as e:
        print(f"An error occurred while fetching user: {e}")
        return None



def create_or_update_user(uid: str):
    user = load_user(uid)

    if not user:
        print("Creating a new user.")
        user = User(
            name=input("Name: "),
            age=int(input("Age: ")),
            gender=input("Gender: "),
            pronouns=input("Pronouns (optional): ") or None,
            location=input("Location: "),
            occupation=input("Occupation: "),
            favorite_books_movies=[],
            pets=[],
            languages_spoken=[],
            cultural_identity=input("Cultural Identity (optional): ") or None,
            religious_identity=input("Religious Identity (optional): ") or None,
            uid=uid,
            secrets={},
        )
    else:
        print(f"User {uid} found. Updating missing fields...")

        if not user.name:
            user.name = input("Name: ")
        if not user.age:
            user.age = int(input("Age: "))
        if not user.gender:
            user.gender = input("Gender: ")
        if not user.location:
            user.location = input("Location: ")
        if not user.occupation:
            user.occupation = input("Occupation: ")
        if not user.cultural_identity:
            user.cultural_identity = input("Cultural Identity (optional): ") or None
        if not user.religious_identity:
            user.religious_identity = input("Religious Identity (optional): ") or None

    # Save user back to Firestore
    save_user_to_firestore(user)


def main():
    print("Validating User with UID 'g'...")
    uid = "g"

    # Load user from Firestore
    user_data = load_user(uid)

    if user_data:
        print(f"User data loaded: {user_data}")
        # Validate user
        if validate_user(user_data):
            print(f"User with UID '{uid}' is valid.")
        else:
            print(f"User with UID '{uid}' is invalid. Please correct the data.")
    else:
        print(f"No user found with UID '{uid}'. Please create the user first.")



if __name__ == "__main__":
    main()
