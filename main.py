from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

import json
import requests

from googletrans import Translator

from config import * 

app = Flask(__name__)
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    print(body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def translate_text(text,dest='en'):
    translator = Translator()
    result = translator.translate(text, dest).text
    return result

import mplfinance as mpf
import pandas_datareader.data as web
import pyimgur

IMGUR_CLIENT_ID = imgur_client_id

def plot_stock_k_chart(IMGUR_CLIENT_ID,stock="0050" , date_from='2021-01-01' ):
    stock =str(stock)+".tw"
    df = web.DataReader(stock, 'yahoo', date_from)
    mpf.plot(df,type='candle',mav=(5,20),volume=True, ylabel=stock.upper()+' Price' ,savefig='testsave.png')
    PATH ="testsave.png"
    im = pyimgur.Imgur(IMGUR_CLIENT_ID)
    uploaded_image = im.upload_image(PATH, title=stock + "candlestick chart")
    return uploaded_image.link

cities = ['基隆市','嘉義市','臺北市','嘉義縣','新北市','臺南市','桃園縣','高雄市','新竹市','屏東縣','新竹縣','臺東縣','苗栗縣','花蓮縣','臺中市','宜蘭縣','彰化縣','澎湖縣','南投縣','金門縣','雲林縣','連江縣']

WEATHER_TOKEN = weather_api

def get(city):
    token = 'CWB-C1DEF032-86A8-4021-846E-3540A5B6453E'
    url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=' + token + '&format=JSON&locationName=' + str(city)
    Data = requests.get(url)
    app.logger.info("Request body: " + str(Data))
    print(str(Data))
    Data = (json.loads(Data.text))['records']['location'][0]['weatherElement']
    res = [[] , [] , []]
    for j in range(3):
        for i in Data:
            res[j].append(i['time'][j])
    return res

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message_type = event.message.type
    user_id = event.source.user_id
    reply_token = event.reply_token
    message = event.message.text
    if event.message.text[:3] == "@翻英":
        content = translate_text(event.message.text[3:], "en")
        message = TextSendMessage(text=content)
        line_bot_api.reply_message(event.reply_token, message)
    if event.message.text[:3] == "@翻日":
        content = translate_text(event.message.text[3:] , "ja")
        message = TextSendMessage(text=content)
        line_bot_api.reply_message(event.reply_token, message)
    if event.message.text[:3] == "@翻中":
        content = translate_text(event.message.text[3:] , "zh-tw")
        message = TextSendMessage(text=content)
        line_bot_api.reply_message(event.reply_token, message)
    if event.message.text[:2].upper() == "@K" :
        input_word = event.message.text.replace(" ","") 
        stock_name = input_word[2:6] 
        start_date = input_word[6:] 
        content = plot_stock_k_chart(IMGUR_CLIENT_ID,stock_name,start_date)
        message = ImageSendMessage(original_content_url=content,preview_image_url=content)
        line_bot_api.reply_message(event.reply_token, message)
    #  -----查詢天氣的指令
    if(message[:2] == '天氣'):
        city = message[3:]
        city = city.replace('台','臺')
        if(not (city in cities)):
            line_bot_api.reply_message(reply_token,TextSendMessage(text="查詢格式為: 天氣 縣市"))
        else:
            res = get(city)
            line_bot_api.reply_message(reply_token, TemplateSendMessage(
                alt_text = city + '未來 36 小時天氣預測',
                template = CarouselTemplate(
                    columns = [
                        CarouselColumn(
                            thumbnail_image_url = 'https://imgur.com/2Wu1rWG.png',
                            title = '{} ~ {}'.format(res[0][0]['startTime'][5:-3],res[0][0]['endTime'][5:-3]),
                            text = '天氣狀況 {}\n溫度 {} ~ {} °C\n降雨機率 {}'.format(data[0]['parameter']['parameterName'],data[2]['parameter']['parameterName'],data[4]['parameter']['parameterName'],data[1]['parameter']['parameterName']),
                            actions = [
                                URIAction(
                                    label = '詳細內容',
                                    uri = 'https://www.cwb.gov.tw/V8/C/W/County/index.html'
                                )
                            ]
                        )for data in res
                    ]
                )
            ))
    else:
        line_bot_api.reply_message(reply_token, TextSendMessage(text=message))



import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 80))
    app.run('0.0.0.0', port=port)