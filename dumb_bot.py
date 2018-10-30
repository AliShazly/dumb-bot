import discord
from discord.ext import commands
from discord.utils import get
import random
import asyncio
import json
import time
from itertools import cycle
import logging
import os
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import requests
from io import BytesIO

# Server invite link - https://discordapp.com/oauth2/authorize?client_id=501250712232132623&scope=bot&permissions=2146958801
# Github repository - https://github.com/AliShazly/dumb-bot

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

logger = logging.getLogger('commands')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('errors.log', 'w', 'utf-8')
logger.addHandler(handler)

# token = open('token.txt', 'r').read()
token = os.environ['TOKEN']
prefix = '?'
client = commands.Bot(command_prefix=f'{prefix}')
client.remove_command('help')


async def reaction_response(message, author, emojis, messages_to_delete=None, timeout=None):
    """Quicker setup for the reaction response feature"""
    for i in emojis:
        await client.add_reaction(message, i)
    reaction = await client.wait_for_reaction(emoji=emojis, message=message, user=author, timeout=timeout)
    if reaction.reaction.emoji == emojis[0]:
        if messages_to_delete != None:
            for i in messages_to_delete:
                await client.delete_message(i)
        return True
    return False


@client.event
async def on_command_error(error, ctx):
    """Error handler"""
    # CheckFailure - User's permissions check failed
    if isinstance(error, commands.CheckFailure):
        embed = discord.Embed(
            title='CheckFailure Error',
            description='You do not have the permissions to use this command.',
            colour=discord.Colour.red()
        )
    # CommandInvokeError - When the user does the command syntax wrong eg. "!roll hello"
    elif isinstance(error, commands.CommandInvokeError):
        embed = discord.Embed(
            title='CommandInvoke Error',
            description=f'There was a problem executing the command. Check what you typed and try again.',
            colour=discord.Colour.red()
        )
    # MissingRequiredArgument - The user entered a command without an argument eg. "!8ball"
    elif isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title='MissingRequiredArgument Error',
            description=f'{error} `{ctx.message.content} [argument]`'.capitalize(
            ),
            colour=discord.Colour.red()
        )
    else:
        embed = discord.Embed(
            title='Error',
            description=f'{error}'.capitalize(),
            colour=discord.Color.red()
        )
    embed.set_footer(text=f'{prefix}help [command] for more info')
    error_msg = await client.send_message(ctx.message.channel, embed=embed)
    print(type(error))
    print(error)
    await reaction_response(error_msg, ctx.message.author, ['❌'], [error_msg])


@client.event
async def on_ready():
    """Prints bot login and version"""
    await client.change_presence(game=discord.Game(type=3, name=f'{len(list(client.servers))} servers | ?help'))
    print(f'We have logged in as {client.user}')
    print(f'Running on discord.py version {discord.__version__}')


@client.event
async def on_message(message):
    """Prints messages to the console"""
    print(f'{message.server}: {message.author}: {message.channel}: {message.content}: {message.embeds}')
    await client.process_commands(message)


@client.event
async def on_server_join(server):
    """Creates a JSON file with the server ID as the name, adds dict keys"""
    server_config = {
        'default_role':'',
        'prefix':'?'
    }
    open(f'{server.id}.json', 'a').close()
    with open(f'{server.id}.json', 'w') as outfile:
        json.dump(server_config, outfile)


@client.command(pass_context = True)
async def defaultrole(ctx,*message):
    """Sets the default role of the server"""
    message = ' '.join(message) # Converts tuple into string with spaces  
    role = discord.utils.get(ctx.message.server.roles, name=message)
    config = json.load(open(f'{ctx.message.server.id}.json'))
    config['default_role'] = str(role.id) # Adds the role ID to the default role key
    with open(f'{ctx.message.server.id}.json','w') as outfile:
        json.dump(config,outfile)
    embed = discord.Embed(
        description = f'default role has been set to `{role}`',
        colour = discord.Colour.orange()
    )
    await client.say(embed=embed)

