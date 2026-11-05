
import asyncio
import glob
import aiohttp
import ollama
from nio import AsyncClient, MatrixRoom, RoomMessageText, InviteMemberEvent

HOMESERVER = "https://matrix.org"
BOT_USERNAME = "llamaa_bot"
BOT_PASSWORD = "your_bot_password_here"  
MODEL = "llama3.2"

BOT_USER_ID = f"@{BOT_USERNAME}:matrix.org"
client = AsyncClient(HOMESERVER, BOT_USER_ID)
ollama_client = ollama.AsyncClient()


def load_documents():
    parts = []
    for path in sorted(glob.glob("docs/*.txt") + glob.glob("docs/*.md")):
        with open(path, "r", encoding="utf-8") as f:
            parts.append(f"--- {path} ---\n{f.read()}")
    return "\n\n".join(parts)


DOCUMENTS = load_documents()


async def ask_ollama(question: str) -> str:
    try:
        response = await ollama_client.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant for workplace procedures. "
                        "Answer ONLY using the documents below. "
                        "If the answer is not in the documents, reply exactly: "
                        "\"I don't know. That isn't covered in the documents.\"\n\n"
                        f"DOCUMENTS:\n{DOCUMENTS}"
                    ),
                },
                {"role": "user", "content": question},
            ],
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Sorry, I couldn't reach the AI model ({e}). Is Ollama running?"


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
    answer = await ask_ollama(event.body)
    await client.room_send(
        room_id=room.room_id,
        message_type="m.room.message",
        content={"msgtype": "m.text", "body": answer},
    )


async def main():
    data = await manual_login()
    client.restore_login(BOT_USER_ID, data["device_id"], data["access_token"])
    print("Logged in as", BOT_USER_ID)
    print(f"Loaded documents ({len(DOCUMENTS)} characters)")

    await client.sync(timeout=30000, full_state=True)
    client.add_event_callback(on_invite, InviteMemberEvent)
    client.add_event_callback(on_message, RoomMessageText)
    print("Bot is running.")
    await client.sync_forever(timeout=30000)


asyncio.run(main())