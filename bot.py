import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from jellyfin_client import JellyfinClient

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True # Required for commands
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Jellyfin Client Setup ---
try:
    jellyfin_client = JellyfinClient()
except ValueError as e:
    print(f"Error initializing Jellyfin Client: {e}")
    jellyfin_client = None

# --- State Management ---
# A set to keep track of sessions we've already sent a notification for.
notified_sessions = set()
# A set to keep track of recently added items we've announced.
announced_item_ids = set()
# A flag to ensure we only populate the initial list of recent items once.
is_first_recent_check = True


@tasks.loop(minutes=30)
async def check_recently_added():
    """Periodically checks for new items added to Jellyfin and announces them."""
    global announced_item_ids, is_first_recent_check

    if not jellyfin_client or not DISCORD_CHANNEL_ID:
        return # Silently fail if not configured

    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        return # Can't find channel

    latest_items = jellyfin_client.get_latest_items()
    if not latest_items:
        return # No items or an error occurred

    # On the first run, populate the set of known items without notifying.
    if is_first_recent_check:
        announced_item_ids = {item['Id'] for item in latest_items}
        is_first_recent_check = False
        print(f"Initial scan complete. Found {len(announced_item_ids)} recent items.")
        return

    # For subsequent checks, find and announce new items.
    new_items = [item for item in latest_items if item['Id'] not in announced_item_ids]
    for item in new_items:
        try:
            await send_recently_added_notification(channel, item)
            announced_item_ids.add(item['Id'])
        except Exception as e:
            print(f"Error sending 'recently added' notification for item {item['Id']}: {e}")


async def send_recently_added_notification(channel, item):
    """Formats and sends a 'Recently Added' notification."""
    title = item.get('Name', 'Unknown Title')
    item_id = item['Id']
    media_type = item.get('Type', 'Item')

    embed = discord.Embed(
        title=f"✨ New {media_type} Added: {title}",
        color=discord.Color.green()
    )

    if media_type == 'Episode' and 'SeriesName' in item:
        embed.description = f"Series: **{item['SeriesName']}**"

    embed.set_image(url=jellyfin_client.get_item_image_url(item_id, "Primary"))
    embed.set_footer(text="Recently added to the library.")

    await channel.send(embed=embed)


@bot.command(name="stats", help="Shows current playback activity on the Jellyfin server.")
async def get_stats(ctx):
    """Command to display current Jellyfin server activity."""
    if not jellyfin_client:
        await ctx.send("The Jellyfin client is not configured. Please check the logs.")
        return

    sessions = jellyfin_client.get_sessions()
    if sessions is None:
        await ctx.send("Could not retrieve session data from Jellyfin.")
        return

    active_sessions = [s for s in sessions if "NowPlayingItem" in s]

    if not active_sessions:
        await ctx.send("✅ No active playback sessions on the server.")
        return

    embed = discord.Embed(
        title="📊 Jellyfin Server Activity",
        color=discord.Color.purple()
    )

    for session in active_sessions:
        user = session.get('UserName', 'Unknown User')
        item = session['NowPlayingItem']
        title = item.get('Name', 'Unknown Title')
        item_type = item.get('Type', 'Item')

        value = f"Watching: **{title}** ({item_type})"
        if item_type == 'Episode':
            series = item.get('SeriesName', 'Unknown Series')
            value = f"Watching: **{series} - {title}**"

        embed.add_field(name=f"👤 {user}", value=value, inline=False)

    embed.set_footer(text=f"Total Active Sessions: {len(active_sessions)}")
    await ctx.send(embed=embed)


@tasks.loop(seconds=10)
async def check_jellyfin_sessions():
    """Periodically checks for new Jellyfin sessions and sends notifications."""
    global notified_sessions  # Declare global at the beginning

    if not jellyfin_client or not DISCORD_CHANNEL_ID:
        if not DISCORD_CHANNEL_ID:
            print("Warning: DISCORD_CHANNEL_ID is not set. Cannot send notifications.")
        # Silently fail if jellyfin_client is not initialized
        return

    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print(f"Error: Could not find channel with ID {DISCORD_CHANNEL_ID}")
        return

    sessions = jellyfin_client.get_sessions()
    if sessions is None:
        return  # Error already printed in client

    current_session_ids = set()
    for session in sessions:
        # We only care about sessions with an active item being played.
        if "NowPlayingItem" not in session:
            continue

        session_id = session['Id']
        current_session_ids.add(session_id)

        # If we haven't notified for this session yet, do it now.
        if session_id not in notified_sessions:
            try:
                await send_now_playing_notification(channel, session)
                notified_sessions.add(session_id)
            except Exception as e:
                print(f"Error sending notification for session {session_id}: {e}")

    # Clean up old sessions from our notified set by reassigning the global variable
    notified_sessions = notified_sessions.intersection(current_session_ids)


async def send_now_playing_notification(channel, session):
    """Formats and sends a 'Now Playing' notification to the specified channel."""
    user_name = session['UserName']
    item = session['NowPlayingItem']
    item_id = item['Id']

    title = item.get('Name', 'Unknown Title')
    media_type = item.get('Type', 'Unknown')

    # Create a rich embed for the notification
    embed = discord.Embed(
        title=f"▶️ Now Playing: {title}",
        color=discord.Color.blue()
    )

    if media_type == 'Episode' and 'SeriesName' in item:
        season_name = item.get('SeasonName', '')
        embed.description = f"From **{item['SeriesName']}**"
        if season_name:
             embed.description += f" - {season_name}"

    embed.set_thumbnail(url=jellyfin_client.get_item_image_url(item_id, "Primary"))
    embed.set_footer(text=f"{user_name} started watching.")

    await channel.send(embed=embed)


@bot.event
async def on_ready():
    """Event handler for when the bot has connected to Discord."""
    print(f'We have logged in as {bot.user}')
    if jellyfin_client:
        check_jellyfin_sessions.start()
        check_recently_added.start()

def main():
    """Main function to run the bot."""
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable not set.")
        return

    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()
