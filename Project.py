# Importing required modules
from st_on_hover_tabs import on_hover_tabs
import random
import time
from datetime import date, datetime, timedelta
import requests
import streamlit as st
import yfinance
import io
from shillelagh.backends.apsw.db import connect
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from captcha.image import ImageCaptcha
from streamlit_echarts import st_echarts
from streamlit.components.v1 import html
from streamlit_js_eval import streamlit_js_eval
from currency_converter import CurrencyConverter


# Configuring the page
st.set_page_config(
    page_title="Stock Market",
    layout="wide",
)

if "user_agent" not in st.session_state:
    user_agent = streamlit_js_eval(js_expressions='/iPhone|iPad|Android/i.test(navigator.userAgent)', key = 'UA')
    while str(user_agent) == "None":
        pass
    st.session_state['user_agent'] = user_agent
if str(st.session_state['user_agent']) == "True":
    st.header("This app can only be viewed on a desktop browser")
    st.stop()


if 'db' not in st.session_state:
    # This connects to google sheets using shillelagh and converts gsheet into sql database
    st.session_state['db'] = eval(st.secrets["connect_to_db"])
users = st.secrets["users_url"]
transaction = st.secrets["transaction_url"]

if 'page' not in st.session_state:
    st.session_state['page'] = 1

# Background image
if st.session_state['page'] in [1, 2, 4, 5, 6, 8, 10]:
    img = st.secrets["main_bg_image"]
else:
    img = st.secrets["bg_image"]

# Styling the webpage
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
    div[data-testid='stSidebarHeader']{{
        display: block;
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
        border-radius:2%;
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
        left: 165px;
        width: 800px;
        border: 1.5px solid;
        background: rgba(255, 255, 255, 0.62);
    }}
    .stCheckbox p{{
        color: #6a0000 !important;
        font-style: italic;
        font-weight: bold;
    }}
    iframe[title="st.iframe"] {{
        display: none;
    }}
    iframe[title="streamlit_js_eval.streamlit_js_eval"]{{
        display: none;
    }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)


# Initializing variables
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'driver' not in st.session_state:
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    try:
        driver.get('https://www.google.com/finance/quote/TSLA:NASDAQ?hl=en')
    except:
        driver = webdriver.Chrome(options=options)
        driver.get('https://www.google.com/finance/quote/TSLA:NASDAQ?hl=en')
    driver.implicitly_wait(2)
    st.session_state['driver'] = driver
if 'captcha' not in st.session_state:
    st.session_state['captcha'] = ""
if 'clicked' not in st.session_state:
    st.session_state['clicked'] = False
if 'company' not in st.session_state:
    st.session_state['company'] = ""
if 'text' not in st.session_state:
    st.session_state['text'] = ""
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
if 'count' not in st.session_state:
    st.session_state['count'] = 1
if 'people' not in st.session_state:
    st.session_state['people'] = ""
if 'information' not in st.session_state:
    st.session_state['information'] = ""


# This function sets all the variables to their initiall state
def clear():
    st.session_state['captcha'] = ""
    st.session_state['clicked'] = False
    st.session_state['company'] = ""
    st.session_state['shares'] = 1
    st.session_state['successful'] = ""
    st.session_state['warning'] = 0
    st.session_state['stock'] = "<select>"
    

# Function to check for internet connectivity
def internet():
    try:
        status = requests.get('https://www.google.com/').status_code
        return True
    except:
        return False

 
# Getting USD - INR conversion rates
@st.cache_data(ttl=120)
def usd():
    c = CurrencyConverter()
    st.session_state['usd'] = round(float(c.convert(1, 'USD', 'INR')), ndigits=2)
    return st.session_state['usd']
usd()


 # Use selenium and scrape price of stock from google
@st.cache_data
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
    try:
        data['Website'] = driver.find_element(By.CSS_SELECTOR, 'c-wiz[aria-busy="false"] .gyFHrc a[rel~="noopener"]').text
    except:
        data['Website'] = None
    return data


# This function displays all the stocks the user owns
def portfolio():
    column2.title("PORTFOLIO")
    data = st.session_state['db'].execute(f"select symbol, sum(shares) from '{transaction}' where user_id = {st.session_state['user']} group by symbol having sum(shares) != 0;")
    data = data.fetchall()
    if not data:
        column2.warning("You currently have not invested in any stocks")
        st.stop()
    if internet():
        sum = 0
        for i in range(len(data)):
            if st.session_state['count'] == 1:
                try:
                    info = get_price(data[i][0])
                except:
                    st.session_state['count'] = 2
                    del st.session_state['driver']
                    st.rerun()
            else:
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
    cash = st.session_state['db'].execute(f"select cash from '{users}' where user_id = {st.session_state['user']};")
    cash = cash.fetchall()[0][0]
    column2.text("Cash left in account: $" + str(cash))
    if internet():
        if cash + sum > 10000:
            column2.text("Profit: $" + str(round(cash + sum - 10000, ndigits=2)))
        elif cash + sum < 10000:
            column2.text("Loss: $" + str(round(10000 - (cash + sum), ndigits=2)))
        column2.subheader("YOUR net worth: $" + str(round(cash + sum, ndigits=2)))
    else:
        column2.warning("No internet connection! To view current prices of the stocks - please connect to the internet and refresh the page.")

        
        
