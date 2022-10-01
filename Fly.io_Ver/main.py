from asyncio import events
from itertools import count
from pickle import GLOBAL
import os, urllib
import flask
from flask import Flask
from linebot import LineBotApi, WebhookHandler

app = Flask(__name__)

##取得綁訂的URL
#==============================================================================================#
# os.environ[''] => 我把值都設在Heroku上,他會去找到相對應的值填進來
line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN']) # Line-Bot 的 Access_Token
handler = WebhookHandler(os.environ['CHANNEL_SECRET'])        # Line-Bot 的 Channel_secret

client_id = os.environ['NOTIFY_CLIENT_ID']                    # Notify 的 Clinet_ID
client_secret = os.environ['NOTIFY_CLIENT_SECRET']            # Notify 的 Clinet_Secret

redirect_uri = f"https://{os.environ['YOUR_HEROKU_APP_NAME']}.herokuapp.com/callback/notify" #回傳地點,你的 Notify 的網址

#把回傳結果包成我們能綁定的網址
def create_auth_link(user_id, client_id=client_id, redirect_uri=redirect_uri):
    #把資料包成jason檔格式 => data
    data = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'notify',
        'state': user_id
    }
    query_str = urllib.parse.urlencode(data)

    return f'https://notify-bot.line.me/oauth/authorize?{query_str}'
    #最後把它包成我們能跟 Line 交換 Access_Token 的網址,也就是綁定的網址
#==============================================================================================#

##拿取幫綁訂人的 Access_token
#==============================================================================================#
import json
def get_token(code, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri):
    url = 'https://notify-bot.line.me/oauth/token'
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    page = urllib.request.urlopen(req).read()
    res = json.loads(page.decode('utf-8'))
    return res['access_token']      #拆解後拿取 Access_Token
#==============================================================================================#

##利用notify發出訊息
#==============================================================================================#
def send_message(access_token, text_message):
    url = 'https://notify-api.line.me/api/notify'
    headers = {"Authorization": "Bearer "+ access_token}
    data = {'message': text_message}
    data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    page = urllib.request.urlopen(req).read() #看是否成功 Ex: {"status":200,"message":"ok"}
#==============================================================================================#

##利用Google Sheet當資料庫
#==============================================================================================#
import pygsheets

#給憑證
gc = pygsheets.authorize(service_file='Licence.json')

# 開啟 Google Sheet
# Url Ex:https://docs.google.com/spreadsheets/d/!@#$%^$%^&*@#$%^/
sheet = gc.open_by_url( 'Your google sheet url' )

def google_sheet(client_id,access_token):
    global Group_id , User_id,Flag

    if Group_id == '' :
        wks = sheet.worksheet_by_title("Person") #找到 Person 分頁並在裡面操作
        Flag='0'
        Count = int( wks.cell( 'C1' ).value )+1  #人數
        index_clinet_id = ""    #先 clear
        #找直列有沒有一樣的,有一樣的就只改 Access_Token
        for i in range( 1 , int(Count) ) :   #他會跑 1 ~ Count (從1到Count,Count那次不會跑)
            index_clinet_id = str(wks.cell( 'A'+str(i) ).value)
            if str(index_clinet_id) == str(client_id) :
                wks.update_value('B'+str(i), access_token)
                Flag='1'
                break #拿到並跳出
        #如果沒有找到就新增資料
        if Flag == '0' :
            Count = int( wks.cell( 'C1' ).value )+1 #新增綁定人資料並統計人數,並讓下次可以跑進迴圈
            wks.update_value('A'+str(Count), client_id) #新增資料
            wks.update_value('B'+str(Count), access_token) #新增資料
            wks.update_value('C'+str(Count), User_id) #新增資料
            wks.update_value('C1', Count)  #更新人數
        User_id = ''
    else:
        wks = sheet.worksheet_by_title("Group")   #找到 Group 分頁並在裡面操作
        Flag='0'
        Count = int( wks.cell( 'C1' ).value )+1   #人數+1
        index_Group_id = ""    #先clear
        #找直列有沒有一樣的,有一樣的就只改 Access_Token
        for i in range( 1 , int(Count) ) :   #他會跑1~Count (從1到Count,Count那次不會跑)
            index_Group_id = str(wks.cell( 'A'+str(i) ).value)
            if str(index_Group_id) == str(Group_id) :
                wks.update_value('B'+str(i), access_token)
                Flag='1'
                break #拿到並跳出
        #如果沒有找到就新增資料
        if Flag == '0' :
            Count = int( wks.cell( 'C1' ).value )+1     #人數+1
            wks.update_value('A'+str(Count), str(Group_id)) #新增資料
            wks.update_value('B'+str(Count), access_token) #新增資料
            wks.update_value('C1', Count)  #更新人數
        Group_id=''
#==============================================================================================#

##利用 handler 處理 LINE 觸發事件
#==============================================================================================#
from linebot.models import MessageEvent, TextMessage, TextSendMessage
Group_id = str   #用來紀錄群組名稱
User_id = str    #用來紀錄使用者名稱
Flag = str       #判定是否重複的值
@handler.add(MessageEvent, message=TextMessage) #監聽當有新訊息時
def handle_message(event):
    global Group_id , User_id
    if event.message.text == "個人訂閱" :
        url = create_auth_link(event)
        #回傳 url 給傳訊息的那 個人 or 群組
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=url) )
        #這邊是利用 event 內的 user_id 去跟 Line 拿到使用者的當前 Line 使用的名子 Ex: Zi-Yu(林子育)
        User_id = line_bot_api.get_profile(event.source.user_id).display_name
        Group_id = ''
    elif event.message.text == "群組訂閱" :
        url = create_auth_link(event)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=url) )
        #因為 event 內只會回傳個人訊息所以無法找到 Group 的名稱,所以只能改拿 Group 的 id
        Group_id = (event.source.group_id)   #Group_id get!
        User_id = ''

#==============================================================================================#


##利用 route 處理指定路由
#==============================================================================================#
from flask import request, abort
from linebot.exceptions import InvalidSignatureError

@app.route("/callback", methods=['POST'])   #當 /callback 這個網頁收到 POST 時會做動
def callback():

    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@app.route("/callback/notify", methods=['GET'])  #當 /callback/notify 這個網頁收到 GET 時會做動
def callback_nofity():
    code = request.args.get('code')

    # Get Access-Token
    access_token = get_token(code, client_id, client_secret, redirect_uri)

    google_sheet(client_id,access_token)    #回傳 Client_id and Access_Token 去紀錄
    send_message(access_token,text_message="你好")   #發訊息

    return '恭喜完成 LINE Notify 連動！請關閉此視窗。'  #網頁顯示
#==============================================================================================#

