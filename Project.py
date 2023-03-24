# Om
# If any of the required modules are not installed - ask the user to install

import mysql.connector as connector
from st_on_hover_tabs import on_hover_tabs
from streamlit_echarts import st_echarts
import requests
import streamlit as st
from webdriver_manager.chrome import ChromeDriverManager
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


# Function to check for internet connectivity
def internet():
    try:
        status = requests.get('https://www.google.com/').status_code
        return True
    except:
        return False

# Initializing variables
if 'user' not in st.session_state:
    st.session_state['user'] = None
    options = webdriver.chrome.options.Options()
    options.add_argument("--headless=True")
    driver = webdriver.Chrome(service=selenium.webdriver.chrome.service.Service(ChromeDriverManager().install()), options=options)
    driver.get('https://www.google.com/finance/quote/TSLA:NASDAQ?hl=en')
    driver.implicitly_wait(2)
    st.session_state['driver'] = driver


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
    form = column2.form(key="admin_login")
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

