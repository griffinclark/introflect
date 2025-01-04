from src.utils.firebase.firebase_init import firestore_client

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


# Main function for demonstration
def main():
    uid = "g"
    key = "whooptastic"
    initial_value = "initial_refresh_token"
    updated_value = "updated_refresh_token"

    try:
        # Create or update a new secret
        print("Creating a new secret...")
        crud_user_secret(uid, key, "create", value=initial_value)

        # Read the secret
        print("Reading the secret...")
        secret_value = crud_user_secret(uid, key, "read")
        print(f"Secret value: {secret_value}")

        # Update the secret
        print("Updating the secret...")
        crud_user_secret(uid, key, "update", value=updated_value)

        # Read the updated secret
        print("Reading the updated secret...")
        updated_secret_value = crud_user_secret(uid, key, "read")
        print(f"Updated secret value: {updated_secret_value}")

        # Delete the secret
        print("Deleting the secret...")
        crud_user_secret(uid, key, "delete")

        # Attempt to read the deleted secret (should raise an error)
        print("Attempting to read deleted secret...")
        crud_user_secret(uid, key, "read")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