# Function to display captcha on screen
def captcha():
    if 'successful' not in st.session_state:
        st.session_state['successful'] = ""
    title = column2.empty()
    title.header("CAPTCHA")
    if not st.session_state['captcha']:
        letters = "ACBDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        image = ImageCaptcha(width=280, height=90)
        captcha = ""
        for i in range(7):
            captcha = captcha + random.choice(letters)
        captcha = captcha.lower()
        st.session_state['text'] = captcha
        data = image.generate(captcha)
        st.session_state['captcha'] = data.getvalue()
    imag = column2.empty()
    imag.image(io.BytesIO(st.session_state['captcha']), width=550)
    txt = column2.empty()
    text = txt.text_input("Enter Captcha Code: ")
    verify = column2.empty()
    if verify.button("Verify"):
        text = text.lower()
        if text == st.session_state['text']:
            imag.empty()
            txt.empty()
            verify.empty()
            title.empty()
            st.session_state['successful'] = True
            return
        else:
            column2.text("Captcha failed!")
            imag.empty()
            txt.empty()
            verify.empty()
            title.empty()
            st.session_state['successful'] = False
            return
        
        
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
                js = """
                <script>
                    function execute(){
                        console.log("running1");
                        var iframe = parent.document.getElementsByTagName("iframe")[1];
                        console.log(iframe);
                        iframe.style.height = "450px";
                        iframe.onload = function () {
                            doc = iframe.contentWindow.document.getElementsByTagName("div");
                            for (var i=0, max=doc.length; i < max; i++) {
                                doc[i].style.height = "400px";
                            }
                        }
                    }
                    execute()
                    function exec(){
                        setInterval(function () {console.log("running2");
                            var iframe = parent.document.getElementsByTagName("iframe")[1];
                            iframe.style.height = "450px";
                            iframe.onload = function () {
                                doc = iframe.contentWindow.document.getElementsByTagName("div");
                                for (var i=0, max=doc.length; i < max; i++) {
                                    doc[i].style.height = "400px";
                                }
                            }
                        }, 1000)
                        
                    }
                    parent.document.getElementsByClassName("css-1n543e5")[0].addEventListener("click", exec);
                </script>
                """
                html(js)
            if data['Website']:
                col1, col2, col3 = st.columns([1, 4.5, 1])
                col2.write("Website: [" + str(data["Website"]) + "](" + str(data["Website"]) + ")")
        else:
            column2.warning("No stock or company exists with that name!")
            st.stop()
        
        
def buy():
    global column2
    column2.title("BUY SHARES")
    cash = st.session_state['db'].execute(f"SELECT cash from '{users}' where user_id = {st.session_state['user']};")
    cash = cash.fetchall()
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
            st.rerun()
        price = shares * data["Price"]
        if cash[0][0] - price < 0:
            st.session_state['clicked'] = False
            st.session_state['warning'] = 2
            st.rerun()
        column2.text("You will be paying an amount of: $" + str(round(price, ndigits=2)))
        column2.text("")
        var1 = column2.empty()
        var1.markdown("-----------------------------------------------------------------------------")
        var2 = st.empty()
        col1, col2 = var2.columns([4.8, 10])
        col2.write("Do you want to continue with the transaction?")
        var3 = st.empty()
        col3, col4, col5, col6 = var3.columns([8, 1.1, 1.1, 9])
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
                st.session_state['db'].execute(f"update '{users}' set cash = cash - {price} where user_id = {st.session_state['user']};")
                trans = st.session_state['db'].execute(f"select transaction_id from '{transaction}'")
                trans = trans.fetchall()
                trans_id = random.randint(10000, 99999)
                while trans_id in trans:
                    trans_id = random.randint(10000, 99999)
                column2.markdown("-----------------------------------------------------------------------------")
                column2.subheader("Price of $" + str(round(price, ndigits=2)) + " has been deducted from your account   Transaction ID: " + str(trans_id))
                column2.markdown("-----------------------------------------------------------------------------")
                date_time = str(datetime.now())[:19] + "a"
                st.session_state['db'].execute(f"insert into '{transaction}' values({st.session_state['user']}, {trans_id}, '{data['Symbol']}',{shares},{data['Price']},'{date_time}');")
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
    data = st.session_state['db'].execute(f"SELECT symbol from '{transaction}' where user_id = {st.session_state['user']} group by symbol having sum(shares) != 0;")
    data = data.fetchall()
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
        shares_owned = st.session_state['db'].execute(f"SELECT sum(shares) from '{transaction}' where user_id = {st.session_state['user']} and symbol = '{stock}' group by symbol;")
        shares_owned = shares_owned.fetchall()[0][0]
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
        col3, col4, col5, col6 = var3.columns([8, 1.1, 1.1, 9])
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
                st.session_state['db'].execute(f"update '{users}' set cash = cash + {price} where user_id = {st.session_state['user']};")
                trans = st.session_state['db'].execute(f"select transaction_id from '{transaction}';")
                trans = trans.fetchall()
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
                st.session_state['db'].execute(f"insert into '{transaction}' values({st.session_state['user']}, {trans_id}, '{stock}',{shares},{data['Price']},'{date_time}');")
                col11.text("Thank you for investing")
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

        
# Show all transactions made by the user
def transactions():
    column2.title("Your Transactions")
    data = st.session_state['db'].execute(f'select transaction_id, symbol, shares, price, ABS(shares) * price, SUBSTRING(transacted,1,LENGTH(transacted)-1) from "{transaction}" where user_id = {st.session_state["user"]} order by transacted desc;')
    data = data.fetchall()
    if not data:
        column2.warning("No transactions have taken place!")
        st.stop()
    data = [("Transaction ID", "Symbol", "Shares", "Price ($)", "Total price ($)", "Transaction Date")] + data
    column2.table(data)


