import discord
import db

def user_embed(guild, message):
    # Change this to message from staff member
    message_embed = discord.Embed(
        title="New Mail from {0}".format(guild.name),
        description=message.content
    )

    return message_embed

def channel_embed(guild, ticket_id):

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
        if response['user'] != ticket['user']:
            author = '{0} as server'.format(guild.get_member(response['user']))
        message_embed.add_field(name="<t:{0}:R>, {1} wrote".format(response['timestamp'], author), value=response['response'], inline=False)

    return message_embed

def close_confirmation(member):
    message_embed = discord.Embed(
        description="Do you want to close the ModMail conversation for **{0}**".format(member)
    )

    return message_embed

def timeout_confirmation(member):
    message_embed = discord.Embed(
        description="Do you want to timeout **{0}** for 24 hours?".format(member)
    )

    return message_embed

def reply_cancel(member):
    message_embed = discord.Embed(
        description="Replying to ModMail conversation for **{0}**".format(member)
    )

    return message_embed

def closed_ticket(staff, member):
    message_embed = discord.Embed(
        description="**{0}** closed the ModMail conversation for **{1}**".format(staff, member)
    )

    return message_embed

def user_timeout(timeout):
    message_embed = discord.Embed(
        description="You have been timed out. You will be able to message ModMail again after <t:{0}>.".format(timeout)
    )

    return message_embed