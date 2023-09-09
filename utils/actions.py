import asyncio
import datetime
from typing import Optional

import discord
from discord.ext import commands

import db
from utils import ticket_embed, uformatter

import logging

logger = logging.getLogger(__name__)


async def waiter(
    bot: commands.Bot, interaction: discord.Interaction
) -> Optional[discord.Message]:
    """
    Waits for a message from the user who initiated the interaction.

    Args:
        bot (commands.Bot): The bot object.
        interaction (discord.Interaction): The interaction object.

    Returns:
        Optional[discord.Message]: The message sent by the user.
    """

    def check(message: discord.Message) -> bool:
        return (
            message.author == interaction.user
            and message.channel == interaction.channel
        )

    try:
        message = await bot.wait_for("message", check=check)
    except asyncio.TimeoutError:
        return None

    return message


async def message_open(
    bot: commands.Bot, interaction: discord.Interaction, member: discord.Member
):
    """
    Sends message embed and opens a ticket for the specified user, if not open already.

    Args:
        bot (commands.Bot): The bot object.
        interaction (discord.Interaction): The interaction object.
        member (discord.Member): The member to open a ticket for.
    """
    ticket = await db.get_ticket_by_user(member.id)

    if ticket:
        await interaction.response.send_message(
            f"There is already a ticket open for {member.name}.", ephemeral=True
        )
        return

    ticket_id = await db.open_ticket(member.id)
    ticket = await db.get_ticket(ticket_id)

    embeds = await ticket_embed.channel_embed(interaction.guild, ticket)

    message_embed, buttons_view = await ticket_embed.MessageButtonsView(
        bot, embeds
    ).return_paginated_embed()
    await interaction.response.send_message(embed=message_embed, view=buttons_view)

    ticket_message = await interaction.original_response()
    logger.debug(f"Ticket message: {ticket_message}")
    await db.update_ticket_message(ticket.ticket_id, ticket_message.id)


async def message_refresh(
    bot: commands.Bot, interaction: discord.Interaction, member: discord.Member
):
    """
    Resends message embed for the specified user if open.

    Args:
        bot (commands.Bot): The bot object.
        interaction (discord.Interaction): The interaction object.
        member (discord.Member): The member to refresh the ticket for.
    """
    ticket = await db.get_ticket_by_user(member.id)

    if not ticket:
        await interaction.response.send_message(
            f"There is no ticket open for {member.name}.", ephemeral=True
        )
        return

    embeds = await ticket_embed.channel_embed(interaction.guild, ticket)

    message_embed, buttons_view = await ticket_embed.MessageButtonsView(
        bot, embeds
    ).return_paginated_embed()
    await interaction.response.send_message(embed=message_embed, view=buttons_view)

    message = await interaction.original_response()
    await db.update_ticket_message(ticket.ticket_id, message.id)

    if ticket.message_id is not None:
        try:
            old_ticket_message = await interaction.channel.fetch_message(
                ticket.message_id
            )
            await old_ticket_message.delete()
        except discord.errors.NotFound:
            # Pass if original ticket message has been deleted already
            pass


async def message_close(
    interaction: discord.Interaction, ticket: db.Ticket, user: discord.Member
):
    """
    Sends close confirmation embed, and if confirmed, will close the ticket.

    Args:
        interaction (discord.Interaction): The interaction object.
        ticket (db.Ticket): The ticket object.
        user (discord.Member): The member to close the ticket for.
    """

    close_embed, confirmation_view = ticket_embed.close_confirmation(user)

    await interaction.response.send_message(embed=close_embed, view=confirmation_view)
    confirmation_view.message = await interaction.original_response()

    await confirmation_view.wait()

    if not confirmation_view.value:
        return
    elif confirmation_view.value:
        await db.close_ticket(ticket.ticket_id)
        ticket_message = await interaction.channel.fetch_message(ticket.message_id)
        await ticket_message.delete()

        await interaction.channel.send(
            embed=ticket_embed.closed_ticket(interaction.user, user)
        )
        logger.info(f"Ticket for user {user.id} closed by {interaction.user.id}")


