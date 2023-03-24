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


if st.session_state['page'] in [1, 2, 4, 5, 6, 8]:
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


# This function displays all the stocks the user owns
def portfolio():
    column2.title("PORTFOLIO")
    db.execute(f"select symbol, sum(shares) from transaction where user_id = {st.session_state['user']} group by symbol having sum(shares) != 0;")
    data = db.fetchall()
    if not data:
        column2.warning("You currently have not invested in any stocks")
        st.stop()
    with st.spinner("Loading..."):
        if internet():
            sum = 0
            for i in range(len(data)):
                info = get_price(data[i][0])
                price = info['Price']
                sum += price * int(data[i][1])
                data[i] = data[i] + (price,)
            data = [("Symbol", "Shares", "Current Price")] + data
        else:
            data = [("Symbol", "Shares")] + data
    column2.table(data)
    if internet():
        column2.text("Total: $" + str(round(sum, ndigits=2)))
    db.execute(f"select cash from users where user_id = {st.session_state['user']};")
    cash = db.fetchall()[0][0]
    column2.text("Cash left in account: $" + str(cash))
    if internet():
        if cash + sum > 10000:
            column2.text("Profit: $" + str(round(cash + sum - 10000, ndigits=2)))
        elif cash + sum < 10000:
            column2.text("Loss: $" + str(round(10000 - (cash + sum), ndigits=2)))
        column2.subheader("YOUR net worth: $" + str(round(cash + sum, ndigits=2)))
    else:
        column2.warning("No internet connection! To view current prices of the stocks - please connect to the internet and refresh the page.")


# Displays price and other required information on any stock entered by the user
def quote():
    column2.title("QUOTE")
    company = column2.text_input("Enter stock symbol or company name: ")
    if column2.button(label="Quote"):
        if not internet():
            column2.warning("No internet connection! Hence current prices cannot be retrieved. Please connect to the internet and refresh the page.")
            st.stop()
        data = get_price(company)
        if data:
            column2.write("Company name: " + str(data["Name"]))
            column2.write("Stock symbol: " + str(data["Symbol"]))
            column2.write("Market price: $" + str(data["Price"]))
            date = []
            value = []
            if data["currency"] == "INR":
                graph = dict(yfinance.download(data['Symbol'] + '.NS', start=str(datetime.now() - timedelta(days=3 * 365))[:10], end=str(datetime.now())[:10])['Open'])
                for i in graph:
                    date.append(str(i.strftime("%x")))
                    value.append(round(graph[i] / usd(), ndigits=2))
            else:
                graph = dict(yfinance.download(data['Symbol'], start=str(datetime.now() - timedelta(days=3 * 365))[:10], end=str(datetime.now())[:10])['Open'])
                for i in graph:
                    date.append(str(i.strftime("%x")))
                    value.append(round(graph[i], ndigits=2))
            if value:
                options = {"height": 300, "tooltip": {"trigger": 'axis'}, "xAxis": {"data": date}, "yAxis": {"type":"value", "axisLine": {"show": True }, "splitLine": {"show": False}}, "series": [{"data": value, "type": 'line'}]}
                st_echarts(options=options)
            if data['Website']:
                col1, col2, col3 = st.columns([1, 4.5, 1])
                col2.write("Website: [" + str(data["Website"]) + "](" + str(data["Website"]) + ")")
        else:
            column2.warning("No stock or company exists with that name!")
            st.stop()


