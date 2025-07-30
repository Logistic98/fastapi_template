# -*- coding: utf-8 -*-

from pydantic import BaseModel
from typing import List, Dict, Optional


class ChatRequest(BaseModel):
    messages: List[Dict]
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    model: Optional[str] = None