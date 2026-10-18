import logging
import os
import shutil
from enum import Enum

import yt_dlp

from services.cookies import get_cookies_path

logger = logging.getLogger(__name__)

OUTPUT_PATH = "./temp"
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024
AUDIO_BITRATE = "192"  # in kbps

BASE_OPTS = {
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "outtmpl": os.path.join(OUTPUT_PATH, "%(title)s [%(id)s].%(ext)s"),
    "extractor_args": {},
    "verbose": True,
    # Required for modern YouTube JS (n/sig) challenges.
    "remote_components": {"ejs:github"},
}

def _yt_box(limit: int) -> str:
    """Return the best stream that fits in a square of this many pixels."""
    return (
        f"bv*[width<={limit}][height<={limit}]+ba/"
        f"b[width<={limit}][height<={limit}]"
    )


# Highest frame first, any codec. 1440p vertical is 1440x2560, so a height cap drops it.
# Later steps only run when the file is over 50 MB.
YT_FORMATS = [
    "bv*+ba/b",
    _yt_box(2560),
    _yt_box(1920),
    _yt_box(1280),
    _yt_box(854),
    _yt_box(640),
]
VIDEO_PLATFORM_OPTIONS = {
    "tt": [
        "mp4[height<=1080]",
        "mp4[height<=720]",
        "mp4[height<=480]",
        "mp4[height<=360]",
        "best",
    ],
}

AUDIO_PLATFORM_OPTIONS = {
    "yt": "bestaudio[ext=m4a]/bestaudio/best",
    "tt": "bestaudio/best",
}


class SelectStatus(str, Enum):
    OK = "ok"
    TOO_LARGE = "too_large"
    FAILED = "failed"


def _video_format_ladder(platform: str, _url: str) -> list[str]:
    if platform == "yt":
        return YT_FORMATS
    return VIDEO_PLATFORM_OPTIONS[platform]


def _extractor_args_for(platform: str, *, use_cookies: bool = False) -> dict:
    if platform != "yt":
        return {}
    # android_vr rejects account cookies. Default tv/web clients now return
    # SABR-only streams and fail age-restricted videos with "page needs to be
    # reloaded". mweb and web_creator still give a direct mp4 when cookies are set.
    if use_cookies:
        return {"youtube": {"player_client": ["mweb", "web_creator"]}}
    # android/web/tv currently expose only a 360p URL (SABR). android_vr
    # still returns a direct 1080p H.264 URL without a PO token.
    return {"youtube": {"player_client": ["android_vr"]}}


def _build_opts(platform: str, *, use_cookies: bool = False) -> dict:
    opts = {
        **BASE_OPTS,
        "extractor_args": _extractor_args_for(platform, use_cookies=use_cookies),
    }
    if platform == "yt" and shutil.which("node"):
        opts["js_runtimes"] = {"node": {}}

    if use_cookies:
        cookie_path = get_cookies_path()
        if cookie_path.is_file():
            opts["cookiefile"] = str(cookie_path)
        else:
            logger.warning("use_cookies=True but cookies file missing: %s", cookie_path)

    return opts


def _format_id_from_selection(formats: list[dict]) -> str:
    """Join multi-stream selection into yt-dlp format id (e.g. 136+140)."""
    return "+".join(f["format_id"] for f in formats if f.get("format_id"))


def _selection_size(formats: list[dict]) -> int | None:
    total = 0
    known = False
    for f in formats:
        size = f.get("filesize") or f.get("filesize_approx")
        if size:
            total += size
            known = True
    return total if known else None


def _selection_vcodec(formats: list[dict]) -> str | None:
    for fmt in formats:
        vcodec = fmt.get("vcodec")
        if vcodec and vcodec != "none":
            return vcodec
    return None


def _selection_resolution(formats: list[dict]) -> str | None:
    for f in formats:
        if f.get("vcodec") and f.get("vcodec") != "none":
            return f.get("resolution") or (
                f"{f['height']}p" if f.get("height") else None
            )
    return formats[0].get("resolution") if formats else None


