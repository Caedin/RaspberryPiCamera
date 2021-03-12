import os
import shutil
import time
from datetime import datetime, timedelta
from helper import parseTimeFromFolder

from PIL import Image, ImageStat
import numpy as np

def brightness( im_file ):
   im = Image.open(im_file).convert('L')
   stat = ImageStat.Stat(im)
   return stat.mean[0]

def calcGamma(brightness):
    floor = 50
    ceiling = 100

    if brightness < floor:
        gamma = np.log( brightness / 255 ) / np.log(floor/255)
    elif brightness > ceiling:
        gamma = np.log( brightness / 255 ) / np.log(ceiling/255)
    else:
        gamma = 1.0
    return gamma

def calcSaturation(brightness):
    floor = 50
    if brightness < floor:
        saturation = np.log( brightness / 255 ) / np.log(floor/255)
    else:
        saturation = 1
    return saturation

def createVideoFromFolder(pictureFolderPath, overwrite=False):
    for directory, subdirectory, filenames in os.walk(pictureFolderPath):
        print(f'Creating videos for: {directory}')
        files = []
        if len(filenames) > 0:
            for f in filenames:
                path = f'{directory}/{f}'
                files.append({ 'createtime': os.path.getmtime(path), 'path' : path})

        if len(files) > 0:
            # Create output folders
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
                # build manifest file, and gather image metrics
                tmp = hex(hash(datetime.now())).split('x')[1]
                file_brightness = np.zeros(len(files))

                files.sort(key= lambda x: x['createtime'])
                with open(f'{tmp}', 'w') as manifest:
                    for i, f in enumerate(files):
                        print(f"file \'{f['path']}\'", file=manifest)
                        file_brightness[i] = brightness(f['path'])
                
                try:
                    # Calculate time
                    filmDate = parseTimeFromFolder(directory)
                    
                    # Make a video only if the folder has new data
                    if filmDate < datetime.now():
                        avg_brightness = np.mean(file_brightness)
                        gamma_offset = calcGamma(avg_brightness)
                        saturation_offset = calcSaturation(avg_brightness)
                        print(f'Creating video {pathBuilder}. Gamma offset: {gamma_offset:0.0f}. Saturation offset: {saturation_offset:0.0f}')
                        os.system(f'ffmpeg -r 25 -f concat -safe 0 -i {tmp} -c:v libx264 -crf 18 -vf fps=25,eq=gamma={gamma_offset:0.0f}:saturation={saturation_offset:0.0f} ./{pathBuilder}/{int(time.mktime(datetime.now().timetuple()))}.mp4')
                finally:
                    os.remove(f'{tmp}')

with open('./videoLog.txt', 'a+') as log:
    s = datetime.now()
    createVideoFromFolder('./Photos', overwrite = False)
    print(f'{datetime.now()}: Time to make videos: {(datetime.now() - s).total_seconds()} in seconds.', file=log)