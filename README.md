# Still Waiting Discord

![Image of the reminder](images/reminder.png)

Still Waiting Discord keeps chats alive by nudging mentioned users who don’t reply or react within 24 hours. Self-host to tweak reminders and timing to fit your server.

## Installation (Free)

1. Click [here](https://discord.com/oauth2/authorize?client_id=1379235275745656994&permissions=274877926400&integration_type=0&scope=bot) to add the bot to your server.
2. Mention someone in a message.
3. If they don't either leave a stamp directly on the mentioned message, or leave a message in the channel/thread within 24 hours, the bot will remind them.
4. If you like this bot, feel free to share it using the link below:

`https://koichin.com/still-waiting/`

## Self-Hosting (Optional)

You can self-host this bot for more control and customization. This is completely optional and requires some basic knowledge of Python and .env files.

### Note

- **Never expose your Discord token or database credentials.** Always add your `secrets` folder to `.gitignore` and keep sensitive information private.
- Do not share your bot publicly while running it locally. If you want to make changes after sharing, create a new bot application and token, and temporarily replace the token to prevent others from using your test bot.
- You can self-host this bot for almost free using services that offer free tiers. It's currently running on a GCP VM for hosting, with Firestore as the database, and these are highly recommended.
  - You can also use other services, but you need to make sure the hosting and database services are compatible with both IPv4 and IPv6.
  - If you want to use a different database service, you may need to modify the code, since it's designed to work with Firestore.

### Steps

The following steps are for using a GCP VM and Firestore.

1. Star this repo.
2. Clone this repo.
   - Run `git clone https://github.com/koichincom/still-waiting-discord.git` in your terminal.
   - Or download the ZIP file and extract it.
3. Install requirements.
   - If you use UV, you don't need to do anything at this step.
   - If you use PIP, run `pip install -r requirements.txt`.
4. Create a `secrets` folder by duplicating [`secrets/.env.example`](secrets/.env.example).
5. Set up Firestore.
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.
   - Enable Firestore for your project.
   - Create a service account and download the JSON key file.
   - Place the JSON key file in the `secrets` folder and rename it to `firestore-credentials.json`.
   - Reference: [Google Cloud Firestore Documentation](https://cloud.google.com/firestore/docs/quickstart-servers)
6. Create your Discord bot and add your bot token to the `.env` file:
   - Go to [Discord Developers](https://discord.com/developers/applications) and create a new application.
   - In the "Bot" tab, enable "PUBLIC BOT" if needed, reset the token, and copy it to your `.env` file.
   - In the "Bot" tab, enable all three intents: Presence, Server Members, and Message Content.
   - Reference: [Tech with Tim on YouTube](https://youtu.be/YD_N6Ffoojw?si=DHn1C2QrfDAwDw82&t=339)
7. Add your bot to your server:
   - Go to the "OAuth2" tab and scroll to "OAuth 2 URL Generator."
   - Select the "bot" scope and set the following permissions:
     - View Channels
     - Send Messages
     - Send Messages in Threads
     - Embed Links
   - Copy the generated URL and use it in your browser to add the bot to your server (the bot must be set to public to share with others).
   - Reference: [Tech with Tim on YouTube](https://youtu.be/YD_N6Ffoojw?si=0P-AwcLC3zhn_M3r&t=606)
8. Edit [`config.py`](src/config.py) to adjust any settings as needed.
9. Deploy to a hosting service; GCP VM is recommended.

## Contribution

This project is open-source under the [`MIT License`](LICENSE). Contributions are welcome! If you have ideas, suggestions, or improvements, feel free to open an issue or submit a pull request.

## Testing

The project includes comprehensive test coverage for all major components. See [`tests/README.md`](tests/README.md) for detailed testing documentation.

## Privacy

This bot does not store any message content. It only stores data for sending reminders and for project statistics.

### Sending Reminders

After sending a reminder, this data is deleted automatically:

- IDs of mentioned users
- IDs of the messages
- IDs of the channels
- Timestamps of the messages received

### Project Statistics

This data is stored permanently and may be used to publicly share bot usage statistics, but it does not include any personal information or message content:

- The number of servers the bot is in
- The number of users who have used the bot
- The number of messages processed by the bot

## Disclaimer

This bot is provided as-is with no guarantees. Use at your own risk. The author and any contributors are not responsible for any issues that arise from using this bot.
