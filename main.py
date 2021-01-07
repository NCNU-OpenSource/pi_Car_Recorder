#-*- coding: UTF-8 -*-
from telegram import ParseMode
import time
import json
import os
import os.path
import logging
import telegram
import picamera
import datetime as dt
from time import sleep
from subprocess import call
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import threading

# 允許 logging。當出現error時能知道哪裡出了問題。
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

flag = False

# 創造Updater，將token pass給Updater。
# 在v12中要加入“use_context = True”（之後版本不需要），用於有新訊息是回應。
# TOKEN、bot和updater要放在def外面。若只放在main()會出現錯誤
TOKEN = "1499587189:AAGtXXGIVnPekHxSjBpZmp4voDUc_Fl7h6Q"
bot = telegram.Bot(token = TOKEN)
updater = Updater(TOKEN, use_context = True)
dp = updater.dispatcher
uid = None
camera_mode = 50 # default value is 50

def run():
    global flag
    global uid
    global camera_mode
    with picamera.PiCamera() as camera:
        while(1):
            startTime = dt.datetime.now().strftime('%Y%m%d%H%M')
            camera.rotation = 180
            camera.brightness = camera_mode
            camera.resolution = (1280, 720)
            camera.start_preview()
            camera.annotate_background = picamera.Color('black')  
            camera.annotate_text = dt.datetime.now().strftime('%Y%-m%-d %H:%M:%S')
            camera.start_recording("%s@%s.h264"%(uid ,startTime))
            start = dt.datetime.now()
            while (dt.datetime.now() - start).seconds < 60:
                camera.annotate_text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                camera.wait_recording(0.2)
                if flag == True:
                    camera.stop_recording()
                    return
            camera.stop_recording()
        #command = ("MP4Box -add %s.h264 %s.mp4" %(startTime, startTime))
        #call([command], shell=True) 

def do_backup():
    os.system('python3 rmVideo.py')
    os.chdir('/home/pi/video/1091_LSA_final')
    os.system('python3 transVideo.py')
    os.system('rclone copy /home/pi/video/1091_LSA_final/mp4Video pi_video:backup')
    return

def start_handler(update, context: CallbackContext):
    # chatbot在接受用戶輸入/start後的output內容
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING) # 會顯示chatbot正在輸入中，增加對話真實感
    time.sleep(0.5) # 在顯示輸入中後停頓0.5秒，然後顯示下一句code的文字
    update.message.reply_text("Hello! 你好👋，{}！我是PI攝者不救🤖".format(update.message.from_user.first_name)) # 給user的output
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(0.5)
    update.message.reply_text("PI攝者不救🤖能根據關鍵字執行行車記錄器內容\n\n❓關於指令使用方法，請輸入 /help \n💬關於PI攝者不救🤖，或想要報錯和反饋💭，請輸入 /about") # 給user的output。output可以分開多次使用update.message.reply_text()。
    reply_markup = ReplyKeyboardMarkup([[KeyboardButton("/about"), KeyboardButton("/backup")]
        , [KeyboardButton("/record"), KeyboardButton("/end")]
        , [KeyboardButton("/search")]
        , [KeyboardButton("/get"), KeyboardButton("/help")]
        , [KeyboardButton("/sun"), KeyboardButton("/night")]])
    bot.sendMessage(chat_id=update.message.chat_id, text="指令如下", reply_markup=reply_markup)


def help_handler(update, context: CallbackContext):

    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(0.5)
    bot.send_message(update.message.chat.id, "<u>《🔍如何使用》</u>\n\n<b>/start</b>  :  開始操作\n\n<b>/about</b>  :  關於PI攝者不救與報錯\n\n<b>/record</b>  :  開始拍攝\n\n<b>/end</b>  :  停止拍攝\n\n<b>/get</b>  :  取得影片雲端連結\n\n<b>/search</b>  :  從本地搜尋影片\n\n<b>/backup</b>  :  手動備份影片到雲端\n\n<b>/help</b>  :  如何使用" , parse_mode=ParseMode.HTML)

def about_handler(update, context: CallbackContext):

    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(0.5)
    update.message.reply_text("感謝使用PI攝者不救🤖️。\n這是一個行車記錄器的BOT，可以控制開始與關閉錄影，也可以取得影片檔案的雲端連結。") 

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("點我前往", url = "https://www.facebook.com/profile.php?id=100003827470832")]])

    bot.send_message(update.message.chat.id, "若要回報錯誤，透過以下連結Facebook私訊林科左回報。", reply_to_message_id = update.message.message_id,
                     reply_markup = reply_markup)

    # chatbot在接受用戶輸入/start後的output內容

# 開始拍攝
def Record_handler(update, context: CallbackContext) :
    global uid 
    uid = update.message.from_user.username
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(0.5)
    update.message.reply_text("開始拍攝！")
    global flag
    flag = False
    t1 = threading.Thread(target = run) 
    t1.start()

# 停止拍攝
def End_handler(update, context: CallbackContext) :
    global flag
    flag = True
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(0.5)
    update.message.reply_text("停止拍攝，影片已儲存至雲端。")

# 取得影片雲端連結
def getVideo_handler(update, context: CallbackContext) :
    time.sleep(0.5)
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("點我前往", url = "https://onedrive.live.com/?authkey=%21AKanIMwDpSXJ3Qw&id=3FF58B5EF46ED07A%211886&cid=3FF58B5EF46ED07A")]])

    bot.send_message(update.message.chat.id, "行車記錄器檔案", reply_to_message_id = update.message.message_id,
                     reply_markup = reply_markup)

