import discord
import json
import db

with open('./config.json', 'r') as config_json:
    config = json.load(config_json)

client = discord.Client()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channel = message.channel
    if isinstance(channel, discord.channel.DMChannel):
        if message.content == 'New':
            await channel.send(db.open_ticket(message.author.id))
        elif message.content == 'Get':
            await channel.send(db.get_ticket_by_user(message.author.id))
        elif message.content == 'Close':
            ticket_id = db.get_ticket_by_user(message.author.id)
            await channel.send(db.close_ticket(ticket_id))


def ready():
    if db.init():
        print('Database sucessfully initialized!')
    else:
        print('Error while initializing database!')

ready()

client.run(config['token'])