placeholder = st.empty()
# The page is divided into 3 columns - the first column has only back button, column 2 has the rest of the data
column1, column2, column3 = st.columns([1, 3.5, 1])


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
    st.sidebar.image(st.secrets["logo"])
    st.sidebar.caption("")
    st.sidebar.caption("")
    column2.header("WELCOME", anchor="welcome")
    with st.sidebar:
        current_tab = on_hover_tabs(tabName=['Home','Login', 'Register', 'Admin','Help','About'], iconName=['home','account_circle','economy','dashboard','help_center','description'], styles = {'tabOptionsStyle': {':hover :hover': {'color': 'blue'}}}, key=105, default_choice=0)
        if current_tab =='Login':
            st.session_state['page'] = 6
            st.rerun()
        elif current_tab == 'Register':
            st.session_state['page'] = 8
            st.rerun()
        elif current_tab == 'Admin':
            st.session_state['page'] = 2
            st.rerun()
        elif current_tab == 'About':
            st.session_state['page'] = 4
            st.rerun()
        elif current_tab == 'Help':
            st.session_state['page'] = 5
            st.rerun()


# Admin login page
elif st.session_state['page'] == 2:
    column2.header("ADMIN")
    column1.text("")
    if column1.button(label="🔙"):
        st.session_state['page'] = 1
        st.rerun()
    username = column2.text_input('Username')
    password = column2.text_input('Password', type="password")
    if column2.button(label="Login"):
        data = st.session_state['db'].execute(f"SELECT username, password from '{users}' where user_id = 1;")
        data = data.fetchall()
        if username != data[0][0]:
            column2.warning('Wrong username')
            st.stop()
        if password != data[0][1][1:]:
            column2.warning("Wrong password")
            st.stop()
        st.session_state['page'] = 3
        st.rerun()


