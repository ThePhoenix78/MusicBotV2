#  coding: utf-8
import re, urllib.parse, urllib.request, sys, os, time, discord
from discord import FFmpegPCMAudio, PCMVolumeTransformer, File
from discord.ext import commands, tasks
from random import choice, shuffle
from unicodedata import normalize
from easy_playlist import Playlists
from yt_dlp import YoutubeDL
from discord.utils import get
from pathlib import Path


version = "2.0.0"
prefix = "-"

bot_token = ""
try:
    with open("bot_token", "r") as f:
        bot_token = f.readlines()[0].strip()
except FileNotFoundError:
    with open("bot_token", "w") as f:
        f.write("TOKEN_HERE")

intents = discord.Intents.all()
client = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), intents=intents, activity=discord.Game("Music go!"), status=discord.Status.online)

dis_status = ['waiting for you', "Music... Music everywhere", "github : https://github.com/ThePhoenix78/Music-Bot-Discord"]


serv_list: dict = {}

base_path = os.getcwd().replace("\\", "/")

music_dir = f"{base_path}/Musique"
down_dir = f"{music_dir}/download"

val = [music_dir, down_dir]

for name in val:
    Path(name).mkdir(exist_ok=True)


idk_voice_channel_msg = "I don't think I am in a voice channel"
msg_not_playing_error = "Music not playing failed pause"
music_not_paused_msg = "Music is not paused"
argument_msg_error = 'Please pass in all required arguments'
heavy_file_msg = "The file : {} is too heavy"
connection_msg = "The bot is connected to {}"
send_file_msg = "Sending file {}"
get_ready_msg = "Getting everything ready now"
msgnofound = "Error! No music was found locally!"
failed_stop = "No music playing failed to stop"
pause_msg = "Music paused!"
volume_msg = "Volume set on {}"
resume_msg = "Resumed music"
result_msg = "{} results found"
restart_msg = "Restarting bot"
stop_msg = "Music stopped"
join_msg = "Joined {}"
added_msg = "Added {}"
left_msg = "Left {}"
playing_msg = "Playing: {} [{}]"

help_msg = """
`/!\\ IMPORTANT NOTE! this bot will load all the musics he know containing the keys words and set it as a playlist /!\\`

>>> Commands

> Music <

- play (music/link) : will play the music
- next : will go to the next song
- previous : will go for the previous song
- add (music/link) : will add a music to the playlist
- pause : will pause the music
- resume : will resume the music
- join : will join the voice chat
- leave : will leave the voice chat
- deco : will disconnect all the members of the current voice chat
- vol (int) : will change the volume of the bot
- w / what : will show the the informations about the music
- sf / sendfile : will send the music as a mp3 format
"""


# ----------------------------SEARCH ENGINE-------------------------------

def convert_request(elem: str):
    res_convert = 0
    if " || " in elem:
        elem = elem.split("||")
        for i in range(len(elem)):
            elem[i] = elem[i].strip().split(" ")
        res_convert = 1

    elif " /= " in elem:
        value = elem.split()
        elem = elem.split("/=")
        notL = 0

        for v in range(len(value)):
            if value[v].startswith("/="):
                notL = v
                break

        for i in range(len(elem)):
            elem[i] = elem[i].strip().split(" ")

        res_convert = (2, notL)

    else:
        elem = elem.split()

    return elem, res_convert


def search_file(key_words, test=False):
    liste = []

    if test in (1, 2):
        for pat,  _,  files in os.walk(music_dir):
            for file in files:
                for elem in key_words:
                    j = 0
                    for i in range(len(elem)):
                        if (str(elem[i]).lower() in file.lower()) and file.endswith(".mp3"):
                            j += 1
                    if j == len(elem):
                        liste.append(f"{pat}/{file}".replace("\\", "/"))

    elif isinstance(test, tuple):
        for pat,  _,  files in os.walk(music_dir):
            for file in files:
                for elem in key_words:
                    j = 0
                    for i in range(len(elem)):
                        if (str(elem[i]).lower() in file.lower() and i != test[1]) and file.endswith(".mp3"):
                            j += 1
                    if j == len(elem):
                        liste.append(f"{pat}/{file}".replace("\\", "/"))

    else:
        for pat,  _,  files in os.walk(music_dir):
            for file in files:
                i = 0
                j = 0
                while i < len(key_words):
                    if str(key_words[i]).lower() in file.lower() and file.endswith(".mp3"):
                        j += 1
                    i += 1
                if j == len(key_words):
                    liste.append(f"{pat}/{file}".replace("\\", "/"))
    return liste


