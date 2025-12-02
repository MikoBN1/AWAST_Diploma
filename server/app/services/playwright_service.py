from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json


def login_and_save_session(
    login_url: str,
    username: str,
    password: str,
    session_file: str = "session.json",
    headless: bool = True,
    slow_mo: int = 0,
) -> dict:

    print(f"[+] Цель: {login_url}")

    driver = None  # ключевой фикс

    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=800,600")
        chrome_options.add_argument("--disable-gpu")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        driver.get(login_url)
        time.sleep(1 + slow_mo / 1000)

        print("[+] Заполняю логин...")
        try:
            driver.find_element(By.NAME, "username").send_keys(username)
        except:
            driver.find_element(By.ID, "username").send_keys(username)

        print("[+] Заполняю пароль...")
        try:
            driver.find_element(By.NAME, "password").send_keys(password)
        except:
            driver.find_element(By.ID, "password").send_keys(password)

        print("[+] Нажимаю кнопку входа...")
        for selector in [
            "//input[@type='submit']",
            "//button[@type='submit']",
            "//button[contains(text(),'Login')]",
            "//input[@value='Login']",
        ]:
            try:
                driver.find_element(By.XPATH, selector).click()
                break
            except:
                pass

        print("[+] Жду загрузки...")
        time.sleep(2 + slow_mo / 1000)

        if "login" in driver.current_url.lower():
            raise Exception("Login failed")

        cookies = driver.get_cookies()
        session = {"cookies": cookies}

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2)

        print(f"[+] Сессия сохранена в {session_file}")

        cookies_dict = {c["name"]: c["value"] for c in cookies}
        cookies_dict["security"] = "low"

        driver.quit()
        return cookies_dict

    except Exception as e:
        print(f"[!] Ошибка: {e}")
        if driver:
            driver.quit()
        raise Exception(str(e))