#查詢檔案名稱
def Search_handler(update, context: CallbackContext) :
    global uid
    uid = update.message.from_user.username
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(0.5)
    result = os.system('ls mp4Video/%s/ | grep .mp4 > ./mp4Video/%s/record.txt' %(uid, uid))
    data = ""
    with open("./mp4Video/"+uid+"/record.txt", "r") as f:
        for line in f:
            data += "<pre>" +line + "</pre>\n"
    #os.system("rm record.txt")
    bot.send_message(update.message.chat.id, data , parse_mode=ParseMode.HTML)
    time.sleep(0.5)
    bot.send_message(update.message.chat.id,"Select the video name below to copy and paste!")

def backup_handler(update, context: CallbackContext):
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(0.5)
    update.message.reply_text("備份中...")
    do_backup()
    update.message.reply_text("備份完成!")

def reply_handler(update, context: CallbackContext):
    """Reply message."""
    global uid 
    uid = update.message.from_user.username
    text = update.message.text
    LEN = len(text)
    MP4 = text[LEN-4:LEN:+1] 
    if (MP4 == ".mp4") :
        with open('./mp4Video/'+uid+'/record.txt', 'r+', encoding='utf8') as mfile :
            for line in mfile.readlines() :
                if text not in line :
                    continue
                else :
                    bot.send_video(chat_id = update.message.chat_id, video = open('mp4Video/'+uid+'/'+ text, 'rb' ))
                    return
            update.message.reply_text("video not found")
    else :
        bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
        time.sleep(0.5)
        update.message.reply_text("對不起，PI攝者不救🤖不能理解你說啥。🤔\n\n關於指令使用方法，請輸入 /help")

def light_handler(update, context: CallbackContext):
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(0.5)
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("日間模式", callback_data = "sun")],
        [InlineKeyboardButton("夜間模式", callback_data="night")]])

    bot.send_message(update.message.chat.id, "透過下面按鈕調整攝影亮度", reply_to_message_id = update.message.message_id,
                     reply_markup = reply_markup)

def getClickButtonData(update, context):
    global camera_mode

    if update.callback_query.data == "sun":
        camera_mode = 40
        bot.send_chat_action(chat_id = update.callback_query.message.chat_id, action = telegram.ChatAction.TYPING)
        time.sleep(0.5)
        update.callback_query.edit_message_text("已更改為日間模式")

    if update.callback_query.data == "night":
        camera_mode = 70
        bot.send_chat_action(chat_id = update.callback_query.message.chat_id, action = telegram.ChatAction.TYPING)
        time.sleep(0.5)
        update.callback_query.edit_message_text("已更改為夜間模式")

def error_handler(bot, update, error, context: CallbackContext):
    bot.send_chat_action(chat_id = update.message.chat_id, action = telegram.ChatAction.TYPING)
    time.sleep(0.5)
    update.message.reply_text("對不起，PI攝者不救🤖不能理解你說啥。🤔\n\n關於指令使用方法，請輸入 /help")

def error(update, context):
    """紀錄Updates時出現的errors。出現error時console就會print出下面logger.warning的內容"""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    """啟動bot"""
# ...
    # 設定使用dispatcher，用來以後設定command和回覆用

    dp.add_handler(CommandHandler("start", start_handler)) # 啟動chatbot
    dp.add_handler(CommandHandler("record", Record_handler)) # 開始拍攝
    dp.add_handler(CommandHandler("end", End_handler)) # 停止拍攝
    dp.add_handler(CommandHandler("get", getVideo_handler)) # 取得影片雲端連結
    dp.add_handler(CommandHandler("search", Search_handler)) # 搜尋本地影片
    dp.add_handler(CommandHandler("help", help_handler)) # 顯示幫助的command
    dp.add_handler(CommandHandler("about", about_handler)) # 顯示關於PI攝者不救🤖️獲報錯
    dp.add_handler(CommandHandler("backup", backup_handler)) # 手動備份檔案
    dp.add_handler(CallbackQueryHandler(getClickButtonData))  #按鈕連結
    dp.add_handler(CommandHandler("light", light_handler)) # 將鏡頭調整為日間模式
    dp.add_handler(MessageHandler(Filters.text, reply_handler)) # 設定若非設定command會回覆用戶不知道說啥的訊息
    dp.add_error_handler(error_handler) # 出現任何非以上能預設的error時會回覆用戶的訊息內容

    # 專門紀錄所有errors的handler，對應def error()
    dp.add_error_handler(error)

    # 啟動Bot。bot程式與Telegram連結有兩種方式：polling和webhook。
    # 兩者的差異可以參考這篇reddit的解釋：https://www.reddit.com/r/TelegramBots/comments/525s40/q_polling_vs_webhook/。
    # 在python-telegram-bot裡面本身有built-in的webhook方法，但是在GCE中暫時還沒摸索到如何設定webhook，因此polling是最便捷的方法。
    updater.start_polling()
    
    # 就是讓程式一直跑。
    # 按照package的說法“start_polling() is non-blocking and will stop the bot gracefully.”。
    # 若要停止按Ctrl-C 就好
    updater.idle()

#運行main()，就會啟動bot。
if __name__ == '__main__':
    main()
