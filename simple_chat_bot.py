import streamlit as st
import uuid

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import JsonOutputParser

from langchain.schema import AIMessage, HumanMessage, SystemMessage

from langchain_core.tools import tool
from langchain_community.llms import Ollama


from llm_tools_manager import ToolManager, ToolReturn
from helper_ollama_http import get_ollama_model_names



# Tools

@tool
def multiply(first: int, second: int) -> int:
    """Multiply two integers together."""
    return first * second

@tool
def add(first: int, second: int) -> int:
    """Add two integers."""
    print('adding')
    return first + second

@tool
def converse(response: str) -> str:
    """Use this to respond conversationally.
       Respond conversationally if no other tools should be called for a given query."""
    return response



# Chat Program

purpose_prompt = "You are a helpful AI agent that loves math."
prompt_about_environment = """Our runtime is using streamlit on python, so use streamlit for rendering."""

def chat_chain_load(model, tool_manager):
    # We rely on global msgs for simplified debugging (needs cleanup imho)

    parser =  JsonOutputParser(return_exceptions=True)
    prompt = ChatPromptTemplate.from_messages(
        [("system", tool_manager.get_format_instructions()),
         ("system", parser.get_format_instructions()),
         ("system", prompt_about_environment),
         ("system", "{purpose_prompt}"),
         MessagesPlaceholder(variable_name="history"),
         ("user",   "{input}"),
         ])
    chain_front = prompt | model

    # Docs: https://api.python.langchain.com/en/latest/runnables/langchain_core.runnables.history.RunnableWithMessageHistory.html
    chain_with_history = RunnableWithMessageHistory(
        chain_front,
        lambda session_id: msgs,
        input_messages_key="input",
        history_messages_key="history",
        ) | parser | tool_manager.tool_chain
    return chain_with_history


def render_session_id(st, st_selector):

    # Set up a Session ID
    if 'session_list' not in st.session_state:
        st.session_state.session_id = uuid.uuid4()
        st.session_state.session_list = [st.session_state.session_id]

    session_id = st_selector.selectbox("Session ID", [st.session_state.session_id] + ["(new)"] + st.session_state.session_list)
    if session_id == "(new)":
        st.session_state.session_id = uuid.uuid4()
        st.session_state.session_list.append(st.session_state.session_id)
        st.rerun()

    return session_id


def render_chat_msg(st_chat, msg_type, content, additional_kwargs):
    ch_container = st_chat.chat_message(msg_type)
    ch_container.write(content)
    if additional_kwargs != None:
        for key, value in additional_kwargs.items():
            ch_container.write(value)


def render_chat_ai_private_note(response_str, additional_kwargs):
    """ Write the assistant a note about tools execution if it was (probably) successful but unknown to it."""
    global msgs

    response_str = str(response_str)
    if response_str.strip() == "" and len(additional_kwargs) != 0:
        msgs.add_message(AIMessage(content="{'private assistant note': tool executed successfully and return an object to user.'}"))


def render_chat_ai_callback(st_chat, response):
    global msgs

    additional_kwargs: dict = {}

    # response is of type str, or a ToolReturn
    if isinstance(response, ToolReturn):
        message = response.message
        if response.data != None:
            additional_kwargs = response.data
    else:
        message = response

    render_chat_ai_private_note(message, additional_kwargs)
    render_chat_msg(st_chat, "assistant", message, additional_kwargs)
    msgs.add_message(AIMessage(content=message, additional_kwargs=additional_kwargs))


def render_chat(st_chat_entry, st_chat):
    global msgs

    # Set up message history.
    msgs = StreamlitChatMessageHistory(key=f"langchain_messages-{session_id}")
    welcome_message = "How can I help you?"

    if len(msgs.messages) == 0:
        msgs.add_ai_message(welcome_message)

    # Render the chat history.
    # We add our tool calls to history so the AI can see them, but we strip them for our chat here.

    for msg in msgs.messages:
        print(f"MSG: {msg}")
        if msg.content.strip().startswith("Execution Attempt") and not display_tools_calls:
            continue
        # JSON Check if the message content begins with '{'
        elif not msg.content.strip().startswith('{') or display_tools_calls:
            render_chat_msg(st_chat, msg.type, msg.content, msg.additional_kwargs)

    # React to user input
    input = st_chat_entry.chat_input("What is up?")
    if input is not None and input != "":

        # Display user input and save to message history.
        st_chat.chat_message("user").write(input)

        # Invoke chain to get reponse.
        chain_config = {"configurable": {"session_id": session_id}}

        # We do a few re-tries and warn - if it triggers it is worth debugging why
        response = None
        for attempt in range(3):
            try:
                response = chain_with_history.invoke(
                    {'input': input,
                     'purpose_prompt': purpose_prompt },
                    chain_config)

                # Display AI assistant response and save to message history.
                render_chat_ai_callback(st_chat, response)

                break
            except Exception as e:
                # Feed error back to user display, and into chat history so LLM see it.
                error_str = f"Execution Attempt {attempt +1} failed, error: {e}"
                render_chat_ai_callback(st_chat, error_str)
                if attempt == 2:  # If the last attempt fails, raise the exception
                    st_chat.error("All attempts failed. Please try again later.")
                    raise


# main program

model_server_url = 'http://localhost:11434'
display_tools_calls = True

# Check if 'model_cache' is in the session state, and if not, initialize it.
if 'available_models' not in st.session_state:
    st.session_state.available_models =  get_ollama_model_names(model_server_url)
model_name = st.sidebar.selectbox("Choose a model", st.session_state.available_models)
print(f"Using model {model_name}")
model = Ollama(model=model_name, format='json', temperature=0.9,  num_predict=128)
tool_manager = ToolManager()

tools = [add, multiply, converse]
tool_manager.set_tool_settings({'default_tool': 'converse'})
tool_manager.load_tools(tools)

chain_with_history = chat_chain_load(model, tool_manager)

st.title("Chatbot with tools")
session_id = render_session_id(st, st.sidebar)

# Global message store for chat
msgs = {}
render_chat(st, st)


# Define the clear_cache function
def clear_cache():
    global msgs

    msgs.clear()
    st.rerun()

# Add the button to the sidebar
if st.sidebar.button("Clear message cache"):
    clear_cache()
