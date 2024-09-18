import groq
import json
from api_handlers import BaseHandler

class GroqHandler(BaseHandler):
    def __init__(self, api_key, model):
        super().__init__()
        self.client = groq.Groq(api_key=api_key)
        self.model = model

    def _make_request(self, messages, max_tokens):
        # Make a request to the Groq API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.2
        )
        return response.choices[0].message.content