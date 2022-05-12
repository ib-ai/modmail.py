import discord, json, asyncio, datetime
import db, ticket_embed, command_formatter, uformatter, embed_reactions
from embed_reactions import embed_reactions
from command_actions import command_actions, post_reactions

with open('./config.json', 'r') as config_json:
    config = json.load(config_json)

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channel = message.channel

    if isinstance(channel, discord.channel.DMChannel):
        await handle_dm(message)
    elif channel.id == config['channel'] and message.content.startswith(config['prefix']):
        await handle_server(message)

@client.event
async def on_reaction_add(reaction, reaction_user):
    if reaction_user == client.user:
        return

    guild = client.get_guild(config['guild'])
    modmail_channel = guild.get_channel(config['channel'])

    message = reaction.message
    channel = message.channel

    if channel.id == config['channel']:
        ticket = db.get_ticket_by_message(message.id)
        if ticket['ticket_id'] == -1:
            return

        await reaction.remove(reaction_user)

        embed_actions = embed_reactions(client, guild, modmail_channel, reaction_user, ticket)

        if str(reaction.emoji) == '🗣️':
            await embed_actions.message_reply()    
        elif str(reaction.emoji) == '❎':
            await embed_actions.message_close()    
        elif str(reaction.emoji) == '⏲️':
            ticket_user = guild.get_member(ticket['user'])
            await embed_actions.message_timeout(ticket_user)    
            
async def handle_dm(message):
    user = message.author

    guild = client.get_guild(config['guild'])
    modmail_channel = guild.get_channel(config['channel'])

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
    guild = client.get_guild(config['guild'])
    modmail_channel = guild.get_channel(config['channel'])

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
        
def ready():
    if db.init():
        print('Database sucessfully initialized!')
    else:
        print('Error while initializing database!')
    
    if "channel" not in config:
        print('Failed to find Modmail text channel from provided ID.')
    
    if "guild" not in config:
        print('Failed to find Guild from provided ID.')
    
    if "prefix" not in config:
        print('Failed to find prefix in config.')


ready()

client.run(config['token'])