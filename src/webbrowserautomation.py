import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

import config

api_key_edit_web_address = 'https://www.binance.com/es/my/settings/api-management'


def reload_firefox(firefox_instance):
    try:
        firefox_instance.close()
        print("Reloading firefox")
    except Exception:
        pass

    # Instantiate Firefox
    options = webdriver.FirefoxOptions()
    if os.name == 'nt':
        options.binary_location = r"C:\Users\jtorres\AppData\Local\Mozilla Firefox\firefox.exe"

    firefox = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()),
                                options=options)

    return firefox


firefox = reload_firefox(None)
firefox.get(api_key_edit_web_address)
print("Acepta las cookies. 10 s para continuar.")
time.sleep(10)

iniciar_sesion_text = firefox.find_element(by=By.ID, value="switch_login")
iniciar_sesion_text.click()

user_textbox = firefox.find_element(by=By.ID, value='username')
user_textbox.send_keys(config.BINANCE_USER)

print('Esperando 10s')
time.sleep(10)
siguiente_button = firefox.find_element(by=By.ID, value='click_login_submit')
siguiente_button.click()

print('Esperando 30s para captcha')
time.sleep(30)

pass_textbox = firefox.find_element(by=By.NAME, value="password")
pass_textbox.send_keys(config.BINANCE_PASS)

print('Esperando 10s')
time.sleep(10)
siguiente_button = firefox.find_element(by=By.ID, value='click_login_submit')
siguiente_button.click()

print('Esperando 2 minutos para verificaciones')