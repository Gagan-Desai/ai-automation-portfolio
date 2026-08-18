
import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from dotenv import  load_dotenv

load_dotenv()

API_KEY = os.environ.get("FASTAPI_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return key