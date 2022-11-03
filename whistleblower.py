import asyncio
import os
import random
import re
import requests
from traceback import format_exc
import nextcord
from nextcord import Interaction,VoiceState,Member
from tabulate import tabulate
from nextcord.ext import commands, tasks
from dotenv import load_dotenv
from web_scraping import HSW_Scraper
from stock_exchange import StockExchanger
from youtube_dl import YoutubeDL
import ffmpeg 
import discord
import urllib.request

def info(mes):
    print(f'INFO - {mes}')
def error(mes):
    print(f'ERROR - {mes}')

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
TT = os.getenv('TENOR')

stock_zone_id = '1011106082292256889'
# channel IDs
bj = ['1011022189610414160','609211701010890784']

user_file = "stockExchange/{}.json"

intents = nextcord.Intents.default()
intents.message_content = True

# takes too long to initialize when not being used
# will be initialized of first call using these
hsw = None
se = None

bot = commands.Bot(intents=intents,command_prefix='!')
channel = bot.get_channel(stock_zone_id)
class numbers:
    def __init__(self):
        self.active_users = []
        self.song_queue = {}
        self.active_vc = {}
        self.hsw = None
        self.se = None

    def add_song(self,channel_id,song_link:str):
        if channel_id not in self.song_queue:
            self.song_queue[channel_id] = [song_link]
        else:
            self.song_queue[channel_id].append(song_link)

    def next_song(self,voice):
        YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        url = self.song_queue[voice.__dict__['server_id']]

        if 'watch?' in url:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                vid_info = ydl.extract_info(url, download=False)
                info(f'garbage:{len(vid_info["entries"])[0]["formats"][0]["url"] if "entries" in vid_info.keys() else vid_info.keys()}\n')
                URL = vid_info['formats'][0]['url']
        else:
            URL = url
        info(URL)
        # check for playlist and add rest to queue
        while voice.is_playing():
            voice.stop()
            voice.cleanup()
        voice.play(nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(url)))

num = numbers()

def is_file(path):
    try:
        f = open(path)
        f.close()
        return True
    except FileNotFoundError:
        return False

@bot.command()
async def search(ctx,*keywords):
    if num.se is None:
        num.se = StockExchanger()
    info('COMMAND: search executed')
    await ctx.message.add_reaction('👀')
    if not keywords:
        await ctx.send('Couldn\'t parse keyword. Using default value...')
        keywords = ('apple','inc')
    keyword = ''
    for word in keywords:
        keyword += word + ' '
    keyword = keyword[:-1]
    resp = num.se.search_symbol(keyword)
    message = '```'
    if resp == []:
        message += f'Couldn\'t locate {keyword}. Try again with different keywords.'
    else:
        for x,r in enumerate(resp,0):
            message+=f"Name: {r['2. name']} \n"
            message+=f"Symbol: {r['1. symbol']} \n\n"
            if x >=5:
                break
    message += '```'
    await ctx.send(message)
    await ctx.message.add_reaction('✅')

@bot.command()
async def create(ctx):
    if num.se is None:
        num.se = StockExchanger()
    info('COMMAND: create executed.')
    await ctx.message.add_reaction('👀')
    user_id = ctx.message.author.id
    
    if not is_file(user_file.format(user_id)):
        num.se.create_file(user_id)
        await ctx.message.add_reaction('✅')
    else:
        await ctx.send('Account already exists. To overwrite current account, use "!create_overwrite"')
        await ctx.message.add_reaction('❌')
        return None

@bot.command()
async def create_overwrite(ctx):
    if num.se is None:
        num.se = StockExchanger()
    info('COMMAND: create_overwrite executed.')
    await ctx.message.add_reaction('👀')
    user_id = ctx.message.author.id
    
    num.se.create_file(user_id)
    await ctx.message.add_reaction('✅')

@bot.command(aliases=['bal'])
async def balance(ctx):
    if num.se is None:
        num.se = StockExchanger()
    info('COMMAND: check balance executed.')
    await ctx.message.add_reaction('👀')
    user_id = ctx.message.author.id
    info(user_id)

    try:
        if is_file(user_file.format(user_id)):
            await ctx.send(num.se.read_balance(user_id))
            await ctx.message.add_reaction('✅')
        else:
            await ctx.send('Couldn\'t locate account. Please create an account and try again later.')
            await ctx.message.add_reaction('❌')
            return None
    except:
        await ctx.send('Couldn\'t locate account balance.')
        await ctx.message.add_reaction('❌')
        return None
 