@client.event
async def on_member_join(member): # ADD WARNING IN HELP COMMAND TO PUT BOT ROLE ABOVE DEFAULT ROLE OR IT WILL NOT WORK
    """Assigns premade role to new members"""
    try:
        config = json.load(open(f'{member.server.id}.json'))
        default_role = config['default_role']
        role = discord.utils.get(member.server.roles, id=default_role)
    except:
        print(f'new member joined {member.server.roles}, no default role set.')
    await client.add_roles(member, role)


@client.command(pass_context=True)
async def ping(ctx):
    """Checks the pingtime of the bot"""
    # Not accurate at all, this entire command needs to be reworked
    pingtime = time.time()
    pingms = await client.say("*Pinging...*")
    ping = (time.time() - pingtime) * 1000
    embed = discord.Embed(
        title='**Pong!** :ping_pong:',
        description=f'The ping time is `{int(ping)}ms`',
        colour=discord.Colour.orange()
    )
    print(f"Pinged bot with a response time of {ping}ms.")
    await client.delete_message(pingms)
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg])


@client.command(pass_context=True)
async def echo(ctx, *message):
    """Echoes whatever the user attatches to the command"""
    output = ''
    for word in message:
        output += f'{word} '
    embed = discord.Embed(
        description=f'{output}',
        colour=discord.Colour.orange()
    )
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg])


@client.command(pass_context=True)
async def flip(ctx):
    """Flips a coin"""
    coinflip = random.choice(['heads', 'tails'])
    embed = discord.Embed(
        description=f'{ctx.message.author.nick} flipped a coin and got **{coinflip}**!',
        colour=discord.Color.orange()
    )
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg])


@client.command(pass_context=True)
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount):
    """Deletes a specified amount of messages"""
    channel = ctx.message.channel
    messages = []
    async for message in client.logs_from(channel, limit=int(amount) + 1):
        messages.append(message)
    await client.delete_messages(messages)
    embed = discord.Embed(
        description=f'**{amount}** messages deleted',
        color=discord.Colour.orange()
    )
    messages_deleted = await client.say(embed=embed)
    await asyncio.sleep(2)
    await client.delete_message(messages_deleted)


# @client.command(pass_context=True)
# async def spam(ctx, *args):
#     """Spams whatever is given in the argument"""
#     output = ''
#     msg_delete = []
#     for word in args:
#         output += word + ' '
#     for _ in range(0, 5):
#         # Adds all spam messages to msg_delete and deletes them all when the user requests
#         delete = await client.say(output)
#         msg_delete.append(delete)
#         await asyncio.sleep(.1)
#     await reaction_response(delete, ctx.message.author, ['❌'], messages_to_delete=(msg_delete))


@client.command(pass_context=True)
async def roll(ctx, *amount):
    """Picks a random number or a random element from a list"""
    amount = ' '.join(amount)  # Converting the amount into a string
    if ',' in amount:
        roll_list = amount.split(',')
        list_choice = random.choice(roll_list)
        embed = discord.Embed(
            description=f'I picked **{list_choice}** from the list!',
            colour=discord.Colour.orange()
        )
        msg = await client.say(embed=embed)
    else:
        amount = int(amount)
        random_num = random.randint(1, amount)
        embed = discord.Embed(
            description=f'**{ctx.message.author.nick}** rolled a {random_num}!',
            colour=discord.Color.orange()
        )
        msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg])


@client.command(name='8ball', pass_context=True)
async def _8ball(ctx, message):
    """Asks the magic 8ball a question"""
    message = ctx.message.content[7:]  # Stripping the "!8ball" from the message
    random_num = random.randint(0, 19)
    responses = json.loads(open('responses.json').read())
    embed = discord.Embed(
        title=':8ball: **8ball**',
        colour=discord.Colour.orange(),
        description=f'Q: {message.capitalize()} \nA: {responses[random_num]}',
    )
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg])


