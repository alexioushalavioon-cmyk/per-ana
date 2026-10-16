"""Optional live search smoke test. Exits 2 when no provider key is configured."""
import asyncio
from app.core.config import settings
from app.services.search import search_web

async def main():
    if settings.search_provider == "none":
        raise SystemExit("SEARCH_PROVIDER is not configured")
    results = await search_web("OpenAI official website", 3)
    assert results and all(r.url.startswith("http") for r in results)
    print({"provider": settings.search_provider, "results": len(results), "first": results[0].url})

if __name__ == "__main__":
    asyncio.run(main())
