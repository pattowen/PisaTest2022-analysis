import streamlit as st
import mysql.connector


def connect_to_database():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            port='3306',
            user='root',
            password='Owen01042545',
            database='pisa2022',
            connect_timeout=12000
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Error: Could not connect to the database. {err}")
        return None



