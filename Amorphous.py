from google import genai
from google.genai import types
import discord
import requests
import random
import re
import os
import threading
import getpass
import json

from time import sleep
import os, os.path

def update_watcher():
    while True:
        sleep(20)
        if os.path.exists("update2"):
            break

channel_sep = True
threading.Thread(target=update_watcher).start()
conversation = []
bot_configs = {}
intents = discord.Intents.all()
intents.message_content = True

client = discord.Client(intents=intents)

print("Tell me your Shape's information and I will save it and run the bot.")

def write_backstory():
    print()
    print("Type '$done' exactly as is, in a line, when you're done writing the backstory!")
    print()
    index = 0
    line = ""
    lines = []
    while line != "$done":
        if index == 0:
            line = input("Backstory: ")
        else:
            line = input(".......... ")
        lines.append(line)
        index += 1
    return '\n'.join(lines[:-1])
    
shape_name = input("Shape name: ")
file_exists = f"{shape_name}.json" in os.listdir()
if not file_exists:
    backstory = write_backstory()
    prefix = input("Prefix: ")
    if not prefix:
        print("Warning: Prefix is empty, may cause unexpected behavior. Did you intend to do this?")
    token = getpass.getpass("Discord Bot Token: ")
    gemini_api_key = getpass.getpass("Gemini API key: ")
    if not token or not gemini_api_key:
        print("ERROR: Discord Bot Token and/or Gemini API key must not be empty, exiting.")
        exit()
    print()
    print("I recommend using only one Discord User ID that belongs to you, the owner of the Shape.")
    BYPASS_ID = input("Comma-separated list of Discord User IDs that are allowed to bypass certain permission checks: ").split(",")
else:
    content = open(f'{shape_name}.json', 'r', encoding='utf-8').read()
    content = json.loads(content)
    backstory = content['backstory']
    prefix = content['prefix']
    token = content['token']
    gemini_api_key = content['api_key']
    BYPASS_ID = content['bypass_id']
    print()
    print(f"Successfully loaded data for {shape_name}, proceeding.")
    print()
    
amorphous_config = {"""shape-name""": shape_name,
                    """backstory""": backstory,
                    """token""": token,
                    """api_key""": gemini_api_key,
                    """prefix""": prefix, 
                    """bypass_id""": bypass_id,
                    """hosting""": """download"""}

if not file_exists:
    with open(f"{shape_name}.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(amorphous_config))
        
# Config_end
rp = amorphous_config["backstory"]
prefix = amorphous_config["prefix"]
gemini_api_key = amorphous_config["api_key"]
token = amorphous_config["token"]
shape_name = amorphous_config["shape-name"]
knowledge_db = []
# if amorphous_config["make_folder"]=="True":
#     if not os.path.exists(shape_name):
#         os.mkdir(shape_name)
#         print("Knowledge created")
#     for file in os.listdir(f"./{shape_name}/"):
#         with open(file,"r") as w:
#             knowledge_db.append([file,w.read()])
model = 'gemini-2.0-flash'
model1= 'gemini-2.5-flash'
model2= "gemini-2.5-pro'

gemini_client = genai.Client(
    api_key=gemini_api_key,
    http_options=types.HttpOptions(api_version='v1alpha')
)

safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
]

config = types.GenerateContentConfig(safety_settings=safety_settings)


def get_convo(guild_id):
    """Retrieves the bot configuration for a given guild, creating a default one if it doesn't exist."""
    if guild_id not in bot_configs:
        bot_configs[guild_id] = {
            "conversation": [],
            "toggle": True  # Default: Ignore commands from bots
        }
    return bot_configs[guild_id]


def update_convo(conversation, guild_id):
    bot_configs[guild_id]["conversation"] = conversation

    return True


async def check_permissions(message):
    # Allow user with specific ID to bypass permission checks
    if message.author.id in BYPASS_ID:
        return True
    if not (message.author.guild_permissions.manage_guild or message.author.guild_permissions.administrator):
        await message.channel.send("You need 'Manage Server' or 'Administrator' permissions to use this command.")
        return False
    return True


