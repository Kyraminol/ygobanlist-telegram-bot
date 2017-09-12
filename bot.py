#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import urllib3
import re
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram import ParseMode
from bs4 import BeautifulSoup
from dateutil.parser import parse

# Logger Config
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)
http = urllib3.PoolManager()

### USER CONFIG
bot_token = "INSERT TOKEN HERE"
### END USER CONFIG


def periodical_check(bot, job):
    banlist = banlist_check()
    if "error" not in banlist:
        with open("last_updated") as f:
            last_update = f.read()
            if last_update:
                try:
                    last_update = parse(last_update)
                except:
                    last_update = None
        if not last_update == banlist["updated"]:
            formatted = "<b>NEW BANNED</b>:\n\n%s" % (banlist_format(banlist),)
            with open("chats") as f:
                for chat in f:
                    bot.send_message(chat, formatted, parse_mode=ParseMode.HTML)
            with open("last_updated", "w") as f:
                f.write(banlist["updated"].strftime("%d/%m/%Y"))
        else:
            print("outdated")
    else:
        print(banlist["error"])


def banlist_check(show_all=False):
    r = http.request("GET", "http://www.yugioh-card.com/en/limited/")
    soup = BeautifulSoup(r.data.decode('utf-8'), "lxml")
    latest_update = parse(soup.find("td", attrs={"class": "update_ttl"}).text.split(":")[1].strip())
    result = {"updated": latest_update,
              "banned": (),
              "limited": (),
              "semi_limited": (),
              "free": ()}
    c_table = "start"
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            if "class" in tr.attrs:
                if tr.attrs["class"] == ["cardlist_atitle"]:
                    tr.decompose()
                    if c_table == "start":
                        c_table = "banned"
                    elif c_table == "banned":
                        c_table = "limited"
                    elif c_table == "limited":
                        c_table = "semi_limited"
                    elif c_table == "semi_limited":
                        c_table = "free"
                    else:
                        c_table = "stop"
            else:
                tr.replace_with("")
            if not c_table == "stop":
                tds = tr.find_all("td")
                if len(tds) > 3:
                    if "colspan" in tds[2].attrs:
                        current = tds[3].text.strip()
                    else:
                        current = tds[4].text.strip()
                    if current or show_all:
                        result[c_table] += ((re.sub(r"\s+", " ", tds[1].text.strip()), current),)
    return result


def banlist_format(banlist):
    ordered = ("banned", "limited", "semi_limited", "free")
    text = ""
    for table in ordered:
        text += "<b>%s</b>:\n" % (re.sub(r"_", " ", table.title()),)
        if len(banlist[table]) > 0:
            for card in banlist[table]:
                if card[1]:
                    old_status = " <i>(%s)</i>" % card[1]
                else:
                    old_status = ""
                text += " • %s%s\n" % (card[0].title(), old_status)
        else:
            text += " • <i>None</i>\n"
        text += "\n"
    return text


def cmd_banlist(bot, update):
    banlist = "<b>Latest Banlist Changes</b>:\n\n%s" % (banlist_format(banlist_check()),)
    bot.send_message(update.message.chat.id, banlist, parse_mode=ParseMode.HTML)


def cmd_banlist_full(bot, update):
    banlist = "<b>Latest Banlist Changes</b>:\n\n%s" % (banlist_format(banlist_check(show_all=True)),)
    bot.send_message(update.message.chat.id, banlist, parse_mode=ParseMode.HTML)


def cmd_unsub_banlist(bot, update):
    from_chat = update.message.chat
    from_user = update.message.from_user
    if not from_chat.type == "private":
        member = bot.get_chat_member(from_chat.id, from_user.id)
        if not member.status == "creator" or not member.status == "administrator":
            return
    with open("chats", "r") as f:
        new_chats = f.read().replace(str(from_chat.id) + "\n", "")
    with open("chats", "w") as f:
        f.write(new_chats)
    bot.send_message(from_chat.id, "Successfully unsubscribed from banlist feed.")


def status_update(bot, update):
    if update.message.new_chat_members:
        bot_id = bot.id
        for user in update.message.new_chat_members:
            if bot_id == user.id:
                chat_id = update.message.chat.id
                bot.send_message(chat_id, "Hi! You are subscribed to new banlists notifications!\n"
                                          "Please type /unsub_banlist if you want to unsubscribe <i>"
                                          "(only admins can do that)</i>.", parse_mode=ParseMode.HTML)
                with open("chats", "a+") as f:
                    chats = f.read().split("\n")
                    if chat_id not in chats:
                        f.write("%s\n" % (chat_id,))


def error_handler(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(bot_token)
    dp = updater.dispatcher
    job = updater.job_queue
    job.run_repeating(periodical_check, 600.0, 0.0)
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, status_update))
    dp.add_handler(CommandHandler("banlist", cmd_banlist))
    dp.add_handler(CommandHandler("banlist_full", cmd_banlist_full))
    dp.add_handler(CommandHandler("unsub_banlist", cmd_unsub_banlist))
    dp.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
