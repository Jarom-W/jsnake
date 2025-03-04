import requests
import base64
import urllib.parse
import tkinter as tk
from tkinter import simpledialog, messagebox

appKey = 'E6F6dwf8WsATpmWuIY2lg9fld1CTYvFo'
appSecret = 'qfJFGzH97U2OI6Ak'
callbackURL = 'https://127.0.0.1'


def getAccessToken(appKey, appSecret, callbackURL):
    authURL = f'https://api.schwabapi.com/v1/oauth/authorize?client_id={appKey}&redirect_uri={callbackURL}&response_type=code'
    print(f"Click to authenticate: {authURL}")

    root = tk.Tk()
    root.withdraw()

    reLink = simpledialog.askstring("Authentication URL", "Please paste the URL here:")

    if not reLink:
        print("No URL was entered. Exiting.")
        return None

    try:
        code = reLink.split('code=')[1].split('&')[0]
        code = urllib.parse.unquote(code)
    except (IndexError, AttributeError):
        print("Invalid URL. Couldn't extract authorization code.")
        return None

    encoded_creds = base64.b64encode(f'{appKey}:{appSecret}'.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_creds}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': callbackURL
    }

    token_url = 'https://api.schwabapi.com/v1/oauth/token'
    response = requests.post(url=token_url, headers=headers, data=data)

    if response.status_code != 200:
        print("Failed to retrieve access token.")
        print(response.json())
        return None

    res = response.json()
    print("Access Token Retrieved")
    return res['access_token']


def getExpirations(access_token, symbol):
    url = f'https://api.schwabapi.com/markets/options/expirations?symbol={symbol}'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('expirations', [])
    else:
        print("Failed to fetch expiration dates")
        return []


def getOptionsChain(access_token, symbol, expiration):
    url = f'https://api.schwabapi.com/markets/options/chains?symbol={symbol}&expirationDate={expiration}&strategy=SINGLE&strikeCount=10'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        options = response.json()
        print(f"Options Chain for {symbol} on {expiration}:")
        print(options)
    else:
        print("Failed to fetch options chain")
        print(response.json())


if __name__ == "__main__":
    access_token = getAccessToken(appKey, appSecret, callbackURL)
    if access_token:
        symbol = simpledialog.askstring("Stock Symbol", "Enter Stock Symbol:")
        expirations = getExpirations(access_token, symbol)

        if expirations:
            root = tk.Tk()
            root.withdraw()
            expiration = simpledialog.askstring("Expiration Dates", f"Available Expirations:\n{', '.join(expirations)}\n\nEnter Expiration Date:")

            if expiration in expirations:
                getOptionsChain(access_token, symbol, expiration)
            else:
                messagebox.showerror("Invalid Date", "The selected expiration is not available.")
        else:
            print("No expiration dates found.")
