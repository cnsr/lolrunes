from config import region, verbose, spells_fixed, regions
import argparse
import requests, lxml, re, json
from bs4 import BeautifulSoup as bs
import lxml.html
from lxml import etree, html
from io import StringIO, BytesIO
import pprint
from PIL import Image, ImageDraw
from utils import *
from telegram.ext import CommandHandler, CallbackQueryHandler, Updater
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, bot
import os
from functools import wraps
from dotenv import load_dotenv

import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

load_dotenv()

TOKEN = os.getenv("TOKEN")

champions = []

button_list = [
    InlineKeyboardButton("default", callback_data='default'),
    InlineKeyboardButton("top", callback_data='top'),
    InlineKeyboardButton("jungle", callback_data='jungle'),
    InlineKeyboardButton("mid", callback_data='mid'),
    InlineKeyboardButton("support", callback_data='support'),
    InlineKeyboardButton("bottom", callback_data='bottom'),
]

def start(update, context):
    body = """
    Welcome to LoL Runes bot!
    Use `/r champion` to get runes for a champion.
    Use `/reg region` to set default region (default bot region is 🇰🇷KR)
    Specify a line (top, jungle, mid, bottom, support) or get the default one.
    Rune stats are pulled from op.gg (unfortunately, without any consent).
    """
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=body,
        parse_mode=ParseMode.MARKDOWN
    )

def uploading(func):
  @wraps(func)
  def wrapped(update, context, *args, **kwargs):
    context.bot.send_chat_action(
      chat_id=update.effective_message.chat_id,
      action=ChatAction.UPLOAD_PHOTO)
    return func(update, context, *args, **kwargs)
  return wrapped


def typing(func):
  @wraps(func)
  def wrapped(update, context, *args, **kwargs):
    context.bot.send_chat_action(
      chat_id=update.effective_message.chat_id,
      action=ChatAction.TYPING)
    return func(update, context, *args, **kwargs)
  return wrapped


def get_url(champion, region='kr', line=None):
    url = ''
    if region in regions:
        if region == 'kr':
            url = f'https://op.gg/champion/{champion}/statistics/'
        else:
            url = f'https://{region}.op.gg/champion/{champion}/statistics'
    else:
        url = f'https://op.gg/champion/{champion}/statistics/'

    if line:
        url += f'{line}'
    
    print(f"URLLLLLLL {url}")

    return url


def get_page(champion, region='kr', line=None):
    # this is the only long part
    r = requests.get(url=get_url(champion, region, line), stream=True)
    r.raw.decode_content = True
    tree = lxml.html.parse(r.raw)

    """
    # MOST COMMON SPELLS
    spells = tree.xpath('//li[@class="champion-stats__list__item"]/img/@src')
    spells_pickrate = tree.xpath('//td[@class="champion-overview__stats champion-overview__stats--pick"]/strong')[:2]
    winrate = tree.xpath('//td[@class="champion-overview__stats champion-overview__stats--win"]/strong')[:2]
    images = []
    for spell in spells:
        imgs = spell.split('/')
        img = list(filter(lambda x: x.startswith('Summoner'), imgs))[0].split('.')[0][8:]
        if img in spells_fixed:
            img = spells_fixed[img]
        images.append(img)
    spells_out = {
        f"{images[0]}, {images[1]}": f"Pickrate: {spells_pickrate[0].text}, Winrate: {winrate[0].text}",
        f"{images[2]}, {images[3]}": f"Pickrate: {spells_pickrate[1].text}, Winrate: {winrate[1].text}",
    }
    """
    # MOST COMMON RUNES
    rune_names = [x.text for x in tree.xpath('//div[@class="champion-stats-summary-rune tabHeaders"]//div[@class="champion-stats-summary-rune__name"]')]
    rune_pages = tree.xpath('//tbody[@class="tabItem ChampionKeystoneRune-1"]//div[@class="perk-page"]')
    rune_pages_secondary = tree.xpath('//tbody[@class="tabItem ChampionKeystoneRune-2"]//div[@class="perk-page"]')
    pages = []
    pages_secondary = []
    for rune_page in rune_pages:
        rune_page = get_etree(rune_page)
        page = rune_page.xpath('//div[contains(@class,"perk-page__item--active")]//img/@alt')
        if page:
            pages.append(page)
    for rune_page in rune_pages_secondary:
        rune_page = get_etree(rune_page)
        page = rune_page.xpath('//div[contains(@class,"perk-page__item--active")]//img/@alt')
        if page:
            pages_secondary.append(page)

    primary_most = make_image(rune_names[0], pages[:2])
    #primary_less = make_image(rune_names[0], pages[2:])
    secondary_most = make_image(rune_names[1], pages_secondary[:2])
    #secondary_less = make_image(rune_names[1], pages_secondary[2:])
    return primary_most, secondary_most


