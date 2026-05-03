from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
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
    Checks if a URL (with payload) triggers JS execution (XSS).
    Uses CDP to intercept window.alert/confirm/prompt before the page loads,
    so detection works regardless of how Selenium handles dialog boxes.
    """
    driver = None
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=800,600")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.set_page_load_timeout(timeout)

        # Intercept alert/confirm/prompt via CDP before any page loads.
        # addScriptToEvaluateOnNewDocument runs on every navigation in this session,
        # so autofocus/onload/onerror payloads are captured even when they fire
        # synchronously during page load (before Selenium can switch_to.alert).
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                window._awast_xss = false;
                window._awast_msg = '';
                const _capture = function(msg) {
                    window._awast_xss = true;
                    window._awast_msg = String(msg !== undefined ? msg : '(no message)');
                };
                window.alert   = _capture;
                window.confirm = function(m) { _capture(m); return true; };
                window.prompt  = function(m) { _capture(m); return ''; };
            """
        })

        if cookies:
            try:
                domain_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
                driver.get(domain_url)
                for name, value in cookies.items():
                    driver.add_cookie({"name": name, "value": value})
            except Exception as ce:
                print(f"[!] Warning: Could not set cookies: {ce}")

        try:
            driver.get(url)
        except UnexpectedAlertPresentException:
            # Fallback: alert dialog appeared before CDP intercept could catch it
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                return True, f"XSS Triggered during page load! Alert: {alert_text}"
            except Exception:
                return True, "XSS Triggered during page load!"

        # Poll every 100ms for up to 2500ms (mirrors JS checkForMockAlert)
        poll_interval = 0.1
        poll_timeout = 2.5
        elapsed = 0.0
        while elapsed < poll_timeout:
            # Primary check: did our interceptor catch a JS call?
            try:
                if driver.execute_script("return window._awast_xss === true;"):
                    msg = driver.execute_script("return window._awast_msg;") or ""
                    return True, f"XSS Triggered! JS executed: alert('{msg}')"
            except Exception:
                pass

            # Fallback: real pending alert dialog
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                return True, f"XSS Triggered! Alert text: {alert_text}"
            except NoAlertPresentException:
                pass
            except Exception:
                pass

            time.sleep(poll_interval)
            elapsed += poll_interval

        return False, "No alert detected."

    except Exception as e:
        return False, f"Error during DOM XSS check: {str(e)}"
    finally:
        if driver:
            driver.quit()
