import time
from datetime import datetime, timedelta

def getHash():
    return hex(hash(datetime.now())).split('x')[1]

def parseTimeFromFolder(folder):
    folder_parts = folder.split('/')
    year, month, day, hour = None, None, None, None

    numerical_values = []
    for p in folder_parts:
        try:
            numerical_values.append(int(p))
        except:
            continue

    if len(numerical_values) > 0:
        year = numerical_values[0]
    if len(numerical_values) > 1:
        month = numerical_values[1]
    if len(numerical_values) > 2:
        day = numerical_values[2]
    if len(numerical_values) > 3:
        hour = numerical_values[3]

    try:
        date = datetime(year = year or 2050, month = month or 1, day = day or 1, hour = hour or 0)
    except:
        print (year, month, day, hour)
        raise 

    return date

def test_time_parse():
    import os
    for directory, subdirectory, filenames in os.walk('./Photos'):
        print(directory, end='\t')
        if directory == './Photos':
            continue
        date = parseTimeFromFolder(directory)
        print(date)

if __name__ == '__main__':
    test_time_parse()