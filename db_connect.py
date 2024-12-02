import streamlit as st
import mysql.connector


def connect_to_database():
    try:
        conn = mysql.connector.connect(
            host='pisa2022-db.ctoeaoqwkbat.us-east-1.rds.amazonaws.com',  
            port=3306,  # Default MySQL port
            user='admin',  # Replace with your RDS master username
            password='Owen01042545',  # Replace with your RDS master password
            database='pisa2022',  # Your database name
            connect_timeout=12000  # Optional: Increase connection timeout for slow connections
        )
        return conn
    except mysql.connector.Error as err:
        if err.errno == 1045:
            st.error("Access denied: Please check your username or password.")
        elif err.errno == 1049:
            st.error("Database not found: Please check the database name.")
        elif err.errno == 2003:
            st.error("Unable to connect to the database: Please check the host and port.")
        else:
            st.error(f"Error: {err}")
        return None

# def connect_to_database():
#     try:
#         conn = mysql.connector.connect(
#             host='localhost',
#             port='3306',
#             user='root',
#             password='Owen01042545',
#             database='pisa2022',
#             connect_timeout=12000
#         )
#         return conn
#     except mysql.connector.Error as err:
#         st.error(f"Error: Could not connect to the database. {err}")
#         return None

