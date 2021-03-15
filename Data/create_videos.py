import os
import shutil
import time
from datetime import datetime, timedelta
from helper import parseTimeFromFolder
from itertools import repeat
import numpy as np
from numba import jit
from multiprocessing import Pool, Queue, Process
import pyvips

def apply_tranformations(container, file):
    if hist_normalize == False and shift_gamma == False:
        return file
    else:
        img = pyvips.Image.new_from_file(file['path'])
        brightness = img.avg()
        if shift_gamma:
            gamma = calcGamma(brightness)
            if gamma > 1:
                img = (img.gamma(exponent = gamma).colourspace('lch') * [1, gamma, 1]).colourspace('srgb')
            else:
                img = img.gamma(exponent = gamma)
        
        if hist_normalize and brightness > 60:
            img = img.hist_equal()
        
        # Save transformed image
        filename = file["path"].split('/')[-1]
        new_path = f'{container}/{filename}'
        img.write_to_file(new_path)
        file['path'] = new_path

        return file

@jit(nopython=True)
def calcGamma(brightness):
    floor = 80
    ceiling = 140
    if brightness < floor:
        gamma = np.log( brightness / 255 ) / np.log(floor/255)
    elif brightness > ceiling:
        gamma = np.log( brightness / 255 ) / np.log(ceiling/255)
    else:
        gamma = 1.0
    return gamma

def transform_images(pictureFolderPath, videoQueue, overwrite=False):
    for directory, subdirectory, filenames in os.walk(pictureFolderPath):
        print(f'Creating videos for: {directory}')

        if len(filenames) > 0:
            # Create output folders
            pathBuilder = directory.replace('Photos', 'Videos')
            if os.path.isdir(pathBuilder) == False:
                pathBuilder = ''
                directory_split = directory.split('/')

                for d in directory_split:
                    if d == 'Photos':
                        d = 'Videos'
                    if d == '.':
                        pathBuilder = d
                    else:
                        pathBuilder = f'{pathBuilder}/{d}'

                    if os.path.isdir(pathBuilder):
                        continue
                    else:
                        os.mkdir(pathBuilder)

            # check overwrite
            if len(os.listdir(f'./{pathBuilder}')) == 0 or overwrite == True:
                # Get info for pictures to merge
                files = []
                if len(filenames) > 0:
                    for f in filenames:
                        path = f'{directory}/{f}'
                        files.append({ 'createtime': os.path.getmtime(path), 'path' : path})
                
                # Calculate time
                filmDate = parseTimeFromFolder(directory)
                
                # Make a video only if the folder has new data
                if filmDate < datetime.now():
                    # build manifest file, and gather image metrics
                    tmp = hex(hash(datetime.now())).split('x')[1]

                    # transformations
                    container = hex(hash(datetime.now())).split('x')[1]
                    os.mkdir(container)
                    with Pool(8) as p:
                        files = p.starmap(apply_tranformations, zip(repeat(container), files))
                    
                    # make video
                    files.sort(key= lambda x: x['createtime'])
                    with open(f'{tmp}', 'w') as manifest:
                        for i, f in enumerate(files):
                            print(f"file \'{f['path']}\'", file=manifest)
                    
                    videoQueue.put((tmp, container, pathBuilder))

    videoQueue.put('DONE')
    videoQueue.put('DONE')
    videoQueue.put('DONE')

def make_video(videoQueue):
    while True:
        msg = videoQueue.get()
        if msg == 'DONE':
            break
        else:
            tmp, container, pathBuilder = msg
            try:
                os.system(f'ffmpeg -r 25 -f concat -safe 0 -i {tmp} -c:v libx264 -crf 18 -vf fps=25 ./{pathBuilder}/{int(time.mktime(datetime.now().timetuple()))}.mp4')
            finally:
                os.remove(f'{tmp}')
                shutil.rmtree(container)


# Configs
hist_normalize = False
shift_gamma = True

with open('./videoLog.txt', 'a+') as log:
    s = datetime.now()
    videoQueue = Queue()

    pool = []
    for _ in range(3):
        p = Process(target=make_video, args=((videoQueue,)))
        p.daemon = True
        p.start()
        pool.append(p)

    s = datetime.now()
    transform_images('./Photos', videoQueue, overwrite = False)

    for p in pool:
        p.join()

    print(f'{datetime.now()}: Time to make videos: {(datetime.now() - s).total_seconds()} in seconds.', file=log)
