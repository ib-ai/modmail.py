import datetime, asyncio
import command_formatter, db, ticket_embed
from embed_reactions import embed_reactions

class command_actions():
    def __init__(self, client, guild, modmail_channel, reaction_user, message, arguments):
        self.client = client
        self.guild = guild
        self.modmail_channel = modmail_channel
        self.reaction_user = reaction_user
        self.message = message
        self.arguments = arguments

    

    async def open_ticket(self):
        member = command_formatter.assert_member(self.guild, self.arguments, 0)

        ticket = db.get_ticket_by_user(member.id)

        # ! Optimise if ticket is already open

        if ticket['ticket_id'] != -1:
            await self.message.channel.send('There is already a ticket open for {0}'.format(member))
            return

        ticket_id = db.open_ticket(member.id)
        ticket = db.get_ticket(ticket_id)
        
        ticket_message = await self.modmail_channel.send(embed=ticket_embed.channel_embed(self.guild, ticket['ticket_id']))
        db.update_ticket_message(ticket['ticket_id'], ticket_message.id)

        await post_reactions(ticket_message)

    async def refresh_ticket(self):
        member = command_formatter.assert_member(self.guild, self.arguments, 0)

        ticket = db.get_ticket_by_user(member.id)

        if ticket['ticket_id'] == -1:
            await self.message.channel.send('There is no ticket open for {0}.'.format(member))
            return

        ticket_message = await self.modmail_channel.send(embed=ticket_embed.channel_embed(self.guild, ticket['ticket_id']))
        db.update_ticket_message(ticket['ticket_id'], ticket_message.id)

        if ticket['message_id'] is not None and ticket['message_id'] != -1:
            old_ticket_message = await self.modmail_channel.fetch_message(ticket['message_id'])
            await old_ticket_message.delete()
        
        await post_reactions(ticket_message)
    
    async def close_ticket(self):
        member = command_formatter.assert_member(self.guild, self.arguments, 0)

        ticket = db.get_ticket_by_user(member.id)

        if ticket['ticket_id'] == -1:
            await self.message.channel.send('There is no ticket open for {0}.'.format(member))
            return
        
        embed_commands = embed_reactions(self.client, self.guild, self.modmail_channel, self.reaction_user, ticket)
        await embed_commands.message_close()

    async def timeout_ticket(self):
        member = command_formatter.assert_member(self.guild, self.arguments, 0)

        embed_commands = embed_reactions(self.client, self.guild, self.modmail_channel, self.reaction_user)
        await embed_commands.message_timeout(member)

    async def untimeout_ticket(self):
        member = command_formatter.assert_member(self.guild, self.arguments, 0)

        timeout = db.get_timeout(member.id)
        current_time = int(datetime.datetime.now().timestamp())

        if timeout == False or (timeout != False and current_time > timeout['timestamp']):
            await self.message.channel.send('{0} is not currently timed out.'.format(member))
            return
        
        confirmation = await self.modmail_channel.send(embed=ticket_embed.untimeout_confirmation(member, timeout['timestamp']))
        await confirmation.add_reaction('✅')
        await confirmation.add_reaction('❎')

        def untimeout_check(reaction, user):
            return user == self.reaction_user and confirmation == reaction.message and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❎')

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=untimeout_check)
            if str(reaction.emoji) == '✅':
                timestamp = int(datetime.datetime.now().timestamp())
                db.set_timeout(member.id, timestamp)
                await member.send(embed=ticket_embed.user_untimeout())
                await self.modmail_channel.send('{0} has been successfully untimed out.'.format(member))
        except asyncio.TimeoutError:
            pass

        await confirmation.delete()

async def post_reactions(message):
    await message.add_reaction('🗣️')
    await message.add_reaction('❎')
    await message.add_reaction('⏲️')