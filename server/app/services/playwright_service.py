from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from typing import Tuple, Dict, Any, Optional
from urllib.parse import urlparse


def login_and_save_session(
    login_url: str,
    username: str,
    password: str,
    session_file: str = "session.json",
    headless: bool = True,
    slow_mo: int = 0,
) -> dict:

    print(f"[+] Цель: {login_url}")

    driver = None

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

        return cookies_dict

    except Exception as e:
        print(f"[!] Ошибка: {e}")
        raise Exception(str(e))
    finally:
        if driver:
            driver.quit()


def check_dom_xss(
    url: str,
    cookies: dict = None,
    headless: bool = True,
    timeout: int = 15
) -> Tuple[bool, str]:
    """
    Checks if a URL (with payload) triggers an alert dialog or other indicators of XSS.
    Returns (is_vulnerable, message)
    """
    driver = None
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=800,600")
        chrome_options.add_argument("--disable-gpu")
        # To avoid being blocked by some WAFs or security headers in headless mode
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.set_page_load_timeout(timeout)

        # Set cookies if provided
        if cookies:
            # We need to be on the domain to set cookies
            try:
                domain_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
                driver.get(domain_url)
                for name, value in cookies.items():
                    driver.add_cookie({"name": name, "value": value})
            except Exception as ce:
                print(f"[!] Warning: Could not set cookies: {ce}")

        # Navigate to the target URL with payload
        driver.get(url)
        
        # Give it a moment to execute JS
        time.sleep(3)

        is_vulnerable = False
        message = "No alert detected."

        try:
            # Check for alert
            alert = driver.switch_to.alert
            alert_text = alert.text
            is_vulnerable = True
            message = f"XSS Triggered! Alert text: {alert_text}"
            alert.accept()
        except:
            # No alert, check if payload is in DOM but maybe not executed
            pass

        return is_vulnerable, message

    except Exception as e:
        return False, f"Error during DOM XSS check: {str(e)}"
    finally:
        if driver:
            driver.quit()
