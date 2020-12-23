import os
from concurrent.futures import ThreadPoolExecutor


def ping(i):
    prefix = '192.168.70'
    result = os.popen('ping {}.{}'.format(prefix, i)).read(66)
    if result.find('无法访问') == -1:
        print('{}.{}'.format(prefix, i))


if __name__ == '__main__':
    excutors = ThreadPoolExecutor(max_workers=255)
    for i in range(1, 255):
        excutors.submit(ping, i)