import sys
import contextlib
from time import time_ns

from playwright.sync_api import Playwright, sync_playwright

def log_note(message: str) -> None:
    timestamp = str(time_ns())[:16]
    print(f"{timestamp} {message}")

def create_user(playwright: Playwright, browser_name: str, username: str, password: str) -> None:
    log_note(f"Launch browser {browser_name}")
    if browser_name == "firefox":
        browser = playwright.firefox.launch(headless=True)
    else:
        # this leverages new headless mode by Chromium: https://developer.chrome.com/articles/new-headless/
        # The mode is however ~40% slower: https://github.com/microsoft/playwright/issues/21216
        browser = playwright.chromium.launch(headless=False,args=["--headless=new"])
    context = browser.new_context()
    try:
        page = context.new_page()
        log_note("Login")
        page.goto("http://nc/")
        page.get_by_label("Account name or email").click()
        page.get_by_label("Account name or email").fill("Crash")
        page.get_by_label("Account name or email").press("Tab")
        page.get_by_label("Password", exact=True).fill("Override")
        page.get_by_label("Password", exact=True).press("Enter")

        log_note("Wait for welcome popup")
        # Sleep to make sure the modal has time to appear before continuing navigation
        sleep(5)

        with contextlib.suppress(Exception):
            page.get_by_role("button", name="Close modal").click(timeout=15_000)
        log_note("Create user")
        page.get_by_role("link", name="Open settings menu").click()
        page.get_by_role("link", name="Users").first.click()
        page.get_by_role("button", name="New user").click()
        page.get_by_placeholder("Username").click()
        page.get_by_placeholder("Username").fill(username)
        page.get_by_placeholder("Username").press("Tab")
        page.get_by_placeholder("Display name").press("Tab")
        page.get_by_placeholder("Password", exact=True).fill(password)
        page.get_by_role("button", name="Add a new user").click()
        log_note("Close browser")

        # ---------------------
        page.close()
        context.close()
        browser.close()
    except Exception as e:
        if hasattr(e, 'message'): # only Playwright error class has this member
            log_note(f"Exception occurred: {e.message}")
        log_note(f"Page content was: {page.content()}")
        raise e


with sync_playwright() as playwright:
    if len(sys.argv) > 1:
        browser_name = sys.argv[1].lower()
        if browser_name not in ["chromium", "firefox"]:
            print("Invalid browser name. Please choose either 'chromium' or 'firefox'.")
            sys.exit(1)
    else:
        browser_name = "chromium"

    create_user(playwright, browser_name, username="docs_dude", password="docsrule!12")
