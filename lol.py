from config import region, verbose, spells_fixed
import argparse
import requests, lxml, re, json
from bs4 import BeautifulSoup as bs
import lxml.html
from lxml import etree, html
from io import StringIO
import pprint
from PIL import Image, ImageDraw

pp = pprint.PrettyPrinter(indent=4)

parser = argparse.ArgumentParser()

parser.add_argument('champion',
                    help="Champion to get info for",
                    type=str)
parser.add_argument('-l', '--line',
                    help="Prefered line, default one will be printed if not specified",
                    type=str)

args = parser.parse_args()

champion = args.champion

# get champion by short handle
if champion in verbose:
    champion = verbose[champion]

regions = [
    'ru', 'kr', 'jp', 'na', 'euw', 'eune', 'oce', 'br', 'las', 'lan', 'tr',
]

url = ''
if region in regions:
    if region == 'kr':
        url = f'https://op.gg/champion/{champion}/statistics/'
    else:
        url = f'https://{region}.op.gg/champion/{champion}/statistics'
else:
    url = f'https://op.gg/champion/{champion}/statistics/'

if args.line:
    url += f'/{args.line}'

def get_page():
    # this is the only long part
    r = requests.get(url, stream=True)
    r.raw.decode_content = True
    tree = lxml.html.parse(r.raw)

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
    pp.pprint(spells_out)
    
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
    
    pages_out = {
        f"Most common {rune_names[0]}": f"{pages[0]}, {pages[1]}",
        f"Less common {rune_names[0]}": f"{pages[2]}, {pages[3]}",
        f"Most common {rune_names[1]}": f"{pages_secondary[0]}, {pages_secondary[1]}",
        f"Less common {rune_names[1]}": f"{pages_secondary[2]}, {pages_secondary[3]}",
    }
    #pp.pprint(pages_out)
    primary_most = make_image(rune_names[0], pages[:2])
    #primary_less = make_image(rune_names[0], pages[2:])
    primary_most.show()
    #primary_less.show()
    secondary_most = make_image(rune_names[1], pages_secondary[:2])
    #secondary_less = make_image(rune_names[1], pages_secondary[2:])
    secondary_most.show()
    #secondary_less.show()

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

# rune images
# https://leagueoflegends.fandom.com/wiki/Press_the_Attack

get_page()