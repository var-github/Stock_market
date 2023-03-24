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
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
import selenium


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


# Function to check for internet connectivity
def internet():
    try:
        status = requests.get('https://www.google.com/').status_code
        return True
    except:
        return False


# Getting USD - INR conversion rates
def usd():
    if 'usd' not in st.session_state or not st.session_state['usd']:
        if internet():
            url = f'https://api.exchangerate.host/timeseries?base={"USD"}&start_date={date.today()}&end_date={date.today()}&symbols={"INR"}'
            data = requests.get(url).text
            st.session_state['usd'] = float(data[data.rfind('INR') + 5:-3])
            return st.session_state['usd']
        else:
            st.session_state['usd'] = ""
    else:
        return st.session_state['usd']
usd()


def get_price(company):
    company = company.strip('.NS')
    driver = st.session_state['driver']
    data = {}
    input_box = driver.find_element(By.CSS_SELECTOR, '.Ax4B8.ZAGvjd')
    input_box.send_keys(Keys.CONTROL + "a")
    input_box.send_keys(Keys.DELETE)
    input_box.send_keys(company)
    input_box.send_keys(Keys.RETURN)
    end = time.time() + 3
    while time.time() < end:
        try:
            sym1 = str(driver.current_url).strip("https://www.google.com/finance/quote/")
            sym1 = sym1[:sym1.find(":")]
            sym2 = driver.find_element(By.CSS_SELECTOR, '.Ax4B8.ZAGvjd').get_attribute("value").partition(' ')[2]
            if sym1 == sym2:
                data["Symbol"] = sym1
                break
        except:
            pass
        time.sleep(0.01)
    else:
        return None
    data["Name"] = driver.find_element(By.CSS_SELECTOR, 'c-wiz[aria-busy="false"] div.zzDege').text
    data['Price'] = driver.find_element(By.CSS_SELECTOR, 'c-wiz[aria-busy="false"] div.YMlKec.fxKbKc').text.replace(',', '')
    if data['Price'][0] == "₹":
        data['currency'] = 'INR'
        data['Price'] = round(float(data['Price'][1:].replace(',', ''))/usd(), ndigits=2)
    else:
        data['currency'] = ""
        data['Price'] = float(data['Price'][1:].replace(',', ''))
    data['Website'] = driver.find_element(By.CSS_SELECTOR, 'c-wiz[aria-busy="false"] .gyFHrc a[rel~="noopener"]').text
    return data


# Function to display captcha on screen
def captcha():
    if 'successful' not in st.session_state:
        st.session_state['successful'] = ""
    if 'captcha' not in st.session_state:
        st.session_state['captcha'] = ""
    title = column2.empty()
    title.header("CAPTCHA")
    file_path = "\\\\".join(str(__file__).split("\\")[:-1]) + "\\\\captcha.png"
    letters = "ACBDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    if not st.session_state['captcha']:
        image = ImageCaptcha(width=280, height=90)
        for i in range(7):
            st.session_state['captcha'] = st.session_state['captcha'] + random.choice(letters)
        st.session_state['captcha'] = st.session_state['captcha'].lower()
        data = image.generate(st.session_state['captcha'])
        image.write(st.session_state['captcha'], file_path)
    image = Image.open(file_path)
    img = column2.empty()
    img.image(image, width=550)
    txt = column2.empty()
    text = txt.text_input("Enter Captcha Code: ")
    text = text.lower()
    verify = column2.empty()
    if verify.button("Verify"):
        os.remove(file_path)
        if text == st.session_state['captcha']:
            img.empty()
            txt.empty()
            verify.empty()
            title.empty()
            st.session_state['successful'] = True
            return
        else:
            column2.text("Captcha failed!")
            img.empty()
            txt.empty()
            verify.empty()
            title.empty()
            st.session_state['successful'] = False
            return


# Initializing variables
if 'user' not in st.session_state:
    st.session_state['user'] = None
    options = webdriver.chrome.options.Options()
    options.add_argument("--headless=True")
    driver = webdriver.Chrome(service=selenium.webdriver.chrome.service.Service(ChromeDriverManager().install()), options=options)
    driver.get('https://www.google.com/finance/quote/TSLA:NASDAQ?hl=en')
    driver.implicitly_wait(2)
    st.session_state['driver'] = driver
if 'captcha' not in st.session_state:
    st.session_state['captcha'] = ""
if 'clicked' not in st.session_state:
    st.session_state['clicked'] = False
if 'company' not in st.session_state:
    st.session_state['company'] = ""
if 'shares' not in st.session_state:
    st.session_state['shares'] = 1
if 'successful' not in st.session_state:
    st.session_state['successful'] = ""
if 'warning' not in st.session_state:
    st.session_state['warning'] = 0
if 'stock' not in st.session_state:
    st.session_state['stock'] = "<select>"
if 'agree' not in st.session_state:
    st.session_state['agree'] = False
if 'name' not in st.session_state:
    st.session_state['name'] = ""
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'password' not in st.session_state:
    st.session_state['password'] = ""
if 'confirm' not in st.session_state:
    st.session_state['confirm'] = ""


# This function sets all the variables to their initiall state
def clear():
    st.session_state['captcha'] = ""
    st.session_state['clicked'] = False
    st.session_state['company'] = ""
    st.session_state['shares'] = 1
    st.session_state['successful'] = ""
    st.session_state['warning'] = 0
    st.session_state['stock'] = "<select>"


# The page is divided into 3 columns - the first column has only back button, column 2 has the rest of the data
column1, column2, column3 = st.columns([1, 3.5, 1])

column2.button("Hi")
