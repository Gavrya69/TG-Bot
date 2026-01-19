import yt_dlp
import os


OUTPUT_PATH = r'.\temp'
MAX_SIZE = 50 * 1024 * 1024 # 50 MB


def download_youtube(url):
    
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
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
        print(f'[{__name__}] Searching for the best format: {url}')
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            best_formats = []
            for f in formats:
                file_size = f.get('filesize') or f.get('filesize_approx')
                if not file_size:
                    continue
                if file_size <= MAX_SIZE:
                    best_formats.append((file_size, f))

            if not best_formats:
                print(f'[{__name__}] Format not found: {url}')
                return None
            
            selected_format = max(best_formats, key=lambda x: x[0])[1]
            file_size = selected_format.get('filesize') or selected_format.get('filesize_approx')
            file_height = selected_format.get('height')
            ydl_opts['format'] = selected_format['format_id']
            
        print(f'[{__name__}] Downloading {(file_size/1024/1024):.3} MB ({file_height}p)): {url}')
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        print(f'[{__name__}] Successfully downloaded {filename}: {url}')
        return filename

    except yt_dlp.utils.DownloadError as e:
        print(f'[{__name__}] Download error: {e}')
        return None