@bot.command(aliases=['purchase'])
async def buy(ctx,ticker, num):
    if num.se is None:
        num.se = StockExchanger()
    info('COMMAND: purchase executed.')
    await ctx.message.add_reaction('👀')
    user_id = ctx.message.author.id

    value = float(num)
    try:
        if is_file(user_file.format(user_id)):
            if num.se.purchase(user_id,ticker,value) != 66:
                await ctx.message.add_reaction('✅')
            else:
                await ctx.send(f'You don\'t have the funds to purchase ${value} of {ticker}.')
                await ctx.message.add_reaction('❌')
                return None
        else:
            await ctx.send('Couldn\'t locate account. Please create an account and try again later.')
            await ctx.message.add_reaction('❌')
            return None
    except:
        await ctx.send(f'Error when attempting to purchase {ticker}. Make sure you have the right Ticker Symbol, funds, and no dollar signs in command.')
        await ctx.message.add_reaction('❌')
        return None

@bot.command()
async def sell(ctx,ticker,num):
    if num.se is None:
        num.se = StockExchanger()
    info('COMMAND: sell executed.')
    await ctx.message.add_reaction('👀')
    user_id = ctx.message.author.id

    value = float(num)
    try:
        if is_file(user_file.format(user_id)):
            if num.se.sell(user_id,ticker,value) != 66:
                await ctx.message.add_reaction('✅')
            else:
                await ctx.send(f'You don\'t have the assets to sell ${value} of {ticker}.')
                await ctx.message.add_reaction('❌')
                return None
        else:
            await ctx.send('Couldn\'t locate account. Please create an account and try again later.')
            await ctx.message.add_reaction('❌')
            return None
    except Exception as e:
        error(f'Couldn\'t run "sell" command. {e}-{format_exc()}')
        await ctx.send(f'Error when attempting to sell {ticker}. Make sure you have the right Ticker Symbol, assets, and no dollar signs in command.')
        await ctx.message.add_reaction('❌')
        return None

@bot.command(name='info')
async def get_info(ctx,ticker='aapl'):
    if num.se is None:
        num.se = StockExchanger()
    info('COMMAND: info executed.')
    await ctx.message.add_reaction('👀')

    data = num.se.preview_stock(ticker)
    info(data)
    desc = ''
    if data['Recommendation'] == 'Buy':
        color = 0x235928
    elif data['Recommendation'] == 'Overweight':
        color = 0x27462D
    elif data['Recommendation'] == 'Underweight':
        color = 0x43292D
    elif data['Recommendation'] == 'Sell':
        color = 0x562529
    else:
        color = 0x2C2F33
    for key in data:
        if key == 'Name':
            continue
        desc += str(key) + ': ' + str(data[key]) + '\n'
    embed = nextcord.Embed(
        title= str(data['Name']),
        description=desc,
        color=color
    )
    await ctx.send(embed=embed)
    await ctx.message.add_reaction('✅')

@bot.command(aliases=['hist'])
async def history(ctx, size=5):
    if num.se is None:
        num.se = StockExchanger()
    size = int(size)
    info('COMMAND: history executed.')
    await ctx.message.add_reaction('👀')
    user_id = ctx.message.author.id
    if is_file(user_file.format(user_id)):
        data = num.se.read_history(user_id)
    else:
        await ctx.send('Couldn\'t locate account. Please create an account and try again later.')
        await ctx.message.add_reaction('❌')
        return None

    if size <= 25:
        tabulated = tabulate(data,['TRANSACTION_TYPE','TICKER','COST_PER_SHARE($)','VALUE($)','START_BALANCE($)','END_BALANCE($)'],tablefmt="orgtbl")
    else:
        tabulated = data[:size].to_string()
    await ctx.send(f'{ctx.message.author.name}\'s history:```{tabulated}```')
    await ctx.message.add_reaction('✅')

@bot.command(aliases=['inv'])
async def inventory(ctx):
    if num.se is None:
        num.se = StockExchanger()
    info('COMMAND: inventory executed.')
    await ctx.message.add_reaction('👀')
    user_id = ctx.message.author.id

    if is_file(user_file.format(user_id)):
        data = num.se.read_stocks(user_id)
    else:
        await ctx.send('Couldn\'t locate account. Please create an account and try again later.')
        await ctx.message.add_reaction('❌')
        return None

    if data.shape[0] <= 25:
        message = tabulate(data,["SHARES","VALUE"],tablefmt="orgtbl")
    else:
        message = data
    await ctx.send(f'{ctx.message.author.name}\'s inventory:```{message}```')
    await ctx.message.add_reaction('✅')


