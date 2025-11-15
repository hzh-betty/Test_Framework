import urllib.parse
import requests
import time
import hmac
import hashlib
import base64


def generate_sign():
    """
    Generate DingTalk robot signature.
    Uses HMAC-SHA256 with timestamp and secret, then Base64 encode and URL encode.
    :return: timestamp, signature
    """
    # Current timestamp in milliseconds
    timestamp = str(round(time.time() * 1000))
    # DingTalk robot secret
    secret = '123'
    secret_enc = secret.encode('utf-8')
    # String to sign: "timestamp\secret"
    str_to_sign = '{}\n{}'.format(timestamp, secret)
    str_to_sign_enc = str_to_sign.encode('utf-8')
    # HMAC-SHA256 signature
    hmac_code = hmac.new(secret_enc, str_to_sign_enc, digestmod=hashlib.sha256).digest()
    # Base64 encode and URL encode
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def send_dd_msg(content_str, at_all=True):
    """
    Send a message to DingTalk robot.
    :param content_str: message content
    :param at_all: whether to @all
    :return: server response
    """
    timestamp_and_sign = generate_sign()
    # Construct webhook URL with access_token, timestamp, and sign
    url = f'https://oapi.dingtalk.com/robot/send?access_token=75d6628cefedc8225695dcde2577f03336f0099cd16d93988a68ad243cf9dd6f&timestamp={timestamp_and_sign[0]}&sign={timestamp_and_sign[1]}'
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    # Message payload
    data = {
        "msg_type": "text",
        "text": {"content": content_str},
        "at": {"isAtAll": at_all},
    }
    res = requests.post(url, json=data, headers=headers)
    return res.text
