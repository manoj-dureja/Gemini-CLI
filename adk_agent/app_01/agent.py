import os
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools import google_search

# We use the Gemini class but trick it into using the Vertex endpoint
custom_llm = Gemini(
    model="gemini-live-2.5-flash-native-audio",
    # This combination often forces the newer, stable v1beta1 endpoint
    api_version="v1beta1",
    vertexai=True
)

root_agent = Agent(
    name="fitness_agent",
    model=custom_llm,
    instruction="Fitness assistant for Manoj and Ratika. Use Google Search for news.",
    tools=[google_search]
)