import discord
from discord.ext import commands

import db
from utils.config import Config
from utils.ticket_embed import MessageButtonsView

import logging

logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

member_cache = discord.MemberCacheFlags.all()

modmail_config = Config()

INITIAL_COGS = ["commands", "listeners"]


class Modmail(commands.Bot):
    def __init__(self):
        super().__init__(
            intents=intents,
            command_prefix=modmail_config.prefix,
            description=modmail_config.status,
            application_id=modmail_config.application_id,
            member_cache_flags=member_cache,
        )

    async def setup_hook(self):
        await db.init()
        logger.info("Database sucessfully initialized!")

        for cog in INITIAL_COGS:
            try:
                await bot.load_extension(f"cogs.{cog}")
                logger.debug(f"Imported cog '{cog}'.")
            except (
                commands.errors.NoEntryPointError,
                commands.errors.ExtensionNotFound,
                commands.errors.ExtensionFailed,
            ) as e:
                logger.fatal(f"Failed to import cog '{cog}'.")
                raise SystemExit(e)

        logger.info("Loaded all cogs.")

        self.add_view(MessageButtonsView(bot, []))
        logger.info("Added all views.")

    async def on_ready(self):
        await bot.change_presence(
            activity=discord.Game(name=modmail_config.status),
            status=discord.Status.online,
        )

        logger.info(f"Bot '{bot.user.name}' is now connected.")

    async def on_command_error(self, ctx: commands.Context, exception) -> None:
        await super().on_command_error(ctx, exception)
        await ctx.send(exception)


bot = Modmail()
bot.run(modmail_config.token.get_secret_value())