def make_image(rune_name, pages):
    rune_main, rune_secondary = (x.strip().lower() for x in rune_name.split('+'))
    WHITE = (255,255,255)
    img = Image.new('RGBA', (512, 256), color = 'black')
    path = 'runes/'
    rune = Image.open(path + rune_main + '/' + rune_main.lower() + '.png')
    d = ImageDraw.Draw(img)
    d.text((10,10), rune_name, fill=WHITE)
    img.paste(rune, (25, 25), rune.convert('RGBA'))
    offset = [125, 35]
    for x in pages[0]:
        rune = Image.open(f"{path}{rune_main}/{x.lower()}.png").resize((64,64), Image.ANTIALIAS)
        if len(x) <= 9:
            x = ' ' * ( (10-len(x) - 1)) + x
        d.text((offset[0],100), str(x), fill=WHITE)
        img.paste(rune, tuple(offset), rune.convert('RGBA'))
        if len(x) * 7 > 75:
            offset[0] += len(x) * 6 + 10
        else:
            offset[0] += 75
    rune = Image.open(path + rune_secondary + '/' + rune_secondary.lower() + '.png')
    img.paste(rune, (25, 125), rune.convert('RGBA'))
    offset = [125, 135]
    for x in pages[1]:
        rune = Image.open(f"{path}{rune_secondary}/{x.lower()}.png").resize((64,64), Image.ANTIALIAS)
        if len(x) <= 9:
            x = ' ' * ( (10-len(x) - 1)) + x
        d.text((offset[0],offset[1] + 75), str(x), fill=WHITE)
        # center image
        offset_centered = offset
        img.paste(rune, tuple(offset), rune.convert('RGBA'))
        if len(x) * 7 > 75:
            offset[0] += len(x) * 6 + 10
        else:
            offset[0] += 75
    #img.show()
    return img


def get_etree(element):
    return html.fromstring(lxml.html.tostring(element))


@typing
def region(update, context):
    """Usage: /reg region"""
    # Seperate ID from command
    key = update.message.text.partition(' ')[1]

    if key not in regions:
        update.message.reply_text('Region not supported. Supported regions: ' + 
            ','.join(regions)
        )
        return

    # Load value
    context.user_data['region'] = key
    update.message.reply_text('Region set to ' + key.upper())


@typing
def runes(update, context):
    try:
        region = context.user_data['region']
    except KeyError:
        region = 'kr'

    champion = update.message.text.partition(' ')[-1].replace(' ', '')
    if champion in verbose:
        champion = verbose[champion]
    if not any(d['id'] == champion for d in champions):
        update.message.reply_text('Champion not found. Message @censr to get this fixed.')
    else:
        context.user_data.clear()
        context.user_data['champ'] = champion
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

        update.message.reply_text("Select line", reply_markup=reply_markup)


@uploading
def button(update, context):
    line = update.callback_query
    
    line = update.callback_query.data
    if update.callback_query.data == 'default':
        line = None
    """updater.bot.edit_message_text(
        text="Selected option: {}".format(update.callback_query.data), 
        chat_id=update.callback_query.message.chat_id,
        message_id=update.callback_query.message.message_id,
    )"""

    try:
        region = context.user_data['region']
    except KeyError:
        region = 'kr'

    images = get_page(context.user_data['champ'], region, line)

    for image in images:
        bio = BytesIO()
        bio.name = 'image.png'
        image.save(bio, 'PNG')
        bio.seek(0)
        updater.bot.send_photo(
            chat_id=update.callback_query.message.chat_id,
            photo=bio
        )


if __name__ == '__main__':
    with open('champions_out.json', 'r+') as champs:
        champions = json.load(champs)

    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('reg', region))
    dispatcher.add_handler(CommandHandler('region', region))
    dispatcher.add_handler(CommandHandler('r', runes))
    dispatcher.add_handler(CommandHandler('runes', runes))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.start_polling()
    updater.idle()