def get_file_path(name):
    for folder, sub_folder, files in os.walk(music_dir):
        for file in files:
            if name.lower() in file.lower() and file.endswith(".mp3"):
                return f"{folder}/{file}".replace("\\", "/")


def filtre_message(message, code):
    return normalize('NFD', message).encode(code, 'ignore').decode("utf8").strip()


def download_url(url):
    url = url.replace("```", "").replace("`", "")

    if ("=" in url and "/" in url and " " not in url) or ("/" in url and " " not in url):

        if "=" in url and "/" in url:
            ide = url.rsplit("=", 1)
            ide = ide[-1]
            music = ide
        elif "/" in url:
            ide = url.rsplit("/")
            ide = ide[-1]
            music = ide

        if get_file_path(music):
            return music

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
                }],
            'extract-audio': True,
            }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        for name in os.listdir():
            if music in name:
                os.system('move /Y {} {}'.format(f'"{name}"', f'{down_dir}/"{name}"'))
                break

        url = f'{name}'
    return url


def search_internet_music(music_name):
    query_string = urllib.parse.urlencode({"search_query": music_name})
    formatUrl = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)

    search_results = re.findall(r"watch\?v=(\S{11})", formatUrl.read().decode())
    clip2 = "https://www.youtube.com/watch?v=" + "{}".format(search_results[0])
    return download_url(clip2)


def get_music(music):
    music = download_url(music)

    elem, res_convert = convert_request(music)
    search = search_file(elem, res_convert)

    if not search:
        music = search_internet_music(music)
        elem, res_convert = convert_request(music)
        search = search_file(elem, res_convert)

    return search

# ------------------------CLASS------------------------------------------------


class MusicManager(Playlists):
    def __init__(self):
        Playlists.__init__(self)

    def add_guild(self, ctx):
        try:
            self.add_playlist(ctx.guild.id, loop=True)
            current = self.get_playlist(ctx.guild.id)
        except Exception:
            self.add_playlist(ctx.id,  loop=True)
            current = self.get_playlist(ctx.id)

        current.guild = ctx
        current.volume = 1.0


playlists = MusicManager()


def music_player(serv):
    voice = get(client.voice_clients,  guild=serv.guild)

    if voice and voice.is_playing():
        voice.stop()

    serv.play()
    current = serv.get_current()
    voice.play(FFmpegPCMAudio(current.file))
    voice.source = PCMVolumeTransformer(voice.source)
    voice.source.volume = serv.volume


