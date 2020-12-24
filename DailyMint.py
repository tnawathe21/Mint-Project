#!/usr/bin/python

import mintapi
import pandas as pd
import keyring
import yagmail
import sys
import time # for sending scheduled email
from datetime import date, datetime, timedelta
from datetime import datetime
from premailer import transform

# First time store username & password in keyring below
#keyring.set_password('mintapi', "username", username)
#keyring.set_password('mintapi',"password", password)
#keyring.set_password('yagmail', 'mygmailusername', 'mygmailpassword')

def get_mint_handle():
    mint_username = keyring.get_password("mintapi", "username")
    mint_password = keyring.get_password("mintapi", "password")
    mint = mintapi.Mint(
        mint_username,  # Email used to log in to Mint
        mint_password,  # Your password used to log in to mint

        # Optional parameters
        mfa_method='sms',  # Can be 'sms' (default), 'email', or 'soft-token'.
                           # if mintapi detects an MFA request, it will trigger the requested method
                           # and prompt on the command line.
        headless=False,  # Whether the chromedriver should work without opening a
                         # visible window (useful for server-side deployments)
        mfa_input_callback=None,  # A callback accepting a single argument (the prompt)
                                  # which returns the user-inputted 2FA code. By default
                                  # the default Python `input` function is used.
        session_path=None, # Directory that the Chrome persistent session will be written/read from.
                           # To avoid the 2FA code being asked for multiple times, you can either set
                           # this parameter or log in by hand in Chrome under the same user this runs
                           # as.
        imap_account=None, # account name used to log in to your IMAP server
        imap_password=None, # account password used to log in to your IMAP server
        imap_server=None,  # IMAP server host name
        imap_folder='INBOX',  # IMAP folder that receives MFA email
        wait_for_sync=False,  # do not wait for accounts to sync
        wait_for_sync_timeout=300,  # number of seconds to wait for sync
    )
    return mint

def extract_data(mint):
    mint.initiate_account_refresh()
    time.sleep(300)
    txs = mint.get_transactions().head(10)
    accts = pd.DataFrame(mint.get_accounts())
    networth = "${:,.2f} k".format(mint.get_net_worth()/1000)
    try:
        credit_score = mint.get_credit_score()
    except:
        credit_score = "No credit score available"
    txs_html  = get_txs_html(txs)
    accts_html = get_accts_html(accts)
    #fix accounts

    return credit_score, networth, txs_html, accts_html

def extract_data_dummy():
    txs = pd.read_csv('test\\transactions.csv', parse_dates=['date'])
    accts = pd.read_csv('test\\accounts.csv', dtype={'status': object})
    networth = "${:,.0f} k".format(7647656.86/1000)
    print("networth:" + networth)
    try:
        credit_score= str(825)
    except:
        credit_score = "No score available"
    
    txs_html  = get_txs_html(txs)
    print("finished getting txs html")
    accts_html = get_accts_html(accts)
    print("finished getting accts html")
    #fix accounts

    return credit_score, networth, txs_html, accts_html

def get_txs_html(txs):
        #fix transactions
    txs = txs.sort_values(by='date', ascending=False).head(20) #sort and trim
    print('Sorted transactions by date')
    txs['amount'] = txs.apply(lambda row: adjust_amt(row), axis=1) #fix amount sign
    print('Applied credit and debit adjustments')
    
    txs = txs.drop(columns=['description', 'transaction_type', 'labels', 'notes']) #drop unnecessary columns before saving transactions
    
    #save transactions
    filename = 'data\Txs_as_of_' + str(date.today()) + '.csv'
    txs.to_csv(filename, index=False)

    format_dict = {'amount':'${0:,.2f}', 'date': '{:%m/%d/%y}'} #format data set
    style = (
        txs.style
        .format(format_dict)
        .applymap(color_negative_red, subset=['amount'])
        # .set_properties(**{'font-size': '10pt', 'font-family': 'Calibri'})
        .set_properties(**{'text-align': 'right'})
        .hide_index() 
    )
    return style.render()

