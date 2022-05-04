import discord
import json
import db, ticket_embed
import asyncio

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
    elif channel.id == config['channel']:
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

        ticket_user = guild.get_member(ticket['user'])

        if str(reaction.emoji) == '🗣️':
            cancel = await modmail_channel.send(embed=ticket_embed.reply_cancel(ticket_user))
            await cancel.add_reaction('❎')

            def reply_cancel(reaction, user):
                return user == reaction_user and cancel == reaction.message and str(reaction.emoji) == '❎'
            def reply_message(message):
                return message.author == reaction_user and message.channel == modmail_channel

            try:
                tasks = [
                    asyncio.create_task(client.wait_for('reaction_add', timeout=60.0, check=reply_cancel), name='cancel'),
                    asyncio.create_task(client.wait_for('message', timeout=60.0,check=reply_message), name='respond')
                ]

                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                event: asyncio.Task = list(done)[0]

                for task in pending:
                    try:
                        task.cancel()
                    except asyncio.CancelledError:
                        pass


                if event.get_name() == 'respond':
                    message = event.result()
                    if  len(message.content) > 0:
                        db.add_ticket_response(ticket['ticket_id'], reaction_user.id, message.content, True)
                        await ticket_user.send(embed=ticket_embed.user_embed(guild, message))
                        ticket_message = await modmail_channel.fetch_message(ticket['message_id'])
                        await ticket_message.edit(embed=ticket_embed.channel_embed(guild, ticket['ticket_id']))
            except asyncio.TimeoutError:
                pass

            await cancel.delete()
        elif str(reaction.emoji) == '❎':
            confirmation = await modmail_channel.send(embed=ticket_embed.close_confirmation(ticket_user))
            await confirmation.add_reaction('✅')
            await confirmation.add_reaction('❎')

            def close_check(reaction, user):
                return user == reaction_user and confirmation == reaction.message and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❎')

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=close_check)
                if str(reaction.emoji) == '✅':
                    db.close_ticket(ticket['ticket_id'])
                    ticket_message = await modmail_channel.fetch_message(ticket['message_id'])
                    await ticket_message.delete()
                    await modmail_channel.send(embed=ticket_embed.closed_ticket(reaction_user, ticket_user))
            except asyncio.TimeoutError:
                pass

            await confirmation.delete()


async def handle_dm(message):
    user = message.author

    guild = client.get_guild(config['guild'])
    modmail_channel = guild.get_channel(config['channel'])

    ticket = db.get_ticket_by_user(user.id)

    if ticket['ticket_id'] == -1:
        ticket_id = db.open_ticket(user.id)
        ticket = db.get_ticket(ticket_id)

    db.add_ticket_response(ticket['ticket_id'], user.id, message.content, False)
    ticket_message = await modmail_channel.send(embed=ticket_embed.channel_embed(guild, ticket['ticket_id']))
    db.update_ticket_message(ticket['ticket_id'], ticket_message.id)
    await message.add_reaction('📨')
    await ticket_message.add_reaction('🗣️')
    await ticket_message.add_reaction('❎')
    await ticket_message.add_reaction('⏲️')

    if ticket['message_id'] is not None and ticket['message_id'] != -1:
        old_ticket_message = await modmail_channel.fetch_message(ticket['message_id'])
        await old_ticket_message.delete()


async def handle_server(message):
    pass   

def ready():
    if db.init():
        print('Database sucessfully initialized!')
    else:
        print('Error while initializing database!')
    
    if "channel" not in config:
        print('Failed to find Modmail text channel from provided ID.')
    
    if "guild" not in config:
        print('Failed to find Guild from provided ID.')

ready()

client.run(config['token'])