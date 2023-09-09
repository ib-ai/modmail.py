import datetime

from discord.ext import commands
import discord

import db
from utils import uformatter, ticket_embed
from utils.config import Config

import logging

logger = logging.getLogger(__name__)

modmail_config = Config()


class Listeners(commands.Cog):
    """Cog to contain all main listener methods."""

    def __init__(self, bot: commands.Bot, modmail_channel: discord.TextChannel) -> None:
        """Constructs necessary attributes for all command action methods.

        Args:
            bot (commands.Bot): The bot object.
            modmail_channel (discord.TextChannel): The specified channel in config.
        """

        self.bot = bot
        self.modmail_channel = modmail_channel

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listener for both DM and server messages.

        Args:
            message (discord.Message): The current message.
        """

        if message.guild is None and not message.author.bot:
            # Handle if user is not in guild
            if not (
                self.modmail_channel.guild.get_member(message.author.id)
                or await self.modmail_channel.guild.fetch_member(message.author.id)
            ):
                try:
                    await message.author.send(
                        "Unable to send message. Please ensure you have joined the server."
                    )
                except discord.errors.Forbidden:
                    pass
                return

            await self.handle_dm(message)

    async def handle_dm(self, message: discord.Message):
        """Handle DM messages.

        Args:
            message (discord.Message): The current message.
        """

        user = message.author

        timeout = await db.get_timeout(user.id)
        current_time = int(datetime.datetime.now().timestamp())

        if timeout and current_time < timeout.timestamp:
            await user.send(embed=ticket_embed.user_timeout(timeout.timestamp))
            return

        response = uformatter.format_message(message)

        if not response:
            return

        # ! Fix for longer messages
        if len(response) > 1000:
            await message.channel.send(
                "Your message is too long. Please shorten your message or send in multiple parts."
            )
            return

        ticket = await db.get_ticket_by_user(user.id)

        if not ticket:
            ticket_id = await db.open_ticket(user.id)
            ticket = await db.get_ticket(ticket_id)
            logger.info(f"Opened new ticket for: {user.id}")

        try:
            if ticket and ticket.message_id is not None:
                old_ticket_message = await self.modmail_channel.fetch_message(
                    ticket.message_id
                )
                await old_ticket_message.delete()
        except discord.errors.NotFound:
            await message.channel.send(
                "You are being rate limited. Please wait a few seconds before trying again."
            )
            return

        # `ticket` truthiness has been checked prior to the following lines
        await db.add_ticket_response(ticket.ticket_id, user.id, response, False)

        embeds = await ticket_embed.channel_embed(self.modmail_channel.guild, ticket)

        message_embed, buttons_view = await ticket_embed.MessageButtonsView(
            self.bot, embeds
        ).return_paginated_embed()

        ticket_message = await self.modmail_channel.send(
            embed=message_embed, view=buttons_view
        )
        await message.add_reaction("📨")

        await db.update_ticket_message(ticket.ticket_id, ticket_message.id)


async def setup(bot: commands.Bot):
    """Setup function for the listeners cog.

    Args:
        bot (commands.Bot): The bot.
    """
    try:
        modmail_channel = await bot.fetch_channel(modmail_config.channel)
    except Exception as e:
        raise ValueError(
            "The channel specified in config was not found. Please check your config."
        ) from e

    if not isinstance(modmail_channel, discord.TextChannel):
        raise TypeError("The channel specified in config was not a text channel.")

    await bot.add_cog(Listeners(bot, modmail_channel))
