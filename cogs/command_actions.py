import datetime, asyncio
import utils.umember as umember, db, utils.ticket_embed as ticket_embed
from utils.embed_reactions import embed_reactions
from discord.ext import commands

class CommandActions(commands.Cog):
    """Cog to contain command action methods."""

    def __init__(self, bot, modmail_channel):
        """Constructs necessary attributes for all command action methods.

        Args:
            bot (commands.Bot): The bot object.
            modmail_channel (discord.Channel): The modmail channel specified in config.
        """

        self.bot = bot
        self.modmail_channel = modmail_channel
        print("\nCog 'Command Actions' loaded")  

    async def cog_check(self, ctx: commands.Context):
        if ctx.channel != self.modmail_channel:
            return False

        if ctx.author == self.bot:
            return False
        
        return True
    
    @commands.command(name="open")
    @commands.guild_only()
    async def open_ticket(self, ctx, member):
        """Opens ticket for specified user if no tickets are currently open."""

        member = umember.assert_member(ctx.guild, member)

        ticket = await db.get_ticket_by_user(member.id)

        if ticket['ticket_id'] != -1:
            await ctx.send('There is already a ticket open for {0}'.format(member))
            return

        ticket_id = await db.open_ticket(member.id)
        ticket = await db.get_ticket(ticket_id)
        
        ticket_message = await ctx.send(embed=await ticket_embed.channel_embed(ctx.guild, ticket['ticket_id']))
        await db.update_ticket_message(ticket['ticket_id'], ticket_message.id)

        await post_reactions(ticket_message)
    
    @commands.command(name="refresh")
    @commands.guild_only()
    async def refresh_ticket(self, ctx, member):
        """Resends embed for specified user if there is a ticket that is already open."""

        member = umember.assert_member(ctx.guild, member)

        ticket = await db.get_ticket_by_user(member.id)

        if ticket['ticket_id'] == -1:
            await self.message.channel.send('There is no ticket open for {0}.'.format(member))
            return

        ticket_message = await ctx.send(embed=await ticket_embed.channel_embed(ctx.guild, ticket['ticket_id']))
        await db.update_ticket_message(ticket['ticket_id'], ticket_message.id)

        if ticket['message_id'] is not None and ticket['message_id'] != -1:
            old_ticket_message = await ctx.channel.fetch_message(ticket['message_id'])
            await old_ticket_message.delete()
        
        await post_reactions(ticket_message)
    
    @commands.command(name="close")
    @commands.guild_only()
    async def close_ticket(self, ctx, member):
        """Closes ticket for specified user given that a ticket is already open."""

        member = umember.assert_member(ctx.guild, member)

        ticket = await db.get_ticket_by_user(member.id)

        if ticket['ticket_id'] == -1:
            await ctx.send('There is no ticket open for {0}.'.format(member))
            return
        
        embed_commands = embed_reactions(self.bot, ctx.guild, self.modmail_channel, ctx.author, ticket)
        await embed_commands.message_close()

    @commands.command(name="timeout")
    @commands.guild_only()
    async def timeout_ticket(self, ctx, member):
        """Times out specified user."""

        member = umember.assert_member(ctx.guild, member)

        embed_commands = embed_reactions(self.bot, ctx.guild, self.modmail_channel, ctx.author)
        await embed_commands.message_timeout(member)

    @commands.command(name="untimeout")
    @commands.guild_only()
    async def untimeout_ticket(self, ctx, member):
        """Removes timeout for specified user given that user is currently timed out."""

        member = umember.assert_member(ctx.guild, member)

        timeout = await db.get_timeout(member.id)
        current_time = int(datetime.datetime.now().timestamp())

        if timeout == False or (timeout != False and current_time > timeout['timestamp']):
            await ctx.send('{0} is not currently timed out.'.format(member))
            return
        
        confirmation = await ctx.send(embed=ticket_embed.untimeout_confirmation(member, timeout['timestamp']))
        await confirmation.add_reaction('✅')
        await confirmation.add_reaction('❎')

        def untimeout_check(reaction, user):
            return user == ctx.author and confirmation == reaction.message and (str(reaction.emoji) == '✅' or str(reaction.emoji) == '❎')

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=untimeout_check)
            if str(reaction.emoji) == '✅':
                timestamp = int(datetime.datetime.now().timestamp())
                await db.set_timeout(member.id, timestamp)
                await member.send(embed=ticket_embed.user_untimeout())
                await self.modmail_channel.send('{0} has been successfully untimed out.'.format(member))
        except asyncio.TimeoutError:
            pass

        await confirmation.delete()
    
    # ! Fix errors
    async def cog_command_error(self, ctx, error):
        if type(error) == commands.errors.CheckFailure:
            print("Command executed in wrong channel.")
        elif type(error) == commands.errors.MissingRequiredArgument:
            await ctx.send("A valid user (and one who is still on the server) was not specified.")
        else:
            await ctx.send(error + "\nIf you do not understand, contact a bot dev.")


async def post_reactions(message):
    """Adds specified reactions to message.

    Args:
        message (discord.Message): The specified message.
    """

    message_reactions = ['🗣️', '❎', '⏲️']

    for reaction in message_reactions:
        await message.add_reaction(reaction)

def setup(bot):
    bot.add_cog(CommandActions(bot))