import discord
from discord.ext import commands
from discord.utils import get
import random
import asyncio
import time
from itertools import cycle
import logging

# Server invite link - https://discordapp.com/oauth2/authorize?client_id=501250712232132623&scope=bot&permissions=2146958801
# Github repository - https://github.com/AliShazly/dumb-bot

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)  # Change to INFO for less entries
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

token = open('token.txt', 'r').read()
client = commands.Bot(command_prefix='?')
prefix = '?'
client.remove_command('help')
server = '463945558348922892'
honk_num = 0
kevin_honk = 0

# Quicker setup for the reaction response feature
async def reaction_response(message, author, emojis, messages_to_delete=None, timeout=None):
    for i in emojis:
        await client.add_reaction(message, i)
    reaction = await client.wait_for_reaction(emoji=emojis, message=message, user=author, timeout=timeout)
    if reaction.reaction.emoji == emojis[0]:
        if messages_to_delete != None:
            for i in messages_to_delete:
                await client.delete_message(i)
        return True
    return False

@client.event  # Error handler
async def on_command_error(error, ctx):
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
            description=f'''There was a problem executing the command. Check what you typed and try again.\n
            `{str(error)[28:]}`''',
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
    await reaction_response(error_msg, ctx.message.author, ['❌'], [error_msg])
    print(type(error))
    print(error)


@client.event  # Prints bot login and version
async def on_ready():
    await client.change_presence(game=discord.Game(name='being bad at python'))
    print(f'We have logged in as {client.user}')
    print(f'Running on discord.py version {discord.__version__}')


@client.event  # Prints messages to the console and collects honk data
async def on_message(message):
    kevin_id = 135213084527689728
    print(f'{message.author}: {message.channel}: {message.content}')
    if message.content == 'gif':
        await client.send_message(message.channel, 'fuck jeremy')
    if ':honk:' in message.content and message.author.id == str(kevin_id):
        global kevin_honk
        kevin_honk += 1
    if ':honk:' in message.content or ':BadHonk:' in message.content:
        global honk_num
        honk_num += 1
    await client.process_commands(message)


@client.event  # Assigns premade role to new members
async def on_member_join(member):
    welcome_role = 'actors'
    role = discord.utils.get(member.server.roles, name=welcome_role)
    await client.add_roles(member, role)


@client.command(pass_context=True)  # Checks the pingtime of the bot
async def ping(ctx):
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
    await reaction_response(msg, ctx.message.author, ['❌'], [msg, ctx.message])


@client.command(pass_context = True)  # Echoes whatever the user attatches to the command
async def echo(ctx, *message):
    output = ''
    for word in message:
        output += f'{word} '
    embed = discord.Embed(
        description=f'{output}',
        colour=discord.Colour.orange()
    )
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg, ctx.message])


@client.command(pass_context=True)  # Flips a coin
async def flip(ctx):
    coinflip = random.choice(['heads', 'tails'])
    embed = discord.Embed(
        description=f'{ctx.message.author.nick} flipped a coin and got **{coinflip}**!',
        colour=discord.Color.orange()
    )
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg, ctx.message])

@client.command(pass_context = True)  # Returns honk stats
async def honk(ctx):
    embed = discord.Embed(
        title='<:honk:483485000713502740> Honks',
        description=f'''There have been {honk_num} honks since the bot was last started
        Kevin has honked {kevin_honk} times ~~ today ~~ *(doesn't work yet)* 
        Kevin has contributed {round((kevin_honk/honk_num), 3)*100}% of the total honks''',
        colour=discord.Colour.orange()
    )
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg, ctx.message])


@client.command(pass_context=True)  # Deletes a specified amount of messages
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount):
    amount = int(amount)
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


@client.command(pass_context = True)  # Spams whatever is given in the argument
# @commands.has_permissions(manage_messages=True)
async def spam(ctx, *args):
    output = ''
    msg_delete = []
    for word in args:
        output += word + ' '
    for _ in range(0, 5):
        delete = await client.say(output)
        msg_delete.append(delete)
        await asyncio.sleep(.1)
    await reaction_response(delete, ctx.message.author, ['❌'], messages_to_delete=([ctx.message] + msg_delete))

# Picks a random number or a random element from a list
@client.command(pass_context=True)
async def roll(ctx, *amount):
    amount = ' '.join(amount)
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
        if amount <= 1:
            embed = discord.Embed(
                description='Please pick a number greater than 1',
                colour=discord.Colour.orange()
            )
            msg = await client.say(embed=embed)
        else:
            random_num = random.randint(1, amount)
            embed = discord.Embed(
                description=f'**{ctx.message.author.nick}** rolled a {random_num}!',
                colour=discord.Color.orange()
            )
            msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg, ctx.message])

