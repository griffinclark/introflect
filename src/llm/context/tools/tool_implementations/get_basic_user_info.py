from src.utils.firebase.firebase_init import firestore_client
def get_basic_user_info(uid: str) -> dict:
    """
    Retrieves basic user information for the given UID from Firestore.

    Args:
        uid (str): The unique identifier for the user.

    Returns:
        dict: A dictionary containing the user's basic information.
    """
    try:
        # Query the users collection to find the document where UID matches the provided uid
        query = firestore_client.collection("users").where("UID", "==", uid).get()
        if not query:
            raise ValueError(f"No user found with UID: {uid}")

        user_doc = query[0].to_dict()

        # Extract only the basic user fields
        basic_user_info = {
            "UID": user_doc.get("UID"),
            "name": user_doc.get("name"),
            "age": user_doc.get("age"),
            "gender": user_doc.get("gender"),
            "location": user_doc.get("location"),
            "occupation": user_doc.get("occupation"),
            "languages_spoken": user_doc.get("languages_spoken", []),
            "favorite_books_and_movies": user_doc.get("favorite_books_and_movies", {}),
            "pets": user_doc.get("pets", {}),
            "cultural_religious_identity": user_doc.get("cultural_religious_identity"),
        }

        return basic_user_info
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve basic user info for UID {uid}: {e}")