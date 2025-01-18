from collections import deque
from typing import List, Dict

class SlidingContextWindow:
    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens
        self.context = deque()

    def add_message(self, role: str, content: str):
        message = {"role": role, "content": content}
        self.context.append(message)
        self._trim_context()

    def _trim_context(self):
        while self._context_length() > self.max_tokens:
            self.context.popleft()

    def _context_length(self) -> int:
        return sum(len(msg["content"].split()) for msg in self.context)

    def get_context(self) -> List[Dict[str, str]]:
        return list(self.context)
