import logging
import os

import yt_dlp

logger = logging.getLogger(__name__)

OUTPUT_PATH = "./temp"
MAX_VIDEO_SIZE = 50 * 1024 * 1024      # 50 MB
MAX_AUDIO_SIZE = 50 * 1024 * 1024     
AUDIO_BITRATE = "192" # in kbps

BASE_OPTS = {
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "outtmpl": os.path.join(OUTPUT_PATH, "%(title)s [%(id)s].%(ext)s"),
    "extractor_args": {},
    "verbose": True,
}

VIDEO_PLATFORM_OPTIONS = {
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

AUDIO_PLATFORM_OPTIONS = {
    "yt": "bestaudio[ext=m4a]/bestaudio/best",
    "tt": "bestaudio/best",
}


def _extractor_args_for(platform: str) -> dict:
    if platform == "yt":
        return {"youtube": ["player_client=android"]}
    if platform == "tt":
        return {}
    return {}


def select_video_format(url: str, platform: str):
    logger.debug("Searching for the best video format: %s", url)

    try:
        for fmt in VIDEO_PLATFORM_OPTIONS[platform]:
            ydl_opts = {
                **BASE_OPTS,
                "format": fmt,
                "merge_output_format": "mp4",
                "extractor_args": _extractor_args_for(platform),
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                selected_format = list(ydl.format_selector(info))[0]

                file_size = selected_format.get("filesize") or selected_format.get("filesize_approx")
                file_resolution = selected_format.get("resolution")

                if file_size and file_size <= MAX_VIDEO_SIZE:
                    return selected_format

                if file_size and file_resolution:
                    logger.warning(
                        "Too big video (%s - %.3f MB): %s",
                        file_resolution,
                        file_size / 1024 / 1024,
                        url,
                    )

        return None

    except yt_dlp.utils.DownloadError:
        logger.exception("Video selecting error:")
        return None


def select_audio_info(url: str, platform: str):
    logger.debug("Searching for the best audio format: %s", url)

    try:
        ydl_opts = {
            **BASE_OPTS,
            "format": AUDIO_PLATFORM_OPTIONS[platform],
            "extractor_args": _extractor_args_for(platform),
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            requested_formats = info.get("requested_formats")
            audio_info = requested_formats[-1] if requested_formats else info

            file_size = audio_info.get("filesize") or audio_info.get("filesize_approx")

            if file_size and file_size <= MAX_AUDIO_SIZE:
                return audio_info

            if file_size:
                logger.warning("Too big audio (%.3f MB): %s", file_size / 1024 / 1024, url)

            return audio_info if file_size is None else None

    except yt_dlp.utils.DownloadError:
        logger.exception("Audio selecting error:")
        return None


def download_video(url: str, selected_format, platform: str) -> str | None:
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    ydl_opts = {
        **BASE_OPTS,
        "format": selected_format["format_id"],
        "merge_output_format": "mp4",
        "extractor_args": _extractor_args_for(platform),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except yt_dlp.utils.DownloadError:
        logger.exception("Video download error from %s", platform)
        return None

    logger.debug("Successfully downloaded video %s: %s", filename, url)
    return filename


def download_audio(url: str, platform: str) -> str | None:
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    ydl_opts = {
        **BASE_OPTS,
        "format": AUDIO_PLATFORM_OPTIONS[platform],
        "extractor_args": _extractor_args_for(platform),
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
        logger.exception("Audio download error from %s", platform)
        return None

    logger.debug("Successfully downloaded audio %s: %s", filename, url)
    return filename