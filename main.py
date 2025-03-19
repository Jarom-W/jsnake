from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import torch
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn").to(device)
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--headless")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.bing.com")

    try:
        search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "q")))
        time.sleep(random.uniform(2, 4))
        search_box.send_keys("Donald Trump")
        search_box.send_keys(Keys.RETURN)
    except TimeoutException:
        print("Error: Bing search page did not load properly.")
        driver.quit()
        exit(1)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.b_algo")))
        results = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a")
        links = [result.get_attribute("href") for result in results[:5]]
    except TimeoutException:
        print("Error: No search results found.")
        driver.quit()
        exit(1)

    for idx, link in enumerate(links, 1):
        try:
            driver.get(link)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            article_text = driver.find_element(By.TAG_NAME, "body").text

            if not article_text.strip():
                print(f"{idx}. {link}\nError: Page has no readable content.\n")
                continue

            max_input_length = 1024
            encoded_article = tokenizer.encode(article_text, truncation=True, max_length=max_input_length, return_tensors="pt").to(device)
            output = model.generate(encoded_article, max_length=200, min_length=50, do_sample=False)
            summarized_text = tokenizer.decode(output[0], skip_special_tokens=True)
            print(f"{idx}. {link}\nSummary: {summarized_text}\n")
        except (TimeoutException, NoSuchElementException):
            print(f"{idx}. {link}\nError: Failed to load or parse content.\n")
        except Exception as e:
            print(f"{idx}. {link}\nUnexpected error: {e}\n")

except WebDriverException as e:
    print(f"WebDriver Error: {e}")
finally:
    driver.quit()

#Testing


















'''
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
'''