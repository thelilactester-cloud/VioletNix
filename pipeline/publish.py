"""Post to YouTube, TikTok (as a draft) and Facebook Reels. Skips any platform without credentials.

TikTok: the API cannot attach a library sound, so the video goes to your TikTok *drafts*;
open the app, tap "Add sound", pick a trending track and publish.
Instagram and Pinterest are posted by hand from schedule.csv.
"""
import os

import requests

import config

FB_API = "https://graph.facebook.com/v21.0"


def youtube(video, title, description, tags):
    if not (config.YT_CLIENT_ID and config.YT_CLIENT_SECRET and config.YT_REFRESH_TOKEN):
        return None
    tok = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": config.YT_CLIENT_ID, "client_secret": config.YT_CLIENT_SECRET,
        "refresh_token": config.YT_REFRESH_TOKEN, "grant_type": "refresh_token"}).json()["access_token"]
    meta = {"snippet": {"title": title[:100], "description": description, "tags": tags,
                        "categoryId": "27"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": True}}
    size = os.path.getsize(video)
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos"
                         "?uploadType=resumable&part=snippet,status", timeout=30, json=meta,
                         headers={"Authorization": f"Bearer {tok}", "X-Upload-Content-Type": "video/mp4",
                                  "X-Upload-Content-Length": str(size)})
    init.raise_for_status()
    with open(video, "rb") as f:
        up = requests.put(init.headers["Location"], data=f, timeout=600,
                          headers={"Content-Type": "video/mp4", "Content-Length": str(size)})
    up.raise_for_status()
    return up.json()["id"]


def tiktok_draft(video):
    if not config.TIKTOK_ACCESS_TOKEN:
        return None
    size = os.path.getsize(video)
    r = requests.post("https://open.tiktokapis.com/v2/post/publish/inbox/video/init/", timeout=30,
                      headers={"Authorization": f"Bearer {config.TIKTOK_ACCESS_TOKEN}"},
                      json={"source_info": {"source": "FILE_UPLOAD", "video_size": size,
                                            "chunk_size": size, "total_chunk_count": 1}})
    r.raise_for_status()
    data = r.json()["data"]
    with open(video, "rb") as f:
        up = requests.put(data["upload_url"], data=f, timeout=600, headers={
            "Content-Type": "video/mp4", "Content-Length": str(size),
            "Content-Range": f"bytes 0-{size - 1}/{size}"})
    up.raise_for_status()
    return data["publish_id"]


def facebook_reel(video, description):
    if not (config.FB_PAGE_ID and config.FB_PAGE_TOKEN):
        return None
    base = f"{FB_API}/{config.FB_PAGE_ID}/video_reels"
    start = requests.post(base, timeout=30, data={"upload_phase": "start",
                                                  "access_token": config.FB_PAGE_TOKEN})
    start.raise_for_status()
    info = start.json()
    size = os.path.getsize(video)
    with open(video, "rb") as f:
        up = requests.post(info["upload_url"], data=f, timeout=600, headers={
            "Authorization": f"OAuth {config.FB_PAGE_TOKEN}", "offset": "0", "file_size": str(size)})
    up.raise_for_status()
    fin = requests.post(base, timeout=60, data={
        "upload_phase": "finish", "video_id": info["video_id"], "video_state": "PUBLISHED",
        "description": description, "access_token": config.FB_PAGE_TOKEN})
    fin.raise_for_status()
    return info["video_id"]
