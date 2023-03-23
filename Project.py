# Om
# If any of the required modules are not installed - ask the user to install

import mysql.connector as connector
from st_on_hover_tabs import on_hover_tabs
from captcha.image import ImageCaptcha
import os
import sys
import random
import yfinance
from datetime import date, datetime, timedelta
from streamlit_echarts import st_echarts
import requests
import streamlit as st
from PIL import Image
import pandas
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver


# Connecting to database and creating required tables
mycon = connector.connect(**st.secrets["mysql"])
db = mycon.cursor()
# SQL giving error
# Configuring the page
st.set_page_config(
    page_title="Stock Market",
    layout="wide",
)


if 'page' not in st.session_state:
    st.session_state['page'] = 1

st.button("Hi")
