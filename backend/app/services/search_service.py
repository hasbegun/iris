"""
Web Search Service using SearXNG
Provides search functionality via SearXNG Docker container
"""
import httpx
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """A single search result"""
    title: str
    url: str
    content: str
    engine: Optional[str] = None


class SearchResponse(BaseModel):
    """Web search response"""
    query: str
    results: List[SearchResult]
    total_results: int


class SearchService:
    """
    Web search service using SearXNG.

    SearXNG runs in a Docker container on localhost:9090
    and aggregates results from multiple search engines.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:9090",
        timeout: int = 10,
        enabled: bool = True
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.enabled = enabled

        # Headers to avoid bot detection
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "X-Forwarded-For": "127.0.0.1",
            "X-Real-IP": "127.0.0.1",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9"
        }

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=headers
        )

    async def search(
        self,
        query: str,
        max_results: int = 5
    ) -> SearchResponse:
        """
        Perform a web search using SearXNG.

        Args:
            query: The search query
            max_results: Maximum number of results to return (default: 5)

        Returns:
            SearchResponse with search results

        Raises:
            Exception: If search fails or SearXNG is unavailable
        """
        if not self.enabled:
            msg = "Search service is disabled"
            logger.warning(msg)
            raise Exception(msg)

        try:
            logger.info(f"Searching for: '{query}'")

            # Call SearXNG API
            response = await self.client.get(
                f"{self.base_url}/search",
                params={
                    "q": query,
                    "format": "json"
                }
            )
            response.raise_for_status()

            data = response.json()

            # Parse results
            raw_results = data.get("results", [])

            # Convert to SearchResult objects, limit to max_results
            results = []
            for item in raw_results[:max_results]:
                try:
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=item.get("content", ""),
                        engine=item.get("engine")
                    )
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to parse search result: {e}")
                    continue

            search_response = SearchResponse(
                query=query,
                results=results,
                total_results=len(results)
            )

            logger.info(f"Found {len(results)} results for query: '{query}'")
            return search_response

        except httpx.HTTPError as e:
            logger.error(f"HTTP error while searching: {e}")
            raise Exception(f"Search failed: {str(e)}")
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            raise Exception(f"Search failed: {str(e)}")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global instance using settings from config
search_service = SearchService(
    base_url=settings.searxng_url,
    timeout=settings.searxng_timeout,
    enabled=settings.searxng_enabled
)
