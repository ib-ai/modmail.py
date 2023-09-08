import asyncio
from typing import Collection, Optional, Union

import discord
from discord.ext import commands
from discord.utils import format_dt

import db
from utils import actions
from utils.config import Config
from utils.pagination import paginated_embed_menus

import logging

logger = logging.getLogger(__name__)

modmail_config = Config()


class ConfirmationView(discord.ui.View):
    """Confirmation view for yes/no operations."""

    def __init__(self, message: Optional[discord.Message] = None, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.message = message
        self.value = None

    async def on_timeout(self) -> None:
        await self.message.delete()
        await super().on_timeout()

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await self.message.delete()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await self.message.delete()
        self.stop()


class CancelView(discord.ui.View):
    """Cancel view for cancelling operations if requested by the user."""

    def __init__(
        self,
        task: asyncio.Task,
        message: Optional[discord.Message] = None,
        timeout: int = 60,
    ) -> None:
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

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.view_cleanup()


class MessageButtonsView(discord.ui.View):
    """Message buttons view for ticket messages."""

    def __init__(self, bot: commands.Bot, embeds: Collection[discord.Embed]):
        super().__init__(timeout=None)
        self.bot = bot
        self.embeds = embeds
        self.current_page = len(self.embeds) - 1

    @discord.ui.button(emoji="💬", custom_id=f"{modmail_config.id_prefix}:reply")
    async def mail_reply(self, interaction: discord.Interaction, _):
        """
        Replies to the ticket.
        """
        ticket = await db.get_ticket_by_message(interaction.message.id)
        await actions.message_reply(self.bot, interaction, ticket)

    @discord.ui.button(emoji="❎", custom_id=f"{modmail_config.id_prefix}:close")
    async def mail_close(self, interaction: discord.Interaction, _):
        """
        Closes the ticket.
        """
        ticket = await db.get_ticket_by_message(interaction.message.id)
        member = interaction.guild.get_member(
            ticket.user
        ) or await interaction.guild.fetch_member(ticket.user)
        await actions.message_close(interaction, ticket, member)

    @discord.ui.button(emoji="⏲️", custom_id=f"{modmail_config.id_prefix}:timeout")
    async def mail_timeout(self, interaction: discord.Interaction, _):
        """
        Times out the user of the ticket.
        """
        ticket = await db.get_ticket_by_message(interaction.message.id)
        member = interaction.guild.get_member(
            ticket.user
        ) or await interaction.guild.fetch_member(ticket.user)
        await actions.message_timeout(interaction, member)

    @discord.ui.button(
        emoji="⬅️",
        style=discord.ButtonStyle.blurple,
        custom_id=f"{modmail_config.id_prefix}:previous_page",
    )
    async def previous_page(self, interaction: discord.Interaction, _):
        """
        Goes to the previous page.
        """
        if len(self.embeds) == 0:
            await interaction.response.send_message(
                "Please refresh this ticket to be able to use pagination.",
                ephemeral=True,
            )
            return

        if self.current_page > 0:
            self.current_page -= 1
            self.update_pagination_buttons()
            await self.update_view(interaction)

    @discord.ui.button(
        emoji="➡️",
        style=discord.ButtonStyle.blurple,
        custom_id=f"{modmail_config.id_prefix}:next_page",
    )
    async def next_page(self, interaction: discord.Interaction, _):
        """
        Goes to the next page.
        """
        if len(self.embeds) == 0:
            await interaction.response.send_message(
                "Please refresh this ticket to be able to use pagination.",
                ephemeral=True,
            )
            return

        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self.update_pagination_buttons()
            await self.update_view(interaction)

    def update_pagination_buttons(self):
        """
        Updates the buttons based on the current page.
        """
        for i in self.children:
            i.disabled = False
        if self.current_page == 0:
            self.children[3].disabled = True
        if self.current_page == len(self.embeds) - 1:
            self.children[4].disabled = True

    async def update_view(self, interaction: discord.Interaction):
        """
        Updates the embed and view.
        """
        await interaction.response.edit_message(
            embed=self.embeds[self.current_page], view=self
        )

    async def return_paginated_embed(
        self,
    ) -> tuple[discord.Embed, discord.ui.View | None]:
        """
        Returns the first embed and containing view.
        """
        self.update_pagination_buttons()  # Disable buttons only one embed

        return self.embeds[self.current_page], self


def user_embed(guild: discord.Guild, message: str) -> discord.Embed:
    """Returns formatted embed for user DMs.

    Args:
        guild (discord.Guild): The guild.
        message (str): The received message content.

    Returns:
        discord.Embed: User DM embed containing the message content.
    """

    message_embed = discord.Embed(
        title=f"New Mail from {guild.name}", description=message
    )

    return message_embed


async def channel_embed(
    guild: discord.Guild, ticket: db.Ticket
) -> Collection[discord.Embed]:
    """Returns formatted embed for modmail channel.

    Args:
        guild (discord.Guild): The guild.
        ticket (db.Ticket): The ticket.

    Returns:
        Collection[discord.Embed]: Collection of embeds for the ticket.
    """

    ticket_member = guild.get_member(ticket.user) or await guild.fetch_member(
        ticket.user
    )

    responses = await db.get_ticket_responses(ticket.ticket_id)

    names = []
    values = []

    for response in responses:
        author = "user"
        if response.as_server:
            author = f"{guild.get_member(response.user)} as server"
        names.append(f"<t:{response.timestamp}:R>, {author} wrote")
        values.append(response.response)

    embed_dict = {
        "title": f"ModMail Conversation for {ticket_member.name}",
        "description": f"User {ticket_member.mention} has **{len(ticket_member.roles) - 1}** roles\n Joined Discord: **{format_dt(ticket_member.created_at, 'D')}**\n Joined Server: **{format_dt(ticket_member.joined_at, 'D')}**",
    }

    embeds = paginated_embed_menus(names, values, embed_dict=embed_dict)

    return embeds


def close_confirmation(member: discord.Member) -> tuple[discord.Embed, discord.ui.View]:
    """Returns embed for ticket close confirmation.

    Args:
        member (discord.Member): The ticket user.

    Returns:
        tuple[discord.Embed, discord.ui.View]: Tuple containing channel embed and view for close confirmation.
    """

    confirmation_view = ConfirmationView()

    message_embed = discord.Embed(
        description=f"Do you want to close the ModMail conversation for **{member.name}**?"
    )

    return message_embed, confirmation_view


def timeout_confirmation(
    member: discord.Member,
) -> tuple[discord.Embed, discord.ui.View]:
    """Returns embed for ticket timeout confirmation.

    Args:
        member (discord.Member): The ticket user.

    Returns:
        tuple[discord.Embed, discord.ui.View]: Tuple containing channel embed and view for timeout confirmation.
    """

    confirmation_view = ConfirmationView()

    message_embed = discord.Embed(
        description=f"Do you want to timeout **{member.name}** for 24 hours?"
    )

    return message_embed, confirmation_view


def untimeout_confirmation(
    member: discord.Member, timeout: int
) -> tuple[discord.Embed, discord.ui.View]:
    """Returns embed for ticket untimeout confirmation.

    Args:
        member (discord.Member): The ticket user.
        timeout (int): The timeout as Epoch milliseconds.

    Returns:
        tuple[discord.Embed, discord.ui.View]: Tuple containing channel embed and view for untimeout confirmation.
    """
    confirmation_view = ConfirmationView()

    message_embed = discord.Embed(
        description=f"Do you want to untimeout **{member.name}** (they are currently timed out until <t:{timeout}>)?"
    )

    return message_embed, confirmation_view


def reply_cancel(
    member: discord.Member, task: asyncio.Task
) -> tuple[discord.Embed, discord.ui.View]:
    """Returns embed for replying to ticket with cancel reaction.

    Args:
        member (discord.Member): The ticket user.
        task (asyncio.Task): The task for the reply (e.g., waiting for user message).

    Returns:
        tuple[discord.Embed, discord.ui.View]: Tuple containing channel embed and view for reply cancellation.
    """

    cancel_view = CancelView(task)
    message_embed = discord.Embed(
        description=f"Replying to ModMail conversation for **{member.name}**"
    )

    return message_embed, cancel_view


def closed_ticket(
    staff: Union[discord.User, discord.Member], member: discord.Member
) -> discord.Embed:
    """Returns embed for closed ticket.

    Args:
        staff (Union[discord.User, discord.Member]): The staff member who closed the ticket.
        member (discord.Member): The ticket user.

    Returns:
        discord.Embed: Channel embed for closed ticket.
    """

    message_embed = discord.Embed(
        description=f"**{staff.name}** closed the ModMail conversation for **{member.name}**"
    )

    return message_embed


def user_timeout(timeout: int) -> discord.Embed:
    """Returns embed for user timeout in DMs.

    Args:
        timeout (int): The timeout as Epoch milliseconds.

    Returns:
        discord.Embed: Channel embed for user timeout.
    """

    message_embed = discord.Embed(
        description=f"You have been timed out. You will be able to message ModMail again after <t:{timeout}> (<t:{timeout}:R>)."
    )

    return message_embed


def user_untimeout() -> discord.Embed:
    """Returns embed for user untimeout in DMs.

    Returns:
        discord.Embed: Channel embed for user untimeout.
    """

    message_embed = discord.Embed(
        description="Your timeout has been removed. You can message ModMail again."
    )

    return message_embed
