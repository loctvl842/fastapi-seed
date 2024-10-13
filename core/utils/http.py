from typing import Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),  # Exponential backoff with a max wait of 10 seconds
    retry=retry_if_exception_type(httpx.HTTPStatusError),  # Retry only on HTTP status errors
)
async def fetch(
    url: str,
    *,
    method: str = "GET",
    client: Optional[httpx.AsyncClient] = None,
    **kwargs,
) -> httpx.Response:
    """
    Sends an asynchronous HTTP request using httpx, with logging and custom connection limits.

    Args:
        url (str): The URL to send the request to.
        method (str, optional): The HTTP method to use. Defaults to 'GET'.
        client (httpx.AsyncClient, optional): An instance of httpx.AsyncClient for connection pooling.
            If None, a new client is created and closed within the function. Defaults to None.
        **kwargs: Additional keyword arguments passed to `client.request`.

    Returns:
        httpx.Response: The HTTP response from the server.
    """
    from core.logger import syslog

    close_client = False
    if client is None:
        client = httpx.AsyncClient()
        close_client = True

    try:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        syslog.info(f"Successfully fetched {response.url}")
        return response.json()
    except httpx.HTTPStatusError as exc:
        print(f"HTTP error occurred: {exc} {exc.request.url}")
        raise
    except httpx.RequestError as exc:
        syslog.error(f"HTTP error: {exc} {exc.request.url}")
        raise
    finally:
        if close_client:
            await client.aclose()