# Admin page
elif st.session_state['page'] == 3:
    column1, column2, column3 = st.columns([1, 4.5, 1])
    st.sidebar.image(st.secrets["logo"])
    st.sidebar.caption("")
    st.sidebar.caption("")
    main = st.empty()
    table = st.empty()
    with st.sidebar:
        current_tab = on_hover_tabs(tabName=['View Users','Transactions', 'Logout'], iconName=['group','credit_card','logout'], styles = {'tabOptionsStyle': {':hover :hover': {'color': 'blue'}}}, key=101, default_choice=0)
        if current_tab == "View Users":
            user = []
            def get_all_users():
                return st.session_state['db'].execute(f"select user_id, username, SUBSTRING(password,2,LENGTH(password)), cash, status from '{users}' where not user_id = 1;")
            data = get_all_users()
            data = data.fetchall()
            for i in data:
                user += [i[1]]
            col1, col2, col3, col4 = main.columns([1.15, 3, 1, 1.1])
            col2.header("Admin")
            disable = col2.multiselect('Select users to disable / enable:', user)
            for i in range(7):
                col3.text("")
            if col3.button(label="DISABLE / ENABLE"):
                for i in disable:
                    status = st.session_state['db'].execute(f'select status from "{users}" where username = "{i}"')
                    if status.fetchall()[0][0] == "ENABLED":
                        st.session_state['db'].execute(f'update "{users}" set status = "DISABLED" where username = "{i}"')
                    else:
                        st.session_state['db'].execute(f'update "{users}" set status = "ENABLED" where username = "{i}"')
                st.rerun()
            data = [("User ID", "Username", "Password", "Cash", "Status")] + data
            col5, col6, col7 = table.columns([1, 3.5, 1])
            col6.table(data)
        elif current_tab == 'Transactions':
            with placeholder.container():
                column1, column2, column3 = st.columns([1, 3.5, 1])
                column2.header("Admin")
                if not st.session_state["people"]:
                    with st.spinner("Loading..."):
                        user = []
                        data = st.session_state['db'].execute(f"select user_id, username, transaction_id, symbol, shares, price, SUBSTRING(transacted,1,LENGTH(transacted)-1) from '{transaction}' natural join '{users}' order by username, transacted desc;")
                        data = data.fetchall()
                        st.session_state["information"] = data
                        for i in data:
                            if i[1] not in user:
                                user += [i[1]]
                        st.session_state["people"] = user
                user = st.session_state["people"]
                data = st.session_state["information"]
                selected = column2.multiselect('Filter by user:', user)
                if selected:
                    data = []
                    select = str(tuple(selected))[:str(selected).rfind("'") + 1] + ")"
                    x = st.session_state["information"]
                    for j in select.replace("(", "").replace(")", "").replace("'", "").split(", "):
                        for i in x:
                            if i[1] == j:
                                data = data + [i]
                data = [("User ID", "Username", "Transaction ID", "Symbol", "Shares", "Price", "Date")] + data
                column2.table(data)
        elif current_tab == 'Logout':
            st.session_state["people"] = ""
            st.session_state["information"] = ""
            st.session_state['page'] = 1
            st.rerun()


# About page
elif st.session_state['page'] == 4:
    column2.header("About")
    column1.text("")
    if column1.button(label="🔙"):
        st.session_state['page'] = 1
        st.rerun()
    column2.warning("Code yet to come!")


# Help page
elif st.session_state['page'] == 5:
    column2.header("Forgotten Password?")
    column1.text("")
    if column1.button("🔙"):
        st.session_state['page'] = 1
        st.rerun()
    usrname = column2.empty()
    username = usrname.text_input('Username')
    l = ["SELECT", "Which city were you born in ?", "Which college did you go to ?", "What is your favourite sport ?",
         "Whats your dream job ?", "First movie you watched :", "Keyword"]
    selctbx = column2.empty()
    q = selctbx.selectbox("Security Question", l)
    prmpt = column2.empty()
    ans = prmpt.text_input("Security prompt")
    btn = column2.empty()
    if btn.button("Check") and q != "SELECT":
        if not username:
            column2.warning("Please enter username !")
            st.stop()
        elif not ans:
            column2.warning("Please enter security prompt !")
            st.stop()
        data = st.session_state['db'].execute(f"select password, status, security_q, prompt from '{users}' where username = '{username}'")
        data = data.fetchall()
        if not data:
            column2.warning("Username not found !!")
            st.stop()
        elif (data[0][2] != q) or (data[0][3] != ans):
            column2.warning("Incorect security question or prompt !!")
            st.stop()
        elif data[0][1] == "DISABLED":
            column2.warning("Your account has been disabled by the ADMIN!")
            st.stop()
        else:
            btn.empty()
            selctbx.empty()
            prmpt.empty()
            usrname.empty()
            username = usrname.text_input('Username', disabled=True, value=username)
            selctbx.selectbox("Security Question", l, disabled=True, index=l.index(q))
            prmpt.text_input("Security prompt", disabled=True, value=ans)
            column2.text("")
            column2.info('Your password is "'+data[0][0][1:]+'"')


# User login page
elif st.session_state['page'] == 6:
    column2.header("LOGIN")
    column1.text("")
    if column1.button(label="🔙"):
        st.session_state['page'] = 1
        st.rerun()
    username = column2.text_input('Username')
    password = column2.text_input('Password', type="password")
    if column2.button(label="Login"):
        data = st.session_state['db'].execute(f'select username, password, user_id, status from "{st.secrets["users_url"]}" where username = "{username}"')
        data = data.fetchall()
        if not data:
            column2.warning("Username not found, Please Register")
            st.stop()
        if data[0][2] == 1:
            column2.warning("The ADMIN cannot login as an user, please login as ADMIN!")
            st.stop()
        if data[0][3] == "DISABLED":
            column2.warning("Your account has been disabled by the ADMIN!")
            st.stop()
        if password == data[0][1][1:]:
            st.session_state['user'] = data[0][2]
            st.session_state['page'] = 7
            st.rerun()
        else:
            column2.warning("Wrong password")



