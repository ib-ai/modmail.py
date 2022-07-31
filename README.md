# modmail.py

ModMail, but in Python

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
