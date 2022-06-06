import streamlit as st
import os

st.write(
	"Has environment variables been set:",
	os.environ["ALTOS_DB_USERNAME"] == st.secrets["ALTOS_DB_USERNAME"])
