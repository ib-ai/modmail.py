import asyncio, datetime
import db, uformatter, ticket_embed

class embed_reactions():
    def __init__(self, client, guild, modmail_channel, reaction_user, ticket=None):
        self.client = client
        self.guild = guild
        self.modmail_channel = modmail_channel
        self.reaction_user = reaction_user
        self.ticket = ticket

    async def message_reply(self):
        ticket_user = self.guild.get_member(self.ticket['user'])

        cancel = await self.modmail_channel.send(embed=ticket_embed.reply_cancel(ticket_user))
        await cancel.add_reaction('❎')

        def reply_cancel(reaction, user):
            return user == self.reaction_user and cancel == reaction.message and str(reaction.emoji) == '❎'
        def reply_message(message):
            return message.author == self.reaction_user and message.channel == self.modmail_channel

        try:
            tasks = [
                asyncio.create_task(self.client.wait_for('reaction_add', timeout=60.0, check=reply_cancel), name='cancel'),
                asyncio.create_task(self.client.wait_for('message', timeout=60.0,check=reply_message), name='respond')
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
                response = uformatter.format_message(message)

                if not response.strip():
                    return
                
                # ! Fix for longer messages
                if len(response) > 1000:
                    await message.channel.send('Your message is too long. Please shorten your message or send in multiple parts.')
                    return
                
                db.add_ticket_response(self.ticket['ticket_id'], self.reaction_user.id, response, True)
                await ticket_user.send(embed=ticket_embed.user_embed(self.guild, response))
                ticket_message = await self.modmail_channel.fetch_message(self.ticket['message_id'])
                await ticket_message.edit(embed=ticket_embed.channel_embed(self.guild, self.ticket['ticket_id']))
        except asyncio.TimeoutError:
            pass

        await cancel.delete()

    async def message_close(self):
        ticket_user = self.guild.get_member(self.ticket['user'])

        confirmation = await self.modmail_channel.send(embed=ticket_embed.close_confirmation(ticket_user))
        await confirmation.add_reaction('✅')
        await confirmation.add_reaction('❎')

        def close_check(reaction, user):
            return user == self.reaction_user and confirmation == reaction.message and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❎')

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=close_check)
            if str(reaction.emoji) == '✅':
                db.close_ticket(self.ticket['ticket_id'])
                ticket_message = await self.modmail_channel.fetch_message(self.ticket['message_id'])
                await ticket_message.delete()
                await self.modmail_channel.send(embed=ticket_embed.closed_ticket(self.reaction_user, ticket_user))
        except asyncio.TimeoutError:
            pass

        await confirmation.delete()

    async def message_timeout(self, ticket_user):
        confirmation = await self.modmail_channel.send(embed=ticket_embed.timeout_confirmation(ticket_user))
        await confirmation.add_reaction('✅')
        await confirmation.add_reaction('❎')

        def timeout_check(reaction, user):
            return user == self.reaction_user and confirmation == reaction.message and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❎')

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=60.0, check=timeout_check)
            if str(reaction.emoji) == '✅':
                # Change below value to custom
                timeout = datetime.datetime.now() + datetime.timedelta(days=1)
                timestamp = int(timeout.timestamp())
                db.set_timeout(ticket_user.id, timestamp)
                await ticket_user.send(embed=ticket_embed.user_timeout(timestamp))
                await self.modmail_channel.send('{0} has been successfully timed out for 24 hours. They will be able to message ModMail again after <t:{1}>.'.format(ticket_user, timestamp))
        except asyncio.TimeoutError:
            pass

        await confirmation.delete()
