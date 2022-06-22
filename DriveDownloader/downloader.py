#############################################
#  Author: Hongwei Fan                      #
#  E-mail: hwnorm@outlook.com               #
#  Homepage: https://github.com/hwfan       #
#############################################
from DriveDownloader.netdrives import get_session
from DriveDownloader.utils import judge_session, MultiThreadDownloader, judge_scheme
import argparse
import os
import sys
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

MAJOR_VERSION = 1
MINOR_VERSION = 6
POST_VERSION = 0
__version__ = "{MAJOR_VERSION}.{MINOR_VERSION}.{POST_VERSION}"
console = Console()
single_progress = Progress(
    TextColumn("[bold blue]Downloading: ", justify="left"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "|",
    DownloadColumn(),
    "|",
    TransferSpeedColumn(),
    "|",
    TimeRemainingColumn(),
    refresh_per_second=10
)
multi_progress = Progress(
    TextColumn("[bold blue]Thread {task.fields[proc_id]}: ", justify="left"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "|",
    DownloadColumn(),
    "|",
    TransferSpeedColumn(),
    "|",
    TimeRemainingColumn(),
    refresh_per_second=10
)

def parse_args():
    parser = argparse.ArgumentParser(description='Drive Downloader Args')
    parser.add_argument('url', help='URL you want to download from.', default='', type=str)
    parser.add_argument('--filename', '-o', help='Target file name.', default='', type=str)
    parser.add_argument('--thread-number', '-n', help='thread number of multithread.', type=int, default=1)
    parser.add_argument('--version', '-v', action='version', version=__version__, help='Version.')
    args = parser.parse_args()
    return args

def download_single_file(url, filename="", thread_number=1, list_suffix=None):
    scheme = judge_scheme(url)
    if scheme == 'http':
        if len(os.environ["http_proxy"]) > 0:
            proxy = os.environ["http_proxy"]
        else:
            proxy = None
    elif scheme == 'https':
        if len(os.environ["https_proxy"]) > 0:
            proxy = os.environ["https_proxy"]
        else:
            proxy = None
    else:
        raise NotImplementedError(f"Unsupported scheme {scheme}")
    used_proxy = proxy
    
    session_name = judge_session(url)
    session_func = get_session(session_name)
    google_fix_logic = False
    if session_name == 'GoogleDrive' and thread_number > 1:
        thread_number = 1
        google_fix_logic = True
    progress_applied = multi_progress if thread_number > 1 else single_progress
    download_session = session_func(used_proxy)
    download_session.connect(url, filename)
    final_filename = download_session.filename
    download_session.show_info(progress_applied, list_suffix)
    if google_fix_logic:
        console.print('[yellow]Warning: Google Drive URL detected. Only one thread will be created.')

    if thread_number > 1:
        download_session = MultiThreadDownloader(progress_applied, session_func, used_proxy, download_session.filesize, thread_number)
        download_session.get(url, final_filename)
        download_session.concatenate(final_filename)
    else:
        download_session.save_response_content(progress_bar=progress_applied)

def download_filelist(args):
    lines = [line for line in open(args.url, 'r')]
    for line_idx, line in enumerate(lines):
        splitted_line = line.strip().split(" ")
        list_suffix = "({:d}/{:d})".format(line_idx+1, len(lines))
        download_single_file(*splitted_line, args.thread_number, list_suffix)

def simple_cli():
    console.print(f"*******************************************************")
    console.print(f"*                                                     *")
    console.print(f"*             DriveDownloader {MAJOR_VERSION}.{MINOR_VERSION}.{POST_VERSION}                   *")
    console.print(f"*  Homesite: https://github.com/hwfan/DriveDownloader *")
    console.print(f"*                                                     *")
    console.print(f"*******************************************************")
    args = parse_args()
    assert len(args.url) > 0, "Please input your URL or filelist path!"
    if os.path.exists(args.url):
        console.print('Downloading filelist: {:s}'.format(os.path.basename(args.url)))
        download_filelist(args)
    else:
        download_single_file(args.url, args.filename, args.thread_number)
        
    console.print('Download finished.')

if __name__ == '__main__':
    simple_cli()
