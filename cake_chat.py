import streamlit as st
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from llm_tools_manager import ToolReturn
from llm_model_cache import ModelCache
from my_tool_calls import my_tools_init, my_tools_get_option_keys
from helper_st_background import st_helper_set_background_img
from helper_st_tool_options import render_options, load_options
from helper_st_tool_options import auto_prompt_isset, auto_prompt_set
from config import Config


prompt_about_environment = """Our runtime is using streamlit on python, so use streamlit for rendering. Mathplotlib is available. If software is missing, stop and ask me to install it using pip."""

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


def render_chat(st_chat_entry, st_chat, st_visuals):
    global msgs
    global config

    # Set up message history.
    msgs = StreamlitChatMessageHistory(key=f"langchain_messages-{session_id}")
    welcome_message = config.get_value_by_key('chat', 'initial_ai_welcome_prompt',
                                              "How can I help you?")
    if len(msgs.messages) == 0:
        if model_cache.settings_cache.get('auto_prompt_at_start', True):
            auto_prompt_set(1, True)
        else:
            msgs.add_ai_message(welcome_message)

    # Render the chat history.
    # We add our tool calls to history so the AI can see them, but we strip them for our chat here.
    display_tools_calls = model_cache.settings_cache.get('display_tools_calls', False)
    for msg in msgs.messages:
        print(f"MSG: {msg}")
        if msg.content.strip().startswith("Execution Attempt") and not display_tools_calls:
            continue
        # JSON Check if the message content begins with '{'
        elif not msg.content.strip().startswith('{') or display_tools_calls:
            render_chat_ai_new_container(st_chat, st_visuals, msg.type)
            render_chat_msg(msg.type, msg.content, msg.additional_kwargs)

    # React to user input
    input = st_chat_entry.chat_input(config.get_value_by_key('chat', 'chat_input_label', "What is up?"))
    if input is not None or auto_prompt_isset():

        # Display user input and save to message history.
        if input != None:
            st_chat.chat_message("user").write(input)
        else:
            input=""
        #msgs.add_user_message(input)

        # Invoke chain to get reponse.
        chain_config = {"configurable": {"session_id": session_id}}

        render_chat_ai_new_container(st_chat, st_visuals, "assistant")
        
        # We do a few re-tries and warn - if it triggers it is worth debugging why
        response = None
        for attempt in range(3):
            try:
                response = chain_with_history.invoke(
                    {'input': input,
                     'purpose_prompt': config.get_value_by_key('chat', 'purpose_prompt') },
                    chain_config)

                # Display AI assistant response and save to message history.
                render_chat_ai_callback(response)

                break
            except Exception as e:
                # Feed error back to user display, and into chat history so LLM see it.
                error_str = f"Execution Attempt {attempt +1} failed, error: {e}"
                render_chat_ai_callback(error_str)
                if attempt == 2:  # If the last attempt fails, raise the exception
                    st_chat.error("All attempts failed. Please try again later.")
                    raise

st_chat_ai_chat_container    = None
st_chat_ai_visuals_container = None

def render_chat_ai_new_container(st_chat, st_visuals, msg_type):
    """ Get our new (/secondary) container to write visuals to.
        Depending on preferences user may just want this in the main chat container."""

    global st_chat_ai_chat_container
    global st_chat_ai_visuals_container

    # disabled so we dont sit with a blank chat msg while waiting for a response
    #st_chat_ai_chat_container = st_chat.chat_message(msg_type)
    st_chat_ai_visuals_container = st_visuals

    return st_chat_ai_chat_container


def render_chat_msg(msg_type, content, additional_kwargs):
    visuals_container = st_chat_ai_visuals_container
    
    if content != None and content != "":
        st_chat_ai_chat_container = st_chat.chat_message(msg_type)

        ch_container = st_chat_ai_chat_container

        ch_container.write(content)
    if additional_kwargs != None:
        for key, value in additional_kwargs.items():
            #visuals_container.write(key)
            visuals_container.write(value)

def render_chat_ai_private_note(response_str, additional_kwargs):
    """ Write the assistant a note about tools execution if it was (probably) successful but unknown to it."""
    global msgs

    response_str = str(response_str)
    if response_str.strip() == "" and len(additional_kwargs) != 0:
        msgs.add_message(AIMessage(content="{'private assistant note': tool executed successfully and return an object to user.'}"))

def render_chat_ai_callback(response):
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
    render_chat_msg("assistant", message, additional_kwargs)
    msgs.add_message(AIMessage(content=message, additional_kwargs=additional_kwargs))


# Load config and set up state
config = Config('resources/cake_tool_bot/config.ini')

# Check if 'model_cache' is in the session state, and if not, initialize it.
if 'model_cache' not in st.session_state:
    st.session_state.model_cache = ModelCache(config)
model_cache: ModelCache = st.session_state.model_cache
model, tool_manager = model_cache.load_model(model_cache.current_model_name)

load_options(model_cache, keys=my_tools_get_option_keys())
chat_options = [('chat_objects_inline', 'Render objects in chat'),
                ('auto_prompt_at_start', 'Automatic prompt at start'),
                ('auto_prompt', 'Automatic prompting for follow up'),
                ('display_tools_calls', 'Display calls'),]
load_options(model_cache, keys=chat_options)
my_tools_init(tool_manager, model_cache)

chain_with_history = chat_chain_load(model, tool_manager)

st.set_page_config(page_title = config.get_value_by_key('ui', 'page_title'),
                   page_icon  = config.get_value_by_key('ui', 'page_icon'),
                   layout = config.get_value_by_key('ui', 'page_layout', "centered"),
                   initial_sidebar_state="auto", menu_items=None)

st_helper_set_background_img(config.get_value_by_key('ui', 'page_background_image', None),
                             0.6, 'contain')

st.title(config.get_value_by_key('chat_ui', 'window_name', "Chatbot with tools"))

session_id = render_session_id(st, st.sidebar)

# Global message store for chat
msgs = {}
model_cache.settings_cache.set({'chat_ai_callback': render_chat_ai_callback})

if model_cache.settings_cache.get('chat_objects_inline', False) == False:
    st_chat, st_visuals = st.columns([2,1], vertical_alignment="bottom")
else:
    st_chat    = st.container()
    st_visuals = st_chat

render_chat(st, st_chat, st_visuals)

def on_model_change(key):
    model_cache.current_model_name = st.session_state[key]

# Sidebar for model selection
model_cache.current_model_name = st.sidebar.selectbox("Choose a model", [model_cache.current_model_name] + model_cache.available_models, key='model_name', args='model_name')
print(f"MODEL NAME is {model_cache.current_model_name}")

# Define the clear_cache function
def clear_cache():
    global msgs

    msgs.clear()
    st.rerun()

# Add the button to the sidebar
if st.sidebar.button("Clear message cache"):
    clear_cache()
st_options_extra = st.sidebar.expander("Extra Options", expanded=True)
render_options(model_cache, st, st_options_extra, keys=my_tools_get_option_keys())
render_options(model_cache, st, st_options_extra, keys=chat_options)