# User menu page
elif st.session_state['page'] == 7:
    column1, column2, column3 = st.columns([1, 4.5, 1])
    if 'tab' not in st.session_state:
        st.session_state['tab'] = "Portfolio"
    top = """
    <style>
        section[data-testid='stSidebar'] > div:hover{
            top: -12%;
        }
        .css-18e3th9 {
            padding: 3rem 1rem 10rem;
        }
    </style>
    """
    st.markdown(top, unsafe_allow_html=True)
    st.sidebar.image(st.secrets["logo"])
    st.sidebar.caption("")
    with st.sidebar:
        current_tab = on_hover_tabs(tabName=['Portfolio', 'Quote', 'Buy', 'Sell', 'History', 'Account', 'Logout'], iconName=['dashboard', 'manage_search', 'money', 'economy', 'history', 'account_circle', 'logout'], styles = {'tabOptionsStyle': {':hover :hover': {'color': 'lightgreen'}}},key=109, default_choice=0)
    if st.session_state['tab'] != current_tab:
        st.session_state['tab'] = current_tab
        clear()
    if current_tab =='Portfolio':
        portfolio()
    elif current_tab == 'Quote':
        quote()
    elif current_tab == 'Buy':
        buy()
    elif current_tab =='Sell':
        sell()
    elif current_tab == 'History':
        transactions()
    elif current_tab == 'Account':
        st.session_state['page'] = 9
        st.rerun()
    elif current_tab == 'Logout':
        st.session_state['page'] = 1
        st.rerun()



# This page is for registering a new user - it has captcha
elif st.session_state['page'] == 8:
    column2.header("Register")    
    column1.text("")
    if column1.button(label="🔙"):
        st.session_state['captcha'] = ""
        st.session_state['clicked'] = False
        st.session_state['agree'] = False
        st.session_state['name'] = ""
        st.session_state['successful'] = ""
        st.session_state['username'] = ""
        st.session_state['password'] = ""
        st.session_state['confirm'] = ""
        st.session_state['page'] = 1
        st.rerun()
    if not st.session_state['clicked']:
        color = """
        <style>
            #register {
                color: #002e80;
            }
        </style>
        """
        st.markdown(color, unsafe_allow_html=True)
        column2.markdown("""            - This program is a simulator of actual investments in stocks and the creation of portfolios in the stock market.

        - When you register the program will give you $10000 online currency - which can only be spent through our program.

        - You can use this money to invest and gain experience on how to invest in the real world. The prices of the stocks are realtime prices (they are not mocks).

        - Any data entered into the program will only be stored locally and will not be shared with any third party companies.

        - The admin will be able to moniter all your activities and can disable your account incase of any fraud.""")
        column2.text("")
        col1, col2, col3, col4 = st.columns([0.9, 1.7, 1, 1.2])
        st.session_state['agree'] = col2.checkbox("I agree that I have read through the guidelines", value=st.session_state['agree'])
        if col4.button("Next ⇥") and st.session_state['agree']:
            st.session_state['clicked'] = True
            st.rerun()
    else:
        name = column2.empty()
        st.session_state['username'] = name.text_input('Enter username:', value=st.session_state['username'], key=15)
        var1 = column2.empty()
        st.session_state['password'] = var1.text_input('Enter password:', type="password", help="Choose a strong password with letters, numbers and symbols", value=st.session_state['password'], key=16)
        var2 = column2.empty()
        st.session_state['confirm'] = var2.text_input('Re-enter password:', type="password", value=st.session_state['confirm'], key=17)
        col1, col2, col3 = st.columns([1.65, 5, 2.4])
        btn = col3.empty()
        btn2 = col2.empty()
        if not st.session_state['captcha']:
            if btn2.button("⇤ Previous"):
                st.session_state['clicked'] = False
                st.rerun()
        if st.session_state['captcha'] or btn.button(label="Register"):
            username = st.session_state['username']
            password = st.session_state['password']
            confirm = st.session_state['confirm']
            if not username:
                column2.warning("Please enter username!")
                st.stop()
            if " " in username:
                column2.warning("Username cannot contain space!")
                st.stop()
            data = st.session_state['db'].execute(f"select username from '{users}' where username = '{username}'")
            data = data.fetchall()
            if data:
                column2.warning("This username is already taken! Please try Again.")
                st.stop()
            if not password:
                column2.warning("Please enter password!")
                st.stop()
            if " " in password:
                column2.warning("The password cannot contain space!")
                st.stop()
            if password != confirm:
                column2.warning("Passwords Not Matching!")
                st.stop()
            name.text_input('Enter username:', disabled=True, value=username, key=18)
            var1.text_input('Enter password:', type="password", help="Choose a strong password with letters, numbers and symbols", disabled=True, value=password, key=19)
            var2.text_input('Re-enter password:', type="password", disabled=True, value=confirm, key=20)
            btn.empty()
            btn2.empty()
            captcha()
            if str(st.session_state['successful']) == "True":
                data = st.session_state['db'].execute(f"select * from '{users}';")
                data = data.fetchall()
                Id = len(data) + 1
                st.session_state['user'] = Id
                st.session_state['text'] = ""
                st.session_state['name'] = ""
                st.session_state['agree'] = False
                st.session_state['confirm'] = ""
                st.session_state['clicked'] = False
                st.session_state['captcha'] = ""
                st.session_state['successful'] = ""
                st.session_state['page'] = 15
                st.rerun()
            elif str(st.session_state['successful']) == "False":
                column2.warning("Registration unsucessfull!")
                st.session_state['username'] = ""
                st.session_state['password'] = ""
                st.session_state['text'] = ""
                st.session_state['name'] = ""
                st.session_state['agree'] = False
                st.session_state['confirm'] = ""
                st.session_state['clicked'] = False
                st.session_state['captcha'] = ""
                st.session_state['successful'] = ""
                st.stop()


