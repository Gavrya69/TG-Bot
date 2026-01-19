import yt_dlp
import os

OUTPUT_PATH = r'.\temp'

def download_youtube(url):
    
    if not os.path.exists(OUTPUT_PATH):
        os.mkdirs(OUTPUT_PATH, exist_ok=True)
        print(f'[{__name__}] Created folder {OUTPUT_PATH}')
    
    ydl_opts = {
        'format': (
            'bv*[ext=mp4][height<=720][vcodec~="^avc"]+ba[ext=m4a]'
            '/b[ext=mp4][height<=720]'
        ),
        'noplaylist': True,
        'extractor_args': {
            'youtube': ['player_client=android']
        },
        'quiet': True,
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s')
    }

    try:
        print(f'[{__name__}] Preparing to download: {url}')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        width = info.get('width')
        height = info.get('height')

        print(f'[{__name__}] Successfully downloaded: {filename} ({height}p)')
        return filename

    except yt_dlp.utils.DownloadError as e:
        print(f'[{__name__}] Download error: {e}')
        return None
