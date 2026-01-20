import yt_dlp
import os


OUTPUT_PATH = r'.\temp'
MAX_SIZE = 50 * 1024 * 1024 # 50 MB

YT_OPTS_LIST = [
    {
        'format': 'bv*[ext=mp4][height<=1080][vcodec~="^avc"]+ba[ext=m4a]/b[ext=mp4][height<=1080]',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': ['player_client=android']},
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s'),
    },
    {
        'format': 'bv*[ext=mp4][height<=720][vcodec~="^avc"]+ba[ext=m4a]/b[ext=mp4][height<=720]',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': ['player_client=android']},
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s'),
    },
    {
        'format': 'bv*[ext=mp4][height<=480][vcodec~="^avc"]+ba[ext=m4a]/b[ext=mp4][height<=480]',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': ['player_client=android']},
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s'),
    },
    {
        'format': 'bv*[ext=mp4][height<=360][vcodec~="^avc"]+ba[ext=m4a]/b[ext=mp4][height<=360]',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': ['player_client=android']},
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s'),
    },
]

TT_OPTS_LIST = [
    {
        'format': 'mp4[height<=1080]',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s'),
    },
    {
        'format': 'mp4[height<=720]',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s'),
    },
    {
        'format': 'mp4[height<=480]',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s'),
    },
    {
        'format': 'mp4[height<=360]',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(OUTPUT_PATH, '%(title)s [%(id)s].%(ext)s'),
    },
]


def select_format_youtube(url):
    try:
        print(f'[{__name__}] Searching for the best format: {url}')
        
        for ydl_opts in YT_OPTS_LIST:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                selected_format = list(ydl.format_selector(info))[0]
                file_size = selected_format.get('filesize') or selected_format.get('filesize_approx')
                file_resolution = selected_format.get('resolution')
                
                if file_size and file_size <= MAX_SIZE:
                    return selected_format
                
                if file_size and file_resolution:
                    print(f'[{__name__}] Too big file ({file_resolution} - {(file_size/1024/1024):.3}): {url}')
        return None
                    
    except yt_dlp.utils.DownloadError as e:
        print(f'[{__name__}] Selecting error: {e}')
        return None     


def select_format_tiktok(url):
    try:
        print(f'[{__name__}] Searching for the best format: {url}')
        
        for ydl_opts in YT_OPTS_LIST:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                selected_format = list(ydl.format_selector(info))[0]
                file_size = selected_format.get('filesize') or selected_format.get('filesize_approx')
                file_resolution = selected_format.get('resolution')
                
                if file_size and file_size <= MAX_SIZE:
                    return selected_format
                
                if file_size and file_resolution:
                    print(f'[{__name__}] Too big file ({(file_size/1024/1024):.3} mb - {file_resolution}): {url}')
        return None
                    
    except yt_dlp.utils.DownloadError as e:
        print(f'[{__name__}] Selecting error: {e}')
        return None           
    

def download_youtube(url, selected_format):
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    ydl_opts = YT_OPTS_LIST[0]
    ydl_opts['format'] = selected_format['format_id']

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        print(f'[{__name__}] Successfully downloaded {filename}: {url}')
        return filename

    except yt_dlp.utils.DownloadError as e:
        print(f'[{__name__}] Download error: {e}')
        return None


def download_tiktok(url):
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    ydl_opts = YT_OPTS_LIST[0]
    ydl_opts['format'] = format['format_id']
    
    try:
        with yt_dlp.YoutubeDL(TT_OPTS_LIST) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        print(f'[{__name__}] Successfully downloaded {filename}: {url}')
        return filename

    except yt_dlp.utils.DownloadError as e:
        print(f'[{__name__}] Download error: {e}')
        return None
