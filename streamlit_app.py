import streamlit as st
import psycopg2
import os

st.write("Has environment variables been set:",
	 os.environ["ALTOS_DB_USERNAME"] == st.secrets["ALTOS_DB_USERNAME"])

def init_connection():
	return psychopg2.connect(**st.secrets["postgres"])
