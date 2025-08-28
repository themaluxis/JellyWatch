# Jellyfin Discord Bot

A Discord bot for monitoring a Jellyfin media server. It provides real-time notifications for playback activity and newly added media, and allows users to check the current server status.

## Features

- **Now Playing Notifications:** Announces in a specific channel when a user starts watching a movie or episode.
- **Recently Added Announcer:** Announces when new movies or episodes are added to the library.
- **Live Activity Stats:** A `!stats` command to show a summary of all current playback sessions.
- **Dockerized:** Easy to deploy and manage using Docker.

## Setup

There are two ways to run the bot: using Docker (recommended for servers like Unraid) or running it directly with Python.

### Docker (Recommended)

1.  **Build the Docker image:**
    ```bash
    docker build -t jellyfin-discord-bot .
    ```

2.  **Run the Docker container:**
    You will need to provide the configuration as environment variables (`-e`) in the `docker run` command.

    ```bash
    docker run -d \
      --name jellyfin-bot \
      -e DISCORD_BOT_TOKEN="your_discord_bot_token" \
      -e DISCORD_CHANNEL_ID="your_discord_channel_id" \
      -e JELLYFIN_SERVER_URL="https://your_jellyfin_server_url" \
      -e JELLYFIN_API_KEY="your_jellyfin_api_key" \
      -e JELLYFIN_USER_ID="your_jellyfin_user_id" \
      --restart unless-stopped \
      jellyfin-discord-bot
    ```

### Python (Manual Setup)

1.  **Clone or download the code.**

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set environment variables:**
    Create a `.env` file in the root of the project and add the required variables (see Configuration section below). Alternatively, you can set them directly in your shell.

4.  **Run the bot:**
    ```bash
    python bot.py
    ```

## Configuration

The bot is configured entirely through environment variables.

| Variable              | Description                                                                                                                               | Required |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `DISCORD_BOT_TOKEN`   | The token for your Discord bot.                                                                                                           | **Yes**  |
| `DISCORD_CHANNEL_ID`  | The ID of the Discord channel where notifications will be sent.                                                                             | **Yes**  |
| `JELLYFIN_SERVER_URL` | The full URL of your Jellyfin server (e.g., `http://192.168.1.100:8096`).                                                                    | **Yes**  |
| `JELLYFIN_API_KEY`    | An API key generated from your Jellyfin dashboard (Admin Dashboard > API Keys).                                                               | **Yes**  |
| `JELLYFIN_USER_ID`    | The ID of a Jellyfin user. This is used by the "Recently Added" announcer. You can find this ID by navigating to a user's profile and copying it from the URL. | **Yes**  |

## Usage

### Commands

-   `!stats`: Shows a summary of all current playback activity on the Jellyfin server.
