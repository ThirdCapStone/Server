from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from auth.env import API_KEY


api_key_header = APIKeyHeader(name="access_token", auto_error=False)


def get_api_key(api_key_header: APIKeyHeader = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Couldn't found validate API KEY"
        )
