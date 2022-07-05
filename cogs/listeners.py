import datetime
from discord.ext import commands

import utils.ticket_embed as ticket_embed, db
import utils.uformatter as uformatter
from cogs.command_actions import post_reactions

class Listeners(commands.Cog):
    """Cog to contain all main listener methods."""

    def __init__(self, bot, guild, modmail_channel):
        """Constructs necessary attributes for all command action methods.

        Args:
            bot (commands.Bot): The bot object.
            guild (discord.Guild): The specified guild in config.
            modmail_channel (discord.Channel): The specified channel in config.
        """

        self.bot = bot
        self.guild = guild
        self.modmail_channel = modmail_channel
        print("\nCog 'Listeners' loaded")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener for both DM and server messages.

        Args:
            message (discord.Message): The current message.
        """

        if message.guild is None and not message.author.bot:
            await self.handle_dm(message)
            return

    async def handle_dm(self, message):
        """Handle DM messages.

        Args:
            message (discord.Message): The current message.
        """
        
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
        ticket_message = await self.modmail_channel.send(embed=ticket_embed.channel_embed(self.guild, ticket['ticket_id']))
        db.update_ticket_message(ticket['ticket_id'], ticket_message.id)
        await message.add_reaction('📨')
        await post_reactions(ticket_message)

        if ticket['message_id'] is not None and ticket['message_id'] != -1:
            old_ticket_message = await self.modmail_channel.fetch_message(ticket['message_id'])
            await old_ticket_message.delete()

def setup(bot):
    bot.add_cog(Listeners(bot))