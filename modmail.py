import os

import discord, json
from discord.ext import commands

import db, utils.embed_reactions as embed_reactions
from cogs.command_actions import CommandActions
from cogs.listeners import Listeners

with open('./config.json', 'r') as config_json:
    config = json.load(config_json)
    
    # Load from environment variable overrides
    if "MODMAIL_TOKEN" in os.environ:
        config["token"] = os.getenv("MODMAIL_TOKEN")
    if "MODMAIL_GUILD" in os.environ:
        config["guild"] = int(os.getenv("MODMAIL_GUILD"))
    if "MODMAIL_CHANNEL" in os.environ:
        config["channel"] = int(os.getenv("MODMAIL_CHANNEL"))
    if "MODMAIL_PREFIX" in os.environ:
        config["prefix"] = os.getenv("MODMAIL_PREFIX")
    if "MODMAIL_STATUS" in os.environ:
        config["status"] = os.getenv("MODMAIL_STATUS")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(intents=intents, command_prefix=config['prefix'])
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
@bot.event
async def on_raw_reaction_add(payload):
    """Handles reactions to messages.

    Args:
        payload (discord.RawReactionActionEvent): Payload for raw reaction methods.
    """
    # Ignore if self
    if payload.user_id == bot.user.id:
        return

    # Ignore if not in guild
    if not payload.guild_id or not payload.guild_id == config['guild']:
        return

    # Ignore if not in modmail channel
    if not payload.channel_id == config['channel']:
        return

    # Ignore if not unicode emoji
    if not payload.emoji.is_unicode_emoji():
        return

    # Get member object
    reaction_user = payload.member

    # Ignore if bot
    if reaction_user.bot:
        return

    # Get unicode emoji
    emoji = payload.emoji.name

    # Get message object
    message = await modmail_channel.fetch_message(payload.message_id)

    await handle_reaction(emoji, message, reaction_user)

async def handle_reaction(emoji, message, reaction_user):
    """Handles reactions for ModMail embeds.

    Args:
        emoji (discord.PartialEmoji): The emoji being used.
        message (discord.Message): The current message.
        reaction_user (discord.Member): The user who triggered the reaction event.
    """
    ticket = db.get_ticket_by_message(message.id)
    if ticket['ticket_id'] == -1:
        return

    await message.remove_reaction(emoji, reaction_user)

    embed_actions = embed_reactions.embed_reactions(bot, guild, modmail_channel, reaction_user, ticket)

    if str(emoji) == '🗣️':
        await embed_actions.message_reply()    
    elif str(emoji) == '❎':
        await embed_actions.message_close()    
    elif str(emoji) == '⏲️':
        ticket_user = guild.get_member(ticket['user'])
        await embed_actions.message_timeout(ticket_user)    
        
@bot.event
async def on_ready():
    global guild, modmail_channel

    guild = bot.get_guild(config['guild'])

    if guild is None:
        print('Failed to find Guild from provided ID.')
        await bot.close()
        return

    modmail_channel = guild.get_channel(config['channel'])

    if modmail_channel is None:
        print('Failed to find Modmail Channel from provided ID.')    
        await bot.close()
        return
      
    await bot.change_presence(activity=discord.Game(name=config['status']), status=discord.Status.online)

    bot.add_cog(Listeners(bot, guild, modmail_channel))
    bot.add_cog(CommandActions(bot, modmail_channel))

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
    bot.run(config['token']) 

else:
    print('Error during starting process')
