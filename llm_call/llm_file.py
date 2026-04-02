
import os

# os.environ["LANGCHAIN_PROJECT"] = "job email" 

from langchain_groq import ChatGroq
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from typing import List
import itertools
from typing import Any
from typing import Iterator
import os
from dotenv import load_dotenv

# load .env
load_dotenv()
# from langchain_core.pydantic_v1 import PrivateAttr
from pydantic import PrivateAttr

# from config import config





# convert to list
GROQ_KEYS = os.getenv("GROQ_KEYS", "").split(",")

# clean list (remove spaces/empty)
GROQ_KEYS = [k.strip() for k in GROQ_KEYS if k.strip()]



GROQ_MODELS = ["openai/gpt-oss-120b",
            #    "openai/gpt-oss-20b",
# "llama-3.1-8b-instant",

# "llama-3.3-70b-versatile",
# "whisper-large-v3",
# "whisper-large-v3-turbo"
]


# GROQ_MODELS = ["llama-3.1-8b-instant"]

LLMS = [
    ChatGroq(groq_api_key=k, model=m, temperature=0)
    for k in GROQ_KEYS
    for m in GROQ_MODELS
]



class RoundRobinLLM(BaseChatModel):
    _cycle = PrivateAttr()
    _llms = PrivateAttr()

    def __init__(self, llms: List[BaseChatModel] | None = None):
        super().__init__()
        self._llms = llms or LLMS
        self._cycle = itertools.cycle(self._llms)

    @property
    def _llm_type(self) -> str:
        return "round-robin-generic"

    def _generate(self, messages: List[BaseMessage], **kwargs):
        llm = next(self._cycle)
        return llm._generate(messages, **kwargs)

    async def _agenerate(self, messages: List[BaseMessage], **kwargs):
        llm = next(self._cycle)
        if hasattr(llm, "_agenerate"):
            return await llm._agenerate(messages, **kwargs)
        raise NotImplementedError(f"{llm} does not support async generation.")

    def with_structured_output(self, schema, **kwargs):
        llm = next(self._cycle)
        return llm.with_structured_output(schema, **kwargs)