def buy():
    global column2
    column2.title("BUY SHARES")
    db.execute(f"SELECT cash from users where user_id = {st.session_state['user']};")
    cash = db.fetchall()
    if cash[0][0] < 100:
        column2.warning("Low Balance!, Your balance is below 100 so you cannot buy any more shares!")
        st.stop()
    name = column2.empty()
    st.session_state['company'] = name.text_input("Enter stock symbol or company name: ", value=st.session_state['company'], key=1)
    num = column2.empty()
    st.session_state['shares'] = num.number_input("Enter the number of shares to be bought: ", min_value=1, value=st.session_state['shares'], max_value=100000, key=2)
    btn = column2.empty()
    war = column2.empty()
    if st.session_state['warning'] == 1:
        war.warning("No stock or company exists with that name!")
    if st.session_state['warning'] == 2:
        war.warning("Not enough money to buy " + str(st.session_state['shares']) + " shares of " + st.session_state['company'] + ". Investment is prohibited!")
    if btn.button("Buy", key=3):
        war.empty()
        st.session_state['warning'] = 0
        st.session_state['clicked'] = True
    if st.session_state['clicked']:
        if not internet():
            column2.warning("No internet connection! Hence current prices cannot be retrieved. Please connect to the internet and refresh the page.")
            st.session_state['clicked'] = False
            st.stop()
        company = st.session_state['company']
        shares = st.session_state['shares']
        btn.empty()
        name.text_input("Enter stock symbol or company name: ", disabled=True, value=company)
        num.number_input("Enter the number of shares to be bought: ", disabled=True, value=shares)
        data = get_price(company)
        column2.text("")
        if data:
            column2.text("Company name: " + str(data["Name"]))
            column2.text("Stock symbol: " + str(data["Symbol"]))
            column2.text("Market price: $" + str(data["Price"]))
        else:
            st.session_state['clicked'] = False
            st.session_state['warning'] = 1
            st.experimental_rerun()
        price = shares * data["Price"]
        if cash[0][0] - price < 0:
            st.session_state['clicked'] = False
            st.session_state['warning'] = 2
            st.experimental_rerun()
        column2.text("You will be paying an amount of: $" + str(round(price, ndigits=2)))
        column2.text("")
        var1 = column2.empty()
        var1.markdown("-----------------------------------------------------------------------------")
        var2 = st.empty()
        col1, col2 = var2.columns([4.8, 10])
        col2.write("Do you want to continue with the transaction?")
        var3 = st.empty()
        col3, col4, col5, col6 = var3.columns([8, 1.1, 1, 9])
        var4 = col4.empty()
        var5 = col5.empty()
        if var4.button("Yes", key=13) or st.session_state['successful'] in [True, False, "run"]:
            st.session_state['successful'] = "run"
            var1.empty()
            var2.empty()
            var4.empty()
            column1, column2, column3 = st.columns([1, 4.5, 1])
            captcha()
            if st.session_state['successful'] == True:
                db.execute(f"update users set cash = cash - {price} where user_id = {st.session_state['user']};")
                db.execute("select transaction_id from transaction")
                trans = db.fetchall()
                trans_id = random.randint(10000, 99999)
                while trans_id in trans:
                    trans_id = random.randint(10000, 99999)
                column2.markdown("-----------------------------------------------------------------------------")
                column2.subheader("Price of $" + str(round(price, ndigits=2)) + " has been deducted from your account   Transaction ID: " + str(trans_id))
                column2.markdown("-----------------------------------------------------------------------------")
                date_time = str(datetime.now())[:19]
                db.execute(f"insert into transaction values({st.session_state['user']}, {trans_id}, '{data['Symbol']}',{shares},{data['Price']},'{date_time}');")
                mycon.commit()
                column2.text("Thank you for investing")
                st.session_state['tab'] = "Portfolio"
                st.stop()
            elif st.session_state['successful'] == False:
                column2.warning("Transaction discarded!")
                st.session_state['captcha'] = ""
                st.session_state['successful'] = ""
                st.session_state['company'] = ""
                st.session_state['shares'] = 1
                st.session_state['clicked'] = False
                st.session_state['tab'] = "Portfolio"
                st.stop()
        if st.session_state['successful'] not in [True, False, "run"]:
            if var5.button("No", key=14):
                var1.empty()
                var2.empty()
                var4.empty()
                var5.empty()
                st.session_state['captcha'] = ""
                st.session_state['successful'] = ""
                st.session_state['company'] = ""
                st.session_state['shares'] = 1
                st.session_state['clicked'] = False
                column2.warning("Transaction discontinued!")
                st.session_state['tab'] = "Portfolio"
                st.stop()
            col7, col8, col9 = st.columns([1, 4.5, 1])
            col8.markdown("-----------------------------------------------------------------------------")
    


