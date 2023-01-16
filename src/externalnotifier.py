import requests


# TO FIND CHAT ID
# TOKEN = "TOKEN"
# url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
#
# print(requests.get(url).json())


def send_telegram_message(token, chat_id, message):
    """
    Sends a telegram message through the specified bot token and chat id
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"

    # Send the message
    requests.get(url).json()