@bot.command(name = 'monitor', description='will send data about house of representative\'s stock trades',guild_ids=bj)
async def monitor(ctx, *args):
    if num.hsw is None:
        num.hsw = HSW_Scraper()
    info('COMMAND: monitor executed.')
    await ctx.message.add_reaction('👀')
    number = 5
    name = ''
    for arg in args:
        if arg.isnumeric():
            number = int(arg)
        else:
            name += f'{arg} '
    info(name)
    name = name[:-1]
    try:
        if name == '':
            name = 'Hon. Nancy Pelosi'
        characters = num.hsw.search_characters(name)
        if characters == []:
            await ctx.send('Couldn\'t find representative.')
            await ctx.message.add_reaction('❌')
            return None
        for person in characters:
            r = num.hsw.house_watcher(person['name'],number)
            embed = nextcord.Embed(
                title= str(r[1]['name']) + '\'s recent trades'
            )
            if r[1]['image'] != None:
                embed.set_image(url = r[1]['image'])
            embed.set_footer(text = r[1]['role'])
            await ctx.send(embed=embed)
            await ctx.send(r[0])
        await ctx.message.add_reaction('✅')
        return None
    except Exception as e:
        info('ERROR: {} - {}'.format(e,format_exc()))
        await ctx.send('Couldn\'t process monitor request')
        await ctx.message.add_reaction('❌')
        return None

@bot.command(pass_context=True)
async def play(ctx:nextcord.Interaction, *args):
    # if ctx.message.author.id == 373656911423209473:
    #     await ctx.send('fuck off tectal')
    #     return
    if len(args) == 0:
        url = 'https://www.youtube.com/watch?v=vPKp29Luryc'
    # check if passed info is a viable url
    elif ['https','watch?','.com'] in args:
        url = args[0]
    # should be a search query now that needs to be assembled and find it's the top video
    else:
        search = '+'.join(args)
        info(search)
        html = urllib.request.urlopen(url = f'https://www.youtube.com/results?search_query={search}')
        ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        url = f"https://www.youtube.com/watch?v={ids[0]}"
        info(url)

    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    
    try:
        voice = await ctx.message.author.voice.channel.connect()
        if not voice.is_playing():
            with YoutubeDL(YDL_OPTIONS) as ydl:
                vid_info = ydl.extract_info(url, download=False)
                info(f'garbage:{len(vid_info["entries"])[0]["formats"][0]["url"] if "entries" in vid_info.keys() else vid_info.keys()}\n')
            URL = vid_info['formats'][0]['url']
            # check for playlist and add rest to queue
            voice.play(nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(executable='./bin/ffmpeg.exe', source = URL, **FFMPEG_OPTIONS)))
            
            voice.is_playing()
            if '&list=' in url:
                YDL_OPTIONS = {'format': 'bestaudio'}
                with YoutubeDL(YDL_OPTIONS) as ydl:
                    vid_info = ydl.extract_info(url, download=False)
                    for entry in vid_info['entries']:
                        num.add_song(ctx.message.guild.id,entry['url'])
            info(f'VC joined: {voice.server_id}')
        else:
            await ctx.send("Already playing song")
            return
    except nextcord.errors.ClientException as e:
        info('adding song to queue because song was already playing')
        num.add_song(ctx.message.guild.id,url)
        info(f'current queue:{num.song_queue}')

    

@bot.command(pass_context=True)
async def next(ctx:nextcord.Interaction):
    for voice in bot.voice_clients:
        if voice.__dict__['server_id'] == ctx.message.guild.id:
            num.next_song(voice)

@bot.command()
async def gif(ctx:nextcord.Interaction, *args):
    info('COMMAND: generating gif.')
    search = ''
    for arg in args:
        search += f'{arg} '
    search = search[:-1]
    await ctx.send(get_gif(search))

