import os
import shutil
import time
from datetime import datetime, timedelta
from helper import parseTimeFromFolder

def merge_video(folder, overwrite = 'n'):
    directory, subdirectory, files = next(os.walk(folder))
    print(directory, subdirectory, files)

    # Before checking all files, recursively call on levels below
    if len(subdirectory) > 0:
        for s in subdirectory:
            merge_video(f'{directory}/{s}', overwrite=overwrite)

        # Check all sub-files and merge
        manifest = []
        for s in subdirectory:
            _, _, files = next(os.walk(f'{directory}/{s}'))
            if len(files) > 0:
                for f in files:
                    if 'cropped' not in f:
                        path = f'{directory}/{s}/{f}'
                        manifest.append({ 'createtime': os.path.getmtime(path), 'path' : path})

        if len(manifest) > 1:
            manifest.sort(key = lambda x: x['path'])
            tmp = hex(hash(datetime.now())).split('x')[1]
            with open(tmp, 'w') as manifest_file:
                for m in manifest:
                    print(f'Adding file {m["path"]} to the manifest')
                    print(f"file \'{m['path']}\'", file=manifest_file)

            try:
                # Check if the bucket isn't full, if it isn't full we default to overwrite to account for new data
                time_now = datetime.now()
                folder_end_time = parseTimeFromFolder(folder)
                if time_now < folder_end_time:
                    overwrite = 'y'

                # Create merged file
                os.system(f'ffmpeg -{overwrite} -f concat -safe 0 -i {tmp} -c copy {folder}/merged.mp4')

                # Create cropped video
                os.system(f'ffmpeg -{overwrite} -f concat -safe 0 -i {tmp} -filter:v "crop=1800:1000:850:1200" -crf 18 {folder}/merged-cropped.mp4')
            finally:
                os.remove(tmp)


merge_video('./Videos', overwrite = 'n')