def gen(model, prompt, streaming=False):
    if streaming:
        return gemini_client.models.generate_content_stream(
            model=model, contents=prompt, config=config
        )
    else:
        return gemini_client.models.generate_content(
            model=model, contents=prompt, config=config
        )


def safesplit(text):
    chunks = []
    chunk_size = 2000
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks


async def safesend(function, text):
    safechunks = safesplit(text)
    for m in safechunks:
        await function(m)


intents = discord.Intents.all()
intents.message_content = True

client = discord.Client(intents=intents)


async def replace_mentions_with_usernames(content: str, message: discord.Message) -> str:
    """
    Replaces user mentions (<@USER_ID> or <@!USER_ID>) in a string
    with their corresponding display names (@DisplayName).

    Args:
        content: The original string content (e.g., message.content).
        message: The discord.Message object containing the mentions.

    Returns:
        The string with mentions replaced by usernames.
    """
    # Start with the original content
    processed_content = content

    # Iterate through each user mentioned in the message
    # message.mentions contains a list of discord.Member or discord.User objects
    for user in message.mentions:
        # user.mention creates the standard mention string (<@USER_ID>)
        # user.display_name gets the user's server nickname if available, otherwise their global username
        mention_string = user.mention
        replacement_string = f"@{user.display_name}"

        # Replace all occurrences of the mention string in the processed content
        # We need to handle both <@USER_ID> and <@!USER_ID> (nickname mention) formats.
        # discord.py's user.mention usually gives <@USER_ID>, but let's be safe.
        # A simple string replace works well here.
        processed_content = processed_content.replace(mention_string, replacement_string)

        # Handle the potential nickname mention format <@!USER_ID> just in case
        # Although user.mention might not produce this directly, it could appear in raw content
        nickname_mention_string = f"<@!{user.id}>"
        processed_content = processed_content.replace(nickname_mention_string, replacement_string)

    # --- Alternative using Regex (more robust if mentions might be malformed) ---
    # If you suspect mentions might not be perfectly captured by message.mentions
    # or you need to handle cases not automatically parsed by discord.py,
    # you could use regex, but it requires fetching members which is slower.

    # pattern = re.compile(r'<@!?(\d+)>') # Matches <@USER_ID> and <@!USER_ID>
    # matches = pattern.finditer(content)
    # processed_content = content # Start fresh if using regex method
    # replacements = {} # Store replacements to avoid modifying the string while iterating

    # for match in matches:
    #     full_mention = match.group(0)
    #     user_id = int(match.group(1))

    #     # Try to find the user in message.mentions first (efficient)
    #     mentioned_user = discord.utils.get(message.mentions, id=user_id)

    #     # If not in mentions, try fetching from the guild (less efficient)
    #     if not mentioned_user and message.guild:
    #         try:
    #             # Note: Fetching might require Member Intents enabled for your bot
    #             mentioned_user = message.guild.get_member(user_id)
    #             # If get_member returns None and you have intents, you might need:
    #             # mentioned_user = await message.guild.fetch_member(user_id)
    #         except discord.NotFound:
    #             mentioned_user = None # User not found in the guild
    #         except discord.Forbidden:
    #             mentioned_user = None # Bot lacks permissions

    #     if mentioned_user:
    #         replacements[full_mention] = f"@{mentioned_user.display_name}"
    #     else:
    #         # Optional: Handle cases where the user ID is invalid or user not found
    #         replacements[full_mention] = f"@UnknownUser({user_id})" # Or keep the original mention

    # # Apply replacements
    # for original, replacement in replacements.items():
    #      processed_content = processed_content.replace(original, replacement)
    # --- End of Regex Alternative ---

    return processed_content


