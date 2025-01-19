import os
from dataclasses import dataclass, field
from typing import List, Dict, Any
import datetime
from src.utils.constants import ChatMessage, Conversation
from src.utils.firebase.firebase_init import firestore_client

# Initialize Firebase app
SERVICE_KEY_PATH = os.path.join("secrets", "service_key.json")
if not os.path.exists(SERVICE_KEY_PATH):
    raise FileNotFoundError(f"Service account key not found at {SERVICE_KEY_PATH}")



class ChatHelper:
    def __init__(self):
        self.db = firestore_client

    def save_conversation(self, conversation: Conversation):
        """
        Saves a conversation to the Firestore database.

        Args:
            conversation (Conversation): The conversation to save.
        """
        doc_ref = self.db.collection("conversations").document(conversation.conversation_id)
        doc_ref.set(conversation.to_dict())

    def update_conversation(self, conversation: Conversation):
        """
        Updates an existing conversation in the Firestore database.

        Args:
            conversation (Conversation): The conversation to update.
        """
        doc_ref = self.db.collection("conversations").document(conversation.conversation_id)
        doc_ref.update({
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "expert_used": msg.expert_used,
                    "expert_version": msg.expert_version,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in conversation.messages
            ],
        })

    def load_conversation(self, conversation_id: str) -> Conversation:
        """
        Loads a conversation from Firestore.

        Args:
            conversation_id (str): The ID of the conversation to load.

        Returns:
            Conversation: The loaded conversation.
        """
        doc_ref = self.db.collection("conversations").document(conversation_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return Conversation(
                conversation_id=data["conversation_id"],
                user_id=data["user_id"],
                messages=[
                    ChatMessage(
                        role=msg["role"],
                        content=msg["content"],
                        expert_used=msg["expert_used"],
                        expert_version=msg["expert_version"],
                        timestamp=datetime.datetime.fromisoformat(msg["timestamp"]),
                    )
                    for msg in data["messages"]
                ],
                created_at=datetime.datetime.fromisoformat(data["created_at"]),
            )
        raise ValueError(f"Conversation with ID {conversation_id} not found.")

    def delete_conversation(self, conversation_id: str):
        """
        Deletes a conversation from Firestore.

        Args:
            conversation_id (str): The ID of the conversation to delete.
        """
        doc_ref = self.db.collection("conversations").document(conversation_id)
        doc_ref.delete()

# Example usage
if __name__ == "__main__":
    chat_helper = ChatHelper()

    # Example conversation
    conversation = Conversation(
        conversation_id="unique_conversation_id",
        user_id="g",
        messages=[
            ChatMessage(
                role="user",
                content="Hello!",
                expert_used="general",
                expert_version=1
            ),
            ChatMessage(
                role="assistant",
                content="Hi there! How can I assist you?",
                expert_used="general",
                expert_version=1
            )
        ]
    )

    # Save the conversation
    chat_helper.save_conversation(conversation)

    # Load the conversation
    loaded_conversation = chat_helper.load_conversation("unique_conversation_id")
    print("Loaded conversation:", loaded_conversation)

    # Update the conversation
    conversation.messages.append(
        ChatMessage(
            role="user",
            content="Can you tell me more about recovery?",
            expert_used="health_expert",
            expert_version=2
        )
    )
    chat_helper.update_conversation(conversation)

    # Delete the conversation
    chat_helper.delete_conversation("unique_conversation_id")