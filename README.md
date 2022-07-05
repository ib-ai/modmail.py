# modmail.py

ModMail, but in Python

# Running the bot

1. Navigate to the root directory.

```
cd <path>/modmail.py
```

2. Copy the `config.example.json`, rename to `config.json`, and replace the relevant values.

3. Build the bot using Docker.

```
docker build -t modmail-py .
```

4. Run the docker container.

```
docker run -it --rm --name modmail-py modmail-py
```