# Account menu
elif st.session_state['page'] == 9:
    column1, column2, column3 = st.columns([1, 4.5, 1])
    st.sidebar.image(st.secrets["logo"])
    st.sidebar.caption("")
    st.sidebar.caption("")
    top = """
    <style>
        section[data-testid='stSidebar'] > div {
            position: relative;
            top: 12%;
            transition: 0.7s ease;
        }
    </style>
    """
    st.markdown(top, unsafe_allow_html=True)
    text1 = st.empty()
    text2 = st.empty()
    text3 = st.empty()
    with st.sidebar:
        current_tab = on_hover_tabs(tabName=['Account Details','Change Password','Delete Account', 'Go Back'], iconName=['account_circle','lock','delete_sweep','fast_rewind'], styles = {'tabOptionsStyle': {':hover :hover': {'color': 'red'}}}, key=102, default_choice=0)
        if current_tab =='Account Details':
            st.session_state['clicked'] = False
            column2.title("ACCOUNT DETAILS")
            user_info = st.session_state['db'].execute(f'select * from "{users}" where user_id = {st.session_state["user"]};')
            user_info = user_info.fetchall()
            companies = st.session_state['db'].execute(f'select distinct(symbol) from "{transaction}" where user_id = {st.session_state["user"]} group by symbol having sum(shares) != 0;')
            companies = companies.fetchall()
            shares = st.session_state['db'].execute(f'select sum(shares) from "{transaction}" where user_id = {st.session_state["user"]};')
            shares = shares.fetchall()
            column2.markdown("--------------------------------------------")
            column2.markdown("**Username**: *" + str(user_info[0][1]) + "*")
            column2.markdown("**Balance**: *$" + str(user_info[0][3]) + "*")
            column2.markdown("**No. of companies invested**: *" + str(len(companies)) + "*")
            column2.markdown("**No. of shares owned**: *" + str(shares[0][0]) + "*")
            column2.markdown("--------------------------------------------")
        elif current_tab == 'Change Password':
            column2.title("CHANGE Password")
            var1 = column2.empty()
            password = var1.text_input('Enter OLD password:', type="password")
            btn = column2.empty()
            if btn.button(label="Verify"):
                data = st.session_state['db'].execute(f"select password from '{users}' where user_id = {st.session_state['user']}")
                data = data.fetchall()
                if password == data[0][0][1:]:
                    st.session_state['clicked'] = True
                else:
                    column2.warning("Incorrect Password! Try Again!")
                    st.stop()
            if st.session_state['clicked']:
                var1.empty()
                btn.empty()
                var2 = column2.empty()
                password = var2.text_input('Enter new password:', type="password", help="Choose a strong password with letters, numbers and symbols", value=st.session_state['password'], key=27)
                var3 = column2.empty()
                confirm = var3.text_input('Re-enter new password:', type="password", value=st.session_state['password'], key=28)
                change = column2.empty()
                if change.button(label="Change password") or st.session_state['password']:
                    if not password:
                        column2.warning("Please enter password!")
                        st.stop()
                    if " " in password:
                        column2.warning("The password cannot contain space!")
                        st.stop()
                    if password != confirm:
                        column2.warning("Passwords Not Matching!")
                        st.stop()
                    var2.empty()
                    var3.empty()
                    change.empty()
                    var2.text_input('Enter new password:', type="password", help="Choose a strong password with letters, numbers and symbols", disabled=True, value=password, key=29)
                    var3.text_input('Re-enter new password:', type="password", disabled=True, value=confirm, key=30)
                    data = st.session_state['db'].execute(f"select password from '{users}' where user_id = {st.session_state['user']}")
                    data = data.fetchall()
                    if password == data[0][0][1:]:
                        st.session_state['password'] = password
                        column2.text("")
                        var4 = column2.empty()
                        var4.markdown("-----------------------------------------------------------------------------------")
                        var5 = text1.empty()
                        col1, col2 = var5.columns([3.4, 10])
                        col2.markdown("**Are you sure you want to keep the password the same as the OLD password?**")
                        var6 = text2.empty()
                        col3, col4, col5, col6 = var6.columns([9, 1.2, 1.2, 9])
                        if col4.button("Yes", key=31):
                            var4.empty()
                            var5.empty()
                            var6.empty()
                            column2.text("")
                            column2.subheader("Password succesfully changed")
                            st.session_state['clicked'] = False
                            st.session_state['password'] = ""
                            st.stop()
                        if col5.button("No", key=32):
                            st.session_state['clicked'] = False
                            st.session_state['password'] = ""
                            st.rerun()
                        col7, col8, col9 = text3.columns([1, 4.5, 1])
                        col8.markdown("-----------------------------------------------------------------------------------")
                        st.stop()
                    password = 'a' + password
                    st.session_state['db'].execute(f'update "{users}" set password = "{password}" where user_id = {st.session_state["user"]};')
                    column2.text("")
                    column2.subheader("Password succesfully changed")
                    st.session_state['clicked'] = False
                    st.session_state['password'] = ""
        elif current_tab == 'Delete Account':
            st.session_state['clicked'] = False
            st.session_state['page'] = 13
            st.rerun()
        elif current_tab == 'Go Back':
            st.session_state['clicked'] = False
            st.session_state['page'] = 7
            st.rerun()

            
