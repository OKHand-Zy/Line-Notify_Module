from apscheduler.schedulers.blocking import BlockingScheduler
from linebot import LineBotApi
from linebot.models import TextSendMessage
import urllib.request
import os
sched = BlockingScheduler()


#定時去戳 url 讓服務不中斷
@sched.scheduled_job('cron', day_of_week='mon-sun', minute='*/25')
def scheduled_job():
    url = "https://{Your Heroku App Name}.herokuapp.com/"
    conn = urllib.request.urlopen(url)
    for key, value in conn.getheaders():
        print(key, value)
    print("戳一下")

#每週 1~日 的 8:30 用 Line-Bot 去 push 一個 message 對象可以是 User 也可以是 Group
@sched.scheduled_job('cron', day_of_week='mon-sun', hour=8, minute=30)
def scheduled_job():
    line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
#   push message to one user or Group
    line_bot_api.push_message('Person or Group Access_Token', TextSendMessage(text='You want send message') )

#每週 3 的 10:00 用 Line-Bot 去 push 一個 message 對象可以是 User 也可以是 Group
@sched.scheduled_job('cron', day_of_week='wed', hour=10)
def scheduled_job():
    line_bot_api = LineBotApi(os.environ['CHANNEL_ACCESS_TOKEN'])
#   push message to one user or Group
    line_bot_api.push_message('Person or Group Access_Token', TextSendMessage(text='You want send message') )

sched.start()
