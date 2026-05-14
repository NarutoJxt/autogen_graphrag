from pathlib import Path

from rich import print
import chainlit as cl
from typing_extensions import Annotated
from chainlit.input_widget import (
   Select, Slider, Switch)
from autogen_core import CancellationToken
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient

import config as app_config
from utils.chainlit_agents import ChainlitUserProxyAgent
from graphrag.cli.query import run_global_search, run_local_search


def get_model_client():
    return OpenAIChatCompletionClient(
        model=app_config.CHAT_MODEL_DEEPSEEK,
        api_key=app_config.API_KEY_DEEPSEEK,
        base_url=app_config.BASE_URL_DEEPSEEK,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": ModelFamily.UNKNOWN,
            "structured_output": False,
        },
    )

@cl.on_chat_start
async def on_chat_start():
  try:
    settings = await cl.ChatSettings(
            [      
                Switch(id="Search_type", label="(GraphRAG) Local Search", initial=True),       
                Select(
                    id="Gen_type",
                    label="(GraphRAG) Content Type",
                    values=["prioritized list", "single paragraph", "multiple paragraphs", "multiple-page report"],
                    initial_index=1,
                ),          
                Slider(
                    id="Community",
                    label="(GraphRAG) Community Level",
                    initial=0,
                    min=0,
                    max=2,
                    step=1,
                ),

            ]
        ).send()

    response_type = settings["Gen_type"]
    community = settings["Community"]
    local_search = settings["Search_type"]
    
    cl.user_session.set("Gen_type", response_type)
    cl.user_session.set("Community", community)
    cl.user_session.set("Search_type", local_search)
    model_client = get_model_client()
    cl.user_session.set("model_client", model_client)

    user_proxy = ChainlitUserProxyAgent(
        name="User_Proxy",
        description="User Proxy Agent",
    )
    
    print("Set agents.")

    cl.user_session.set("Query Agent", user_proxy)

    msg = cl.Message(content=f"""Hello! What task would you like to get done today?      
                     """, 
                     author="User_Proxy")
    await msg.send()

    print("Message sent.")
    
  except Exception as e:
    print("Error: ", e)
    pass

@cl.on_settings_update
async def setup_agent(settings):
    response_type = settings["Gen_type"]
    community = settings["Community"]
    local_search = settings["Search_type"]
    cl.user_session.set("Gen_type", response_type)
    cl.user_session.set("Community", community)
    cl.user_session.set("Search_type", local_search)
    print("on_settings_update", settings)

@cl.on_message
async def run_conversation(message: cl.Message):
    print("Running conversation")
    INPUT_DIR = None
    ROOT_DIR = '.'    
    CONTEXT = message.content
    MAX_ITER = 10   
    RESPONSE_TYPE = cl.user_session.get("Gen_type")
    COMMUNITY = cl.user_session.get("Community")
    LOCAL_SEARCH = cl.user_session.get("Search_type")

    model_client = cl.user_session.get("model_client") or get_model_client()

    async def query_graphRAG(
        question: Annotated[str, "Query string containing information that you want from RAG search"],
    ) -> str:
        """Retrieve content for code generation and question answering using GraphRAG."""
        root = Path(ROOT_DIR)
        data_dir = Path(INPUT_DIR) if INPUT_DIR else None
        community = int(COMMUNITY) if COMMUNITY is not None else 0
        if LOCAL_SEARCH:
            print(LOCAL_SEARCH)
            out = run_local_search(
                data_dir,
                root,
                community,
                RESPONSE_TYPE,
                streaming=False,
                query=question,
                verbose=False,
            )
        else:
            out = run_global_search(
                data_dir,
                root,
                community,
                dynamic_community_selection=False,
                response_type=RESPONSE_TYPE,
                streaming=False,
                query=question,
                verbose=False,
            )
        result = out[0] if isinstance(out, tuple) else out
        await cl.Message(content=result).send()
        return result

    retriever = AssistantAgent(
        "Retriever",
        model_client,
        tools=[query_graphRAG],
        system_message=(
            "Use the query_graphRAG tool to retrieve knowledge-graph context before answering. "
            "When the user's question is answered, end with TERMINATE."
        ),
        description="Retriever Agent",
    )

    termination = TextMentionTermination("TERMINATE")
    # Single-agent team: avoids User_Proxy being selected next, which would open
    # Chainlit AskUserMessage ("Enter your response") instead of letting the assistant reply.
    team = RoundRobinGroupChat(
        [retriever],
        termination_condition=termination,
        max_turns=MAX_ITER,
    )

    token = CancellationToken()
    async for msg in team.run_stream(task=CONTEXT, cancellation_token=token):
        if isinstance(msg, TextMessage):
            await cl.Message(content=msg.content, author=msg.source).send()
        elif isinstance(msg, TaskResult):
            break
      
