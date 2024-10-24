import contextlib
import sys
from time import sleep, time_ns
import signal

from playwright.sync_api import Playwright, sync_playwright

from helpers.helper_functions import log_note, get_random_text, login_nextcloud, close_modal, timeout_handler


def run(playwright: Playwright, browser_name: str) -> None:
    log_note(f"Launch browser {browser_name}")
    if browser_name == "firefox":
        browser = playwright.firefox.launch(headless=True)
    else:
        # this leverages new headless mode by Chromium: https://developer.chrome.com/articles/new-headless/
        # The mode is however ~40% slower: https://github.com/microsoft/playwright/issues/21216
        browser = playwright.chromium.launch(headless=False,args=["--headless=new"])
    context = browser.new_context()
    page = context.new_page()
    try:
        log_note("Login")
        page.goto("http://nc/")
        login_nextcloud(page)

        log_note("Create new text file")
        page.get_by_role("link", name="Files").click()
        page.get_by_role("link", name="New file/folder menu").click()
        page.get_by_role("link", name="New text file").click()
        page.locator("#view7-input-file").fill("colab_meeting.md")
        page.locator("#view7-input-file").press("Enter")
        page.get_by_role("button", name="Create a new file with the selected template").click()

        close_modal(page)

        page.keyboard.press("Escape")
        log_note("Share file with other user")
        page.get_by_role("link", name="colab_meeting .md").get_by_role("link", name="Share").click()
        page.get_by_placeholder("Name, email, or Federated Cloud ID …").click()
        page.get_by_placeholder("Name, email, or Federated Cloud ID …").fill("docs")
        page.get_by_text("docs_dude").first.click()
        page.get_by_text("Save Share").first.click()
        log_note("Close browser")
        page.close()

        # ---------------------
        context.close()
        browser.close()
    except Exception as e:
        if hasattr(e, 'message'): # only Playwright error class has this member
            log_note(f"Exception occurred: {e.message}")

        # set a timeout. Since the call to page.content() is blocking we need to defer it to the OS
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)
        log_note(f"Page content was: {page.content()}")
        signal.alarm(0) # remove timeout signal

        raise e


with sync_playwright() as playwright:
    if len(sys.argv) > 1:
        browser_name = sys.argv[1].lower()
        if browser_name not in ["chromium", "firefox"]:
            print("Invalid browser name. Please choose either 'chromium' or 'firefox'.")
            sys.exit(1)
    else:
        browser_name = "chromium"

    run(playwright, browser_name)
