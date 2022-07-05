import re

ID_PATTERN = re.compile('^\\d{17,20}$')
MEMBER_MENTION_PATTERN = re.compile('^<@!?\\d{17,20}>$')
NAME_PATTERN = re.compile('^.{2,32}#[0-9]{4}$')

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