def sell():
    global column2
    column2.title("SELL SHARES")
    db.execute(f"SELECT symbol from transaction where user_id = {st.session_state['user']} group by symbol having sum(shares) != 0;")
    data = db.fetchall()
    for i in range(len(data)):
        data[i] = data[i][0]
    data = ['<select>'] + data
    name = column2.empty()
    st.session_state['stock'] = name.selectbox("Choose a stock to sell:", data, index=data.index(st.session_state['stock']), key=1)
    num = column2.empty()
    st.session_state['shares'] = num.number_input("Enter the number of shares to be sold: ", min_value=1, value=st.session_state['shares'], max_value=100000, key=2)
    btn = column2.empty()
    if btn.button("Sell") and st.session_state['stock'] != '<select>':
        st.session_state['clicked'] = True
    if st.session_state['clicked']:
        shares = st.session_state['shares']
        stock = st.session_state['stock']
        if not internet():
            column2.warning("No internet connection! Hence current prices cannot be retrieved. Please connect to the internet and refresh the page.")
            st.session_state['clicked'] = False
            st.stop()
        db.execute(f"SELECT sum(shares) from transaction where user_id = {st.session_state['user']} and symbol = '{stock}' group by symbol;")
        shares_owned = db.fetchall()[0][0]
        if shares > shares_owned:
            column2.warning("You own only " + str(shares_owned) + " shares of " + stock + ", you cannot sell " + str(shares) + " shares!")
            st.stop()
        name.selectbox("Choose a stock to sell:", data, index=data.index(stock), disabled=True, key=3)
        num.number_input("Enter the number of shares to be sold: ", disabled=True, value=shares, key=4)
        btn.empty()
        data = get_price(stock)
        price = round(int(shares) * data["Price"], ndigits=2)
        column2.text("")
        column2.subheader("Transaction INFO")
        column2.text("Symbol: " + str(data["Symbol"]))
        column2.text("Company: " + str(data["Name"]))
        column2.text("You own: " + str(shares_owned) + " share(s)")
        column2.text("Current Price: " + str(data["Price"]))
        column2.text("")
        column2.text("You are selling " + str(shares) + " share(s) and will be gaining an amount of $" + str(round(price, ndigits=2)))
        column2.text("")
        var1 = column2.empty()
        var1.markdown("-----------------------------------------------------------------------------")
        var2 = st.empty()
        col1, col2 = var2.columns([4.8, 10])
        col2.write("Do you want to continue with the transaction?")
        var3 = st.empty()
        col3, col4, col5, col6 = var3.columns([8, 1, 1, 9])
        var4 = col4.empty()
        var5 = col5.empty()
        if var4.button("Yes") or st.session_state['successful'] in [True, False, "run"]:
            st.session_state['successful'] = "run"
            var1.empty()
            var2.empty()
            var4.empty()
            column1, column2, column3 = st.columns([1, 4.5, 1])
            captcha()
            if st.session_state['successful'] == True:
                db.execute(f"update users set cash = cash + {price} where user_id = {st.session_state['user']};")
                db.execute("select transaction_id from transaction;")
                trans = db.fetchall()
                trans_id = random.randint(10000, 99999)
                while trans_id in trans:
                    trans_id = random.randint(10000, 99999)
                column2.markdown("-----------------------------------------------------------------------------")
                col7, col8, col9 = st.columns([1, 4.5, 1.1])
                col8.subheader("Price of $" + str(price) + " has been added to your account    Transaction ID: " + str(trans_id))
                col10, col11, col12 = st.columns([1, 4.5, 1])
                col11.markdown("-----------------------------------------------------------------------------")
                date_time = str(datetime.now())[:19]
                shares *= -1
                db.execute(f"insert into transaction values({st.session_state['user']}, {trans_id}, '{stock}',{shares},{data['Price']},'{date_time}');")
                col11.text("Thank you for investing")
                mycon.commit()
                st.session_state['tab'] = "Portfolio"
                st.stop()
            elif st.session_state['successful'] == False:
                column2.warning("Transaction discarded!")
                st.session_state['captcha'] = ""
                st.session_state['successful'] = ""
                st.session_state['stock'] = "<select>"
                st.session_state['shares'] = 1
                st.session_state['clicked'] = False
                st.session_state['tab'] = "Portfolio"
                st.stop()
        if st.session_state['successful'] not in [True, False, "run"]:
            if var5.button("No"):
                var1.empty()
                var2.empty()
                var4.empty()
                var5.empty()
                st.session_state['clicked'] = False
                column2.warning("Transaction discontinued!")
                st.session_state['tab'] = "Portfolio"
                st.stop()
            col7, col8, col9 = st.columns([1, 4.5, 1])
            col8.markdown("-----------------------------------------------------------------------------")



def transactions():
    column2.title("Your Transactions")
    db.execute(f'select transaction_id, symbol, shares, price, ABS(shares) * price, transacted from transaction where user_id = {st.session_state["user"]} order by transacted desc;')
    data = db.fetchall()
    if not data:
        column2.warning("No transactions have taken place!")
        st.stop()
    data = [("Transaction ID", "Symbol", "Shares", "Price ($)", "Total price ($)", "Transaction Date")] + data
    column2.table(data)


