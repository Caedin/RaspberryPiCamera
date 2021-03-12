import time
from datetime import datetime, timedelta

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
        numerical_values[-1] += 1
        for n in numerical_values:
            if year == None:
                year = n
            elif month == None:
                if n > 12:
                    year += 1
                    n = 0
                month = n
            elif day == None:
                if n > 31:
                    month += 1
                    n = 0
                day = n
            elif hour == None:
                if n > 23:
                    day += 1
                    n = 0
                hour = n

    try:
        date = datetime(year = year or 2050, month = month or 1, day = day or 1, hour = hour or 0)
    except:
        print (year, month, day, hour)
        raise 

    return date