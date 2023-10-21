from config import Config
from discord.ext import commands
import discord
import json
import asyncio
import re

# Set the white checkmark emoji
solved_emoji = '✅'

# Cooldown dictionary to track the cooldown for each channel
captcha_cooldowns = {}

# Dictionary to track if a captcha has already been detected in a channel
captcha_detected = {}

def find_word(words, user_input):
    for word in words:
        if len(word) != len(user_input):
            continue
        match = True
        for i in range(len(word)):
            if user_input[i] != '_' and user_input[i] != word[i]:
                match = False
                break
        if match:
            return word
    return None

async def send_hint_and_solution(channel, hint, solution):
    if hint:
        await channel.send(hint)
    if solution:
        await asyncio.sleep(5)  # Delay between hint and solution
        await channel.send(solution)

def start():
    bot = commands.Bot(command_prefix='!')

    @bot.event
    async def on_ready():
        await bot.change_presence(status=discord.Status.offline)
        print('We have logged in as {0.user}'.format(bot))
        print('Bot Is Ready...')

    @bot.event
    async def on_message(message):
        try:
            poketwo = 716390085896962058

            # Check if the message is in the current spawn channel
            if message.channel.id in [int(channel_id) for channel_id in Config.spawn_channels]:
                if message.author.id == int(poketwo) and message.embeds:
                    embed_title = message.embeds[0].title
                    if 'wild pokémon has appeared!' in embed_title:
                        hint_message = '<@716390085896962058> h'
                        await asyncio.sleep(4)  # Delay before sending hint
                        await send_hint_and_solution(message.channel, hint_message, '')

                if message.author.id == int(poketwo) and message.content.startswith('The pokémon is '):
                    extracted_word = message.content[len('The pokémon is '):].strip('.').strip().replace('\\', '')
                    print(f'Pokemon Hint: {extracted_word}')
                    result = find_word(words, extracted_word)
                    if result:
                        await asyncio.sleep(6)
                        hint_message = '<@716390085896962058> c ' + result
                        await send_hint_and_solution(message.channel, hint_message, '')
                        print(f"Search Result: {result}")
                    else:
                        print("Pokemon Not Found In Database")

            if 'human' in message.content:
                for channel_id in Config.spawn_channels:
                    if message.channel.id == int(channel_id):
                        pattern = r'https://verify\.poketwo\.net/captcha/[0-9]+'
                        match = re.search(pattern, message.content)
                        if match:
                            url = match.group()
                            print('Captcha Detected in Spawn Channel')
                            if channel_id not in captcha_cooldowns:
                                captcha_cooldowns[channel_id] = 0

                            # Check for cooldown
                            if captcha_cooldowns[channel_id] > 0:
                                print(f"Captcha detection on channel {channel_id} is on cooldown.")
                                return

                            # Check if captcha has already been detected in this channel
                            if channel_id in captcha_detected:
                                print(f"Captcha has already been detected in channel {channel_id}. Skipping.")
                                return

                            # Mention the owners in the message
                            notification_message = f"Captcha detected in a spawn channel.\n"
                            notification_message += f"Message Link: {message.jump_url}\n"
                            notification_message += f"Captcha Link: {url}\n"
                            notification_message += f"<@1146945488998895710> "  # Replace with your owner ID

                            # Find the 'general' channel by name and get its ID
                            general_channel = discord.utils.get(message.guild.channels, name='general')
                            if general_channel:
                                sent_message = await general_channel.send(notification_message)

                                # Add reactions to the message to allow users to confirm captcha solved
                                await sent_message.add_reaction(solved_emoji)
                                await sent_message.add_reaction("❌")

                                # Set a 20-minute cooldown (1200 seconds) for the channel
                                captcha_cooldowns[channel_id] = 1200
                                captcha_detected[channel_id] = True

        except Exception as e:
            print(f"Error in on_message: {e}")

    with open('pokemon.json', 'r', encoding='utf-8') as f:
        words = json.load(f)

    bot.run(Config.token)

start()
