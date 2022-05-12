import discord, json, asyncio, datetime
import db, ticket_embed, command_formatter, uformatter, embed_reactions
from embed_reactions import embed_reactions
from command_actions import command_actions, post_reactions

with open('./config.json', 'r') as config_json:
    config = json.load(config_json)

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
guild = None
modmail_channel = None

def bot_ready(func):
    def wrapper(*args,**kwargs):
        if guild is None or modmail_channel is None:
            print('Bot not ready yet')
            return

        ret = func(cursor, *args, *kwargs)
        return ret
    return wrapper

@bot_ready
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channel = message.channel

    if isinstance(channel, discord.channel.DMChannel):
        await handle_dm(message)
    elif channel.id == config['channel'] and message.content.startswith(config['prefix']):
        await handle_server(message)

@bot_ready
@client.event
async def on_raw_reaction_add(payload):
    #Ignore if self
    if payload.user_id == client.user.id:
        return

    #Ignore if not in guild
    if not payload.guild_id or not payload.guild_id == config['guild']:
        return

    #Ignore if not in modmail channel
    if not payload.channel_id == config['channel']:
        return

    #Ignore if not unicode emoji
    if not payload.emoji.is_unicode_emoji():
        return

    #Get member object
    reaction_user = payload.member

    #Ignore if bot
    if reaction_user.bot:
        return

    #Get unicode emoji
    emoji = payload.emoji.name

    #Get message object
    message = await modmail_channel.fetch_message(payload.message_id)

    await handle_reaction(emoji, message, reaction_user)

async def handle_reaction(emoji, message, reaction_user):
    ticket = db.get_ticket_by_message(message.id)
    if ticket['ticket_id'] == -1:
        return

    await message.remove_reaction(emoji, reaction_user)

    embed_actions = embed_reactions(client, guild, modmail_channel, reaction_user, ticket)

    if str(emoji) == '🗣️':
        await embed_actions.message_reply()    
    elif str(emoji) == '❎':
        await embed_actions.message_close()    
    elif str(emoji) == '⏲️':
        ticket_user = guild.get_member(ticket['user'])
        await embed_actions.message_timeout(ticket_user)    
            
async def handle_dm(message):
    user = message.author

    timeout = db.get_timeout(user.id)
    current_time = int(datetime.datetime.now().timestamp())

    if timeout != False and current_time < timeout['timestamp']:
        await user.send(embed=ticket_embed.user_timeout(timeout['timestamp']))
        return
    
    response = uformatter.format_message(message)

    if not response.strip():
        return
    
    # ! Fix for longer messages
    if len(response) > 1000:
        await message.channel.send('Your message is too long. Please shorten your message or send in multiple parts.')
        return

    ticket = db.get_ticket_by_user(user.id)

    if ticket['ticket_id'] == -1:
        ticket_id = db.open_ticket(user.id)
        ticket = db.get_ticket(ticket_id)
 
    db.add_ticket_response(ticket['ticket_id'], user.id, response, False)
    ticket_message = await modmail_channel.send(embed=ticket_embed.channel_embed(guild, ticket['ticket_id']))
    db.update_ticket_message(ticket['ticket_id'], ticket_message.id)
    await message.add_reaction('📨')
    await post_reactions(ticket_message)

    if ticket['message_id'] is not None and ticket['message_id'] != -1:
        old_ticket_message = await modmail_channel.fetch_message(ticket['message_id'])
        await old_ticket_message.delete()


async def handle_server(message):
    command, arguments = command_formatter.get_command(config['prefix'], message.content)
    server_user = message.author

    print(command, arguments)

    server_actions = command_actions(client, guild, modmail_channel, server_user, message, arguments)

    try:
        if command == 'ping':
            await message.channel.send('Pong! Latency: {0}ms'.format(int(client.latency)))
        elif command == 'open':
            await server_actions.open_ticket()
        elif command == 'refresh':
            await server_actions.refresh_ticket()
        elif command == 'close':
            await server_actions.close_ticket()
        elif command == 'timeout':
            await server_actions.timeout_ticket()
        elif command == 'untimeout':
            await server_actions.untimeout_ticket()

    except RuntimeError as e:
        await message.channel.send(str(e))
        
@client.event
async def on_ready():
    global guild, modmail_channel

    guild = client.get_guild(config['guild'])

    if guild is None:
        print('Failed to find Guild from provided ID.')
        await client.close()
        return

    modmail_channel = guild.get_channel(config['channel'])

    if modmail_channel is None:
        print('Failed to find Modmail Channel from provided ID.')    
        await client.close()
        return

def ready():
    if db.init():
        print('Database sucessfully initialized!')
    else:
        print('Error while initializing database!')
        return False

    if "guild" not in config:
        print('No Guild ID provided.')
        return False

    if "channel" not in config:
        print('No Channel ID provided.')
        return False
    
    if "prefix" not in config:
        print('Failed to find prefix in config.')
        return False

    return True

success = ready()

if success:
    client.run(config['token'])
else:
    print('Error during staring process')