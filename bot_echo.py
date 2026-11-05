import asyncio
import aiohttp
from nio import AsyncClient, MatrixRoom, RoomMessageText, InviteMemberEvent

HOMESERVER = "https://matrix.org"
BOT_USERNAME = "llamaa_bot"        
BOT_PASSWORD = "EazeZone1"

BOT_USER_ID = f"@{BOT_USERNAME}:matrix.org"
client = AsyncClient(HOMESERVER, BOT_USER_ID)


async def manual_login():
    url = f"{HOMESERVER}/_matrix/client/v3/login"
    payload = {
        "type": "m.login.password",
        "identifier": {"type": "m.id.user", "user": BOT_USERNAME},
        "password": BOT_PASSWORD,
        "initial_device_display_name": "ollama-bot",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"Login failed ({resp.status}): {data}")
            return data


async def on_invite(room: MatrixRoom, event: InviteMemberEvent):
    await client.join(room.room_id)
    print(f"Joined room {room.room_id}")


async def on_message(room: MatrixRoom, event: RoomMessageText):
    if event.sender == client.user_id:
        return
    print(f"{event.sender}: {event.body}")
    await client.room_send(
        room_id=room.room_id,
        message_type="m.room.message",
        content={"msgtype": "m.text", "body": f"You said: {event.body}"},
    )


async def main():
    data = await manual_login()
    client.restore_login(BOT_USER_ID, data["device_id"], data["access_token"])
    print("Logged in as", BOT_USER_ID)

    await client.sync(timeout=30000, full_state=True)  # skip old messages
    client.add_event_callback(on_invite, InviteMemberEvent)
    client.add_event_callback(on_message, RoomMessageText)
    print("Bot is running. Now invite it to a room.")
    await client.sync_forever(timeout=30000)


asyncio.run(main())