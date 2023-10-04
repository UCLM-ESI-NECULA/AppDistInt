import requests


class RemoteFIFO:
    """Access to FIFO service"""

    def __init__(self, url: str):
        self._url_ = url if url.endswith('/') else (url + '/')
        self.check_status()

    def check_status(self):
        """Call remote hello()"""
        result = requests.get(self._url_)
        print(self._url_)
        if result.status_code != 200:
            raise Exception('Remote service not ready')

    @property
    def head(self):
        """Get Head item"""
        result = requests.get(f'{self._url_}head')
        if result.status_code == 204:
            return
        return result.content.decode()

    @property
    def put(self, item: str):
        """Put new Item"""
        result = requests.put(f'{self._url_}head', data=item)
        if result.status_code != 200:
            raise Exception(f'Cannot put new item. Status={result.status_code}')


if __name__ == '__main__':
    fifo = RemoteFIFO('http://localhost:4999/api/v1')
    print(fifo.head)
    fifo.put('pepe')
    print(fifo.head)
