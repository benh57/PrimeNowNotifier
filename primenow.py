from cefpython3 import cefpython as cef

import bs4
import time
import platform
import sys

settings = {
    "debug": False,
    "log_severity": cef.LOGSEVERITY_INFO,
    "log_file": "debug.log"
}

options = {
    "username": "<AMAZONEMAIL>",
    "password": "<AMAZONPW>"
}

browser = None

BASE_URL = "https://primenow.amazon.com/"
CART_URL = "https://primenow.amazon.com/cart"
CHECKOUT_URL = "https://primenow.amazon.com/checkout/enter-checkout"


def set_javascript_bindings(browser):
    bindings = cef.JavascriptBindings(bindToFrames=False, bindToPopups=False)
    #  bindings.SetFunction("html_to_data_uri", html_to_data_uri)
    browser.SetJavascriptBindings(bindings)


def set_client_handlers(browser):
    client_handlers = [LoadHandler()]
    for handler in client_handlers:
        browser.SetClientHandler(handler)


class ParseCheckoutVisitor(object):
    def Visit(self, value):
        print(value)
        soup = bs4.BeautifulSoup(value, features="html.parser")
        try:
            link = soup.find('span', class_='cart-checkout-button').find("a")
            if link:
                dest = link['href']
                print("Found link href {}{}".format(BASE_URL.strip('/'), dest))
                browser.ExecuteJavascript("window.location.href = \"{}{}\"".format(BASE_URL.strip('/'), dest))
                return
            else:
                print("Found no link under the checkout span!")

        except AttributeError: 
                print('Could not find checkout button!')

checkoutvisitor = ParseCheckoutVisitor()


class TimeSlotVisitor(object):
    def Visit(self, value):
        no_slot_pattern = 'No delivery windows available'
        if no_slot_pattern in value:
            print("NO SLOTS! Sleep a bit, then reloadPage... ")
            time.sleep(30)
            browser.Reload()
        else:
            print('SLOTS OPEN!')
            while 1:
                os.system('say "Slots for delivery opened"')
                time.sleep(30)

timeslotvisitor = TimeSlotVisitor()


class LoadHandler(object):
    def OnLoadingStateChange(self, browser, is_loading, **_):
        # This callback is called twice, once when loading starts
        # (is_loading=True) and second time when loading ends
        # (is_loading=False).
        if not is_loading:
            print("Load complete!")

            url = browser.GetUrl()

            print("url: {}".format(url))
            if url == BASE_URL:
                print("Main page, Attempting to nav to Cart...")
                browser.ExecuteJavascript("window.location.href = '{}'".format(CART_URL))
            elif url.startswith("https://primenow.amazon.com/ap/signin"):
                print("Signin page, Attempting to sign in...")
                browser.ExecuteJavascript("document.getElementById('ap_email').value = '{}'".format(options["username"]))
                browser.ExecuteJavascript("document.getElementById('ap_password').value = '{}'".format(options["password"]))
                #browser.ExecuteJavascript("document.signIn.submit()")
            elif url.startswith("https://primenow.amazon.com/ap/mfa"):
                print("MFA Page. Enter your amazon MFA code.")
            elif url.startswith(CART_URL):
                print("Cart page, navigate to first order page...")
                browser.GetMainFrame().GetSource(checkoutvisitor)
            elif url.startswith(CHECKOUT_URL):
                print("On checkout page! Check for timeslots....")
                browser.GetMainFrame().GetSource(timeslotvisitor)
            else:
                print("Did not match any case urls. Doing nothing.")


def main():
    global browser
    check_versions()
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize(settings=settings)
    browser = cef.CreateBrowserSync(url="https://primenow.amazon.com/signin")
    set_client_handlers(browser)
    set_javascript_bindings(browser)
    #  browser.ShowDevTools()
    cef.MessageLoop()
    cef.Shutdown()


def check_versions():
    ver = cef.GetVersion()
    print("[primenow.py] CEF Python {ver}".format(ver=ver["version"]))
    print("[primenow.py] Chromium {ver}".format(ver=ver["chrome_version"]))
    print("[primenow.py] CEF {ver}".format(ver=ver["cef_version"]))
    print("[primenow.py] Python {ver} {arch}".format(
        ver=platform.python_version(), arch=platform.architecture()[0]))
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"


if __name__ == '__main__':
    main()
