from typing import Optional

import chainlit as cl
from autogen_agentchat.agents import UserProxyAgent
from autogen_core import CancellationToken


async def ask_helper(func, **kwargs):
    res = await func(**kwargs).send()
    while not res:
        res = await func(**kwargs).send()
    return res


async def _chainlit_user_input(
    prompt: str, cancellation_token: Optional[CancellationToken] = None
) -> str:
    if prompt.startswith(
        "Provide feedback to chat_manager. Press enter to skip and use auto-reply"
    ):
        res = await ask_helper(
            cl.AskActionMessage,
            content="Continue or provide feedback?",
            actions=[
                cl.Action(name="continue", value="continue", label="✅ Continue"),
                cl.Action(name="feedback", value="feedback", label="💬 Provide feedback"),
                cl.Action(name="exit", value="exit", label="🔚 Exit Conversation"),
            ],
        )
        if res.get("value") == "continue":
            return ""
        if res.get("value") == "exit":
            return "exit"

    reply = await ask_helper(cl.AskUserMessage, content=prompt, timeout=60)
    return reply["output"].strip()


class ChainlitUserProxyAgent(UserProxyAgent):
    """User agent that collects input via Chainlit (AgentChat 0.4+)."""

    def __init__(self, name: str, *, description: str = "A human admin") -> None:
        super().__init__(name=name, description=description, input_func=_chainlit_user_input)
