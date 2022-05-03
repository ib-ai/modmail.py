import discord

async def user_embed(channel, message):
    # Change this to message from staff member
    message_embed = discord.Embed(
        title="New Mail from {0}".format(message.author),
        description=message.content
    )

    await channel.send(embed=message_embed)

async def channel_embed(channel, message, member):
    message_embed = discord.Embed(
        title="ModMail Conversation for {0}".format(member),
        description="User {0} has **{1}** roles\n Joined Discord: **{2}**\n Joined Server: **{3}**"
            .format(member.mention, len(member.roles), member.created_at.strftime("%B %d %Y"), member.joined_at.strftime("%B %d %Y"))
    )

    message_embed.add_field(name="On {0}, user wrote".format(message.created_at.strftime("%B %d %Y %H:%M:%S %Z")), value=message.content)

    await channel.send(embed=message_embed)