async def find_member(message, member_identifier):
    member = None

    # Attempt to get member by mention
    if member_identifier.startswith('<@') and member_identifier.endswith('>'):
        # Handle both normal mentions and nickname mentions
        member_id = ''.join(filter(str.isdigit, member_identifier))
        try:
            member_id = int(member_id)
            member = message.guild.get_member(member_id)
        except ValueError:
            await message.channel.send("Invalid member mention format.")
            return None
    else:
        # Attempt to find by exact match first
        for m in message.guild.members:
            # Check nickname exact match
            if m.nick and m.nick.lower() == member_identifier.lower():
                member = m
                break
            # Check username exact match
            if m.name.lower() == member_identifier.lower():
                member = m
                break

        # If no exact match, try partial match
        if member is None:
            # Attempt to find by nickname or username (partial match)
            for m in message.guild.members:
                if m.nick and member_identifier.lower() in m.nick.lower():
                    member = m
                    break

            # If not found by nickname, try by username
            if member is None:
                for m in message.guild.members:
                    if member_identifier.lower() in m.name.lower():
                        member = m
                        break

    if not member:
        # await message.channel.send(f"Member not found: '{member_identifier}'")
        return "@" + member_identifier

    return member


async def fix_member(msg, dmessage):
    temp = msg
    replaced = []
    replace = re.findall("@?(.*) ", msg + " ")
    for m in replace:
        replace.append(await find_member(dmessage, m))
    d = 0
    for m in replaced:
        temp = temp.replace(replace[d], m)
        d += 1
    return temp


toggle = False


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.change_presence(activity=discord.CustomActivity(name="something"))


activated_channels = []
ignored_channels = []


