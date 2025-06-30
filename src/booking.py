# Initialization and global variables
from seleniumbase import SB
import datetime
import requests
import time
import random
import json

from dotenv import load_dotenv
import os

load_dotenv()

with open('users.json', 'r') as file:
        users = json.load(file)

website_login = 'https://www.ssdcl.com.sg/User/Login'
website_booking = 'https://www.ssdcl.com.sg/User/Booking/BookingList'
website_basket = 'https://www.ssdcl.com.sg/User/Payment/ReviewItems'
website_confirm_payment = 'https://www.ssdcl.com.sg/User/Payment/ConfirmPurchase'

telegram_bot = 'driving_slots_bot'
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

telegram_message_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"

message = ''

usr = users['Alex']

# Telegram sender function
# message_send - message to send
def send_telegram_message(message_send, usr):
    payload = {
        "chat_id": usr['chat_id'],
        "text": message_send
    }

    try:
        response = requests.post(telegram_message_url, data=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        print("Message sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

# Slots selection
# msg - available slots; usr - get user profile
def slot_selection(msg, usr):
    
    slots_to_book = usr['slots']

    available_booking = {}
    potential_booking = []
    slots_selected = []

    slots_on_date = {}
    slots_double = []
    slots_single = []
    slots_single_temp = []

    for ms in msg:
        available_booking[ms.split('_')[2].split(' ')[0] + 'S' + ms.split('_')[1]] = ms

    for book in available_booking:
        if book in slots_to_book:
            potential_booking.append(available_booking[book])
    
    message = "Potential booking: " + str(potential_booking)
    
    with open("SSDC_log.txt", "a") as f:
            f.write(message+ '\n')
    print(message)

    for slot in potential_booking:
        day = slot.split('_')[2].split(' ')[0]
        interval = slot.split('_')[1]

        if day in slots_on_date:
            slots_on_date[day].append([interval, slot])
        else:
            slots_on_date[day] = [[interval, slot]]

    for date in slots_on_date:

        doubles = 0
        singles = 0
        if len(slots_on_date[date]) > 1:
            for i in range(len(slots_on_date[date])-1):
                if (int(slots_on_date[date][i+1][0]) == int(slots_on_date[date][i][0]) + 1) and (doubles == 0):
                    slots_double.append(slots_on_date[date][i][1])
                    slots_double.append(slots_on_date[date][i+1][1])
                    doubles = 1
                elif singles == 0:
                    slots_single_temp = slots_on_date[date][i][1]
                    singles = 1

            if doubles == 0:
                slots_single.append(slots_single_temp)

        else:
            slots_single.append(slots_on_date[date][0][1])

    slots_selected = slots_double + slots_single

    if len(slots_selected) > usr['N_slots_book']:
        slots_selected = slots_selected[:usr['N_slots_book']]

    message = "Selected booking: " + str(slots_selected)
    
    with open("SSDC_log.txt", "a") as f:
            f.write(message+ '\n')
    print(message)

    return slots_selected

# Sending selenium request
# usr - user to login
def selenium_request(usr):
    print("Start")
    with open("SSDC_log.txt", "a") as f:
        f.write("----------\n")
        f.write(str(datetime.datetime.now()) + '\n')
    chrome_binary_path = "/opt/google/chrome/google-chrome" 
    with SB(uc=True, xvfb=True, binary_location = chrome_binary_path, headless=True) as sb:
        print('SB started')
        user_agent = sb.driver.execute_script("return navigator.userAgent;")
        print(f"User-Agent: {user_agent}")
        try:
            sb.driver.uc_open_with_reconnect(website_login, 4)
            sb.sleep(2)
            # /// sb.save_screenshot(str(datetime.datetime.now()),folder='screenshots')
            sb.uc_gui_click_cf()
            #sb.uc_gui_handle_captcha()
            #sb.uc_gui_click_captcha()
            print(sb.get_page_title())
        except:
            send_telegram_message('CAPTCHA problem', usr)
            with open("SSDC_log.txt", "a") as f:             
                f.write('CAPTCHA problem' + '\n')
                print('CAPTCHA problem')

        print('Login')
       # try:
         # Login page
        sb.save_screenshot(str(datetime.datetime.now()),folder='screenshots')
        sb.type('input[name="UserName"]', usr['login'])
        sb.type('input[name="Password"]', usr['password'])
        sb.click("button.btn-general-form")
        
            # Class selection
        sb.uc_open(website_booking)
        sb.uc_gui_handle_cf()
        
        sb.click('select[name="scid"]')
        sb.click('option:contains("Class 2B")')
            # /// sb.uc_click('option:contains("Class 3")')
        
            # New booking selection
        sb.uc_gui_handle_cf()
        sb.click('a[id="btnNewBooking"]')

            # Check for booking
        sb.click('input[id="chkProceed"]')
        sb.click('a[id="lnkProceed"]')
        sb.sleep(1)
        '''
            except:
            send_telegram_message('Navigation problem', usr)
            with open("SSDC_log.txt", "a") as f:
                f.write('Navigation problem' + '\n')
                print('Navigation problem')
        '''
        print('Get availability')
        try:
            availability = []
            #message = ''
            # addon for course selector
            sb.click('select[name="BookingType"]')
            sb.click('option:contains("Theory Lesson")')

            sb.click('input[id="button-searchDate"]')
            if sb.is_element_visible('div[id="modalMsgContent"]'):
                with open("SSDC_log.txt", "a") as f:
                    message = sb.get_text('div[id="modalMsgContent"]')
                    f.write(message + '\n')
                    print(message)
            else:
                sb.click('a[id="btn_checkforava"]')
                
                if sb.is_element_visible('div[id="modalMsgContent"]'):
                    with open("SSDC_log.txt", "a") as f:
                        message = sb.get_text('div[id="modalMsgContent"]')
                        f.write(message + '\n')
                        print(message)
                else:
                    available_bookings = sb.find_elements('a.slotBooking')
                            
                    # iterating through available slots
                    for book in available_bookings:
                        availability.append(book.get_attribute("id"))

                    message = list(set(availability))

                    with open("SSDC_log.txt", "a") as f:
                        f.write(str(message)+ '\n')
                        print(message)
                    
                    selected = slot_selection(message, users['Alex'])
                    
                    # Selecting slots to bucket
                    for slot in selected:
                        sb.click('a[id="' + slot + '"]')
                        sb.click('button.btn-general-short')
                    
                    # Calling a bucket, confirming purchase and making payment
                    sb.uc_open(website_basket)
                    sb.uc_open(website_confirm_payment)
                    #sb.click('a[id=makePayment]')

                    slots_booked = ''
                    for slot in selected:
                        slots_booked = slots_booked + slot.split('_')[2].split(' ')[0] + ' S' + slot.split('_')[1] + '\n'
                        
                    message = "Slots booked:\n" + '- ' + str(slots_booked)
            
            send_telegram_message(message, usr)
        except:
            send_telegram_message('Booking problem',usr)
            with open("SSDC_log.txt", "a") as f:
                f.write('Booking problem' + '\n')
                print('Booking problem')

selenium_request(usr)
