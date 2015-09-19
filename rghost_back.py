import queue
import bs4
from requests import get
from urllib.request import urlopen, Request
from threading import Thread

# Юзать регулярки!

BASE_URL = 'http://rghost.ru/search?utf8=%E2%9C%93'
SITE_URL = 'http://rghost.ru'
FILE_SELECTOR = 'li[tooltip_for_file]'
URL_SELECTOR = 'a'
TITLE_SELECTOR = 'a'
SIZE_SELECTOR = 'span.filesize'

DOWN_SELECTOR = '#actions > .large'
NAME_SELECTOR = '.wrap'
# DATE_SELECTOR = ''

THREAD_COUNT = 5
BAD_FILE = -1

HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 6.0; rv:14.0) Gecko/20100101 ',
                  'Firefox/14.0.1'),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'DNT': '1'
}

class Parser:
    def __init__(self, query, page_limit=2, extension=''):
        self.selectors = {'file':   FILE_SELECTOR,
                          'url':    URL_SELECTOR,
                          'title':  TITLE_SELECTOR,
                          'size':   SIZE_SELECTOR}
        self.query = query.replace(' ', '+')
        self.base = BASE_URL + "&s=%s" % query
        self.page_limit = page_limit
        self.extension = extension

        self.queue = queue.Queue(maxsize=THREAD_COUNT)
        self.threads = []
        self.results = queue.Queue()

    def download(self, url):
        return urlopen(url).read()

    def pager(self, page=1):
        if self.page_limit < page:
            for i in range(THREAD_COUNT):
                self.queue.put(None)
            return None
        page_url = self.base + "&page=%s" % page
        soup = bs4.BeautifulSoup(self.download(page_url))
        files = soup.select(self.selectors['file'])
        if not files:
            return None
        for file in files:
            self.queue.put(file)
        self.pager(page+1)

    class File:
        def __init__(self, title, url, size): #, date):
            self.title = title
            self.url = SITE_URL + url
            self.size = size

        def __str__(self):
            return '%s\n%s\nsize:%s\n\n' % (self.title, self.url, self.size)

    def file_perform(self, file):
        """
        :param file: tag- from soup
        :return: object file
        perform html to object File
        """
        title = file.select(self.selectors['title'])[0].text
        if self.extension and not title.lower().endswith(self.extension.lower()):
            return BAD_FILE
        url = file.select(self.selectors['url'])[0].attrs['href']
        size = file.select(self.selectors['size'])[0].text
        size = size.strip()
        return self.File(title, url, size)  # , date)

    def routine(self):
        while True:
            source = self.queue.get()

            # Если пришло ничего, то завершить
            if not source:
                break
            file = self.file_perform(source)

            # Если не плохой файл, то его в результаты
            if file is not BAD_FILE:
                self.results.put(file)
            self.queue.task_done()

    def start(self):

        for i in range(THREAD_COUNT):
            t = Thread(target=self.routine)
            t.start()
            self.threads.append(t)
        self.pager()
        return self.results


class LinkLoader:
    def __init__(self, destination, files=None, file_links=None):
        self.que = queue.Queue()
        if files:
            for file in files:
                self.que.put(file.url)
        if file_links:
            for link in file_links:
                print(link)
                self.que.put(link)
        # self.que.join()

        # self.result_que = queue.Queue()

        self.destination = destination

    def routine(self):
        while True:

            link_to_file = self.que.get()
            if link_to_file is None:
                break

            html = get(link_to_file, HEADERS)
            soup = bs4.BeautifulSoup(html.content)

            down_link = soup.select(DOWN_SELECTOR)[0].attrs['href']

            # name = [first 3 symbols from link] filename
            name = "[%s] %s" % (link_to_file.split('/')[-1][:3], soup.select(NAME_SELECTOR)[0].text)

            file_name = '/'+'/'.join(s.strip('/') for s in [self.destination, name])
            with open(file_name, 'wb') as file:
                file.write(get(down_link, HEADERS).content)
            self.que.task_done()

    def start(self):
        for i in range(THREAD_COUNT):
            t = Thread(target=self.routine)
            t.start()
        for i in range(THREAD_COUNT):
            self.que.put(None)


def test_link():

    dest = '/mnt/exe/Text/Python/Rghost_down/test/'
    urls = """http://rghost.ru/60334963
http://rghost.ru/49039162
http://rghost.ru/59220352
http://rghost.ru/7tbh2NpCB
http://rghost.ru/8HRLfkkdB
http://rghost.ru/68rPV4vjw"""
    urls = urls.split('\n')
    downer = LinkLoader(dest, file_links=urls)
    downer.start()
def test_parser():
    p = Parser('base', extension='.txt')
    res = p.start()
    print(res.qsize())
    while res.qsize() > 0:
        print(res.get().url)

    print(res.qsize())

# test_link()

