import streamlit as st
from database import *
import pandas as pd



st.set_page_config(page_title="Pisa2022 Data Analysis Tool")
st.title("Data Vitualization")

result = view_all_data()
df=pd.DataFrame(result,columns=["CNT"])
st.dataframe(df)

st.sidebar.image(r"C:\1stApril\Work\4rd_Year\4rd2\CSS400_Project_Development\CN1-2023\pisa2022_analysis\StreamlitDev\image\PISA-Blog-Ilustración.png")


st.title("ONLINE PISA TEST2022 ANALYTICS DASHBOARD")

with open('style.css') as f: 
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html =True)



df = pd.read_csv(r'C:\1stApril\Work\4rd_Year\4rd2\CSS400_Project_Development\CN1-2023\pisa2022_analysis\StreamlitDev\pisa2022.csv')
