#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from telegram.ext import Updater

# Logger Config
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

### USER CONFIG
bot_token = "INSERT TOKEN HERE"
### END USER CONFIG


def error_handler(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(bot_token)
    dp = updater.dispatcher
    dp.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
