from typing import Literal, Optional
from discord.ext import commands
from discord import app_commands
import discord
import sys

import db
from utils import config, actions

import logging

logger = logging.getLogger(__name__)


class Commands(commands.Cog):
    """Cog to contain command action methods."""

    def __init__(self, bot: commands.Bot,
                 modmail_channel: discord.TextChannel) -> None:
        """Constructs necessary attributes for all command action methods.

        Args:
            bot (commands.Bot): The bot object.
            modmail_channel (discord.TextChannel): The modmail channel specified in config.
        """

        self.bot = bot
        self.modmail_channel = modmail_channel

    async def cog_check(self, ctx: commands.Context):
        if ctx.channel != self.modmail_channel:
            await ctx.send("Command must be used in the modmail channel.")
            return False

        if ctx.author == self.bot:
            await ctx.send("Bots cannot use commands.")
            return False

        return True

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.channel != self.modmail_channel:
            await interaction.response.send_message(
                "Command must be used in the modmail channel.")
            return False

        if "resolved" in interaction.data and "users" in interaction.data[
                "resolved"] and len(interaction.data["resolved"]["users"]) > 0:
            user_id = next(iter(interaction.data["resolved"]["users"]))
            user = interaction.data["resolved"]["users"][user_id]
            if "bot" in user and user["bot"]:
                await interaction.response.send_message(
                    "Invalid user specified.")
                return False

        return True

    @commands.command(name="sync")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def sync(self,
                   ctx: commands.Context,
                   spec: Optional[Literal["~"]] = None):
        """
        Syncs commands to the current guild or globally.

        Args:
            ctx (commands.Context): The command context.
            spec (Optional[Literal["~"]]): If "~", syncs globally. Defaults to None.
        """
        if spec == "~":
            synced = await ctx.bot.tree.sync()
        else:
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)

        await ctx.send(
            f"Synced {len(synced)} commands {'to the current guild' if spec is None else 'globally'}."
        )
        return

    @app_commands.command(name="open")
    @commands.guild_only()
    async def open_ticket(self, interaction: discord.Interaction,
                          member: discord.Member):
        """Opens ticket for specified user if no tickets are currently open."""

        await actions.message_open(self.bot, interaction, member)

    @app_commands.command(name="refresh")
    @commands.guild_only()
    async def refresh_ticket(self, interaction: discord.Interaction,
                             member: discord.Member):
        """Resends embed for specified user if there is a ticket that is already open."""

        await actions.message_refresh(self.bot, interaction, member)

    @app_commands.command(name="close")
    @commands.guild_only()
    async def close_ticket(self, interaction: discord.Interaction,
                           member: discord.Member):
        """Closes ticket for specified user given that a ticket is already open."""

        ticket = await db.get_ticket_by_user(member.id)

        if not ticket:
            await interaction.response.send_message(
                f'There is no ticket open for {member.name}.', ephemeral=True)
            return

        await actions.message_close(interaction, ticket, member)

    @app_commands.command(name="timeout")
    @commands.guild_only()
    async def timeout_ticket(self, interaction: discord.Interaction,
                             member: discord.Member):
        """Times out specified user."""
        await actions.message_timeout(interaction, member)

    @app_commands.command(name="untimeout")
    @commands.guild_only()
    async def untimeout_ticket(self, interaction: discord.Interaction,
                               member: discord.Member):
        """Removes timeout for specified user given that user is currently timed out."""

        await actions.message_untimeout(interaction, member)

    async def cog_command_error(self, ctx: commands.Context,
                                error: commands.CommandError):
        if type(error) == commands.errors.CheckFailure:
            logger.error("Checks failed for interaction.")
        elif type(error) == commands.errors.MissingRequiredArgument:
            await ctx.send(
                "A valid user (and one who is still on the server) was not specified."
            )
        else:
            await ctx.send(
                str(error) + "\nIf you do not understand, contact a bot dev.")

    async def cog_app_command_error(self, interaction: discord.Interaction,
                                    error: app_commands.AppCommandError):
        if type(error) == app_commands.errors.CheckFailure:
            logger.error("Checks failed for interaction.")
        else:
            await interaction.response.send_message(
                str(error) + "\nIf you do not understand, contact a bot dev.")
        logger.error(error)


async def setup(bot: commands.Bot):
    try:
        modmail_channel = await bot.fetch_channel(config.channel)

        if type(modmail_channel) != discord.TextChannel:
            raise TypeError(
                "The channel specified in config was not a text channel.")
    except Exception as e:
        logger.error(e)
        logger.fatal(
            "The channel specified in config was not found. Please check your config."
        )
        sys.exit(-1)

    await bot.add_cog(Commands(bot, modmail_channel))
