import yt_dlp
import os

OUTPUT_PATH = r'.\temp'

def download_youtube(url):
    ydl_opts = {
        'format': 'bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]',
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'extractor_args': {
            'youtube': ['player_client=android']
        },
        'quiet': False
    }

    try:
        print(f'Preparing to download: {url}')

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        width = info.get('width')
        height = info.get('height')

        print(f'Successfully downloaded: {filename}')
        return filename, width, height

    except yt_dlp.utils.DownloadError as e:
        print(f'Download error: {e}')
        return None
