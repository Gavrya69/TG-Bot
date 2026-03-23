import logging
import os

import yt_dlp

logger = logging.getLogger(__name__)

OUTPUT_PATH = r".\temp"
MAX_SIZE = 50 * 1024 * 1024  # 50 MB

BASE_OPTS = {
    "merge_output_format": "mp4",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "outtmpl": os.path.join(OUTPUT_PATH, "%(title)s [%(id)s].%(ext)s"),
    "extractor_args": {},
    "verbose": True,
}

PLATFORM_OPTIONS = {
    "yt": [
        'bv*[ext=mp4][height<=1080][vcodec~="^avc"]+ba[ext=m4a]/b[ext=mp4][height<=1080]',
        'bv*[ext=mp4][height<=720][vcodec~="^avc"]+ba[ext=m4a]/b[ext=mp4][height<=720]',
        'bv*[ext=mp4][height<=480][vcodec~="^avc"]+ba[ext=m4a]/b[ext=mp4][height<=480]',
        'bv*[ext=mp4][height<=360][vcodec~="^avc"]+ba[ext=m4a]/b[ext=mp4][height<=360]',
    ],
    "tt": [
        "mp4[height<=1080]",
        "mp4[height<=720]",
        "mp4[height<=480]",
        "mp4[height<=360]",
    ],
}


def select_format(url, platform):
    logger.debug("Searching for the best format: %s", url)

    if platform == "yt":
        BASE_OPTS["extractor_args"] = {"youtube": ["player_client=android"]}
    elif platform == "tt":
        BASE_OPTS["extractor_args"] = {}

    try:
        for format in PLATFORM_OPTIONS[platform]:
            ydl_opts = {**BASE_OPTS, "format": format}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                selected_format = list(ydl.format_selector(info))[0]
                file_size = selected_format.get("filesize") or selected_format.get("filesize_approx")
                file_resolution = selected_format.get("resolution")

                if file_size and file_size <= MAX_SIZE:
                    return selected_format

                if file_size and file_resolution:
                    logger.warning("Too big file (%s - %.3f): %s", file_resolution, file_size / 1024 / 1024, url)
    except yt_dlp.utils.DownloadError:
        logger.exception("Selecting error:")


def download_video(url, selected_format, platform) -> str | None:
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    ydl_opts = {**BASE_OPTS, "format": selected_format["format_id"]}

    if platform == "yt":
        ydl_opts["extractor_args"] = {"youtube": ["player_client=android"]}
    elif platform == "tt":
        ydl_opts["extractor_args"] = {}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except yt_dlp.utils.DownloadError:
        logger.exception("Download error from %s", platform)
        return None

    logger.debug("Successfully downloaded %s: %s", filename, url)
    return filename
