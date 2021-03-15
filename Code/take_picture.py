import os
import paramiko
from scp import SCPClient
import datetime
import shutil
import json

from PIL import Image, ImageStat
import numpy as np

def brightness( im_file ):
   im = Image.open(im_file).convert('L')
   stat = ImageStat.Stat(im)
   return stat.mean[0]

def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def logError():
    import traceback
    msg = traceback.format_exc()
    with open('/home/pi/Camera/error_log.txt', 'a+') as logFile:
        print(f'{datetime.datetime.now()}:', file=logFile)
        print(msg, file=logFile)

def getShutter():
    with open('/home/pi/Camera/Code/config.json', 'r') as config:
        configs = json.load(config)
    return configs['shutterSpeed']
    
def saveShutter(ss):
    with open('/home/pi/Camera/Code/config.json', 'r') as config:
        configs = json.load(config)

    configs['shutterSpeed'] = ss
    with open('/home/pi/Camera/Code/config.json', 'w') as config:
        json.dump(configs, config)


class FileLock():
    def __init__(self, lock = '/home/pi/Camera/Code/lock'):
        self.lock = lock
    
    def __enter__(self):
        if os.path.isfile(self.lock):
            raise Exception('Lock file not available, process is currently running. Exiting without taking image')
        else:
            with open(self.lock, 'w') as lockFile:
                print(f'{hex(hash(datetime.datetime.now()))}', file=lockFile)
        return self
    
    def __exit__(self, type, value, traceback):
        if os.path.isfile(self.lock):
            os.remove(self.lock)
        else:
            raise Exception('Attempting to release lock, yet lock not available. Exiting due to unexpected system state.')
    

# Configs
imageFolder = '/home/pi/Camera/Photos'
timestamp = datetime.datetime.now()
year = f'{timestamp.year:04d}'
month = f'{timestamp.month:02d}'
day = f'{timestamp.day:02d}'
hour = f'{timestamp.hour:02d}'
filetype = 'jpg'
brightness_floor = 80
brightness_ceiling = 150

def take_picture(pathList, fileName = None, shutterspeed = None):
    # Check directory exists
    path = ''
    for p in pathList:
        path = f'{path}/{p}'
        if os.path.isdir(path) == False:
            os.mkdir(path)

    if fileName is None:
        fileName = f'{imageFolder}/{year}/{month}/{day}/{hour}/{hex(hash(timestamp))[2:]}.{filetype}'

    print(f'Taking picture {fileName}, shutterspeed is {shutterspeed}')
    if shutterspeed is None:
        os.system(f'raspistill -o {fileName} --quality 100 --nopreview --vstab --timeout 5000 -mm matrix')
    else:
        os.system(f'raspistill -o {fileName} --quality 100 --nopreview --vstab --timeout 5000 -mm matrix -ss {shutterspeed} --drc med')
    return fileName

def get_ssh_configs():
    with open('/home/pi/Camera/Code/ssh.config', 'r') as c:
        k = json.load(c)
    return k['server'], k['user'], k['password'], k['port']

def send_picture(imageFolder):
    server, user, password, port = get_ssh_configs()

    ssh = createSSHClient(server, port, user, password)
    scp = SCPClient(ssh.get_transport())

    scp.put(imageFolder, f'/C:/Users/kilax/Code/RaspberryPi/Camera/Data/', recursive=True, preserve_times=True)

try:
    pathList = [imageFolder, year, month, day, hour]

    with FileLock() as lock:
        pic = take_picture(pathList)
        avg_brightness = brightness(pic)
        print(f'Brightness: {avg_brightness}')

        if avg_brightness > brightness_floor and avg_brightness < brightness_ceiling:
            send_picture(imageFolder)
        else:
            def retake_pic(pic, shutterspeed):
                pic = take_picture(pathList, fileName = pic, shutterspeed = shutterspeed)
                avg_brightness = brightness(pic)
                print(f'New brightness: {avg_brightness}')
                return pic, avg_brightness

            shutterspeed = getShutter()
            pic, avg_brightness = retake_pic(pic, shutterspeed)
            while avg_brightness < brightness_floor or avg_brightness > brightness_ceiling:
                if avg_brightness < brightness_floor:
                    shutterspeed *= 1.25
                elif avg_brightness > brightness_ceiling:
                    shutterspeed /= 1.25
                pic, avg_brightness = retake_pic(pic, shutterspeed)

            saveShutter(shutterspeed)
            send_picture(imageFolder)

        # Only delete photos if no errors above
        shutil.rmtree(imageFolder)

except Exception as e:
    logError()

