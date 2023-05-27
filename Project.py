from st_on_hover_tabs import on_hover_tabs
import random
import time
import requests
import streamlit as st
from shillelagh.backends.apsw.db import connect
from geopy.geocoders import Nominatim
import pandas
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


# Configuring the page
st.set_page_config(
    page_title="Stock Market",
    layout="wide",
)


if 'db' not in st.session_state:
    # This connects to google sheets using shillelagh and converts gsheet into sql database
    st.session_state['db'] = eval(st.secrets["connect_to_db"])
users = st.secrets["users_url"]
transaction = st.secrets["transaction_url"]

if 'page' not in st.session_state:
    st.session_state['page'] = 1


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
    button[title='View fullscreen'], a:not(a[target=_blank]), footer {{visibility: hidden;}}
    [data-testid="stAppViewContainer"] > .main {{
        background-image: url("{img}");
        background-repeat: no-repeat;
        background-size: 120%;
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


# Initializing variables
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'driver' not in st.session_state:
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')
    st.session_state['driver'] = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    st.session_state['driver'].get('https://www.google.com/finance/quote/TSLA:NASDAQ?hl=en')
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


# Function to check for internet connectivity
def internet():
    try:
        status = requests.get('https://www.google.com/').status_code
        return True
    except:
        return False

 
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
    st.text(driver.find_element_by_xpath("/html/body").text)
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


# This function displays all the stocks the user owns
@st.cache_data
def portfolio():
    column2.title("PORTFOLIO")
    data = st.session_state['db'].execute(f"select symbol, sum(shares) from '{transaction}' where user_id = {st.session_state['user']} group by symbol having sum(shares) != 0;")
    data = data.fetchall()
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
        elif current_tab == 'Contact Us':
            st.session_state['page'] = 4
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
    username = column2.text_input('Username')
    password = column2.text_input('Password', type="password")
    if column2.button(label="Login"):
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
            pass
        elif current_tab == 'Transactions':
            pass
        elif current_tab == 'Logout':
            st.session_state['page'] = 1
            st.experimental_rerun()


elif st.session_state['page'] == 4:
    column2.header("Contact Us")
    column1.text("")
    if column1.button(label="🔙"):
        st.session_state['page'] = 1
        st.experimental_rerun()
    data = pandas.DataFrame({'locations' : ['NPS RNR', 'WTC Bengaluru', 'Manyata Tech Park'], 'lat' : [12.984104, 13.012611,  13.046943], 'lon' : [77.549458, 77.555953, 77.621297]})
    city = column2.text_input('Please enter your city so we cannect you to the closest customer care center').lower()
    if not internet():
        column2.warning("No internet !!")
        st.stop()
    if column2.button("Check"):
        if not city:
            column2.warning("Please enter city name !!")
        else:
            geolocator = Nominatim(user_agent="Finance123")
            location = geolocator.geocode(city)
            if not location:
                column2.warning("Please enter valid city name !!")
                st.stop()
            if city.lower() not in ["bengaluru","bangalore"]:
                lat = location.latitude
                long = location.longitude
                data = pandas.DataFrame({'locations' : [city], 'lat' : [lat], 'lon' : [long]})
            column2.text("Thank you for contacting, we have an available line")
            mob = random.randint(9000000000,9999999999)
            column2.text("Mobile Number:" + str(mob))
            column2.text("")
    col1, col2, col3 = st.columns([1, 11, 1])
    col2.map(data)


elif st.session_state['page'] == 5:
    column2.header("Help")
    column1.text("")
    if column1.button("🔙"):
        st.session_state['page'] = 1
        st.experimental_rerun()

    column2.markdown("""            - **This program is a simulator of actual investments in stocks and the creation of portfolios in the stock market.**

    - **When you register the program will give you $10000 online currency - which can only be spent through our program.**

    - **You can use this money to invest and gain experience on how to invest in the real world. The prices of the stocks are realtime prices (they are not mocks).**

    - **Any data entered into the program will only be stored locally and will not be shared with any third party companies.**

    - **The admin will be able to moniter all your activities and can disable your account incase of any fraud.**""")
    
    column2.text("")    
    column2.header("Forgotten Password?")
    username = column2.text_input('Username')
    if column2.button("Check"):
        pass


# User login page
elif st.session_state['page'] == 6:
    column2.header("LOGIN")
    column1.text("")
    if column1.button(label="🔙"):
        st.session_state['page'] = 1
        st.experimental_rerun()
    username = column2.text_input('Username')
    password = column2.text_input('Password', type="password")
    if column2.button(label="Login"):
        data = st.session_state['db'].execute(f'select username, password, user_id, status from "{st.secrets["users_url"]}" where username = "{username}"')
        data = data.fetchall()
        if not data:
            column2.warning("Username not found, Please Register")
            st.stop()
        st.text(data)
        if data[0][2] == 1:
            column2.warning("The ADMIN cannot login as an user, please login as ADMIN!")
            st.stop()
        if data[0][3] == "DISABLED":
            column2.warning("Your account has been disabled by the ADMIN!")
            st.stop()
        if password == data[0][1][1:]:
            st.session_state['user'] = data[0][2]
            st.session_state['page'] = 7
            st.experimental_rerun()
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
    st.sidebar.image("https://app.omnistock.io/uploads/logo/yktS4FqNbQGn3TychVaEzDIkHoiJa4Ei5HPSAIAy.png")
    st.sidebar.caption("")
    with st.sidebar:
        current_tab = on_hover_tabs(tabName=['Portfolio', 'Quote', 'Buy', 'Sell', 'History', 'Account', 'Logout'], iconName=['dashboard', 'manage_search', 'money', 'economy', 'history', 'account_circle', 'logout'], styles = {'tabOptionsStyle': {':hover :hover': {'color': 'lightgreen'}}},key=109, default_choice=0)
    if st.session_state['tab'] != current_tab:
        st.session_state['tab'] = current_tab
        pass
    if current_tab =='Portfolio':
        portfolio()
    elif current_tab == 'Quote':
        pass
    elif current_tab == 'Buy':
        pass
    elif current_tab =='Sell':
        pass
    elif current_tab == 'History':
        pass
    elif current_tab == 'Account':
        pass
    elif current_tab == 'Logout':
        st.session_state['page'] = 1
        st.experimental_rerun()



# Explaination
# If the code was run in the python then the program runs the streamlit command to open GUI
# Streamlit files have to be run from command prompt to open the website (GUI)
# The command is 'streamlit run <file name with full path>'
# When the cmd command runs - streamlit opens the program to display - and it needs to run the actuall code and not try to run cmd prompt command again
# If st.runtime.scriptrunner.get_script_run_ctx() is None then streamlit command was not run hence run cmd command
# If st.runtime.scriptrunner.get_script_run_ctx() is not None just run normal code
