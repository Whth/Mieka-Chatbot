import aiohttp


async def fetch_src(url:str):
    """
    Asynchronously fetches the source code from a given URL.

    Args:
        url (str): The URL to fetch the source code from.

    Returns:
        str: The source code as a string.

    Raises:
        aiohttp.ClientError: If there was an error in the HTTP request.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=True) as response:
            text = await response.text()
            return text