# Delete account confirmation
elif st.session_state['page'] == 13:
    col1, col2, col3 = st.columns([3, 3.5, 3])
    col1.text("")
    if col1.button(label="🔙"):
        st.session_state['page'] = 9
        st.rerun()
    col4, col5, col6 = st.columns([2, 4.5, 2])
    col5.markdown('''            <div id="del"><h1 style="text-align: center; color: darkblue;">DELETE ACCOUNT</h1>

            --------------------------------------------------------
            <p style="text-align: center; color: green;"><font size="5.9"><b>IMPORTANT: Please Read Terms and Conditions</b></font></p>

            --------------------------------------------------------
            - **WARNING: All the stocks which you own WILL be SOLD immediately.**

            - **A fine of $100 will be applied for deleting your account and your details.**

            - **A detailed list of all your purchases and shares will be displayed and the FOLLOWING price would be added to your account balance.**

            - **Being a sensitive matter, any wrong detail will abort the deletion of the account.**

            - **This action is irreversible so please be careful !!**
            --------------------------------------------------------
            </div><div style="height: 480px"></div>
            <style>
            #del{
                position: absolute;
                top: -15%
            }
            .st-at{
                background-color: rgba(28, 131, 225, 0.2)
            }
            </style>
            ''', unsafe_allow_html=True)
    col5.text("")
    var1 = st.empty()
    col7, col8, col9 = var1.columns([2.15, 3.5, 2.4])
    col8.info("Do you want to continue to delete your account?")
    var2 = st.empty()
    col10, col11, col12, col13 = var2.columns([9, 1.3, 1.3, 9.5])
    if col11.button("Yes"):
        st.session_state['page'] = 14
        st.rerun()
    if col12.button("No"):
        st.session_state['clicked'] = False
        st.session_state['page'] = 7
        st.rerun()
    else:
        col14, col15, col16 = st.columns([2, 4.5, 2])
        col15.markdown("--------------------------------------------------------")
            
            
            
