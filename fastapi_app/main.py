import os
import uuid
import docker
from typing import List, TypedDict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# --- Tool Definition: Secure C++ Code Executor ---
@tool
def cpp_code_executor(code: str):
    """
    Executes a given C++ code snippet and returns its standard output.
    The code is run inside a secure, isolated Docker container.
    The input code must be a complete, runnable C++ program.
    """
    client = docker.from_env()
    container_name = f"cpp-executor-{uuid.uuid4()}"

    dockerfile_content = """
    FROM gcc:latest
    WORKDIR /app
    COPY . .
    RUN g++ -o myapp main.cpp
    CMD ["./myapp"]
    """

    temp_dir = f"./temp_{container_name}"
    os.makedirs(temp_dir, exist_ok=True)

    with open(f"{temp_dir}/main.cpp", "w") as f:
        f.write(code)

    with open(f"{temp_dir}/Dockerfile", "w") as f:
        f.write(dockerfile_content)

    try:
        image, build_logs = client.images.build(path=temp_dir, tag=container_name, rm=True)
        container = client.containers.run(image.id, detach=False, name=container_name, remove=True)
        output = container.decode('utf-8')
        return f"Execution successful. Output:\n```\n{output}\n```"
    except docker.errors.BuildError as e:
        return f"Error during build: {e}"
    except docker.errors.ContainerError as e:
        return f"Error during execution: {e}"
    finally:
        # Clean up the temporary files and directory
        os.remove(f"{temp_dir}/main.cpp")
        os.remove(f"{temp_dir}/Dockerfile")
        os.rmdir(temp_dir)


tools = [cpp_code_executor]


# --- LangGraph State Definition ---
class GraphState(TypedDict):
    messages: List[BaseMessage]


# --- LangGraph Nodes ---
def call_model(state: GraphState):
    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0)
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def call_tool(state: GraphState):
    last_message = state["messages"][-1]
    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {"messages": [AIMessage(content="No tool to call.")]}

    tool_call = last_message.tool_calls[0]
    tool_name = tool_call["name"]

    tool_to_call = next((t for t in tools if t.name == tool_name), None)

    if not tool_to_call:
        return {"messages": [ToolMessage(content=f"Tool '{tool_name}' not found.", tool_call_id=tool_call["id"])]}

    result = tool_to_call.invoke(tool_call["args"])
    tool_message = ToolMessage(content=str(result), tool_call_id=tool_call["id"])
    return {"messages": [tool_message]}


# --- LangGraph Conditional Edges ---
def should_continue(state: GraphState):
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "call_tool"
    else:
        return END


# --- Build the Graph ---
workflow = StateGraph(GraphState)
workflow.add_node("call_model", call_model)
workflow.add_node("call_tool", call_tool)
workflow.set_entry_point("call_model")
workflow.add_conditional_edges(
    "call_model",
    should_continue,
    {"call_tool": "call_tool", END: END},
)
workflow.add_edge("call_tool", "call_model")
langgraph_app = workflow.compile()

# --- FastAPI Application Setup ---
app = FastAPI(
    title="LangGraph Chatbot Server",
    description="A FastAPI server for a LangGraph-powered chatbot.",
    version="1.0.0",
)


# Pydantic models for robust validation
class HistoryItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[HistoryItem]] = []


# Streaming function to interact with the LangGraph app
async def stream_events(request: ChatRequest):
    messages = []
    for item in request.history:
        if item.role == 'user':
            messages.append(HumanMessage(content=item.content))
        elif item.role == 'assistant':
            messages.append(AIMessage(content=item.content))

    messages.append(HumanMessage(content=request.message))

    async for event in langgraph_app.astream({"messages": messages}):
        if "call_model" in event:
            response_message = event["call_model"]["messages"][-1]
            if isinstance(response_message, AIMessage):
                yield response_message.content


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(stream_events(request), media_type="text/event-stream")


@app.get("/")
async def root():
    return {"status": "ok"}