# MAIN CODE
# Every page is a separete if block, the variable - st.session_state['page'] - moniters which page is currently displayed
if st.session_state['page'] == 1:
    column1, column2, column3 = st.columns([1, 4.5, 1])
    home_page = """
    <p style="position: absolute; color: lightblack; font-size:24px; left: 15.4%; padding-right:15.4%">
        <b>
            Welcome to Omni-Stocks, a website equiped with a verstalie real-life platform for 
            comencing investments. The money being utilised is NOT REAL and has no effect on the 
            actual market. Our website allows users to invest in both NASDAQ and NSE. A wide range 
            of real-time data and analytics is available on our website. Enjoy your experience
        </b>
    </p>
    """
    st.markdown(home_page, unsafe_allow_html=True)
    st.sidebar.image("https://app.omnistock.io/uploads/logo/yktS4FqNbQGn3TychVaEzDIkHoiJa4Ei5HPSAIAy.png")
    st.sidebar.caption("")
    st.sidebar.caption("")
    column2.header("WELCOME", anchor="welcome")
    with st.sidebar:
        current_tab = on_hover_tabs(tabName=['Home','Login', 'Register', 'Admin','Contact Us','Help'], iconName=['home','account_circle','economy','dashboard','phone','help_center'], styles = {'tabOptionsStyle': {':hover :hover': {'color': 'blue'}}}, key=105, default_choice=0)
        if current_tab =='Login':
            st.session_state['page'] = 6
            st.experimental_rerun()
        elif current_tab == 'Register':
            st.session_state['page'] = 8
            st.experimental_rerun()
        elif current_tab == 'Admin':
            st.session_state['page'] = 2
            st.experimental_rerun()
        elif current_tab == 'Help':
            st.session_state['page'] = 5
            st.experimental_rerun()


# Admin login page
elif st.session_state['page'] == 2:
    column2.header("ADMIN")
    column1.text("")
    if column1.button(label="🔙"):
        st.session_state['page'] = 1
        st.experimental_rerun()
    form = column2.form()
    username = form.text_input('Username')
    password = form.text_input('Password', type="password")
    if form.form_submit_button(label="Login"):
        db.execute("SELECT username, password from users where user_id = 1;")
        data = db.fetchall()
        if username != data[0][0]:
            column2.warning('Wrong username')
            st.stop()
        if password != data[0][1]:
            column2.warning("Wrong password")
            st.stop()
        st.session_state['page'] = 3
        st.experimental_rerun()


# Admin page
elif st.session_state['page'] == 3:
    column1, column2, column3 = st.columns([1, 4.5, 1])
    st.sidebar.image("https://app.omnistock.io/uploads/logo/yktS4FqNbQGn3TychVaEzDIkHoiJa4Ei5HPSAIAy.png")
    st.sidebar.caption("")
    st.sidebar.caption("")
    main = st.empty()
    table = st.empty()
    with st.sidebar:
        current_tab = on_hover_tabs(tabName=['View Users','Transactions', 'Logout'], iconName=['group','credit_card','logout'], styles = {'tabOptionsStyle': {':hover :hover': {'color': 'blue'}}}, key=101, default_choice=0)
        if current_tab == "View Users":
            users = []
            db.execute("select * from users where not user_id = 1;")
            data = db.fetchall()
            for i in data:
                users += [i[1]]
            col1, col2, col3, col4 = main.columns([1.15, 3, 1, 1.1])
            col2.header("Admin")
            disable = col2.multiselect('Select users to disable / enable:', users)
            for i in range(7):
                col3.text("")
            if col3.button(label="DISABLE / ENABLE"):
                for i in disable:
                    db.execute(f'select status from users where username = "{i}"')
                    if db.fetchall()[0][0] == "ENABLED":
                        db.execute(f'update users set status = "DISABLED" where username = "{i}"')
                    else:
                        db.execute(f'update users set status = "ENABLED" where username = "{i}"')
                mycon.commit()
                st.experimental_rerun()
            data = [("User ID", "Username", "Password", "Cash", "Status")] + data
            col5, col6, col7 = table.columns([1, 3.5, 1])
            col6.table(data)
        elif current_tab == 'Transactions':
            column2.header("Admin")
            users = []
            db.execute("select user_id, username, transaction_id, symbol, shares, price, transacted from transaction natural join users order by username, transacted desc;")
            data = db.fetchall()
            for i in data:
                if i[1] not in users:
                    users += [i[1]]
            selected = column2.multiselect('Filter by user:', users)
            if selected:
                select = str(tuple(selected))[:str(selected).rfind("'") + 1] + ")"
                db.execute(f"select user_id, username, transaction_id, symbol, shares, price, transacted from transaction natural join users where username in {select} order by transacted desc;")
                data = db.fetchall()
            data = [("User ID", "Username", "Transaction ID", "Symbol", "Shares", "Price", "Date")] + data
            column2.table(data)
        elif current_tab == 'Logout':
            st.session_state['page'] = 1
            st.experimental_rerun()