@client.event
async def on_message(message):
    global activated_channels
    # Support both DMs and guild channels
    if message.guild:
        guild_id = message.guild.id
    else:
        guild_id = f"user_{message.author.id}"

    toggle = get_convo(guild_id=guild_id)["toggle"]
    conversation = get_convo(guild_id=guild_id)["conversation"]

    if (message.author == client.user) and message.content.startswith("(system response)\n"): return
    channel_tag = ""
    if channel_sep:
        channel_tag = "{" + message.channel.name + "}"
    else:
        channel_tag = ""
    cleanedup = await replace_mentions_with_usernames(message.content, message)
    print(f"[{message.author}]({message.author.display_name}){channel_tag}  : {cleanedup}")
    conversation.append(f"[{message.author.name}]({message.author.display_name}){channel_tag}:" + cleanedup)

    update_convo(conversation, guild_id)
    if message.attachments:
        rem = len(conversation) - 1
        for attachment in message.attachments:
            # Download the attachment using requests
            r = requests.get(attachment.url)
            if r:
                # Check if the request was successful
                if r.status_code == 200:
                    content = r.content
                    # base64.b64encode(bytes(r.text)).decode()
                    response = gemini_client.models.generate_content(

                        contents=[
                            types.Part.from_bytes(

                                data=content,
                                mime_type='image/png',
                            ),
                            'Describe this image in detail! Do not use markdown. keep all of it in a single line!'
                        ], model=model, config=config
                    )
                    print(response.text)

                    conversation[rem] += "(System image support)[File attached, Image description:" + response.text

                    print(f"Downloaded {attachment.filename}")

    if message.author == client.user:
        return
    ran_command = False
    if message.content.startswith(f'{prefix} help'):
        help_text = (
            f"**{shape_name} Bot Commands:**\n"
            f"`{prefix} help` - Show this help message\n"
            f"`{prefix} activate` - Activate bot in this channel\n"
            f"`{prefix} deactivate` - Deactivate bot in this channel (or add channel to exclusion list with manage server perms)\n"
            f"`{prefix} wack` - Wipe conversation history\n"
            f"`{prefix} toggle` - Toggle bot ignoring other bots\n"
            f"`{prefix} allow` - Allow bot to respond in channel\n"
            f"`{prefix} reset` - Reset bot to default state\n"
            "Mention the bot or reply to its message to chat.\n\n"
            "Powered by Amorphous Discord Engine and Gemini 2.0 Flash but actually powered by Python"
        )
        await message.channel.send(help_text)
        ran_command = True
    if message.content.startswith(f'{prefix} allow'):
        await message.channel.send("Allowed.")
        ignored_channels.remove(message.channel.id)
        ran_command = True
    if message.content.startswith(f'{prefix} activate'):
        activated_channels.append(message.channel.id)
        await message.channel.send('(system response)\n>(activated)')
        ran_command = True
    if message.content.startswith(f'{prefix} deactivate'):
        if message.channel.id in activated_channels:
            activated_channels.remove(message.channel.id)
            await message.channel.send('(system response)\n> Deactivated.')
        else:
            message.channel.send("test")
            if check_permissions(message.author):
                if not message.channel.id in ignored_channels:
                    await message.channel.send('(system response)\nAdded to exclusion.')
                    ignored_channels.append(message.channel.id)
            else:
                await message.channel.send('(system response)\nHELL NAW; ')
        ran_command = True

    if message.content.startswith(f"{prefix} toggle"):
        await message.channel.send("(system response)\n Bro this is dangerous af u sure? Activated prepare for chaOS")
        toggle = not (toggle)
        ran_command = True
    if message.content.startswith(f'{prefix} wack'):
        conversation.clear()
        await message.channel.send('(system response)\n> Conversation history wiped! 💀')
        ran_command = True
    if len(conversation) > 600:
        conversation.remove(conversation[0])
    update_convo(conversation, guild_id)

    bot_configs[guild_id]["toggle"] = toggle
    if ran_command:
        return
    # Ignore messages from bots (including itself and other bots)
    if message.author.bot and toggle:
        return
    # Always respond if this is a reply to the bot's own message
    if message.reference:
        try:
            replied_message = await message.channel.fetch_message(message.reference.message_id)
            if replied_message.author == client.user:
                should_respond = True
        except Exception:
            pass
    # replace with your channel IDs

    should_respond = False

    # Check if channel is activated
    if message.channel.id in activated_channels:
        should_respond = True
    else:
        # Respond if pinged or random chance (1 in 5)
        if client.user in message.mentions or random.randint(1, 100000) == 1:
            should_respond = True
    if message.channel.id in ignored_channels:
        should_respond = False
    if isinstance(message.channel, discord.channel.DMChannel):
        should_respond = True
    if should_respond:
        try:
            async with message.channel.typing():
                l = gen(model, rp + str(
                    conversation) + f";You username here is {client.user}; Please generate a response based on the text above!  ").text.removeprefix(
                    str(client.user)).removeprefix(":")
                # l = gen(model, str(knowledge_db)+rp+str(conversation)+f"; Write a response to the conversation above following the prompt! You username here is {client.user} Only write the message part of the message, do not narrate other; ",streaming=True)
                # msg = await message.channel.send("(...)")
                # full_msg = ""
                # async with message.channel.typing():
                #     for chunk in l:
                #         if len(full_msg)>1500:
                #             msg = await message.channel.send("(...)")
                #             full_msg = ""
                #         full_msg+=chunk.text
                #         await msg.edit(content=full_msg)
                # await safesend(message.channel.send, l)
        except Exception as e:
            try:
                l = ("(API CREDITS RAN OUT; Using free model; Please wait.) \n") + str(e)
                print(l)
                l = ""
                l += gen(model1, rp + str(conversation) + f";Your username here is {client.user}; Please generate a response based on the text above!  ").text.removeprefix(
                    str(client.user)).removeprefix(":")
            except Exception as inner_e:
                l += "PRIMARY AND FALLBACK MODEL FAILED. MORE INFORMATION: " + str(inner_e)
                print(l)
                l= ""
                try:
                    l += gen(model2, rp + str(conversation) + f";Your username here is {client.user}; Please generate a response based on the text above!  ").text.removeprefix(
                    str(client.user)).removeprefix(":")
                except Exception as another_e:
                    l += "PRIMARY AND 2 OTHER FALLBACK MODELS FAILED. MORE INFORMATION: " + str(another_÷)
                    

        print(l)
        await safesend(message.channel.send, l)


client.run(token)
