import datetime
import logging
from typing import Optional

import discord
from discord.ext import commands

import db
from utils import ticket_embed, uformatter
from utils.config import Config

logger = logging.getLogger(__name__)

modmail_config = Config()


class Listeners(commands.Cog):
    """Cog to contain all main listener methods."""

    def __init__(
        self,
        bot: commands.Bot,
        modmail_channel: discord.TextChannel,
        allowed_guild: Optional[discord.Guild] = None,
    ) -> None:
        """Constructs necessary attributes for all command action methods.

        Args:
            bot (commands.Bot): The bot object.
            modmail_channel (discord.TextChannel): The specified channel in config.
            allowed_guild (discord.Guild, optional): The allowed guild specified in config. Defaults to None.
        """

        self.bot = bot
        self.modmail_channel = modmail_channel
        self.allowed_guild = allowed_guild

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listener for both DM and server messages.

        Args:
            message (discord.Message): The current message.
        """
        # Accepts messages from DMs only and ignore bots
        if message.guild is None and not message.author.bot:
            # Scenario 1: Main Guild
            try:
                if self.modmail_channel.guild.get_member(
                    message.author.id
                ) or await self.modmail_channel.guild.fetch_member(message.author.id):
                    await self.handle_dm(message, self.modmail_channel.guild)
                    return
            except discord.errors.NotFound:
                pass

            # Scenario 2: Allowed Guild
            try:
                if self.allowed_guild and (
                    self.allowed_guild.get_member(message.author.id)
                    or await self.allowed_guild.fetch_member(message.author.id)
                ):
                    await self.handle_dm(message, self.allowed_guild)
                    return
            except discord.errors.NotFound:
                pass

            # Scenario 3: Neither Guild
            try:
                join_message = "Unable to send message. Please ensure you are in the IB Discord Server (https://discord.com/invite/ibo)."

                if modmail_config.allowed_guild:
                    join_message += f"\n\nIf you are submitting a ban appeal, please join the IB Discord Ban Appeals server ({modmail_config.allowed_guild.invite})."

                await message.author.send(join_message)
            except discord.errors.Forbidden:
                pass

    async def handle_dm(self, message: discord.Message, source_guild: discord.Guild):
        """Handle DM messages.

        Args:
            message (discord.Message): The current message.
            source_guild (discord.Guild): The guild where the message originated.
        """

        user = message.author
        guild = self.bot.get_guild(self.modmail_channel.guild.id)

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

        embeds = await ticket_embed.channel_embed(guild, source_guild, ticket)

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

    allowed_guild = None
    if modmail_config.allowed_guild:
        try:
            allowed_guild = await bot.fetch_guild(modmail_config.allowed_guild.guild_id)
        except Exception as e:
            raise ValueError(
                "The guild specified in config was not found. Please check your config."
            ) from e

    await bot.add_cog(Listeners(bot, modmail_channel, allowed_guild))
