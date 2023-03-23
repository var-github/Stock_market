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
"""
from geopy.geocoders import Nominatim
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
"""

# Connecting to database and creating required tables
mycon = connector.connect(host="sql12.freemysqlhosting.net", user="sql12608034", password="G47UQim29M", database="sql12608034", port=3306)
st.button("Hi")
