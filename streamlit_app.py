import streamlit as st
import psycopg2
import os

st.write("Has environment variables been set:",
	 os.environ["user"] == st.secrets["user"])

def init_connection():
	return psychopg2.connect(**st.secrets["postgres"])
