# modmail.py

ModMail, but in Python

# Configuration

- `name`: The bot's name.
- `token`: The bot's user token retrieved from Discord Developer Portal.
- `application_id`: The bot's application ID retrieved from Discord Developer Portal.
- `channel`: Modmail channel ID in guild (must be `TextChannel`).
- `prefix`: The bot prefix (needed for slash command sync command).
- `status`: The bot status.
- `id_prefix`: The bot prefix for persistent views (e.g., `mm`)
- `allowed_guild`: The alternate guild to accept modmails from. This is optional.

## Sample `config.json`

```json
{
  "name": "ModMail",
  "token": "abc123",
  "application_id": 1234567890,
  "channel": 1234567890,
  "prefix": "]",
  "status": "DM to contact",
  "id_prefix": "mm",
  "allowed_guild": {
    "guild_id": 1234567890,
    "invite": "https://discord.gg/invite"
  }
}
```

# Running the bot

1. Navigate to the root directory.

```
cd <path>/modmail.py
```

2. Copy the `config.example.json`, rename to `config.json`, and replace the relevant values.
   If you want to inject the config at runtime using environment variables, don't replace the values.

3. Build the bot using Docker.

```
docker image build -t modmail-py .
```

4. Run the docker container.

```
docker container run --name modmail \
    -v database:/database \
    modmail-py
```

As aforementioned, you can also inject environment variables.

```
docker container run --name modmail \
    -v database:/database \
    -e MODMAIL_TOKEN=foo \
    -e MODMAIL_CHANNEL=321 \
    -e MODMAIL_PREFIX=! \
    modmail-py
```

# Contributions

For information regarding contributing to this project, please read [CONTRIBUTING.md](CONTRIBUTING.md).