@client.command(pass_context=True)
async def snap(ctx, role = None):
    """Snaps half the people in a sepcific role, defaults to @everyone"""
    role = discord.utils.get(ctx.message.server.roles, name=role)
    members = []
    # Stripping offline members from being snapped
    for member in ctx.message.server.members:
        if role in member.roles and str(member.status) != 'offline':
            members.append(member.name)
        elif role == None and str(member.status) != 'offline':
            members.append(member.name)
    random.shuffle(members)
    snap_num = 0
    # Ending with an empty value so the last member in the list gets included in the message
    snapped = [' ']
    for i in members:
        if snap_num % 2 == 0:
            # Inserting at the beginning so the empty string stays at the end
            snapped.insert(0, i)
        snap_num += 1
    embed_snapped = discord.Embed(
        title=':ok_hand:**Snapped**:ok_hand: ',
        colour=discord.Colour.purple(),
        description=' was snapped!\n'.join(snapped)
    )
    msg = await client.say(embed=embed_snapped)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg])


@client.command(pass_context=True)
async def owo(ctx, *message):
    """Owoifies text"""
    output = ''
    for word in message:
        output += f'{word} '
    faces = ["(・`ω´・)", ";;w;;", "UwU", ">w<", "^w^", '(。O ω O。)']
    # There has to be a better way to do this but this command is so stupid i dont care
    output = output.replace('l', 'w')
    output = output.replace('r', 'w')
    output = output.replace('na', 'nya')
    output = output.replace('ne', 'nye')
    output = output.replace('ni', 'nyi')
    output = output.replace('no', 'nyo')
    output = output.replace('nu', 'nyu')
    output = output.replace('ove', 'uv')
    embed = discord.Embed(
        title=f'{ctx.message.author.nick} says:',
        description=output + random.choice(faces),
        colour=discord.Colour.orange()
    )
    await client.say(embed=embed)


@client.command(pass_context=True)
async def clap(ctx, *message):
    """Clapifies a message"""
    output = ''
    for word in message:
        output += f'{word} '
    output = output.replace(' ', ':clap:')  # Replacing every space with a clap
    embed = discord.Embed(
        title=f'{ctx.message.author.nick} says:',
        description=output,
        colour=discord.Colour.orange()
    )
    await client.say(embed=embed)


@client.command(pass_context=True)
async def poll(ctx, message):
    """Creates a poll"""
    def to_emoji(num):  # Turns a number from 1-26 into an emoji from a-z
        base = 0x1f1e6
        return chr(base + num)
    title = ctx.message.content[6:]
    poll_created = discord.Embed(
        description='I have created your poll, What are your options? *(separate by commas)*',
        colour=discord.Colour.orange()
    )
    temp_message = await client.say(embed=poll_created)
    # Waits for the user's message and assigns it to options_raw
    options_raw = await client.wait_for_message(timeout=None, author=ctx.message.author, channel=ctx.message.channel)
    options_list = options_raw.content.split(',')
    for i in range(len(options_list)):
        # Adds the corresponding emoji in front of every choice
        options_list[i] = f'{to_emoji(i)}: {options_list[i].strip().capitalize()}'
    options_output = '\n'.join(options_list)
    embed = discord.Embed(
        title=f'{title.title()}',
        colour=discord.Colour.orange(),
        description=options_output
    )
    await client.delete_message(temp_message)
    poll = await client.say(embed=embed)
    for i in range(len(options_list)):
        await client.add_reaction(poll, to_emoji(i))