def select_video_format(
    url: str,
    platform: str,
    *,
    use_cookies: bool = False,
) -> tuple[dict | None, SelectStatus]:
    logger.debug(
        "Searching for the best video format (cookies=%s): %s",
        use_cookies,
        url,
    )

    saw_extract_ok = False
    last_error: Exception | None = None

    for fmt in _video_format_ladder(platform, url):
        ydl_opts = {
            **_build_opts(platform, use_cookies=use_cookies),
            "format": fmt,
            "merge_output_format": "mp4",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                selected = list(ydl.format_selector(info))
                if not selected:
                    continue

                saw_extract_ok = True
                file_size = _selection_size(selected)
                file_resolution = _selection_resolution(selected)
                format_id = _format_id_from_selection(selected)

                chosen = {
                    "format_id": format_id,
                    "resolution": file_resolution,
                    "filesize": file_size,
                    "vcodec": _selection_vcodec(selected),
                }
                if file_size and file_size <= MAX_VIDEO_SIZE:
                    return chosen, SelectStatus.OK

                if file_size is None:
                    # Size unknown — allow download attempt at this quality.
                    return chosen, SelectStatus.OK

                logger.warning(
                    "Too big video (%s - %.3f MB, fmt=%s): %s",
                    file_resolution,
                    file_size / 1024 / 1024,
                    format_id,
                    url,
                )

        except yt_dlp.utils.DownloadError as exc:
            last_error = exc
            msg = str(exc).lower()
            # Format missing for this selector — try next ladder step.
            if "requested format is not available" in msg or "format is not available" in msg:
                logger.debug("Format not available (%s), trying next: %s", fmt, url)
                continue
            # Auth / extract failures — no point trying other format strings.
            logger.exception("Video selecting error (cookies=%s):", use_cookies)
            return None, SelectStatus.FAILED
        except Exception:
            logger.exception("Unexpected video select error (cookies=%s):", use_cookies)
            return None, SelectStatus.FAILED

    if saw_extract_ok:
        return None, SelectStatus.TOO_LARGE

    if last_error is not None:
        logger.error("Video selecting failed (cookies=%s): %s", use_cookies, last_error)
    return None, SelectStatus.FAILED


def select_audio_info(
    url: str,
    platform: str,
    *,
    use_cookies: bool = False,
) -> tuple[dict | None, SelectStatus]:
    logger.debug(
        "Searching for the best audio format (cookies=%s): %s",
        use_cookies,
        url,
    )

    try:
        ydl_opts = {
            **_build_opts(platform, use_cookies=use_cookies),
            "format": AUDIO_PLATFORM_OPTIONS[platform],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            requested_formats = info.get("requested_formats")
            audio_info = requested_formats[-1] if requested_formats else info

            file_size = audio_info.get("filesize") or audio_info.get("filesize_approx")

            if file_size and file_size <= MAX_AUDIO_SIZE:
                return audio_info, SelectStatus.OK

            if file_size:
                logger.warning(
                    "Too big audio (%.3f MB): %s",
                    file_size / 1024 / 1024,
                    url,
                )
                return None, SelectStatus.TOO_LARGE

            return audio_info, SelectStatus.OK

    except yt_dlp.utils.DownloadError:
        logger.exception("Audio selecting error (cookies=%s):", use_cookies)
        return None, SelectStatus.FAILED


def download_video(
    url: str,
    selected_format: dict,
    platform: str,
    *,
    use_cookies: bool = False,
) -> str | None:
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    ydl_opts = {
        **_build_opts(platform, use_cookies=use_cookies),
        "format": selected_format["format_id"],
        "merge_output_format": "mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # After merge, extension is often mp4 even if prepare_filename used other ext.
            base, ext = os.path.splitext(filename)
            if ext.lower() != ".mp4":
                mp4_name = base + ".mp4"
                if os.path.exists(mp4_name):
                    filename = mp4_name
    except yt_dlp.utils.DownloadError:
        logger.exception(
            "Video download error from %s (cookies=%s)",
            platform,
            use_cookies,
        )
        return None

    logger.debug("Successfully downloaded video %s: %s", filename, url)
    return filename


def download_audio(
    url: str,
    platform: str,
    *,
    use_cookies: bool = False,
) -> str | None:
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    ydl_opts = {
        **_build_opts(platform, use_cookies=use_cookies),
        "format": AUDIO_PLATFORM_OPTIONS[platform],
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": AUDIO_BITRATE,
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            original_filename = ydl.prepare_filename(info)
            filename = os.path.splitext(original_filename)[0] + ".mp3"
    except yt_dlp.utils.DownloadError:
        logger.exception(
            "Audio download error from %s (cookies=%s)",
            platform,
            use_cookies,
        )
        return None

    logger.debug("Successfully downloaded audio %s: %s", filename, url)
    return filename
