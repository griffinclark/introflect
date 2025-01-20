from src.utils.firebase.firebase_init import firestore_client
from typing import Dict, List

def add_chimp(user_uid: str, chimp_data: Dict[str, str]):
    """
    Adds a new chimp to the Firestore collection with an auto-generated ID 
    and updates the user's social graph.

    Args:
        user_uid (str): UID of the user.
        chimp_data (Dict[str, str]): Data for the new chimp (excluding UID).
    """
    try:
        # Add the chimp to the "chimps" collection with an auto-generated ID
        chimps_ref = firestore_client.collection("chimps")
        chimp_doc_ref = chimps_ref.add(chimp_data)
        chimp_id = chimp_doc_ref[1].id
        print(f"Chimp {chimp_id} added successfully.")

        # Update the user's social graph
        user_ref = firestore_client.collection("users").document(user_uid)
        user_doc = user_ref.get()

        if not user_doc.exists():
            raise ValueError(f"User with UID {user_uid} does not exist.")

        user_data = user_doc.to_dict()
        social_graph = user_data.get("social_graph_chimps", [])

        if chimp_id not in social_graph:
            social_graph.append(chimp_id)
            user_ref.update({"social_graph_chimps": social_graph})
            print(f"Chimp {chimp_id} added to user {user_uid}'s social graph.")
        else:
            print(f"Chimp {chimp_id} is already in user {user_uid}'s social graph.")

    except Exception as e:
        print(f"Error adding chimp: {e}")

def get_chimps(user_uid: str) -> List[Dict[str, str]]:
    """
    Retrieves all chimps associated with a given user.

    Args:
        user_uid (str): UID of the user.

    Returns:
        List[Dict[str, str]]: A list of chimp data dictionaries.
    """
    try:
        # Get the user's social graph
        user_ref = firestore_client.collection("users").document(user_uid)
        user_doc = user_ref.get()

        if not user_doc.exists():
            raise ValueError(f"User with UID {user_uid} does not exist.")

        user_data = user_doc.to_dict()
        chimp_ids = user_data.get("social_graph_chimps", [])

        # Fetch chimp data for each chimp ID
        chimps = []
        for chimp_id in chimp_ids:
            chimp_ref = firestore_client.collection("chimps").document(chimp_id)
            chimp_doc = chimp_ref.get()

            if chimp_doc.exists:
                chimps.append(chimp_doc.to_dict())
            else:
                print(f"Warning: Chimp with ID {chimp_id} does not exist.")

        return chimps

    except Exception as e:
        print(f"Error retrieving chimps: {e}")
        return []

def main():
    print("Chimp Management CLI")
    user_uid = "g"

    chimp_data = {
        "name": input("Chimp Name: ").strip(),
        "approx_age": input("Approximate Age: ").strip(),
        "how_we_met": input("How We Met: ").strip(),
        "why_the_relationship_matters": input("Why the Relationship Matters: ").strip(),
        "one_story": input("One Story: ").strip()
    }

    add_chimp(user_uid, chimp_data)

    # Log all chimps for the user
    print("\nRetrieving all chimps for the user...")
    chimps = get_chimps(user_uid)
    if chimps:
        print("Chimps in the user's social graph:")
        for i, chimp in enumerate(chimps, 1):
            print(f"\nChimp {i}:")
            for key, value in chimp.items():
                print(f"  {key}: {value}")
    else:
        print("No chimps found in the user's social graph.")

if __name__ == "__main__":
    main()
