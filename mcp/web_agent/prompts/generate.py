"""Generation prompts for web_agent's LLM-backed providers (gemma via NVIDIA).

The model cannot browse; each prompt asks for a best-effort answer from its own
knowledge and to flag uncertainty inside the text fields.
"""

NEWS_GEN = (
    "You are a news assistant. From your own knowledge (you cannot browse), list up to "
    "{limit} notable recent news items about '{query}'. For each item provide a headline "
    "(title), the likely source outlet (source), a plausible canonical URL (url), and a "
    "1-2 sentence summary. If you are unsure how current your knowledge is, say so in "
    "the summary. Set query to '{query}'."
)

WEATHER_GEN = (
    "You are a weather assistant without live data access. Give a best-effort, typical "
    "current weather estimate for {location}: temperature in Celsius (temperature_c), a "
    "short condition description (condition), and humidity percent (humidity_pct). "
    "Mention in condition that this is an estimate. Set location to '{location}'."
)

PAGE_GEN = (
    "You are a web page summarizer without live browsing. Based on your knowledge of the "
    "site and URL structure, describe the page at {url}: give its likely title (title) "
    "and a concise description of its likely content (text). State clearly in text that "
    "this is inferred, not fetched. Set url to '{url}'."
)
