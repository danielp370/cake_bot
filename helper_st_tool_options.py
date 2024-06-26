from llm_tools_manager import ToolManager
import streamlit as st

def load_tool_options(tool_manager, keys):
    for key in keys:
        if key[0] not in st.session_state:
            value = tool_manager.config.get_boolean_by_key('my_tools', key[0], False)
            st.session_state[key[0]] = value
        tool_manager.set_tool_settings({key[0]: st.session_state[key[0]]})


def render_tool_options(tool_manager, st, st_settings_container, keys):
    # Expose options to streamlit settings

    def create_checkbox(key):
        def on_checkbox_change():
            value = st.session_state[key[0]]
            print(f"Checkbox '{key}' now {value}")
            tool_manager.set_tool_settings({key[0]: value})

        if key[0] not in st.session_state:
            value = tool_manager.config.get_boolean_by_key('my_tools', key[0], False)
            st.session_state[key[0]] = value
        tool_manager.set_tool_settings({key[0]: st.session_state[key[0]]})
        st_settings_container.checkbox(key[1], key=key[0], on_change=on_checkbox_change)

    for key in keys:
        create_checkbox(key)


@st.experimental_dialog("Confirm Unsafe Execution")
def helper_unsafe_user_dialog(content, execute_function, callback):

    st.write(f"Please confirm the following is ok to execute:")
    st.code(content);

    def on_click_allow(content):
        response = callback(execute_function, content, None)

    def on_click_deny():
        callback(execute_function, None, "User denied execution")

    col1, col2 = st.columns([1, 1])

    if col1.button(":green[Allow]", on_click=on_click_allow, args=[content]) or \
        col2.button(":red[Deny]", on_click=on_click_deny):
        # rerun should re-render without the dialog
        st.rerun()

    return None

# automatic re-prompting kicker
def auto_prompt_isset():
    if 'auto_prompt_count' not in st.session_state:
        st.session_state.auto_prompt_count = -1

    st.session_state.auto_prompt_count = st.session_state.auto_prompt_count - 1

    if st.session_state.auto_prompt_count <= 0:
        return False
    return True

def auto_prompt_set(tries, clear=False):
    # Only sets if there is not already one underway (must be -1 or less).
    if 'auto_prompt_count' not in st.session_state:
        st.session_state.auto_prompt_count = -1

    if st.session_state.auto_prompt_count < 0 or clear == True:
        st.session_state.auto_prompt_count = tries
