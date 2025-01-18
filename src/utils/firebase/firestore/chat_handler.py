import os
import json
from typing import Dict, Any, List
from google.cloud import firestore
from datetime import datetime
from dataclasses import asdict
from src.utils.constants import ChatContext, ChatMessage


class FirestoreChatHandler:
    def __init__(self, collection_name: str = "chats"):
        self.db = firestore.Client()
        self.collection_name = collection_name

    def save_chat_context(self, chat_context: ChatContext):
        """Save or update a chat context in Firestore."""
        doc_ref = self.db.collection(self.collection_name).document(chat_context.user_id)
        chat_dict = asdict(chat_context)
        chat_dict["context"] = [asdict(msg) for msg in chat_context.context]
        doc_ref.set(chat_dict, merge=True)

    def load_chat_context(self, user_id: str, max_tokens: int) -> ChatContext:
        """Load a chat context from Firestore or create a new one."""
        doc_ref = self.db.collection(self.collection_name).document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            context = [ChatMessage(**msg) for msg in data.get("context", [])]
            return ChatContext(
                user_id=user_id,
                max_tokens=data.get("max_tokens", max_tokens),
                context=context,
                token_count=data.get("token_count", 0),
            )
        else:
            return ChatContext(user_id=user_id, max_tokens=max_tokens)

    def add_message_to_context(self, chat_context: ChatContext, role: str, content: str, expert_used: str, expert_version: int, model_type: str):
        """Add a new message to the chat context and manage token limits."""
        # Estimate tokens based on model type
        token_multiplier = 1.2 if model_type == "gpt" else 1.0  # Adjust based on model
        estimated_tokens = int(len(content.split()) * token_multiplier)

        # Add the new message
        new_message = ChatMessage(
            role=role,
            content=content,
            expert_used=expert_used,
            expert_version=expert_version
        )
        chat_context.context.append(new_message)
        chat_context.token_count += estimated_tokens

        # Trim context if it exceeds max_tokens
        while chat_context.token_count > chat_context.max_tokens:
            removed_message = chat_context.context.pop(0)
            chat_context.token_count -= int(len(removed_message.content.split()) * token_multiplier)

        # Save the updated chat context
        self.save_chat_context(chat_context)

        return chat_context

    def archive_chat(self, user_id: str, archive_collection: str = "archived_chats"):
        """Archive a user's chat context by moving it to a separate Firestore collection."""
        doc_ref = self.db.collection(self.collection_name).document(user_id)
        doc = doc_ref.get()

        if doc.exists:
            archived_ref = self.db.collection(archive_collection).document(user_id)
            archived_ref.set(doc.to_dict(), merge=True)

            # Retain the document in the original collection (no deletion)
        else:
            raise ValueError(f"No chat context found for user_id: {user_id}")
