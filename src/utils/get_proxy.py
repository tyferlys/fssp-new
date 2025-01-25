import asyncio

import aiohttp
import loguru

from config import get_settings

settings = get_settings()

async def get_proxy() -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{settings.proxy_host}/get_proxy") as response:
                if response.status == 200:
                    result = await response.json()
                    return result["proxyString"]
                return None
    except Exception as e:
        loguru.logger.error(str(e))
        return None

if __name__ == "__main__":
    asyncio.run(get_proxy())