@client.command(name='8ball', pass_context=True)  # 8ball
async def _8ball(ctx, message):
    message = ctx.message.content[7:]
    random_num = random.randint(0, 19)
    responses = open('responses.txt').read().splitlines()
    embed = discord.Embed(
        title=':8ball: **8ball**',
        colour=discord.Colour.orange(),
        description=f'Q: {message.capitalize()} \nA: {responses[random_num]}',
    )
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg, ctx.message])

# Snaps half the people in a sepcific role, defaults to @everyone
@client.command(pass_context=True)
async def snap(ctx, role: discord.Role = None):
    members = []
    for member in ctx.message.server.members:
        if role in member.roles and str(member.status) != 'offline':
            members.append(member.name)
        elif role == None and str(member.status) != 'offline':
            members.append(member.name)
    random.shuffle(members)
    snap_num = 0
    snapped = [' '] # Empty value so the last member in the list gets included in the message
    for i in members:
        if snap_num % 2 == 0:
            snapped.insert(0, i) # Inserting at the beginning so the empty string stays at the end
        snap_num += 1
    embed_snapped = discord.Embed(
        title=':ok_hand:**Snapped**:ok_hand: ',
        colour=discord.Colour.purple(),
        description = ' was snapped!\n'.join(snapped)
    )
    msg = await client.say(embed=embed_snapped)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg, ctx.message])

@client.command(pass_context=True)  # owoifies text
async def owo(ctx, *message):
    output = ''
    for word in message:
        output += f'{word} '
    faces = ["(・`ω´・)", ";;w;;", "UwU", ">w<", "^w^", '(。O ω O。)']
    # This is ugly af and you should be ashamed
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


@client.command(pass_context=True)  # Clapifies a message
async def clap(ctx, *message):
    output = ''
    for word in message:
        output += f'{word} '
    output = output.replace(' ', ':clap:')
    embed = discord.Embed(
        title=f'{ctx.message.author.nick} says:',
        description=output,
        colour=discord.Colour.orange()
    )
    await client.say(embed=embed)


@client.command(pass_context=True)  # Creates a poll
async def poll(ctx, message):
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


# Exiles a user to a "you're wrong" channel, and gives them a temp role that has no perms. After the time is up they are returned to normal
@client.command(pass_context=True)
# @commands.has_permissions(manage_messages=True)
async def kevin(ctx, member: discord.Member, seconds=20):
    destination = client.get_channel('503452748017303553')
    initial_channel = member.voice_channel
    ali_id = 197156566288302080
    producer = discord.utils.get(member.server.roles, name='Producer')
    if seconds > 20:
        raise IndexError
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
    elif producer in member.roles:
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

@client.command(pass_context=True)  # Help window
async def help(ctx, *, message='all'):
    embed = discord.Embed(
        title='__Dumb Bot Help__',
        description='This bot is really stupid, but it works sometimes.',
        colour=discord.Colour.orange(),
    )
    embed.set_footer(text='Dumb Bot by Ali El-Shazly')
    embed.set_thumbnail(url='https://bit.ly/2Pg7YXm')
    if 'ping' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}ping', value='Returns the response time of the bot', inline=False)
    if 'echo' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}echo [message]', value='Returns [message] as an embed', inline=False)
    if 'clear' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}clear [amount]', value='**__Admin command__** Clears [amount] messages from the chat', inline=False)
    if 'spam' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}spam [message]', value='**__Admin command__** Returns [message] 5 times', inline=False)
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
            name=f'{prefix}snap [role]', value='Snaps half the people in [role], to make things truly balanced', inline=False)
    if 'owo' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}owo [message]', value='Owoifies [message] >w< ', inline=False)
    if 'clap' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}clap [message]', value='Clapifies [message]', inline=False)
    if 'owo' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}poll [message]', value='Creates a poll with [message] as the title', inline=False)
    if 'kevin' in message or message == 'all':
        embed.add_field(
            name=f'{prefix}kevin [user] [time]', value='Exiles [user] for [time] seconds. Default = 20secs', inline=False)
    if message == 'x' or message == 'all':
        embed.add_field(
            name=f'Red ❌', value='Click the red ❌ underneath a bot message to delete it and the command that summoned it. Can only be done by summoner.', inline=False)
    msg = await client.say(embed=embed)
    await reaction_response(msg, ctx.message.author, ['❌'], [msg, ctx.message])
    


# Make snap work with role names
# Make snap not snap bots
# Honk counter per day
# !Google command
# Make layers in the help command that you can cycle through with reactions
# Make user stats command
# Make !hug and !amicool and other novelty commands
# Make clear clear messages that were sent a couple secconds ago
client.run(token)