def convert_time(value):
    val2, val = int(value//60), int(value % 60)
    message = f"{val2}min {val}s."

    if val2 > 60:
        val3, val2 = int(val2//60), int(val2 % 60)
        message = f"{val3}h {val2}min {val}s."

    return message


@playlists.event("music_over")
def music_over(data):
    print(f"[{data.playlist.name}] {data.music.name} is over, next song now!")
    data.playlist.next()
    music_player(data.playlist)

# -----------------------------EVENTS--------------------------------


@client.event
async def on_ready():
    servers = client.guilds

    for server in servers:
        playlists.add_guild(server)

    change_status.start()
    print("version : ", f"{os.path.basename(sys.argv[0])} {version}")
    print("Logged in as : ", client.user.name)
    print("ID : ", client.user.id)


@client.event
async def on_guild_join(ctx):
    servers = client.guilds
    for server in servers:
        if server not in playlists.get_playlist(server.id):
            playlists.add_guild(server)


@client.event
async def on_command_error(ctx,  error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(argument_msg_error)


@client.event
async def on_voice_state_update(member, before, after):
    serv = playlists.get_playlist(member.guild.id)
    voice_state = member.guild.voice_client

    if not (voice_state and len(voice_state.channel.members) == 1):
        return

    voice = get(client.voice_clients,  guild=serv.guild)

    if voice and voice.is_playing():
        voice.stop()

    if voice and voice.is_connected():
        await voice.disconnect()

    serv.clear()


# -----------------------------VOICE COMMANDS----------------------------


timer = time.time()


@client.command(aliases=["version", "ping"])
async def ver(ctx):
    value = int(time.time()-timer)
    await ctx.send(f"version : {version}\nping : {round(client.latency * 1000)}ms :ping_pong:\ntime up : {convert_time(value)}")


@client.command(pass_context=True, aliases=["p"])
async def play(ctx, *, music: str):
    serv = playlists.get_playlist(ctx.guild.id)

    try:
        channel = ctx.message.author.voice.channel
        voice = get(client.voice_clients,  guild=ctx.guild)
    except Exception:
        return

    serv.clear()

    if not voice or (voice and not voice.is_connected()):
        channel = ctx.message.author.voice.channel

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()

        await voice.disconnect()

        if voice and voice.is_connected():
            await voice.move_to(channel)
            print(connection_msg.format(channel))
        else:
            voice = await channel.connect()
            print(connection_msg.format(channel))

        await ctx.send(join_msg.format(channel))

    await ctx.send(get_ready_msg)

    search = get_music(music)

    if not search:
        await ctx.send(msgnofound)
        return

    serv.add_music(search)
    music_player(serv)
    await ctx.send(playing_msg.format(serv.current.name, convert_time(serv.current.length)))


@client.command()
async def join(ctx):
    channel = ctx.message.author.voice.channel

    voice = get(client.voice_clients,  guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

    await voice.disconnect()

    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        voice = await channel.connect()

    await ctx.send(join_msg.format(channel))


@client.command()
async def leave(ctx):
    serv = playlists.get_playlist(ctx.guild.id)
    serv.clear()

    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients,  guild=ctx.guild)

    if voice and voice.is_playing():
        voice.stop()

    if voice and voice.is_connected():
        await voice.disconnect()
        await ctx.send(left_msg.format(channel))
    else:
        await ctx.send(idk_voice_channel_msg)


@client.command()
async def next(ctx):
    serv = playlists.get_playlist(ctx.guild.id)
    serv.next()
    music_player(serv)
    await ctx.send(playing_msg.format(serv.current.name, convert_time(serv.current.length)))


@client.command()
async def previous(ctx):
    serv = playlists.get_playlist(ctx.guild.id)
    a = serv.previous()
    music_player(serv)
    await ctx.send(playing_msg.format(serv.current.name, convert_time(serv.current.length)))


@client.command(pass_context=True, aliases=["volume"])
async def vol(ctx, nb):
    serv = playlists.get_playlist(ctx.guild.id)
    vol = int(nb)
    vol = vol/10 if vol <= 1 else vol/100

    voice = get(client.voice_clients,  guild=ctx.guild)
    voice.source = PCMVolumeTransformer(voice.source)
    voice.source.volume = vol

    serv.volume = vol
    await ctx.send(volume_msg.format(vol))


@client.command()
async def replay(ctx):
    serv = playlists.get_playlist(ctx.guild.id)
    music_player(serv)
    await ctx.send(playing_msg.format(serv.current.name, convert_time(serv.current.length)))


@client.command(aliases=["w"])
async def what(ctx):
    serv = playlists.get_playlist(ctx.guild.id)
    val = serv.current.timer if serv.current.timer > 0 else 0
    await ctx.send(f"Music : {serv.current.name} [{int(val/60)} : {int(val % 60)}/{convert_time(serv.current.length)}]")


@client.command()
async def add(ctx, *, music):
    serv = playlists.get_playlist(ctx.guild.id)

    search = get_music(music)

    if not search:
        await ctx.send(msgnofound)
        return

    shuffle(search)
    serv.add_music(search)
    await ctx.send(added_msg.format(music))


@client.command()
async def pause(ctx):
    serv = playlists.get_playlist(ctx.guild.id)

    voice = get(client.voice_clients,  guild=ctx.guild)

    if voice and voice.is_playing():
        serv.pause()
        voice.pause()
        await ctx.send(pause_msg)
    else:
        await ctx.send(msg_not_playing_error)


@client.command()
async def resume(ctx):
    serv = playlists.get_playlist(ctx.guild.id)

    voice = get(client.voice_clients,  guild=ctx.guild)

    if voice and voice.is_paused():
        serv.resume()
        voice.resume()
        await ctx.send(resume_msg)
    else:
        await ctx.send(music_not_paused_msg)


@client.command()
async def stop(ctx):
    serv = playlists.get_playlist(ctx.guild.id)

    voice = get(client.voice_clients,  guild=ctx.guild)

    if voice and voice.is_playing():
        voice.stop()
        serv.clear()
        await ctx.send(stop_msg)

    else:
        await ctx.send(failed_stop)


@client.command()
async def deco(ctx):
    try:
        channel = ctx.message.author.voice.channel
    except Exception:
        return

    voice = get(client.voice_clients,  guild=ctx.guild)

    if voice and voice.is_playing():
        voice.stop()

    if voice and voice.is_connected():
        await voice.disconnect()

    victims = ctx.guild.members

    kick_channel = await ctx.guild.create_voice_channel("kick")

    for victim_member in victims:
        try:
            if victim_member.voice.channel == channel:
                await victim_member.move_to(kick_channel,  reason="deco")
        except Exception:
            pass

    await kick_channel.delete()

# --------------------------------BASICS COMMANDS-------------------------------


@client.command()
async def size(ctx, *, message):
    elem, res_convert = convert_request(message)
    a = search_file(elem, res_convert)
    await ctx.send(result_msg.format(len(a)))


@client.command(aliases=["list"])
async def liste(ctx, *, message="."):
    elem, res_convert = convert_request(message)
    a = search_file(elem, res_convert)

    playliste = []
    if len(a) <= 10:
        for i in range(len(a)):
            playliste.append(a[i])
            await ctx.send("```"+str(a[i])+"```")
        return

    i = 0
    while i <= 10:
        ran = choice(a)
        if ran not in playliste:
            playliste.append(ran)
            await ctx.send("```"+str(ran)+"```")
            i += 1


@client.command(aliases=["sendfile"])
async def sf(ctx, *, music: str):
    await ctx.send(get_ready_msg)

    search = get_music(music)

    if not search:
        await ctx.send(msgnofound)
        return

    b = choice(search)

    if os.path.getsize(b) >= 8000000:
        await ctx.send(heavy_file_msg.format(file))
        return

    await ctx.send(send_file_msg.format(str(file)))

    with open(b,  'rb') as fp:
        await ctx.send(file=File(fp,  file))


@client.command(pass_context=True)
async def move(ctx, *, chan=""):

    victim = ctx.guild.members
    val = ctx.guild.voice_channels

    for i in range(len(val)):
        if str(chan) == str(val[i]):
            kick_channel = val[i]
            break
        elif str(chan).upper() in str(val[i]).upper():
            kick_channel = val[i]
            break

    for i in range(len(victim)):
        victim_member = victim[i]
        try:
            if victim_member.voice.channel in val and ("AFK" not in str(victim_member.voice.channel).upper()):
                await victim_member.move_to(kick_channel, reason="")
        except Exception:
            pass


# ------------------------------------TASKS-------------------------------------


@client.command()
async def reboot(ctx):
    serv = playlists.get_playlist(ctx.guild.id)

    await client.change_presence(activity=discord.Game("Shutting down..."), status=discord.Status.dnd)
    voice = get(client.voice_clients,  guild=ctx.guild)

    if voice and voice.is_playing():
        voice.stop()

    if voice and voice.is_connected():
        await voice.disconnect()

    serv.clear()

    await ctx.send(restart_msg)
    os.execv(sys.executable, ["None", os.path.basename(sys.argv[0])])


iter = 0


@tasks.loop(seconds=127)
async def change_status():
    global iter
    await client.change_presence(activity=discord.Game(dis_status[iter]))
    iter += 1
    if iter > len(dis_status)-1:
        iter = 0


client.run(bot_token) # , log_handler=None)
# code by ThePhoenix78 on GitHub
