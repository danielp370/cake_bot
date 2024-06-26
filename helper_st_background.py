import base64
import streamlit as st

def st_helper_set_background_img(bin_file, opacity=0.6, scale_mode='cover'):

    if bin_file == None:
        return

    # opacity between 0.0 and 1.0
    bin_file_ext = bin_file.split('.')[-1]

    st.markdown(
         f"""
         <style>
         .stApp {{
             background: linear-gradient(rgba(0,0,0,{opacity}),rgba(0,0,0,{opacity})),url(data:{bin_file_ext};base64,{base64.b64encode(open(bin_file, "rb").read()).decode()});
             background-size: {scale_mode};
             background-repeat: no-repeat;
             background-position: center;
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
