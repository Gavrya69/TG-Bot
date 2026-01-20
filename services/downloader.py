import yt_dlp
import os


OUTPUT_PATH = r'.\temp'
MAX_SIZE = 50 * 1024 * 1024 # 50 MB

YT_OPTS = {
        'format': (
            'bv*[ext=mp4][height<=720][vcodec~="^avc"]+ba[ext=m4a]'
            '/b[ext=mp4][height<=720]'
        ),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'extractor_args': {
            'youtube': ['player_client=android']
        },
        'quiet': True,
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s')
    }
TT_OPTS = {
        'format': 'mp4',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s'),
        # 'http_headers': {
        #     'User-Agent': (
        #         'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        #         'AppleWebKit/537.36 (KHTML, like Gecko) '
        #         'Chrome/120.0.0.0 Safari/537.36'
        #     )
        # },
    }


def check_youtube(url):
    try:
        print(f'[{__name__}] Searching for the best format: {url}')
        
        with yt_dlp.YoutubeDL(YT_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            best_formats = []
            for f in formats:
                if f.get('ext') != 'mp4' or f.get('vcodec') == 'none':
                    continue
                file_size = f.get('filesize') or f.get('filesize_approx')
                if file_size and file_size <= MAX_SIZE:
                    best_formats.append((file_size, f))

            if not best_formats:
                print(f'[{__name__}] Format not found: {url}')
                return None
            
            print(f'[{__name__}] Founded the best format: {url}')
            selected_format = max(best_formats, key=lambda x: x[0])[1]
            return selected_format
        
    except yt_dlp.utils.DownloadError as e:
        print(f'[{__name__}] Checking error {e}: {url}')
        return None


def download_youtube(url, selected_format):
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    ydl_opts = YT_OPTS
    ydl_opts['format'] = selected_format['format_id']
    
    file_size = (selected_format.get('filesize') or selected_format.get('filesize_approx'))/1024/1024
    file_height = selected_format.get('height')

    print(f'[{__name__}] Downloading {file_size:.3} mb ({file_height}p): {url}')
    try:
        with yt_dlp.YoutubeDL(YT_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        print(f'[{__name__}] Successfully downloaded {filename}: {url}')
        return filename

    except yt_dlp.utils.DownloadError as e:
        print(f'[{__name__}] Download error: {e}')
        return None


def check_tiktok(url):
    pass


def download_tiktok(url):
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    ydl_opts = TT_OPTS
    ydl_opts['format'] = format['format_id']
    
    file_size = (format.get('filesize') or format.get('filesize_approx'))/1024/1024
    file_height = format.get('height')

    print(f'[{__name__}] Downloading {file_size:.3} mb ({file_height}p): {url}')
    try:
        with yt_dlp.YoutubeDL(YT_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        print(f'[{__name__}] Successfully downloaded {filename}: {url}')
        return filename

    except yt_dlp.utils.DownloadError as e:
        print(f'[{__name__}] Download error: {e}')
        return None