def get_accts_html(accts):
    accts = accts[accts['value'] != 0 ] #filter out zero dollar accounts

    # commented this out since my csv doesn't have a status heading
    try:
        accts = accts[accts['status'].str.contains('1')] #only active accounts
    except:
        accts = accts # if there is no status column in accounts, ignore above line

    accts = accts[['id','value', 'accountName',  'fiLoginDisplayName']] #extract only relevent columns
    accts = accts.sort_values(by=['value'], ascending=False)

    #save accounts
    filename = 'data\Accounts_as_of_' + str(date.today()) + '.csv'
    accts.to_csv(filename, index=False)

    today = str(date.today())# Get today's date

    try:  # open history file if available so we can compare with the last pull
        print('Loading history.')
        accts_history = pd.read_csv('data\\accounts_history.csv', index_col=[0])
        print('History file loaded.')
    except:  #history file doesn't exist so create a new one
        #history file add values of every day date column e.g.
        #  name, login, 2020-09-18, 2020-09-17, ... last, diff
        #  abc, xyz, 100, 99, 101, ... 100, 1
        accts_history = accts.copy()
        accts_history.rename(columns={'value':'last'}, inplace=True)

    # drop names columns (use names from the latest pull )
    accts_history = accts_history.drop(columns=['accountName', 'fiLoginDisplayName', today], errors='ignore')

    # rename "value" column to today's date e.g. 2020-09-18
    accts.rename(columns={'value':today}, inplace=True)
    #join new accounts and old values over id.
    accts = pd.merge(accts, accts_history, on=["id"])
    #calculate changes from last so we can display the diff
    accts['diff'] = accts[today].sub(accts['last'], axis = 0)
    # update last with the current.
    accts['last'] = accts[today]
    #store the history file with today's column added.
    accts.to_csv('data\\accounts_history.csv')

    #keep relevant column
    accts = accts[['accountName',today, 'diff']]
    #Show the biggest change first 
    #sort descending by absolute value of  'diff'
    accts.reindex(accts['diff'].abs().sort_values(ascending=False).index)
    format_dict = {today:'${0:,.0f}', 'diff':'${0:,.0f}'} 
    style = (
        accts.style
        .format(format_dict)
        .applymap(color_negative_red, subset=[today, 'diff'])
        .set_properties(**{'text-align': 'right'})
        .hide_index() 
    )
    return style.render()

def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'red' if val < 0 else 'green'
    return 'color: %s' % color

def adjust_amt(row):
    if row['transaction_type'] == 'debit':
        return row['amount'] * -1
    elif row['transaction_type'] == 'credit':
        return row['amount']
    else:
        return np.NaN

def generate_html(credit_score, networth, txs_html, accts_html):
    pd.set_option('colheader_justify', 'center')
    with open('email_template.html', 'r') as file:
        email_template = file.read()
    today = date.today().strftime("%d/%m/%Y")
    return email_template.format(
        date_time=today, 
        networth=networth, 
        score=credit_score,
        transactions= transform(txs_html), 
        accounts=transform(accts_html))
    
def send_email(html):
    if len(sys.argv) == 2:
        to_email = sys.argv[1]
    else:
        to_email = sys.argv[2]
    print('sending email to ' + to_email)
    
    yag = yagmail.SMTP(to_email)
    
    yag.send(to = to_email, subject = 'DailyMint Update', contents = html)
    print('email sent')
    return

def write_to_file(html):
    f = open("test\email.html", "w")
    f.write(html)
    f.close()
    print("Wrote to file email.html")

def test():
    credit_score, networth, txs_html, accts_html = extract_data_dummy()
    html = generate_html(credit_score, networth, txs_html, accts_html)
    #print(html)
    send_email(html)
    #write_to_file(html)

def print_help():
    print ("usage: python DailyMint.py setup (for the first time setup)\n\
       python DailyMint.py myemail@xyz.com (going forward)\n\
       python DailyMint.py test myemail@xyz.com (for testing)")

def setup():
    print ("One time setup")
    print("Input mint username:")
    mint_username = input()
    print("Input mint password:")
    mint_password = input()
    print("Input gmail username:")
    gmail_username = input()
    print("Input gmail password:")
    gmail_password = input()
    keyring.set_password('DialyMint', "username", mint_username)
    keyring.set_password('DailyMint',"password", mint_password)
    keyring.set_password('DailyMint',"gmail_username", gmail_username)
    keyring.set_password('yagmail', gmail_username, gmail_password)

    print("You entered: {},{},{},{}\nPlease run setup again if thats not right"\
        .format(mint_username, mint_password, gmail_username, gmail_password))

def main():
    # Options:
    # test email@example.com (for testing)
    # setup (for first time users)
    # email@example.com (going forward)

    if len(sys.argv) < 2:
        print_help()
        return
    elif((sys.argv[1] == 'test') and len(sys.argv) == 2): # user did not provide an email
        print_help()
        return
    elif(sys.argv[1] == 'setup'):
        setup()
    elif(sys.argv[1] == 'test' and len(sys.argv) == 3):
        test()
        return
    else:
        mint =  get_mint_handle()
        credit_score, networth, txs_html, accts_html = extract_data(mint)
        html = generate_html(credit_score, networth, txs_html, accts_html)
        #print(html)
        send_email(html)
        mint.close()

main()