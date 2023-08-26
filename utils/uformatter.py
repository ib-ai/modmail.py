import discord


def format_message(message: discord.Message) -> str:
    """
    Formats message to include attachments as links.

    Args:
        message (discord.Message): Message to format.

    Returns:
        str: Formatted message.
    """
    attachments = message.attachments
    formatted_message = f"{message.content}".strip()
    for attachment in attachments:
        attachment_type = "Unknown"
        if attachment.content_type.startswith("image"):
            attachment_type = "Image"
        elif attachment.content_type.startswith("video"):
            attachment_type = "Video"
        formatted_message += f"\n[{attachment_type} Attachment]({attachment.url})"

    return formatted_message
