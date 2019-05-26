from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#DB connetion
import psycopg2

conn = psycopg2.connect(database="d9qhj5vp59kcbi", user="yrxbydaawwsgci", password="d578a56195e8bdd35fb51a8869003d2c1db5c2dcb71bff80f6ef0b5e307a3239", host="ec2-23-21-116-188.compute-1.amazonaws.com", port="5432")

print ("Opened database successfully")

cur = conn.cursor()


import sys
import urllib.parse
import datetime
import os
import random

app = Flask(__name__)

# token of line bot

import json
me=json.loads(open('line.json',encoding = 'utf8').read())
# Channel Access Token
line_bot_api = LineBotApi(me['token'])
# Channel Secret
handler = WebhookHandler(me['secret'])

# set routing
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature'] #驗證數位簽章
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK' # status code 200

# 呼叫時判斷時間區段
def getLasting(lag=0):
    nowHour=(datetime.datetime.now()+datetime.timedelta(hours=lag)).hour
    #print(nowHour,file=sys.stdout)
    if nowHour>=5 and nowHour<=10:
        return "morning"
    elif nowHour>10 and nowHour<=14:
        return "noon"
    elif nowHour>14 and nowHour<17:
        return "afternoon"
    elif nowHour>17 and nowHour<23:
        return "night"
    else:
        return "midnight"

# 輸入文字  回傳image物件
def calligraphy(text):
    urltext=urllib.parse.quote(text)
    url='https://www.moedict.tw/'+urltext+'.png?font=wt064'
    return ImageSendMessage(original_content_url=url,preview_image_url=url)

# 根據當前時間回傳問候物件
def greetingImage():
    lasting=getLasting(8) # UTC+8
    if lasting is "morning":
        morningImageLib=["https://stickershop.line-scdn.net/stickershop/v1/sticker/45626942/android/sticker.png",
                         "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626943/android/sticker.png",
                         "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626944/android/sticker.png",
                         "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626945/android/sticker.png",
                         "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626946/android/sticker.png"]
        url=random.choice(morningImageLib)
    elif lasting is "noon":
        noonImageLib=["https://stickershop.line-scdn.net/stickershop/v1/sticker/16942847/android/sticker.png",
                     "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626966/android/sticker.png",
                     "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626964/android/sticker.png",
                     "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626958/android/sticker.png"]
        url=random.choice(noonImageLib)
    elif lasting is "afternoon":
        url="https://stickershop.line-scdn.net/stickershop/v1/sticker/25268450/android/sticker.png"
    elif lasting is "night":
        nightImageLib=["https://stickershop.line-scdn.net/stickershop/v1/sticker/16942855/android/sticker.png",
                       "https://stickershop.line-scdn.net/stickershop/v1/sticker/16942852/android/sticker.png",
                       "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626986/android/sticker.png",
                       "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626980/android/sticker.png",
                       "https://stickershop.line-scdn.net/stickershop/v1/sticker/45626982/android/sticker.png"]
        url=random.choice(nightImageLib)
    elif lasting is "midnight":
        url="https://stickershop.line-scdn.net/stickershop/v1/sticker/45626986/android/sticker.png"

    return [TextSendMessage("您好，"+userName),ImageSendMessage(original_content_url=url,preview_image_url=url)]

def searchOrderHistory(id):
    sqlString="SELECT \"UNAME\",\"ORDER_TIME\",\"RESERV_TIME\",\"HOUR\",\"VERIFY\" FROM \"USER_INFO\" \
               WHERE \"UID\"='"+id+"' ORDER BY \"RESERV_TIME\""
    cur.execute(sqlString)
    conn.commit()
    rows=cur.fetchall()
    if len(rows)==0:
        return TextSendMessage(text="查無訂單紀錄")
    msg="歷史訂單資料如下:\n\n"
    for row in rows:
        #print(row, file=sys.stdout)
        msg+=("姓名: "+row[0]+" , 下單時間: "+row[1].strftime("%Y-%m-%d %H:%M")+" , 打掃時間: "+row[2].strftime("%Y-%m-%d %H:%M")+" , 時數: "+str(row[3])+"小時")
        if row[4]=="N":
            msg+=" (未完成)\n\n"
        else:
            msg+=" (已完成)\n\n"
    msg+="所有未開始的打掃排程皆可取消"

    if len(msg)<2000:
        return TextSendMessage(text=msg)
    else:
        return TextSendMessage(text="訂單過長，請聯絡客服")

def deleteOrder(id):
    nowTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sqlString="SELECT \"UNAME\",\"ORDER_TIME\",\"RESERV_TIME\",\"HOUR\" FROM \"USER_INFO\" WHERE \"UID\"='"+id+"' AND \"RESERV_TIME\">'"+nowTime+"' ORDER BY \"RESERV_TIME\""
    cur.execute(sqlString)
    conn.commit()
    rows=cur.fetchall()
    if len(rows)==0:
        return TextSendMessage(text="查無可取消的訂單")
    for row in rows:
        print(row, file=sys.stdout)


