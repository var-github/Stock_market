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
db.execute("create table if not exists users (user_id int primary key, username varchar(30) not null unique, password text not null, cash float(7, 2) default 10000.00, status varchar(8) default 'ENABLED');")
db.execute("create table if not exists transaction (user_id int, transaction_id int primary key, symbol varchar(15) not null, shares int not null, price float(7, 2) not null, transacted char(19));")


# Configuring the page
st.set_page_config(
    page_title="Stock Market",
    layout="wide",
)


if 'page' not in st.session_state:
    st.session_state['page'] = 1

# If admin account is not created, then admin account has to be created first
db.execute("SELECT username from users where user_id = 1;")
data = db.fetchall()
if not data:
    st.session_state['page'] = 10


if st.session_state['page'] in [1, 2, 4, 5, 6, 8, 10]:
    img = 'https://img.freepik.com/stock-market-forex-trading-graph-graphic-double-exposure_73426-193.jpg'
else:
    img = 'https://cdn.pixabay.com/photo/2018/01/12/16/16/growth-3078543_1280.png'

css = f"""
<style>
    section[data-testid='stSidebar'] {{
        top: -1%;
        background-color: #111;
        min-width:unset !important;
        width: unset !important;
    }}
    /* Hide close button on the streamlit navigation menu */
    button[kind="header"] {{
        display: none;
    }}
    /* The navigation menu */
    section[data-testid='stSidebar'] > div {{
        height: 120%;
        width: 75px;
        position: relative;
        top: 0;
        left: 0;
        background-color: #111;
        transition: 0.7s ease;
    }}
    /* The navigation menu on hover */
    section[data-testid='stSidebar'] > div:hover{{
        top: -10%;
        width: 270px;
    }}
    section[data-testid='stSidebar'] > div:hover img{{
        position: relative;
        transition: 0.7s ease;
        max-width: 80% !important;
        left: 10% !important;
    }}
    section[data-testid='stSidebar'] > div img{{
        position: relative;
        left: 10% !important;
        max-width: 100% !important;
        transition: 0.7s ease;
    }}
    #MainMenu {{
        visibility: hidden;
    }}
    button[title='View fullscreen'], a:not(a[target=_blank]), footer {{visibility: hidden;}}
    footer:after {{
        content:'Made with Streamlit'; 
        visibility: visible;
        display: block;
        position: relative;
        #background-color: red;
        padding: 3px;
        top: 1px;
    }}
    .stSpinner{{
        position: fixed;
        width: 40%;
        top: 45%;
        left: 45%;
    }}
    [data-testid="stAppViewContainer"] > .main {{
        background-image: url("{img}");
        background-repeat: no-repeat;
        background-size: 120%;
    }}
    [data-testid="stHeader"] {{
        display: none;
    }}
    #welcome {{
        color: lightyellow;
        font-size:50px;
        border-radius:2%
    }}
    table {{
        background-color: rgba(255, 255, 255, 0.3);
       -webkit-backdrop-filter: blur(4px);
       backdrop-filter: blur(4px);
    }}
    table > tbody > tr:nth-of-type(1) > td {{
        font-weight: bold;
        text-align: center! important;
        font-family: "Times New Roman", Times, serif;
    }}
    table > tbody > tr:nth-of-type(1) {{
        background: lightgrey;
    }}
    td {{
        text-align: center! important;
    }}
    th {{
        display: none;
    }}
    hr {{
        background-color: #00000040;
    }}
    iframe[title="streamlit_echarts.st_echarts"] {{
        position: relative;
        left: 185px;
        width: 800px;
        border: 1.5px solid;
        background: rgba(255, 255, 255, 0.62);
    }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

