import streamlit as st
import mysql.connector
from sqlalchemy import create_engine

# MySQL connection
conn = mysql.connector.connect(
    host='localhost',
    port='3306',
    user='root',
    password='Owen01042545',
    database='pisa2022',
    connect_timeout=12000
)
cursor = conn.cursor()

##fetch
def view_all_data():
    cursor.execute('select CNT from pisa2022_data order by CNT asc' )
    data=cursor.fetchall()
    return data



