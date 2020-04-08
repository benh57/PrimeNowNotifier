# Amazon Primt Now Automated Slot Check Script

Yes, amid COVID-19 trying to get Amazon Prime Now delivery slots can get cumbersome. To free you of the constant hassle of checking for slots (and almost never finding one), this automated script can notify you of when new delivery slots open.


## Usage:

Tested on Mac OS. 

_The script works after you have added all the items to your cart! Note, have your cart ready before running this script! 


### After you clone the project:

Optional (recommended): 
1. Install and activate a virtualenv. 
2. virtualenv . 
3. source bin/activate


To set up / run the script:

1. Run the requirements.txt (```$ pip install -r requirements.txt```)
2. Make sure you have a cart ready to go on your Prime Now website.
3. Run primenow.py (``` $ python primenow.py```)
4. When run this script, a chrome will pop up and Amazon will ask you to login. 
5. Log in, and enter OTP if prompted.
6. Script should navigate you to the 'checkout' page automatically and refresh every 30 seconds, looking for slots.

When a slot opens, the script will start yelling at you via the 'say' command.


### Credit

Using some ideas and code / inspiration from pcomputo: https://github.com/pcomputo/Whole-Foods-Delivery-Slot