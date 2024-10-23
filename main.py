import asyncio
import os
import uuid
from contextlib import contextmanager

import streamlit as st
from dotenv import load_dotenv
from lyzr_agent.agent import Agent
from lyzr_agent.environment import Environment
from lyzr_agent.feature import Feature
from lyzr_agent.llm.lyzr_llm import LyzrLLM
from lyzr_agent.modules.types import FeatureType
from lyzr_agent.tools.perplexity_tool.index import perplexity_tool
from pymongo import MongoClient

load_dotenv()

from tools import duckduckgo_search_tool

client = MongoClient("mongodb://localhost:27017/")
db = client["agent"]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


def init_agent():
    openai_llm_config = {
        "provider": "openai",
        "model": "gpt-4o",
        "config": {"temperature": 0.2, "top_p": 0.9},
        "env": {"OPENAI_API_KEY": OPENAI_API_KEY},
    }

    env = Environment(
        features=[
            Feature(
                type=FeatureType.SHORT_TERM_MEMORY,
            ),
            Feature(type=FeatureType.TOOL_CALLING, config={"max_tries": 3}),
        ],
        tools=[
            perplexity_tool(
                api_key=PERPLEXITY_API_KEY,
                model="llama-3.1-sonar-small-128k-online",
            ),
            duckduckgo_search_tool,
        ],
        llm=LyzrLLM(openai_llm_config),
        db_client=db,
    )

    agent = Agent(
        env=env,
        system_prompt="""You are an intelligent location mapping agent. You will be given a title and description of a place. Your task is to find the latitude and loongitude of the place.
        1. Use the perplexity tool to search for the place and get its coordinates.
        2. Use the duckduckgo_search tool to search for the place and get its coordinates and cross-verify the results with the perplexity tool.
        3. If the duckduckgo_search tool does not return any results, return "I could not find the place."
        4. If you find the place, return the coordinates in the format "latitude, longitude".
        5. If the place is not accurate, return "I could not find the place."
        Make sure the place is accurate by checking the description and title. Use the tools to get the coordinates of the place and verify the place with the description and title.

        Output format:
        LATITUDE, LONGITUDE
    """,
        name="jaunt bot",
    )

    return agent


if "agent" not in st.session_state:
    st.session_state.agent = init_agent()

    # Initialize the agent
agent = st.session_state.agent


st.title("Jaunt App")

st.markdown(
    """1. Search title in perplexity
2. Search title in duckduckgo
3. Cross verify the results
4. If the place is not accurate, return "I could not find the place."
5. If the place is accurate, return the coordinates in the format "latitude, longitude".
"""
)

# st.header("Title")
# title = st.text_input("Enter the title of the place")

# st.header("Description")
# description = st.text_area("Enter the description of the place")


@contextmanager
def get_event_loop():
    """Safely manage event loop lifecycle."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        loop.close()


async def process_coordinates(title: str, description: str, agent) -> list:
    """Handle the async processing of coordinates."""
    user_id = "user1"  # Consider making this dynamic or from configuration
    session_id = str(uuid.uuid4().hex)
    new_input = f"title: {title} description: {description}"
    messages = [{"role": "user", "content": new_input}]

    return await agent.chat(user_id=user_id, session_id=session_id, messages=messages)


def handle_coordinate_search():
    """Main handler for the coordinate search button."""
    if not (title := st.session_state.get("title")):
        st.error("Please enter a title")
        return

    if not (description := st.session_state.get("description")):
        st.error("Please enter a description")
        return

    with get_event_loop() as loop:
        try:
            messages = loop.run_until_complete(
                process_coordinates(title, description, agent)
            )
            st.write(messages[-1]["content"])
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")


st.text_input("Title", key="title")
st.text_area("Description", key="description")
if st.button("Find Coordinates"):
    handle_coordinate_search()
    # if title and description:
    #     user_id = "user1"
    #     session_id = str(uuid.uuid4().hex)
    #     messages = []

    #     # Create a new thread for the async function
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)

    #     # Run the async function in the new thread
    #     try:
    #         new_input = "title: " + title + " description: " + description
    #         # Add the user's message to the messages list
    #         messages.append({"role": "user", "content": new_input})
    #         messages = loop.run_until_complete(
    #             agent.chat(
    #                 user_id=user_id,
    #                 session_id=session_id,
    #                 messages=messages,
    #             )
    #         )
    #         st.write(messages[-1]["content"])
    #     except Exception as e:
    #         st.write(e)
    #     finally:
    #         # Close the event loop to free up resources
    #         loop.close()
    # else:
    #     st.write("Please enter a title and description")
