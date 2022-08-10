import discord
import db

def user_embed(guild, message):
    """Returns formatted embed for user DMs.

    Args:
        guild (discord.Guild): The guild.
        message (str): The received message content.

    Returns:
        discord.Embed: User DM embed containing the message content.
    """

    message_embed = discord.Embed(
        title="New Mail from {0}".format(guild.name),
        description=message
    )

    return message_embed

def channel_embed(guild, ticket_id):
    """Returns formatted embed for channel.

    Args:
        guild (discord.Guild): The guild.
        ticket_id (int): The ticket id.

    Returns:
        discord.Embed: Channel embed containing message and user content.
    """

    ticket = db.get_ticket(ticket_id)

    ticket_member = guild.get_member(ticket['user'])

    message_embed = discord.Embed(
        title="ModMail Conversation for {0}".format(ticket_member),
        description="User {0} has **{1}** roles\n Joined Discord: **{2}**\n Joined Server: **{3}**"
            .format(ticket_member.mention, len(ticket_member.roles), ticket_member.created_at.strftime("%B %d %Y"), ticket_member.joined_at.strftime("%B %d %Y"))
    )

    responses = db.get_ticket_responses(ticket_id)

    for response in responses:
        author = 'user'
        if response['as_server']:
            author = '{0} as server'.format(guild.get_member(response['user']))
        message_embed.add_field(name="<t:{0}:R>, {1} wrote".format(response['timestamp'], author), value=response['response'], inline=False)

    return message_embed

def close_confirmation(member):
    """Returns embed for ticket close confirmation.

    Args:
        member (discord.Member): The ticket user.

    Returns:
        discord.Embed: Channel embed for close confirmation.
    """

    message_embed = discord.Embed(
        description="Do you want to close the ModMail conversation for **{0}**?".format(member)
    )

    return message_embed

def timeout_confirmation(member):
    """Returns embed for ticket timeout confirmation.

    Args:
        member (discord.Member): The ticket user.

    Returns:
        discord.Embed: Channel embed for timeout confirmation.
    """

    message_embed = discord.Embed(
        description="Do you want to timeout **{0}** for 24 hours?".format(member)
    )

    return message_embed

def untimeout_confirmation(member, timeout):
    """Returns embed for ticket untimeout confirmation.

    Args:
        member (discord.Member): The ticket user.
        timeout (int): The timeout as Epoch milliseconds.

    Returns:
        discord.Embed: Channel embed for untimeout confirmation.
    """

    message_embed = discord.Embed(
        description="Do you want to untimeout **{0}** (they are currently timed out until <t:{1}>)?".format(member, timeout)
    )

    return message_embed

def reply_cancel(member):
    """Returns embed for replying to ticket with cancel reaction.

    Args:
        member (discord.Member): The ticket user.

    Returns:
        discord.Embed: Channel embed for ticket reply.
    """

    message_embed = discord.Embed(
        description="Replying to ModMail conversation for **{0}**".format(member)
    )

    return message_embed

def closed_ticket(staff, member):
    """Returns embed for closed ticket.

    Args:
        staff (discord.Member): The staff member who closed the ticket.
        member (discord.Member): The ticket user.

    Returns:
        discord.Embed: Channel embed for closed ticket.
    """

    message_embed = discord.Embed(
        description="**{0}** closed the ModMail conversation for **{1}**".format(staff, member)
    )

    return message_embed

def user_timeout(timeout):
    """Returns embed for user timeout in DMs.

    Args:
        timeout (int): The timeout as Epoch milliseconds.

    Returns:
        discord.Embed: Channel embed for user timeout.
    """

    message_embed = discord.Embed(
        description="You have been timed out. You will be able to message ModMail again after <t:{0}>.".format(timeout)
    )

    return message_embed

def user_untimeout():
    """Returns embed for user untimeout in DMs.

    Returns:
        discord.Embed: Channel embed for user untimeout.
    """
    
    message_embed = discord.Embed(
        description="Your timeout has been removed. You can message ModMail again.".format()
    )

    return message_embed