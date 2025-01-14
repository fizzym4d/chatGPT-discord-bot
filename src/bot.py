import discord
from discord import app_commands
from src import responses
from src import log

logger = log.setup_logger(__name__)

config = responses.get_config()

isPrivate2 = False
isReplyAll2 = False

class aclient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="/chat2 | /help2")


async def send_message(message, user_message):
    global isReplyAll2
    if not isReplyAll2:
        author = message.user.id
        await message.response.defer(ephemeral=isPrivate2)
    else:
        author = message.author.id
    try:
        response = '> **' + user_message + '** - <@' + \
            str(author) + '> \n\n'
        response = f"{response}{await responses.handle_response(user_message)}"
        if len(response) > 1900:
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            if "```" in response:
                # Split the response if the code block exists
                parts = response.split("```")
                # Send the first message
                if isReplyAll2:
                    await message.channel.send(parts[0])
                else:
                    await message.followup.send(parts[0])
                # Send the code block in a seperate message
                code_block = parts[1].split("\n")
                formatted_code_block = ""
                for line in code_block:
                    while len(line) > 1900:
                        # Split the line at the 50th character
                        formatted_code_block += line[:1900] + "\n"
                        line = line[1900:]
                    formatted_code_block += line + "\n"  # Add the line and seperate with new line

                # Send the code block in a separate message
                if (len(formatted_code_block) > 2000):
                    code_block_chunks = [formatted_code_block[i:i+1900]
                                         for i in range(0, len(formatted_code_block), 1900)]
                    for chunk in code_block_chunks:
                        if isReplyAll2:
                            await message.channel.send("```" + chunk + "```")
                        else:
                            await message.followup.send("```" + chunk + "```")
                else:
                    if isReplyAll2:
                        await message.channel.send("```" + formatted_code_block + "```")
                    else:
                        await message.followup.send("```" + formatted_code_block + "```")
                # Send the remaining of the response in another message

                if len(parts) >= 3:
                    if isReplyAll2:
                        await message.channel.send(parts[2])
                    else:
                        await message.followup.send(parts[2])
            else:
                response_chunks = [response[i:i+1900]
                                   for i in range(0, len(response), 1900)]
                for chunk in response_chunks:
                    if isReplyAll2:
                        await message.channel.send(chunk)
                    else:
                        await message.followup.send(chunk)
                        
        else:
            if isReplyAll2:
                await message.channel.send(response)
            else:
                await message.followup.send(response)
    except Exception as e:
        if isReplyAll2:
            await message.channel.send("> **Error: Something went wrong, please try again later!**")
        else:
            await message.followup.send("> **Error: Something went wrong, please try again later!**")
        logger.exception(f"Error while sending message: {e}")


async def send_start_prompt(client):
    import os
    import os.path

    config_dir = os.path.abspath(__file__ + "/../../")
    prompt_name = 'starting-prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r") as f:
                prompt = f.read()
                if (config['discord_channel_id']):
                    logger.info(f"Send starting prompt with size {len(prompt)}")
                    responseMessage = await responses.handle_response(prompt)
                    channel = client.get_channel(int(config['discord_channel_id']))
                    await channel.send(responseMessage)
                    logger.info(f"Starting prompt response:{responseMessage}")
                else:
                    logger.info("No Channel selected. Skip sending starting prompt.")
        else:
            logger.info(f"No {prompt_name}. Skip sending starting prompt.")
    except Exception as e:
        logger.exception(f"Error while sending starting prompt: {e}")


def run_discord_bot():
    client = aclient()

    @client.event
    async def on_ready():
        await send_start_prompt(client)
        await client.tree.sync()
        logger.info(f'{client.user} is now running!')

    @client.tree.command(name="chat2", description="Have a chat with ChatGPT 2")

    async def chat2(interaction: discord.Interaction, *, message: str):
        global isReplyAll2
        if isReplyAll2:
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send("> **Warn: You already on replyAll mode. If you want to use slash command, switch to normal mode, use `/replyall` again**")
            logger.warning("\x1b[31mYou already on replyAll mode, can't use slash command!\x1b[0m")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        user_message = message
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
        await send_message(interaction, user_message)

    @client.tree.command(name="private2", description="Toggle private2 access with ChatGPT 2")
    async def private2(interaction: discord.Interaction):
        global isPrivate2
        await interaction.response.defer(ephemeral=False)
        if not isPrivate2:
            isPrivate2 = not isPrivate2
            logger.warning("\x1b[31mSwitch to private2 mode\x1b[0m")
            await interaction.followup.send("> **Info: Next, the response will be sent via private2 message. If you want to switch back to public2 mode, use `/public2`**")
        else:
            logger.info("You already on private2 mode!")
            await interaction.followup.send("> **Warn: You already on private2 mode. If you want to switch to public2 mode, use `/public2`**")

    @client.tree.command(name="public2", description="Toggle public2 access with ChatGPT 2")
    async def public2(interaction: discord.Interaction):
        global isPrivate2
        await interaction.response.defer(ephemeral=False)
        if isPrivate2:
            isPrivate2 = not isPrivate2
            await interaction.followup.send("> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private2 mode, use `/private2`**")
            logger.warning("\x1b[31mSwitch to public2 mode\x1b[0m")
        else:
            await interaction.followup.send("> **Warn: You already on public2 mode. If you want to switch to private2 mode, use `/private2`**")
            logger.info("You already on public2 mode!")

    @client.tree.command(name="replyall2", description="Toggle replyAll access with ChatGPT 2")
    async def replyall2(interaction: discord.Interaction):
        global isReplyAll2
        await interaction.response.defer(ephemeral=False)
        if isReplyAll2:
            await interaction.followup.send("> **Info: The bot will only response to the slash command `/chat` next. If you want to switch back to replyAll mode, use `/replyAll` again.**")
            logger.warning("\x1b[31mSwitch to normal mode\x1b[0m")
        else:
            await interaction.followup.send("> **Info: Next, the bot will response to all message in the server. If you want to switch back to normal mode, use `/replyAll` again.**")
            logger.warning("\x1b[31mSwitch to replyAll mode\x1b[0m")
        isReplyAll2 = not isReplyAll2
            
    @client.tree.command(name="reset2", description="Complete reset2 ChatGPT 2 conversation history")
    async def reset2(interaction: discord.Interaction):
        responses.chatbot.reset2()
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("> **Info: I have forgotten everything.**")
        logger.warning(
            "\x1b[31mChatGPT 2 bot has been successfully reset2\x1b[0m")
        await send_start_prompt(client)
        
    @client.tree.command(name="help2", description="Show help2 for the ChatGPT 2 Bot")
    async def help2(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(":star:**BASIC COMMANDS** \n\n    - `/chat2 [message]` Chat with ChatGPT 2!\n    - `/public2` ChatGPT 2 switch to public2 mode \n    - `/replyall`  ChatGPT switch between replyall mode and default mode\n    - `/reset2` Clear ChatGPT conversation history\n\nFor complete documentation, please visit https://github.com/Zero6992/chatGPT-discord-bot")
        logger.info(
            "\x1b[31mSomeone need help2!\x1b[0m")

    @client.event
    async def on_message(message):
        if isReplyAll2:
            if message.author == client.user:
                return
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
            logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
            await send_message(message, user_message)
            
    TOKEN = config['discord_bot_token']
    client.run(TOKEN)
