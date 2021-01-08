import os
import time
from concurrent.futures import ThreadPoolExecutor

from common.log import logger


def ping(i):
    prefix = '192.168.70'
    result = os.popen('ping {}.{}'.format(prefix, i)).read(66)
    if result.find('无法访问') == -1:
        print('{}.{}'.format(prefix, i))


def log_with_single_process(process_name):
    while True:
        logger.info(f'{process_name}' + ': hello world'*20)
        time.sleep(0.01)


def multiprocess_log():
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=2) as excutor:
        excutor.submit(log_with_single_process, 'process-1')
        excutor.submit(log_with_single_process, 'process-2')

def ttt():
    import numpy
    import pandas as pd
    import requests
    import time
    requests.packages.urllib3.disable_warnings()

    shuju = pd.read_excel('导航距离小于直线距离.xlsx', encoding='ISO-8859-1')
    # output = pd.DataFrame(data=None, index=None, columns=None, dtype=None, copy=False)
    # 起点的经纬度
    shuju['Start_Decode1'] = shuju['Start_Decode1'].astype('str')
    shuju['Start_Decode2'] = shuju['Start_Decode2'].astype('str')
    origins = shuju['Start_Decode2'].str.cat(shuju['Start_Decode1'], sep=',')
    # 目的地的经纬度
    shuju['End_Decode1'] = shuju['End_Decode1'].astype('str')
    shuju['End_Decode2'] = shuju['End_Decode2'].astype('str')
    destinations = shuju['End_Decode2'].str.cat(shuju['End_Decode1'], sep=',')
    distance = []

    def geocode(origin, destination, distance):
        parameters = {'key': 'cebfccd04be1f4881f97dfdf4996ede8', 'origin': origin, 'destination': destination}
        base = 'https://restapi.amap.com/v4/direction/bicycling?parameters'
        response = requests.get(base, parameters, verify=False)
        answer = response.json()
        distance.append(answer['data']['paths'][0]['distance'])
        # street.append(answer['regeocode']['addressComponent']['streetNumber']['street'])
        # print(answer['data']['paths'][0]['distance'])
        # answer['data']['paths'][0]['distance']   骑行距离
        print("骑行距离", answer['data']['paths'][0]['distance'])

    for i in range(len(origins)):
        try:
            origin = origins[i]
            destination = destinations[i]
            geocode(origin, destination, distance)
        except:
            print("Connection refused by the server..")
            print("Let me sleep for 20 seconds")
            print("ZZzzzz...")
            time.sleep(20)
            print("Was a nice sleep, now let me continue...")
            origin = origins[i]
            destination = destinations[i]
            geocode(origin, destination, distance)

    data_df = pd.DataFrame(distance)
    data_df.to_excel('导航骑行距离.xlsx')


if __name__ == '__main__':
    # excutors = ThreadPoolExecutor(max_workers=255)
    # for i in range(1, 255):
    #     excutors.submit(ping, i)
    # log_with_single_process('process-1')
    multiprocess_log()