def format_message(message):
    attachments = message.attachments
    formatted_message = '{0}'.format(message.content)
    for attachment in attachments:
        type = 'Unknown'
        if attachment.content_type.startswith('image'):
            type = 'Image'
        elif attachment.content_type.startswith('video'):
            type = 'Video'
        formatted_message += '\n[{0} Attachment]({1})'.format(type, attachment.url)
    return formatted_message