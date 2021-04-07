import os
import shutil
import time
from datetime import datetime, timedelta
from helper import parseTimeFromFolder, getHash

def merge_video(folder = './Videos', overwrite = 'n', derivatives = False):
    directory, subdirectory, files = next(os.walk(folder))
    print(directory, subdirectory, files)

    # Before checking all files, recursively call on levels below
    if len(subdirectory) > 0:
        for s in subdirectory:
            if s == 'derivatives':
                continue
            else:
                merge_video(f'{directory}/{s}', overwrite=overwrite, derivatives = derivatives)

        # Read in merge history
        mergehistory = []
        if os.path.isfile(f'{directory}/.mergehistory'):
            with open(f'{directory}/.mergehistory', 'r') as previous_merge_file:
                mergehistory = []
                for line in previous_merge_file.readlines():
                    path = line.split(' ')[1].replace('\'', '').replace('\n', '')
                    mergehistory.append(path)

        # Check all sub-files and merge
        manifest = []
        for s in subdirectory:
            if s == 'derivatives':
                continue
            _, _, files = next(os.walk(f'{directory}/{s}'))
            if len(files) > 0:
                for f in files:
                    if 'cropped' in f or '.mergehistory' in f:
                        continue
                    else:
                        path = f'{directory}/{s}/{f}'
                        time_now = datetime.now()
                        folder_end_time = parseTimeFromFolder(path)
                        if time_now >= folder_end_time:
                            manifest.append({ 'createtime': os.path.getmtime(path), 'path' : path})

        if len(manifest) > 1:
            # handle merge history
            if overwrite == 'n' and len(mergehistory) > 0:
                paths_to_exclude = set(mergehistory)
                manifest = list(filter(lambda x: x['path'] not in paths_to_exclude, manifest))
                manifest.sort(key = lambda x: x['path'])
                manifest.insert(0, { 'createtime': 0.0, 'path' : f'{folder}/merged.mp4'})
            else:
                manifest.sort(key = lambda x: x['path'])

            if len(manifest) > 1:
                # create manifest for rendering the video
                tmp = getHash()
                with open(tmp, 'w') as manifest_file:
                    print(tmp)
                    for m in manifest:
                        print(f'Adding file {m["path"]} to the manifest')
                        print(f"file \'{m['path']}\'", file=manifest_file)

                # record the history of the manifest
                merge_file_format = [f"file \'{m}\'" for m in mergehistory]
                path_format = [f"file \'{m['path']}\'" for m in manifest]
                if overwrite == 'n' and len(merge_file_format) > 0:
                    new_files = merge_file_format + path_format[1:]
                else:
                    new_files = path_format
                with open(f'{folder}/.mergehistory', 'w') as mergehistoryfile:
                    for n in new_files:
                        print(n.replace('\n', ''), file=mergehistoryfile)

                try:
                    # Check if the bucket isn't full, if it isn't full we default to overwrite to account for new data
                    time_now = datetime.now()
                    folder_end_time = parseTimeFromFolder(folder)
                    if time_now < folder_end_time:
                        overwrite = 'y'

                    # Create merged file
                    out = getHash()
                    os.system(f'ffmpeg -{overwrite} -f concat -safe 0 -i {tmp} -c copy {folder}/{out}.mp4')
                    os.replace(f'{folder}/{out}.mp4', f'{folder}/merged.mp4')

                    # Create cropped & sped up video
                    if derivatives:
                        if os.path.isdir(f'{folder}/derivatives') == False:
                            os.mkdir(f'{folder}/derivatives')

                        os.system(f'ffmpeg -{overwrite} -i {folder}/merged.mp4 -c:v libx264 -b:v 10M -maxrate 10M -bufsize 10M -filter:v "setpts=(1/4)*PTS" {folder}/derivatives/merged-4x.mp4')
                        os.system(f'ffmpeg -{overwrite} -i {folder}/merged.mp4 -c:v libx264 -b:v 10M -maxrate 10M -bufsize 10M -filter:v "setpts=(1/8)*PTS" {folder}/derivatives/merged-8x.mp4')
                        os.system(f'ffmpeg -{overwrite} -i {folder}/merged.mp4 -c:v libx264 -b:v 10M -maxrate 10M -bufsize 10M -filter:v "setpts=(1/16)*PTS" {folder}/derivatives/merged-16x.mp4')

                        # Plants were too big for crop after end of March
                        if folder_end_time < datetime(year = 2021, month = 3, day = 1):
                            os.system(f'ffmpeg -{overwrite} -i {folder}/merged.mp4 -c:v libx264 -b:v 10M -maxrate 10M -bufsize 10M -vf crop=1200:800:450:500 {folder}/derivatives/merged-cropped.mp4')
                            os.system(f'ffmpeg -{overwrite} -i {folder}/derivatives/merged-4x.mp4 -c:v libx264 -b:v 10M -maxrate 10M -bufsize 10M -vf crop=1200:800:450:500 {folder}/derivatives/merged-cropped-4x.mp4')
                            os.system(f'ffmpeg -{overwrite} -i {folder}/derivatives/merged-8x.mp4 -c:v libx264 -b:v 10M -maxrate 10M -bufsize 10M -vf crop=1200:800:450:500 {folder}/derivatives/merged-cropped-8x.mp4')
                            os.system(f'ffmpeg -{overwrite} -i {folder}/derivatives/merged-16x.mp4 -c:v libx264 -b:v 10M -maxrate 10M -bufsize 10M -vf crop=1200:800:450:500 {folder}/derivatives/merged-cropped-16x.mp4')
                finally:
                    os.remove(tmp)

import sys
if len(sys.argv) >= 3:
    overwrite = sys.argv[2]
    folder = sys.argv[1]
elif len(sys.argv) >= 2:
    overwrite = 'n'
    folder = sys.argv[1]
else:
    overwrite = 'n'
    folder = './Videos'

merge_video(folder, overwrite = overwrite, derivatives = True)