#根據line ID為每筆訂單建立一個class
class User():
    def __init__(self,id):
        self.id=id # lineID
        self.name="未輸入姓名" # 預約者名稱
        self.time=datetime.datetime.now() # 預約時間
        self.hour="未選擇時數" # 時數
        self.tel="未輸入電話" # 連絡電話
        self.action="init" # 初始狀態(init)/新增訂單(order)/查詢(search)/刪除(cancel)
        self.state="init" # 此訂單的狀態，系統判斷用
    #檢查訂單資料是否都被填寫 回傳填寫狀況
    #之後得新增更多防呆判斷
    def checkInfoComplete(self):
        if self.name=="" or self.name=="未輸入姓名":
            return "姓名"
        if self.tel=="" or self.tel=="未輸入電話":
            return "電話"
        if self.time=="" or self.time=="未選擇時間":
            return "未選擇時間"
        if self.hour=="" or self.hour=="未選擇時數":
            return "時數"
        return "complete"

#主選單
def showMainMenu():
    message = TemplateSendMessage(
        alt_text='主選單',
        template=ButtonsTemplate(
            title="功能主選單",
            text="請選擇要執行的操作",
            actions=[
                MessageAction(
                    label="立刻開始預約打掃",
                    text="立刻開始預約打掃"
                ),
                MessageAction(
                    label="查詢歷史訂單",
                    text="查詢歷史訂單"
                ),
                MessageAction(
                    label="取消預約",
                    text="取消預約"
                ),
                URIAction(
                    label="拜訪我們的網站",
                    uri="https://google.com"
                )
            ]
        )
    )
    return message

#新增訂單時顯示的menu
def showOrderMenu(order):
    message = TemplateSendMessage(
        alt_text='預約中',
        template=ButtonsTemplate(
            title="清潔服務預約中",
            text="下方顯示當前預約資料，點選以進行填寫或修改\n輸入 '確認' 以完成預約",
            actions=[
                MessageAction(
                    label=("姓名: "+order.name),
                    text="我要輸入姓名"
                ),
                MessageAction(
                    label=("電話: "+order.tel),
                    text="我要輸入電話"
                ),
                MessageAction(
                    label=("服務時數: "+order.hour),
                    text="我要輸入時數"
                ),
                DatetimePickerTemplateAction(
                    label=("服務時間: "+order.time.strftime("%m/%d %H:%M")),
                    data="input_daytime",
                    mode='datetime',
                    min= datetime.datetime.now().strftime("%Y-%m-%dt%H:%M")
                )
            ]
        )
    )
    return message



#加入好友時的歡迎訊息
@handler.add(FollowEvent)
def handle_follow(event):
    print("new follower: "+event.source.user_id, file=sys.stdout)
    name=line_bot_api.get_profile(event.source.user_id).display_name
    welcomeMsg=name+" 您好\n歡迎使用CleanUp清潔服務預約機器人\n馬上輸入任意文字開始體驗"
    alertMsg="第一次發話時可能需5~10秒回應\n請耐心等候🙏🙏"
    line_bot_api.reply_message(event.reply_token,[TextSendMessage(text=welcomeMsg),TextSendMessage(text=alertMsg)])


# 同時處理多位使用者時使用必須避免填到別人
# 使用currentUserList暫存追蹤所有正在下訂單(未完成送出)的人
# 完成下單後移出list
currentUserList=[]


# 處理Postback
@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data == 'input_daytime':
        reserveTime=event.postback.params['datetime'].replace("T"," ")
        print(reserveTime, file=sys.stdout)
        # find user
        for user in currentUserList:
            if user.id==event.source.user_id:
                user.time=datetime.datetime.strptime(reserveTime+":00", "%Y-%m-%d %H:%M:%S")
                line_bot_api.push_message(event.source.user_id, [TextSendMessage(text="服務時間已更新"),showOrderMenu(user)])