# Final check before deleting account
elif st.session_state['page'] == 14:
    if 'deleted' not in st.session_state:
        st.session_state['deleted'] = False
    col1, col2 = st.columns([1, 1.7])
    col1.text("")
    var1 = col1.empty()
    if var1.button(label="🔙"):
        st.session_state['deleted'] = False
        st.session_state['clicked'] = False
        st.session_state['page'] = 9
        st.rerun()
    if not st.session_state['clicked']:
        col2.header("Confirm details")
        var2 = st.empty()
        col3, col4, col5 = var2.columns([1, 3.5, 1])
        username = col4.text_input("Enter your username: ", key=33)
        password = col4.text_input("Enter your password: ", key=34)
        if col4.button("Confirm"):
            data = st.session_state['db'].execute(f"select username, password from '{users}' where user_id={st.session_state['user']};")
            data = data.fetchall()
            if not username:
                col4.warning("Please enter username!")
                st.stop()
            if not password:
                col4.warning("Please enter password!")
                st.stop()
            if username != data[0][0]:
                var2.empty()
                col6, col7, col8 = var2.columns([1, 3.5, 1])
                username = col7.text_input("Enter your username: ", disabled=True, value=username, key=35)
                password = col7.text_input("Enter your password: ", disabled=True, value=password, key=36)
                col7.warning("Incorrect username - deletion of account aborted!")
                st.stop()
            if password != data[0][1][1:]:
                var2.empty()
                col6, col7, col8 = var2.columns([1, 3.5, 1])
                username = col7.text_input("Enter your username: ", disabled=True, value=username, key=37)
                password = col7.text_input("Enter your password: ", disabled=True, value=password, key=38)
                col7.warning("Incorrect password - deletion of account aborted!")
                st.stop()
            st.session_state['clicked'] = True
            st.rerun()
    elif not st.session_state['deleted']:
        col2.header("DELETE ACCOUNT")
        col3, col4, col5 = st.columns([1, 3.5, 1])
        data = st.session_state['db'].execute(f"select symbol, sum(shares) from '{transaction}' where user_id = {st.session_state['user']} group by symbol;")
        data = data.fetchall()
        connection = internet()
        status = ""
        total = 0
        for i in data:
            if int(i[1]) != 0:
                if not connection:
                    status = "Unsold"
                    break
                stock = get_price(i[0])
                total += int(i[1]) * stock["Price"]
        if status == "Unsold":
            col4.warning("No internet connection so your stocks cannot be sold! Your account cannot be deleted with unsold stocks! Please connect to the internet and try again.")
            st.stop()
        col4.text("A total of: $" + str(total) + " will be credited into your account")
        col4.text("You will also be debitted $100 as fine")
        user_info = st.session_state['db'].execute(f"select cash from '{users}' where user_id = {st.session_state['user']};")
        user_info = user_info.fetchall()
        credit = user_info[0][0] + total - 100
        col4.text("Your net Balance is: $" + str(credit))
        col4.text("")
        col4.markdown("-----------------------------------------------------------------------------------")
        var2 = st.empty()
        col6, col7, col8 = var2.columns([1.1, 3.5, 1.38])
        col7.info("Are you sure you want to delete your account?")
        var3 = st.empty()
        col9, col_10, col_11, col_12 = var3.columns([8.5, 1.2, 1, 9])
        if col_10.button("Yes"):
            data = st.session_state['db'].execute(f"select * from '{users}';")
            Id = len(data.fetchall())
            st.session_state['db'].execute(f'delete from "{users}" where user_id = {st.session_state["user"]};')
            st.session_state['db'].execute(f'delete from "{transaction}" where user_id = {st.session_state["user"]};')
            for i in range(st.session_state["user"], Id):
                st.session_state['db'].execute(f"update '{users}' set user_id = {i} where user_id = {i + 1};")
                st.session_state['db'].execute(f"update '{transaction}' set user_id = {i} where user_id = {i + 1};")
            st.session_state['deleted'] = True
            st.rerun()
        if col_11.button("No"):
            st.session_state['deleted'] = False
            st.session_state['clicked'] = False
            st.session_state['page'] = 7
            st.rerun()
        if not st.session_state['deleted']:
            col_13, col_14, col_15 = st.columns([1, 3.5, 1])
            col_14.markdown("-----------------------------------------------------------------------------------")
    else:
        var1.empty()
        col3, col4, col5 = st.columns([1, 3.5, 1])
        col4.markdown("-----------------------------------------------------------------------------------")
        col6, col7 = st.columns([1.5, 3])
        col7.subheader("Account deleted successfully")
        col8, col9 = st.columns([2.2, 3])
        if col9.button("Go back home"):
            st.session_state['deleted'] = False
            st.session_state['clicked'] = False
            st.session_state['user'] = None
            st.session_state['page'] = 1
            st.rerun()
        col_10, col_11, col_12 = st.columns([1, 3.5, 1])
        col_11.markdown("-----------------------------------------------------------------------------------")


# Security question
elif st.session_state['page'] == 15:
    column2.header("Security Question")
    l = ["Which city were you born in ?", "Which college did you go to ?", "What is your favourite sport ?",
         "Whats your dream job ?", "First movie you watched :", "Keyword"]
    q = column2.selectbox("Security Question", l, help="This will be to recover forgotten password")
    ans = column2.text_input("")
    if column2.button("Submit"):
        if not ans.strip():
            column2.warning("Prompt for security question cannot be empty or space")
            st.stop()
        username = st.session_state["username"]
        password = st.session_state["password"]
        Id = st.session_state["user"]
        st.session_state['db'].execute(f'insert into "{users}" values ({Id},"{username}","{"a" + password}", 10000.00, "ENABLED", "{q}", "{ans}");')
        st.session_state["username"] = ""
        st.session_state["password"] = ""
        st.session_state['page'] = 7
        st.rerun()


