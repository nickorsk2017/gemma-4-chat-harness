"""HTTP request / response contracts for web_agent tools."""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent_core.envelope import AgentResponse
from web_agent.schemas.web import NewsResult, SearchResult, Weather, WebPage


class NewsRequest(BaseModel):
    query: str = Field(..., description="Topic to fetch news about.")
    limit: int = Field(default=5, ge=1, le=20)


class SearchRequest(BaseModel):
    prompt: str = Field(..., description="What to search the live web for.")
    max_results: int = Field(default=5, ge=1, le=10)


class WeatherRequest(BaseModel):
    location: str = Field(..., description="City or place name.")


class FetchRequest(BaseModel):
    url: str = Field(..., description="Absolute URL to fetch.")


NewsResponse = AgentResponse[NewsResult]
SearchResponse = AgentResponse[SearchResult]
WeatherResponse = AgentResponse[Weather]
FetchResponse = AgentResponse[WebPage]
