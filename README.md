# modmail.py

ModMail, but in Python

# Configuration

- `token`: The bot's user token retrieved from Discord Developer Portal.
- `application_id`: The bot's application ID retrieved from Discord Developer Portal.
- `guild`: The guild ID.
- `channel`: Modmail channel ID in specified guild (must be `TextChannel`).
- `prefix`: The bot prefix (needed for slash command sync command).
- `status`: The bot status.
- `id_prefix`: The bot prefix for persistent views (e.g., `mm`)

## Sample `config.json`

```json
{
  "token": "abc123",
  "application_id": 1234567890,
  "guild": 1234567890,
  "channel": 1234567890,
  "prefix": "]",
  "status": "DM to contact",
  "id_prefix": "mm"
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
    -e MODMAIL_GUILD=123 \
    -e MODMAIL_CHANNEL=321 \
    -e MODMAIL_PREFIX=! \
    modmail-py
```

# Contributions

For information regarding contributing to this project, please read [CONTRIBUTING.md](CONTRIBUTING.md).