@bot.command(aliases=['gen','photo','image'])
async def generate(ctx:nextcord.Interaction, *args):
    info('COMMAND: generating ai picture.')
    search = ''
    for arg in args:
        search += f'{arg} '
    search = search[:-1]
    info(search)
    params = {
        'text':search
    }
    headers = {
        'api-key':'0df59b56-fa17-4450-9e4f-657ebabfe4f6'
    }
    
    r = requests.post("https://api.deepai.org/api/text2img",data=params,headers=headers).json()
    try:
        await ctx.send(r['output_url'])
    except:
        info(f'could\'t print your shit image or whatever, {r}')

@bot.listen("on_message")
async def on_message1(message:nextcord.Message):
    gif_odds = random.randint(1,5)
    if gif_odds != 1:
        return
    if '<@&722649800075640892>' in message.content:
        csgif = [
            'https://tenor.com/view/csgo-time-cs-time-hasbulla-counter-strike-gif-25438577',
            'https://tenor.com/view/csgo-loona-time-for-cs-gif-22797047',
            'https://tenor.com/view/belle-delphine-csgo-hop-on-0equals0-hop-on-csgo-gif-26053428',
            'https://tenor.com/view/csgo-counter-strike-counter-strike-global-offensive-hop-on-hop-on-csgo-gif-24575259',
            'https://tenor.com/view/interium-edgebug-jumpbug-longjump-csgo-gif-21356157',
            'https://tenor.com/view/cs-gif-21762104'
        ]
        await message.channel.send(random.choice(csgif))
    if '<@&764301528453873664>' in message.content:
        phas_gif = [
            'https://tenor.com/view/phas-phasmophobia-phasmophobia-ghost-phas-dance-phas-vr-gif-22975367',
            'https://tenor.com/view/phasmophobia-get-on-phasmophobia-get-on-phas-gif-22434530',
            'https://tenor.com/view/phas-hop-on-phas-spooky-phasmophobia-gay-gif-26288730',
            'https://tenor.com/view/phas-phasmophobia-monokuma-loli-phas-gif-19536550',
            'https://tenor.com/view/chatting-3d-pepe-pepechat-chat-gif-23310696',
            'https://tenor.com/view/phasmophobia-get-on-phasmophobia-gaming-funny-dog-ghost-dog-gif-26380675',
            'https://tenor.com/view/phasmophobia-gif-24144854',
            'https://tenor.com/view/phasmophobia-peepo-gif-19202078',
            'https://tenor.com/view/pewdiepie-aparacer-fantasma-phasmophobia-hola-gif-19895389'
        ]
        await message.channel.send(random.choice(phas_gif))

