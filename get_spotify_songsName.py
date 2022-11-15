import traceback
from urllib.error import HTTPError
import requests, bs4, sys, os, threading, logging

def setup_logger(name: str, log_file: str, level: int=logging.INFO, encoding_: str="utf-8") -> logging.Logger:
    """To setup as many loggers as I want"""
    formatter = logging.Formatter('[%(levelname)s] [%(name)s]: %(message)s - %(asctime)s')

    handler = logging.FileHandler(log_file, encoding= encoding_)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def log(func):
    """A decorator to log errors in a separate file"""

    def wrapper(*args):
        threadName = threading.current_thread().name 
        logger = setup_logger(name = threadName, log_file = f'{threadName}.log', level = logging.INFO)
        logger.info('thread started')
        
        try:
            func(*args, logger)
        except Exception as e:
            logger.error(traceback.format_exc())
        finally:        
            logger.info('thread ended')

    return wrapper

@log
def songs_infos(data: list[str], threadsResults: list[list[str]], index: int, logger: logging.Logger = None) -> None:
    """create list to store songs info when got add it to the thread results list"""


    songsInfo: list[str] = list()

    for url in data:
        songsInfo.append(song_info(url, logger))

    logger.debug(songsInfo)
    threadsResults[index].extend(songsInfo)

def song_info(url: str, logger: logging.Logger = None) -> str:
    """
    get urls for songs in spotify from songsUrls.txt file
        use request to get html and parse it with bs4
        get name of song with span[dir="auto"] -> first element text
        get name of song writer a -> second element text"""

    logger.info(f'Trying to connect to {url}')

    result = requests.get(url)

    try:
        result.raise_for_status()
    except HTTPError as e:
        print(e, '\n')
        print(f'An error occurred with {url}')
        return f'Error - {url}'

    soup = bs4.BeautifulSoup(result.text, 'html.parser')

    logger.info('connected successfully getting song info\n')

    songName = soup.select('span[dir="auto"]')[0].text
    songAuthor = soup.select('a')[1].text


    return f'{songName}\t{songAuthor}'

def main():

    print('getting songs urls from songsUrl file')

    # Get songs url <data> and put them into a list
    with open('songsUrls.txt', 'r') as urlsFile:
        data: list[str] = urlsFile.read().split('\n')

    """split the data <known length of 505> into 5 parts
    create two list one for holding the 5 threads and one for holding the 5 results of the threads"""

    partitionIncreases: int = 101
    numberOfPartitions: int = len(data)//partitionIncreases

    threads: list[threading.Thread] = [None] * numberOfPartitions
    threadsResults: list[list[str]] = [[] for _ in range(numberOfPartitions)]

    start = 0
    end = partitionIncreases

    # input the needed parameters to the thread and starting it
    for i in range(numberOfPartitions):
        threads[i] = threading.Thread(target= songs_infos, args= [data[start : end], threadsResults, i], name= f'Thread-{i+1}')
        threads[i].start()
        start = end
        end += partitionIncreases
        
    print('using urls')

    # wait until all threads have ended and then add results to songs info list
    songsInfo: list[str] = []
    for i, thread in enumerate(threads):
        thread.join()
        songsInfo.extend(threadsResults[i])

    print('writing to the songsName file')

    # write songs info to a file utf-8 encoding because of arabic letters
    with open('songsNames.txt', 'w', encoding= 'utf-8') as namesFile:
        for info in songsInfo:
            namesFile.write(info + '\n')

    print('Done')

if __name__ == "__main__":
    os.chdir(sys.path[0])
    main()