@client.command(pass_context=True, aliases=['kevin'])
async def exile(ctx, member: discord.Member, seconds=20):
    """Exiles a user to a "you're wrong" channel, and gives them a temp role that has no perms. After the time is up they are returned to normal"""
    destination = client.get_channel('503452748017303553')
    initial_channel = member.voice_channel
    ali_id = 197156566288302080
    # producer = discord.utils.get(member.server.roles, name='Producer')
    # best_friend_role = discord.utils.get(member.server.roles, name='Best Friend role')
    if seconds > 20:
        raise IndexError('Can not kevin someone for more than 20 seconds')
    # Checking to see if ali is the one being kevined, invokes a special message
    elif member.id == str(ali_id):
        embed = discord.Embed(
            title='F̨̛A̷̸̷̧̢T҉҉A͞L̸̕͜ ̨̡E̶͢͟R̢͡R̡͘O̴̡͘R̴̨͘',
            description='͏̷I̴҉̨ ̴̨a̴̢͢͝m̶̕ ̸̨̛͟u̶̢ǹ҉̡ą̨̀͡͝b̵̀́l̡e̷̛͡ ̛̕͏t̷̀̕o̧͢ ̸̛̕c̨̛̕͞o̴͠҉͟m̸̢̀p̷͢l͏̶è̸̸̵̴t̶͢e̴̡͜͠ ̶̧̕͘ý͘͝ớ̵̛u̵̵͢͞͠ŗ̸̛͢͟ ̢̕҉̡r̸̷e̕͞q̶̵̕͝͡ư͟͡ę̵͟s̴̨͟t͠҉.̷̸͟',
            colour=discord.Colour.red()
        )
        msg = await client.say(embed=embed)
        doit = get(client.get_all_emojis(), name='doit')
        check = await reaction_response(msg, ctx.message.author, [doit], timeout=30)
        if check == False:
            return
    # If the user is an admin then, the bot doesn't have perms to change thier role.
    elif ctx.message.author.server_permissions.administrator:
        t_end = time.time() + seconds
        while time.time() < t_end:
            await client.move_member(member, destination)
            await asyncio.sleep(.8)
        await client.move_member(member, initial_channel)
        return
    roles = []
    for role in member.roles:
        roles.append(role)
    kevin = discord.utils.get(member.server.roles, name='kevin')
    await client.replace_roles(member, kevin)
    t_end = time.time() + seconds
    while time.time() < t_end:
        await client.move_member(member, destination)
        await asyncio.sleep(.8)
    for role in roles:
        await client.add_roles(member, role)
        await asyncio.sleep(.8)
    await client.remove_roles(member, kevin)
    await client.move_member(member, initial_channel)


@client.command(pass_context=True)
async def deepfry(ctx, quality=None, image_url=None):
    """Deep fries an image"""
    channel = ctx.message.channel
    # If no link is provided, the bot assigns the URL of the last image sent in the channel to the image_link var
    if image_url == None:
        async for message in client.logs_from(channel, limit=30):
            if message.attachments != []:
                attachments_dict = message.attachments[0]
                image_url = attachments_dict['url']
                break

    # Need to use requests to read the image otherwise it returns a 403:FORBIDDEN error
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))  # Reading the raw image data
    img = img.convert('RGB')  # Converting RGBA into RGB

    # Resizes and resamples the image multiple times, then crushes the histogram
    if quality == 'crush':
        width, height = img.width, img.height
        img = img.resize((int(width ** .75), int(height ** .75)),
                         resample=Image.LANCZOS)
        img = img.resize((int(width ** .88), int(height ** .88)),
                         resample=Image.BILINEAR)
        img = img.resize((int(width ** .9), int(height ** .9)),
                         resample=Image.BICUBIC)
        img = img.resize((width, height), resample=Image.BICUBIC)
        img = ImageOps.posterize(img, 5)

    # Deep fries the image
    sharpness = ImageEnhance.Sharpness(img)
    img = sharpness.enhance(70)  # Sharpness
    brightnesss = ImageEnhance.Brightness(img)
    img = brightnesss.enhance(2)  # Brightness
    saturation = ImageEnhance.Color(img)
    img = saturation.enhance(2)  # Saturation
    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(3)  # Contrast
    img = img.filter(ImageFilter.SMOOTH_MORE)
    img = ImageOps.equalize(img)

    img.save(fp=f'fried.jpg', format='JPEG', quality=8)
    await client.send_file(channel, 'fried.jpg')
    os.remove('fried.jpg')


