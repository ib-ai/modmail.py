import asyncio
import discord
from discord.ext import commands
from discord.utils import format_dt
import db
from typing import Optional, Union

from utils import actions, config

import logging

logger = logging.getLogger(__name__)


class ConfirmationView(discord.ui.View):

    def __init__(self,
                 message: Optional[discord.Message] = None,
                 timeout: int = 60):
        super().__init__(timeout=timeout)
        self.message = message
        self.value = None

    async def on_timeout(self) -> None:
        await self.message.delete()
        await super().on_timeout()

    @discord.ui.button(label='Yes', style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction,
                  button: discord.ui.Button):
        self.value = True
        await self.message.delete()
        self.stop()

    @discord.ui.button(label='No', style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction,
                 button: discord.ui.Button):
        self.value = False
        await self.message.delete()
        self.stop()


class CancelView(discord.ui.View):

    def __init__(self,
                 task: asyncio.Task,
                 message: Optional[discord.Message] = None,
                 timeout: int = 60) -> None:
        super().__init__(timeout=timeout)
        self.message = message
        self.task = task

    async def view_cleanup(self) -> None:
        self.stop()
        if self.message:
            await self.message.delete()

        self.task.cancel()

    async def on_timeout(self) -> None:
        await self.view_cleanup()
        await super().on_timeout()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        await self.view_cleanup()


class MessageButtonsView(discord.ui.View):

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(emoji="💬", custom_id=f"{config.id_prefix}:reply")
    async def mail_reply(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        ticket = await db.get_ticket_by_message(interaction.message.id)
        await actions.message_reply(self.bot, interaction, ticket)

    @discord.ui.button(emoji="❎", custom_id=f"{config.id_prefix}:close")
    async def mail_close(self, interaction: discord.Interaction,
                         button: discord.ui.Button):
        ticket = await db.get_ticket_by_message(interaction.message.id)
        member = interaction.guild.get_member(
            ticket.user) or await interaction.guild.fetch_member(ticket.user)
        await actions.message_close(interaction, ticket, member)

    @discord.ui.button(emoji="⏲️", custom_id=f"{config.id_prefix}:timeout")
    async def mail_timeout(self, interaction: discord.Interaction,
                           button: discord.ui.Button):
        ticket = await db.get_ticket_by_message(interaction.message.id)
        member = interaction.guild.get_member(
            ticket.user) or await interaction.guild.fetch_member(ticket.user)
        await actions.message_timeout(interaction, member)


def user_embed(guild: discord.Guild, message: str) -> discord.Embed:
    """Returns formatted embed for user DMs.

    Args:
        guild (discord.Guild): The guild.
        message (str): The received message content.

    Returns:
        discord.Embed: User DM embed containing the message content.
    """

    message_embed = discord.Embed(title=f"New Mail from {guild.name}",
                                  description=message)

    return message_embed


async def channel_embed(
        bot: commands.Bot, guild: discord.Guild,
        ticket: db.Ticket) -> tuple[discord.Embed, discord.ui.View]:
    """Returns formatted embed for channel.

    Args:
        guild (discord.Guild): The guild.
        ticket (Ticket): The ticket.

    Returns:
        discord.Embed: Channel embed containing message and user content.
    """

    # WARNING: Handle when user is not in guild or in DM listener
    ticket_member = guild.get_member(ticket.user) or await guild.fetch_member(
        ticket.user)

    message_embed = discord.Embed(
        title=f"ModMail Conversation for {ticket_member}",
        description=
        f"User {ticket_member.mention} has **{len(ticket_member.roles) - 1}** roles\n Joined Discord: **{format_dt(ticket_member.created_at, 'D')}**\n Joined Server: **{format_dt(ticket_member.joined_at, 'D')}**"
    )

    responses = await db.get_ticket_responses(ticket.ticket_id)

    for response in responses:
        author = 'user'
        if response.as_server:
            author = f'{guild.get_member(response.user)} as server'
        message_embed.add_field(
            name=f"<t:{response.timestamp}:R>, {author} wrote",
            value=response.response,
            inline=False)

    message_buttons_view = MessageButtonsView(bot)
    return message_embed, message_buttons_view


def close_confirmation(
        member: discord.Member) -> tuple[discord.Embed, discord.ui.View]:
    """Returns embed for ticket close confirmation.

    Args:
        member (discord.Member): The ticket user.

    Returns:
        discord.Embed: Channel embed for close confirmation.
    """

    confirmation_view = ConfirmationView()

    message_embed = discord.Embed(
        description=
        f"Do you want to close the ModMail conversation for **{member.name}**?"
    )

    return message_embed, confirmation_view


def timeout_confirmation(
        member: discord.Member) -> tuple[discord.Embed, discord.ui.View]:
    """Returns embed for ticket timeout confirmation.

    Args:
        member (discord.Member): The ticket user.

    Returns:
        discord.Embed: Channel embed for timeout confirmation.
    """

    confirmation_view = ConfirmationView()

    message_embed = discord.Embed(
        description=f"Do you want to timeout **{member.name}** for 24 hours?")

    return message_embed, confirmation_view


def untimeout_confirmation(
        member: discord.Member,
        timeout: int) -> tuple[discord.Embed, discord.ui.View]:
    """Returns embed for ticket untimeout confirmation.

    Args:
        member (discord.Member): The ticket user.
        timeout (int): The timeout as Epoch milliseconds.

    Returns:
        discord.Embed: Channel embed for untimeout confirmation.
    """
    confirmation_view = ConfirmationView()

    message_embed = discord.Embed(
        description=
        f"Do you want to untimeout **{member.name}** (they are currently timed out until <t:{timeout}>)?"
    )

    return message_embed, confirmation_view


def reply_cancel(member: discord.Member,
                 task: asyncio.Task) -> tuple[discord.Embed, discord.ui.View]:
    """Returns embed for replying to ticket with cancel reaction.

    Args:
        member (discord.Member): The ticket user.

    Returns:
        discord.Embed: Channel embed for ticket reply.
    """

    cancel_view = CancelView(task)
    message_embed = discord.Embed(
        description=f"Replying to ModMail conversation for **{member}**")

    return message_embed, cancel_view


def closed_ticket(staff: Union[discord.User, discord.Member],
                  member: discord.Member) -> discord.Embed:
    """Returns embed for closed ticket.

    Args:
        staff (Union[discord.User, discord.Member]): The staff member who closed the ticket.
        member (discord.Member): The ticket user.

    Returns:
        discord.Embed: Channel embed for closed ticket.
    """

    message_embed = discord.Embed(
        description=
        f"**{staff}** closed the ModMail conversation for **{member}**")

    return message_embed


def user_timeout(timeout: int) -> discord.Embed:
    """Returns embed for user timeout in DMs.

    Args:
        timeout (int): The timeout as Epoch milliseconds.

    Returns:
        discord.Embed: Channel embed for user timeout.
    """

    message_embed = discord.Embed(
        description=
        f"You have been timed out. You will be able to message ModMail again after <t:{timeout}>."
    )

    return message_embed


def user_untimeout() -> discord.Embed:
    """Returns embed for user untimeout in DMs.

    Returns:
        discord.Embed: Channel embed for user untimeout.
    """

    message_embed = discord.Embed(
        description=
        "Your timeout has been removed. You can message ModMail again.")

    return message_embed