async def message_reply(
    bot: commands.Bot, interaction: discord.Interaction, ticket: db.Ticket
):
    """
    Adds staff reply to ticket and updates original embed.

    Args:
        bot (commands.Bot): The bot object.
        interaction (discord.Interaction): The interaction object.
        ticket (db.Ticket): The ticket object.
    """

    ticket_user = interaction.guild.get_member(ticket.user)

    if not ticket_user:
        await interaction.response.send_message(
            "Cannot reply to ticket as user is not in the server."
        )
        return

    task = bot.loop.create_task(waiter(bot, interaction))

    reply_embed, cancel_view = ticket_embed.reply_cancel(ticket_user, task)
    await interaction.response.send_message(embed=reply_embed, view=cancel_view)
    cancel_view.message = await interaction.original_response()

    await task
    await cancel_view.view_cleanup()

    try:
        message = task.result()

        if not message:
            return

        response = uformatter.format_message(message)

        if not response.strip():
            return

        # ! Fix for longer messages
        if len(response) > 1000:
            await interaction.channel.send(
                "Your message is too long. Please shorten your message or send in multiple parts."
            )
            return

        try:
            await ticket_user.send(
                embed=ticket_embed.user_embed(interaction.guild, response)
            )
            await db.add_ticket_response(
                ticket.ticket_id, interaction.user.id, response, True
            )
            ticket_message = await interaction.channel.fetch_message(ticket.message_id)

            embeds = await ticket_embed.channel_embed(interaction.guild, ticket)

            channel_embed, buttons_view = await ticket_embed.MessageButtonsView(
                bot, embeds
            ).return_paginated_embed()

            await ticket_message.edit(embed=channel_embed, view=buttons_view)
        except discord.errors.Forbidden:
            await interaction.channel.send(
                "Could not send ModMail message to specified user due to privacy settings."
            )

    except Exception as e:
        raise RuntimeError(e)
    except asyncio.CancelledError:
        return


async def message_timeout(interaction: discord.Interaction, member: discord.Member):
    """Sends timeout confirmation embed, and if confirmed, will timeout the specified ticket user.

    Args:
        interaction (discord.Interaction): The interaction object.
        member (discord.Member): The member to timeout.
    """

    timeout_embed, confirmation_view = ticket_embed.timeout_confirmation(member)

    await interaction.response.send_message(embed=timeout_embed, view=confirmation_view)
    confirmation_view.message = await interaction.original_response()

    await confirmation_view.wait()

    if confirmation_view.value is None:
        return
    elif confirmation_view.value:
        timeout = datetime.datetime.now() + datetime.timedelta(days=1)
        timestamp = int(timeout.timestamp())
        await db.set_timeout(member.id, timestamp)
        logger.info(f"User {member.id} timed out by {interaction.user.id}")

        await interaction.channel.send(
            f"{member.name} has been successfully timed out for 24 hours. They will be able to message ModMail again after <t:{timestamp}>."
        )

        try:
            await member.send(embed=ticket_embed.user_timeout(timestamp))
        except discord.errors.Forbidden:
            await interaction.channel.send(
                "Could not send timeout message to specified user due to privacy settings."
            )


async def message_untimeout(interaction: discord.Interaction, member: discord.Member):
    """
    Sends untimeout confirmation embed, and if confirmed, will remove the timeout for the specified ticket user.

    Args:
        interaction (discord.Interaction): The interaction object.
        member (discord.Member): The member to remove the timeout for.
    """
    timeout = await db.get_timeout(member.id)
    current_time = int(datetime.datetime.now().timestamp())

    if not timeout or (current_time > timeout.timestamp):
        await interaction.response.send_message(
            f"{member.name} is not currently timed out.", ephemeral=True
        )
        return

    untimeout_embed, confirmation_view = ticket_embed.untimeout_confirmation(
        member, timeout.timestamp
    )

    await interaction.response.send_message(
        embed=untimeout_embed, view=confirmation_view
    )
    confirmation_view.message = await interaction.original_response()

    await confirmation_view.wait()

    if confirmation_view.value is None:
        return
    elif confirmation_view.value:
        timestamp = int(datetime.datetime.now().timestamp())
        await db.set_timeout(member.id, timestamp)
        logger.info(f"Timeout removed for {member.id}.")

        await interaction.channel.send(f"Timeout has been removed for {member.name}.")

        try:
            await member.send(embed=ticket_embed.user_untimeout())
        except discord.errors.Forbidden:
            await interaction.channel.send(
                "Could not send untimeout message to specified user due to privacy settings."
            )