@client.command(pass_context=True)
async def jpeg(ctx, quality=2, image_url=None):
    """Applies a JPEG filter to an image, same ideas as deepfry"""
    channel = ctx.message.channel
    if image_url == None:
        async for message in client.logs_from(channel, limit=30):
            if message.attachments != []:
                attachments_dict = message.attachments[0]
                image_url = attachments_dict['url']
                break
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img = img.convert('RGB')
    img.save(fp='jpegged.jpg', format='JPEG', quality=quality)
    await client.send_file(channel, 'jpegged.jpg')
    os.remove('jpegged.jpg')


@client.command()
async def servers():
    """Debug command, prints server info to console"""
    servers=list(client.servers)
    for i in servers:
        print('\n')
        print(f'id = {i.id}')
        print(f'name = {i.name}')
        # print(f'owner = {i.owner}')
        # print(f'members = {len(list(i.members))}')
        # for x in i.members:
        #     print(f'member = {x.name}')
        print('\n')


@client.command(pass_context=True)
async def help(ctx, *, message='all'):
    """Help window"""
    embed = discord.Embed(
        title='__Dumb Bot Help__',
        description=f'This bot is currently in development. Report errors to Nacho#4642\n{prefix}help [command] to get help with a specific command',
        colour=discord.Colour.orange(),
    )
    embed.set_footer(text='Dumb Bot by Nacho#4642')
    embed.set_thumbnail(url='https://bit.ly/2Pg7YXm')
    if 'ping' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}ping', value='Returns the response time of the bot', inline=False)
    if 'echo' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}echo [message]', value='Returns [message] as an embed', inline=False)
    if 'clear' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}clear [amount]', value='Clears [amount] messages from the chat', inline=False)
    if 'spam' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}spam [message]', value='Returns [message] 5 times', inline=False)
    if 'roll' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}roll [value]', value=f'Returns a random number between 1 and [value]', inline=False)
    if 'roll' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}roll [list]', value='Returns a random value from [list], separate values with a comma', inline=False)
    if 'flip' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}flip', value='Returns heads or tails', inline=False)
    if '8ball' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}8ball [message]', value='Returns an answer from the magic 8 ball', inline=False)
    if 'snap' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}snap [role_name]', value='Snaps half the people in [role_name], to make things truly balanced', inline=False)
    if 'owo' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}owo [message]', value='Owoifies [message] >w< ', inline=False)
    if 'clap' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}clap [message]', value='Clapifies [message]', inline=False)
    if 'poll' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}poll [message]', value='Creates a poll with [message] as the title. Poll paramaters are collected in the next message sent by the user', inline=False)
    if 'exile' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}exile [user] [time]', value='Exiles [user] for [time] seconds. Default = 20secs', inline=False)
    if 'deepfry' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}deepfry [quality] [image_url]', value='Deep fries [image_url]. If [image_url] is not provided, deep fries the last image sent in the channel', inline=False)
    if 'jpeg' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}jpeg [quality] [image_url]', value='Applies a JPEG filter to [image_url] with a quality setting of [quality]', inline=False)
    if 'defaultrole' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}defaultrole [role_name]', value='Sets [role_name] as the default new member role. [role_name] must be lower than the bot role in the higherarchy', inline=False)
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg, ctx.message])


#        TODO:
# I guess you have to make the bot more professional now
# Refresh config command
# Add debug commands only you can access
# Add an exile channel to the json stuff
# Separate help by catagories
# Math command
# Case sensetivity stuff
# Un-delete command
# Osu stats
# !Google command
client.run(token)