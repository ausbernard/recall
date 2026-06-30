"""Config in one place. Environment overrides."""

import os
from dotenv import load_dotenv

load_dotenv()

def load_config():
    return {
        "api_key": os.environ("RECALL_API_KEY"),
        "model": os.environ("RECALL_MODEL", "claude-haiku-4-5-20251001"),
        "temperature": float("RECALL_TEMPERATURE", "0,0"),
        "embedding_model": os.environ.get("RECALL_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
    }

def get_api_key():
    return load_config()["api_key"]

def get_model():
    return load_config()["model"]

def get_temperature():
    return load_config()["temperature"]

def get_embedding_model():
    return load_config()["embedding_model"]