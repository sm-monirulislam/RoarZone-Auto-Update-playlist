import aiohttp
import asyncio
import json
import time
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO)

INPUT_API = "https://sm-iptv-channel-data.pages.dev/RoarZone_id.json"

M3U_FILE = "RoarZone.m3u"
JSON_DATA_FILE = "RoarZone_data.json"

BASE_URL = "https://tv.roarzone.info"
API_PATH = "/api/android/stream.php"

BD_TZ = timezone(timedelta(hours=6))

def load_old_ids():
    if not os.path.exists(JSON_DATA_FILE):
        return {}
    with open(JSON_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {ch["title"]: ch["id"] for ch in data.get("response", [])}

async def fetch_stream(session, ch, sem, old_ids):
    async with sem:
        try:
            params = {"channel": ch["stream_name"]}
            headers = {
                "User-Agent": "RoarZoneTV/1.0.1 (Android 9)",
                "Referer": BASE_URL,
                "Origin": BASE_URL,
                "X-App-Build": "2",
                "X-App-Package": "info.roarzone.tv",
                "X-App-Version": "1.0.1",
                "X-Android-SDK": "28",
                "X-Request-Timestamp": str(int(time.time()))
            }

            async with session.get(BASE_URL + API_PATH, params=params, headers=headers) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                if not data.get("success"):
                    return None

                ch["url"] = data["url"].replace("\\/", "/")
                ch["id"] = old_ids.get(ch["title"]) or str(uuid.uuid4())
                return ch

        except Exception as e:
            logging.error(f'{ch.get("title")} -> {e}')
            return None

async def main():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.get(INPUT_API) as r:
            cfg = await r.json()

        channels = cfg.get("channels", [])
        sem = asyncio.Semaphore(60)
        old_ids = load_old_ids()

        tasks = [fetch_stream(session, ch, sem, old_ids) for ch in channels]
        results = [r for r in await asyncio.gather(*tasks) if r]

    # =========================
    # WRITE M3U (WITH HEADER)
    # =========================
    now_bd = datetime.now(BD_TZ).strftime("%Y-%m-%d %H:%M:%S")

    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#=================================\n")
        f.write("# 🖥️ Developed by: Monirul Islam\n")
        f.write("# 🔗 Telegram: https://t.me/monirul_Islam_SM\n")
        f.write(f"# 🕒 Last Updated: {now_bd} (BD Time)\n")
        f.write(f"# 📺 Channels Count: {len(results)}\n")
        f.write("#=================================\n\n")

        for ch in results:
            f.write(
                f'#EXTINF:-1 group-title="{ch["category"]}" '
                f'tvg-logo="{ch["logo"]}",{ch["title"]}\n'
            )
            f.write(ch["url"] + "\n")

    # =========================
    # WRITE JSON
    # =========================
    output = {
        "status": "success",
        "name": "RoarZone Live Channels",
        "owner": "Monirul Islam",
        "channels_amount": len(results),
        "Last_update": datetime.now(BD_TZ).strftime("%Y-%m-%d"),
        "response": [
            {
                "id": ch["id"],
                "title": ch["title"],
                "logo": ch["logo"],
                "url": ch["url"],
                "category": ch["category"]
            } for ch in results
        ]
    }

    with open(JSON_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("DONE")

if __name__ == "__main__":
    asyncio.run(main())