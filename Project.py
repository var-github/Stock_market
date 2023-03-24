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


st.button("Bye")