@tasks.loop(minutes=10)
async def random_meme_sounds():
    odds = random.randint(1,200)
    info(f'Random number for meme: {odds}')
    if odds != 1  or len(num.active_users) == 0:
        return
    memes = [
        [
            'Ladies and gentlemen, at this time we ask that you please '
            'rise and remove your caps as we honor America with the playing '
            'of our National Anthem.',
            'https://www.youtube.com/watch?v=vPKp29Luryc'
        ],
        [
            'Gorilla in a bag.',
            'https://youtu.be/DZmkKgreH-M'
        ],
        [
            'Pro fortnite gamers.',
            'https://youtu.be/YCVXe5ZmZrs'
        ],
        [
            'Endangered species.',
            'https://youtu.be/Mxa4WNMDLEE'
        ],
        [
            'Welcome, football fans. Let\'s get ready for some prime time football.',
            'https://youtu.be/KxNGMvNIvP8'
        ],
        [
            'I pride myself and think of myself as a man of faith, '
            'as there\'s a drive into deep left field by Castellanos '
            'and that\'ll be a home run',
            'https://youtu.be/5LECJbMDhJQ'
        ],
        [
            'M I N I  M A L L',
            'https://youtu.be/MhVz3WGFDKM'
        ],
        [
            'the silence.',
            'https://youtu.be/htsfDg1chr8'
        ],
        [
            'H E Y',
            'https://youtu.be/Rl1HcsdVf0w'
        ],
        [ 
            'Namethan probably just said something.',
            'https://youtu.be/ZazNbG_3m9A'
        ],
        [
            'Back to school.',
            'https://youtu.be/xWGt86_Whac'
        ],
        [
            'Jones massaging with bbq.',
            'https://youtu.be/WPkMUU9tUqk'
        ],
        [
            'jesus is my "friend".',
            'https://youtu.be/Kppx4bzfAaE'
        ],
        [
            'African mall at 2 am.',
            'https://youtu.be/D__6hwqjZAs'
        ],
        [
            'p̵e̵t̵a̷h̷.̶ t̵̬̚ḥ̷̂ȇ̷̙.̶̟͐. ḩ̸̪̺̝̞́̾͑͒͛̾̿̓́͛o̷̢̜̪̰̱͈͗̓͜͝͠r̷̨̨̼͙̦͖̐̃̓̅͝͠͝s̷̨̨̬̬̻̤͗̉̐̅̉̑̉ë̴̟͛͛̋͗̓̾̈́͑̚͠.̸͇̼̞̤͐̋̌͊̏̊̀̉͝͠',
            'https://youtu.be/roi2cyto-yk'
        ],
        [
            'petah does a cum.',
            'https://youtu.be/hnACyCBm8aY'
        ],
        [
            'Fallen kingdom.',
            'https://youtu.be/I-sH53vXP2A'
        ],
        [
            'Creepa! Awwwww man.',
            'https://youtu.be/cPJUBQd-PNM'
        ],
        [
            'Sex time (long).',
            'https://youtu.be/KAwyWkksXuo'
        ],
        [
            'Sex time (short).',
            'https://youtu.be/-khHhU00d1Q'
        ],
        [
            'Crazy frog.',
            'https://youtu.be/k85mRPqvMbE'
        ],
        [
            'Look for the gummy bear album in stores on November 13th.',
            'https://youtu.be/lBcBv6Ti5I4'
        ],
        [
            'Oh im a gummy bear.',
            'https://youtu.be/astISOttCQ0'
        ],
        [
            'Diggin\' minecraft style.',
            'https://youtu.be/CVxMTl6cUSE'
        ],
        [
            'Oof-dah.',
            'https://youtu.be/UkdFjOd2kuk'
        ],
        [
            'when you need a little revive .',
            'https://youtu.be/-XDoiXkkP4k'
        ],
        [
            'zombies round.',
            'https://youtu.be/AShdfcWla6M'
        ],
        [
            'Shutting down.',
            'https://youtu.be/Gb2jGy76v0Y'
        ],
        [
            'Start up.',
            'https://youtu.be/7nQ2oiVqKHw'
        ],
        [
            'Discord call.',
            'https://youtu.be/lIrE6CYHgRU'
        ],
        [
            'USB disconnect.',
            'https://youtu.be/JjkQzPsKv1Y'
        ],
        [
            'Reverb fart.',
            'https://youtu.be/Qi1KebO4bzc'
        ], 
        [
            'wow.',
            'https://youtu.be/mBr8mcLj9QY'
        ], 
        [
            'i am speed.',
            'https://youtu.be/4GwBhbwRv-4'
        ], 
        [
            'i fucked ur mom shit lips.',
            'https://youtu.be/1PXx9DWeAWw'
        ], 
        [
            'lightning mcqueef makes me cry.',
            'https://youtu.be/ba7DEM7Trn8'
        ], 
        [
            'oh no bro.',
            'https://youtu.be/skkNqKFCQ8Q'
        ], 
        [
            'skin? on your body?',
            'https://youtu.be/5AU2EudKYI4'
        ], 
        [
            'Gibby fucking dies.',
            'https://youtu.be/9KpynRZI_j0'
        ], 
        [
            'watch yo jet.',
            'https://youtu.be/jIaudEo9yCU'
        ], 
        [
            'It do go down.',
            'https://youtu.be/DYzT-Pk6Ogw'
        ], 
        [
            'Flower Garden.',
            'https://youtu.be/DTpksvCC-hg'
        ], 
        [
            'Arabic Nokia.',
            'https://youtu.be/7qKlU2a9-Zg'
        ], 
        [
            'The true infinity stone.',
            'https://youtu.be/Vk4KK-gh0FM'
        ], 
        [
            'Stroking.',
            'https://youtu.be/2aq85Z9372Y'
        ], 
        [
            'Bad to the bone.',
            'https://youtu.be/BtjCSazoy9U'
        ], 
        [
            'Chinese fish.',
            'https://youtu.be/J2aJlb-bmuM'
        ], 
        [
            'Globglogabgalab.',
            'https://youtu.be/cIwRQwAS_YY'
        ], 
        [
            'Jesus is the one.',
            'https://youtu.be/-pypV-JPU1k'
        ], 
        [
            'I get why my dad left.',
            'https://youtu.be/RTPMqb3-sO0'
        ], 
        [
            'Carelessly whispering.',
            'https://youtu.be/izGwDsrQ1eQ'
        ],
        [
            'Using that walk.',
            'https://youtu.be/ePCY-PwehfY'
        ],
        [
            'dutchie.',
            'https://youtu.be/EsyUa63NM1E'
        ],
        [
            'Sweet dreams.',
            'https://youtu.be/qeMFqkcPYcg'
        ],
        [
            'Still dre.',
            'https://youtu.be/QqZFpoc59kc'
        ],
        [
            'Thats not mud...',
            'https://youtu.be/SBgQezOF8kY'
        ],
        [
            'Biggest iron.',
            'https://youtu.be/zzICMIu5zFY'
        ],
        [
            'Ring of Fire.',
            'https://youtu.be/1WaV2x8GXj0'
        ],
        [
            'Wimoweh.',
            'https://youtu.be/N7MYqz7KgIs'
        ],
        [
            'Day-O.',
            'https://youtu.be/DYYkJ0kwNss'
        ],
        [
            'Brass Monkey.',
            'https://youtu.be/acY2VSskD80'
        ],
        [
            'That\'s my purse.',
            'https://youtu.be/u_t7ojOwJCs'
        ],
        [
            'Hooked on a feeling.',
            'https://youtu.be/7q0UTFq-o-o'
        ],
        [
            'Hooked on a feeling.',
            'https://youtu.be/7q0UTFq-o-o'
        ],
        [
            'Hooked on a feeling.',
            'https://youtu.be/7q0UTFq-o-o'
        ],

    ]
    # for debugging new memes
    # index = 7 # info(f'index: {index}') # meme = memes[index]
    meme = random.choice(memes)
    info(meme[0])
    url = meme[1]
    author = random.choice(num.active_users)
    for member in bot.get_all_members():
        if member.id == author.id:
            author = member
            break
    
    info(f'picking lucky user {author}\'s VC')
    YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    with YoutubeDL(YDL_OPTIONS) as ydl:
        extracted = ydl.extract_info(url, download=False)
    URL = extracted['formats'][0]['url']

    try:
        voice = await author.voice.channel.connect()
        if not voice.is_playing():
            voice.play(nextcord.PCMVolumeTransformer(nextcord.FFmpegPCMAudio(executable='./bin/ffmpeg.exe', source = URL, **FFMPEG_OPTIONS)))
            voice.is_playing()
            info(f'playing meme')
    except:
        error('couldn\'t connect to VC')

    

