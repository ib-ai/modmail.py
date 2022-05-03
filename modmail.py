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
        await channel.send('Test')

def ready():
    db.init()

ready()

client.run(config['token'])