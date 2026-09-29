"""Canonical record kinds shared by collectors, JEV, BI and graph."""
from __future__ import annotations

from enum import Enum


class RecordKind(str, Enum):
    PROFILE = "PROFILE"
    POST = "POST"
    COMMENT = "COMMENT"
    REPLY = "REPLY"
    MEDIA = "MEDIA"
    OWNER_EXPORT_CONTAINER = "OWNER_EXPORT_CONTAINER"
    UNKNOWN = "UNKNOWN"


POST_TYPES = {
    "post", "public_post", "social_post", "public_post_snapshot", "video",
    "video_snapshot", "public_video_metadata", "public_photo_metadata", "media",
    "owner_export_post",
}
PROFILE_TYPES = {"profile", "profile_snapshot", "public_profile_snapshot", "page_snapshot"}
COMMENT_TYPES = {"comment", "owner_export_comment"}
REPLY_TYPES = {"reply", "owner_export_reply"}
MEDIA_TYPES = {"media_asset", "owner_export_media"}


def canonical_record_kind(source_type: str) -> RecordKind:
    value = str(source_type or "").strip().lower()
    if value in POST_TYPES:
        return RecordKind.POST
    if value in PROFILE_TYPES:
        return RecordKind.PROFILE
    if value in COMMENT_TYPES or "comment" in value:
        return RecordKind.COMMENT
    if value in REPLY_TYPES or "reply" in value:
        return RecordKind.REPLY
    if value in MEDIA_TYPES:
        return RecordKind.MEDIA
    if value == "owner_export":
        return RecordKind.OWNER_EXPORT_CONTAINER
    return RecordKind.UNKNOWN