# 處理TextMessage
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global currentUserList
    #print(len(currentUserList), file=sys.stdout)
    userExist=False
    # 獲得用戶資訊
    userID=event.source.user_id # 由一串英數組成的ID
    profile = line_bot_api.get_profile(userID)
    userName=profile.display_name
    # 確保不要填到別人的資料
    for user in currentUserList: # 根據ID檢查訂單是否正在處理中
        if user.id==userID:
            userExist=True
            currentUser=user
    if not userExist: # 新訂單
        currentUser=User(userID)
        currentUserList.append(currentUser)


    #主選單部分
    if currentUser.action=="init":
        if currentUser.state=="init":
            msg="您好，歡迎使用Cleanup清潔服務預約機器人，請從以下選單選擇您想使用的服務"
            line_bot_api.reply_message(event.reply_token,[TextSendMessage(text=msg),showMainMenu()])
            currentUser.state="usingButton"
        elif currentUser.state=="usingButton":
            if event.message.text=="立刻開始預約打掃":
                line_bot_api.reply_message(event.reply_token,[TextSendMessage(text="正在協助您預約打掃，請依照指示操作"),showOrderMenu(currentUser)])
                currentUser.action="order"
                currentUser.state="usingButton"
            elif event.message.text=="查詢歷史訂單":
                result=searchOrderHistory(currentUser.id)
                line_bot_api.push_message(currentUser.id,result)
                currentUser.action="init"
                currentUser.state="usingButton"
            elif event.message.text=="取消預約":
                #result=deleteOrder(currentUser.id)
                #line_bot_api.push_message(currentUser.id,result)
                line_bot_api.reply_message(event.reply_token,[TextSendMessage(text="此功能仍在開發中")])
                currentUser.action="init"
                currentUser.state="usingButton"
            else:
                msg="很抱歉，我不清楚這句話的意思，請從選單選擇功能"
                line_bot_api.reply_message(event.reply_token,[TextSendMessage(text=msg),showMainMenu()])

    #新增訂單部分
    elif currentUser.action=="order":
        print('目前正在處理: '+currentUser.id+"的訂單", file=sys.stdout)
        if currentUser.state=="init":
            line_bot_api.reply_message(event.reply_token,[TextSendMessage(text="歡迎使用，請依照指示操作"),showOrderMenu(currentUser)])
            currentUser.state="usingButton"
        elif event.message.text=="我要輸入姓名" and currentUser.state=="usingButton":
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text="請問尊姓大名?"))
            currentUser.state="getName"
        elif currentUser.state=="getName":
            currentUser.name=event.message.text
            line_bot_api.reply_message(event.reply_token,[TextSendMessage(text="已收到您的資訊"),showOrderMenu(currentUser)])
            currentUser.state="usingButton"
        elif event.message.text=="我要輸入電話" and currentUser.state=="usingButton":
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請問連絡電話?"))
            currentUser.state="getTel"
        elif currentUser.state=="getTel":
            currentUser.tel=event.message.text
            line_bot_api.reply_message(event.reply_token,[TextSendMessage(text="已收到您的資訊"),showOrderMenu(currentUser)])
            currentUser.state="usingButton"
        elif event.message.text=="我要輸入時數" and currentUser.state=="usingButton":
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請問希望的服務時數?"))
            currentUser.state="getHour"
        elif currentUser.state=="getHour":
            # maybe use button template?
            currentUser.hour=event.message.text
            line_bot_api.reply_message(event.reply_token,[TextSendMessage(text="已收到您的資訊"),showOrderMenu(currentUser)])
            currentUser.state="usingButton"
        elif event.message.text=="確認":
            completeChecker=currentUser.checkInfoComplete()
            if completeChecker=="complete":
                orderTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reserveTime=currentUser.time.strftime("%Y-%m-%d %H:%M:%S")
                orderInfo="姓名: "+currentUser.name+"\n電話: "+currentUser.tel+"\n時間: "+currentUser.time.strftime("%m/%d %H:%M")+"\n時數:"+currentUser.hour
                sqlString="INSERT INTO public.\"USER_INFO\"(\"UNAME\", \"TEL\", \"ORDER_TIME\", \"RESERV_TIME\", \"HOUR\", \"VERIFY\", \"UID\") VALUES ( '" +\
                currentUser.name + "', '" + currentUser.tel + "', '" + orderTime + "', '" + reserveTime +\
                 "', '" + currentUser.hour + "', 'N', '" + currentUser.id + "')"
                cur.execute(sqlString)
                conn.commit()
                line_bot_api.reply_message(event.reply_token,[TextSendMessage(text="恭喜，預約已完成"),TextSendMessage(text=orderInfo),TextSendMessage(text="輸入任意訊息以執行其他操作")])
                currentUserList.remove(currentUser) # 完成預約，將使用者從list移除
                del currentUser # 下次輸入時再重新建立currentUser
            else:
                line_bot_api.reply_message(event.reply_token,[TextSendMessage(text="資料有誤，請檢查 "+completeChecker+" 欄位"),showOrderMenu(currentUser)])
                currentUser.state="usingButton"
        else: # 未定義操作
            msg="很抱歉，我不清楚這句話的意思，請從選單選擇功能或輸入'確認'送出訂單"
            line_bot_api.reply_message(event.reply_token,[TextSendMessage(text=msg),showOrderMenu(currentUser)])
            currentUser.state="usingButton"

    #搜尋訂單部分
    elif currentUser.action=="search":
        currentUser.state="init"
        currentUser.action="init"

    #刪除訂單部分
    elif currentUser.action=="cancel":
        line_bot_api.reply_message(event.reply_token,[TextSendMessage(text="此功能仍在開發中")])
        currentUser.state="init"
        currentUser.action="init"
    else:
        msg="發生未知錯誤，請聯絡客服人員"
        line_bot_api.reply_message(event.reply_token,[TextSendMessage(text=msg)])
    


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

