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
