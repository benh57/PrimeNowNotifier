from cefpython3 import cefpython as cef

import bs4
import time
import platform
import sys
import os
import argparse

settings = {
    "debug": False,
    "log_severity": cef.LOGSEVERITY_ERROR,
    "log_file": "debug.log"
}

options = {
    "username": "<AMAZONEMAIL>",
    "password": "<AMAZONPW>"
}

browser = None
notifications = []
pushbullet_api_key = None

# Webhook example for IFTTT maker channel
# If <Webhook> then <anything>...
# Create if 'webhook' event triggered with 'event' trigger 'primenow'
#
# Get your webhook url from the webhook channel settings, example:
#    https://maker.ifttt.com/trigger/primenow/with/key/<webhookkey>
#
webhook_url = None

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


def webhookNotification():
    import requests
    response = requests.post(
        webhook_url, data={},
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Webhook request returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )


def speakNotification():
    os.system('say "Slots for delivery opened"')


def pushBulletNotification():
    from pushbullet import Pushbullet
    pb = Pushbullet(pushbullet_api_key)
    push = pb.push_note("Prime Now Slots Open!", "Prime Now Delivery Slots have opened!")


class TimeSlotVisitor(object):
    def Visit(self, value):
        no_slot_pattern = 'No delivery windows available'
        if no_slot_pattern in value:
            print("NO SLOTS! Sleep a bit, then reloadPage... ")
        else:
            print('SLOTS OPEN!')
            for notification in notifications:
                notification()

        time.sleep(30)
        browser.Reload()

timeslotvisitor = TimeSlotVisitor()


class LoadHandler(object):
    def OnLoadingStateChange(self, browser, is_loading, **_):
        # This callback is called twice, once when loading starts
        # (is_loading=True) and second time when loading ends
        # (is_loading=False).
        if not is_loading:
            url = browser.GetUrl()

            print("At url: {}".format(url))
            if url == BASE_URL:
                print("Main page, Attempting to nav to Cart...")
                browser.ExecuteJavascript("window.location.href = '{}'".format(CART_URL))
            elif url.startswith("https://primenow.amazon.com/ap/signin"):
                print("Signin page, Please sign in...")
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
    global pushbullet_api_key
    global browser
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--webhook-url', help='Enable webhook notiifcations to specified url')
    parser.add_argument('-s', '--enable-say', action='store_true', help='Enable speech notiifcations')
    parser.add_argument('-p', '--enable-pushbullet', action='store_true', help='Enable pushbullet notiifcations')
    parser.add_argument('-k', '--pushbullet_key', help='Pushbullet API Key')
    parser.add_argument('-u', '--username', help='Amazon Username (optional for autocomplete)')

    parsed_args = parser.parse_args()

    if parsed_args.pushbullet_key:
        pushbullet_api_key = parsed_args.pushbullet_key

    if parsed_args.webhook_url:
        webhook_url = parsed_args.webhook_url      

    if parsed_args.enable_pushbullet:
        if not pushbullet_api_key:
            print("ERROR: Must set a valid PUSHBULLET_API_KEY via -k or hardcode into the script.")
            exit(1)
        print("PushBullet support enabled.")
        notifications.append(pushBulletNotification)

    if parsed_args.enable_say:
        print("Speech support enabled.")
        notifications.append(speakNotification)

    if parsed_args.webhook_url:
        print("Webhook support enabled.")
        notifications.append(webhookNotification)

    if parsed_args.username:
        options['username'] = parsed_args.username

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
