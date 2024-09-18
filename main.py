import streamlit as st
from dashboard import *



def main():
    
    st.set_page_config(
        page_title="Pisa2022 Analysis tool",
        page_icon="🌎",
        initial_sidebar_state="expanded",
    )
    st.sidebar.image(r'C:\1stApril\Work\4rd_Year\4rd2\CSS400_Project_Development\CN1-2023\pisa2022_analysis\StreamlitDev\image\PISA-Blog-Ilustración.png')
    with st.sidebar: page = option_menu(
        menu_title="Main Menu",
        options=["Home","Analytics"],
        menu_icon=["cast"],
        icons=["house","file-earmark-bar-graph"],
        default_index=0
    )
    if page == "Home":
        home_page()
    if page == "Analytics":
        analytics_page()






if __name__ == '__main__':
    main()
