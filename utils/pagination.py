from typing import Union, Optional
from collections.abc import Collection

import discord

NAME_SIZE_LIMIT = 256
VALUE_SIZE_LIMIT = 1024


def paginated_embed_menus(
    names: Collection[str],
    values: Collection[str],
    pagesize: int = 10,
    *,
    inline: Union[Collection[bool], bool] = False,
    embed_dict: Optional[dict] = None,
) -> Collection[discord.Embed]:
    """
    Generates embeds for a paginated embed view.

    Args:
        names (Collection[str]): Names of fields to be added/paginated.
        values (Collection[str]): Values of fields to be added/paginated.
        pagesize (int, optional): Maximum number of items per page. Defaults to 10.
        inline (Union[Collection[bool], bool], optional): Whether embed fields should be inline or not. Defaults to False.
        embed_dict (Optional[dict], optional): Partial embed dictionary (for setting a title, description, etc.). Footer and fields must not be set. Defaults to None.

    Returns:
        Collection[discord.Embed]: Collection of embeds for paginated embed view.
    """
    N = len(names)
    if N != len(values):
        raise ValueError(
            'names and values for paginated embed menus must be of equal length.'
        )
    if isinstance(inline, bool):
        inline = [inline] * N
    elif N != len(inline):
        raise ValueError(
            '"inline" must be boolean or a collection of booleans of equal length to names/values for paginated embed menus.'
        )

    if embed_dict:
        if 'title' in embed_dict and len(embed_dict['title']) > 256:
            raise ValueError('title cannot be over 256 characters')
        if 'description' in embed_dict and len(
                embed_dict['description']) > 4096:
            raise ValueError('desription cannot be over 4096 characters')
        if 'footer' in embed_dict:
            raise ValueError('embed_dict "footer" key must not be set.')
        if 'fields' in embed_dict:
            raise ValueError('embed_dict "fields" key must not be set.')
    else:
        embed_dict = {  # default
            'description': 'Here is a list of entries.'
        }

    if N == 0:
        return [discord.Embed.from_dict(embed_dict)]

    embeds: Collection[discord.Embed] = []
    current: discord.Embed = discord.Embed.from_dict(embed_dict)
    pages = 1
    items = 0
    for name, value, inline_field in zip(names, values, inline):
        if items == pagesize or len(current) + len(name) + len(
                value) > 5090:  # leave 10 chars for footers
            embeds.append(current)
            current = discord.Embed.from_dict(embed_dict)
            pages += 1
            items = 0

        current.add_field(name=name, value=value, inline=inline_field)
        items += 1
    embeds.append(current)
    for page, embed in enumerate(embeds):
        embed.set_footer(text=f"Page {page+1}/{pages}")

    return embeds