@bot.event
async def on_voice_state_update(member:Member,before:VoiceState,after:VoiceState):
    if member.voice != None and not member.bot:
        if member not in num.active_users:
            info(f'user joined: {member}')
            num.active_users.append(member)
    elif not member.bot:
        try:
            info(f'user left: {member}')
            num.active_users.remove(member)
        except ValueError as v:
            error(f'value error. Couldn\'t remove {member} from active VC user list.')
            


@bot.event
async def on_ready():
    info(f'{bot.user} has connected to Discord!')

def get_gif(search):
    params = {
        'q': search,
        'key': TT,
        'media_filter': 'gif,tinygif',
        'client_key': 'memeBot',
        'limit': 50,
    }
    data = requests.get(url='https://tenor.googleapis.com/v2/search?', params=params).json()['results']
    gifs=[]
    for item in data:
        gifs.append(item.get('url'))
    return random.choice(gifs)

@tasks.loop(seconds=1)
async def clean_up_time():
    for voice in bot.voice_clients:
        if voice.is_playing():
            num.active_vc[voice] = 0
        else:
            if voice in num.active_vc:
                if num.active_vc[voice] >= 10:
                    await voice.disconnect()
                    try:
                        await voice.cleanup()
                    except:
                        error('couldn\'t clean up voice')
                elif num.active_vc[voice] >= 3:
                    if voice.__dict__['server_id'] in num.song_queue:
                        if len(num.song_queue[voice.__dict__['server_id']]) > 0:
                            num.next_song(voice.__dict__['server_id'])
                else:
                    num.active_vc[voice] += 1

            

@clean_up_time.before_loop
async def before_clean_up():
    await bot.wait_until_ready()

@random_meme_sounds.before_loop
async def before_american():
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    info('starting up random music')


clean_up_time.start()
random_meme_sounds.start()
bot.run(TOKEN)