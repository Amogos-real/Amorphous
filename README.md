# **Amorphous.py**

## **How to use Amorphous.py**

1. Run `git clone https://github.com/Amogos-real/Amorphous & cd Amorphous`
2. Create a `.env` (environment) file with the following content:
  ```
  Name=YOUR_BOT_NAME
  Rp=ESCAPED_FORM_OF_YOUR_BOTS_SYSTEM_PROMPT
  Gemini=YOUR_GEMINI_API_KEY
  Id=YOUR_BOTS_DISCORD_ID
  User=OWNERS_DISCORD_ID
  Discord=YOUR_BOTS_DISCORD_TOKEN
  ```
  Replace the following placeholders:
  - YOUR_BOT_NAME: The name of the Discord bot.
  - ESCAPED_FORM_OF_YOUR_BOTS_SYSTEM_PROMPT: Your bot's system prompt, but with all newlines replaced with `\n`.
  - YOUR_GEMINI_API_KEY: Your Gemini API key (open https://aistudio.google.com/apikey and follow the instructions if you don't already have one). **THIS KEY MUST BE KEPT ABSOLUTELY SECRET. DO NOT PUBLISH IT AND DO NOT COMMIT IT TO ANY PUBLIC REPOSITORY.**
  - YOUR_BOTS_DISCORD_ID: The Bot ID of the Discord bot (see [https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID)).
  - OWNERS_DISCORD_ID: Your own Discord User ID.
  - YOUR_BOTS_DISCORD_TOKEN: The bot's Discord token. **ALSO KEEP THIS SECRET AS WELL.**
3. Run `pip install -r requirements.txt`
  - This step is very important because otherwise you'll get a bunch of ModuleNotFoundError messages.
4. Run `python Amorphous.py`

## **Important notes**

- The bot will be running on your own local computer. The moment you shut your computer down or your internet becomes terrible, the bot will go offline instantly.
- The terminal has logs to help you debug issues, and it also is the core of the bot, so unless you do intend to shut the bot down, do not close it.

<sup>This README.md was written by [@UnbuiltAlmond8](https://github.com/UnbuiltAlmond8).</sup>
