import re

ID_PATTERN = re.compile('^\\d{17,20}$')
MEMBER_MENTION_PATTERN = re.compile('^<@!?\\d{17,20}>$')
NAME_PATTERN = re.compile('^.{2,32}#[0-9]{4}$')

def get_command(prefix, content):
    """Returns the command and the following arguments when given the message content.

    Args:
        prefix (str): The specified bot prefix passed through from bot config.
        content (str): The contents of the message.

    Returns:
        tuple: A tuple containing the command itself and array of arguments.
    """    
    command_split = content[len(prefix):].split(' ')
    return command_split[0], command_split[1:]

def get_member(guild, input):
    member = None

    if ID_PATTERN.match(input) or MEMBER_MENTION_PATTERN.match(input):
        member = guild.get_member(int(re.sub('[^0-9]', '', input)))
    elif NAME_PATTERN.match(input):
        member = guild.get_member_named(input)
    
    if member is not None and not member.bot:
        return member
    else:
        return None

def assert_member(guild, argument):    
    member = get_member(guild, argument)

    if member is None:
        raise RuntimeError("Please specify a valid user.")

    return member

def assert_arguments(args, length):
    if len(args) < length:
        raise RuntimeError("Invalid number of arguments.")
