'''
connect is an experimental bittorrent clint

Created By : Anisujjaman Shohan
Starting date : 31 May 2024
End Date : 

'''

import aiohttp
import socket
import logging
import random
from struct import unpack
from urllib.parse import urlencode

import bencoding

class TrackerResponse:
    '''
    The response from the tracker after connecting to the URL
    '''

    def __init__(self, response: dict):
        self._response = response

    @property
    def failure(self): # for failure response
        if b'failure reason' in self._response:
            return self._response[b'failure reason'].decode('utf-8')
        return None
    
    @property
    def interval(self) -> int: # time waiting in between sending periodic request to the tracker
        return self._response.get(b'interval', 0)
    
    @property
    def complete(self) -> int: # numbers of seeders with complete file
        return self._response.get(b'complete', 0)
    
    @property
    def incomplete(self) -> int: # number of leechers
        return self._response.get(b'incomplete', 0)
    
    '''
    A list of tuples for each peer structure(port, ip)
    '''
    @property
    def peers(self):
        peers = self._response[b'peers']
        if type(peers) == list:
            logging.debug('Dictionary model peers are returned by tracker')
            raise NotImplementedError()
        else:
            logging.debug('Binary model peers are returned by tracker')
            '''
            now spliting the string of 6 byte into two pieces of 4 and 2
            recpectively. First 4 characters are port and last 2 are tcp 
            '''
            peers = [peers[i:i+6] for i in range(0, len(peers), 6)]
            return [(socket.inet_ntoa(p[:4]), _decode_port(p[4:])) for p in peers]
    
    def __str__(self):
        return "incomplete: {incomplete}"\
                "complete: {complete}"\
                "interval: {interval}"\
                "peers: {peers}\n".format(incomplete=self.incomplete,
                                          complete=self.complete,
                                          interval=self.interval,
                                          peers=", ".join([x for (x, _) in self.peers]))
    


# to represent connections for a torrent that is either seeding or downloading
class Tracker:
    def __init__(self, torrent):
        self._torrent = torrent
        self._peer_id = _calculate_peer_id()
        self._http_client = aiohttp.ClientSession()

    async def connect(self, first: bool = None, uploaded: int = 0, downloaded: int = 0):
        '''
        this is an announce call to the tracker to update the statistics, also to connect the available peers
        '''
        params = {
            'info_hash': self._torrent.info_hash,
            'peer_id': self._peer_id,
            'port': 6881,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': self._torrent.total_size - downloaded,
            'compact': 1
        }
        if first:
            params['event'] = 'started'
        
        url = self._torrent.announce + '?' + urlencode(params)
        logging.info('Connecting to the tracker: ' + url)

        async with self._http_client.get(url) as response:
            if not response.status == 200:
                raise ConnectionError('Unable to connect to the tracker: status code{}'.format(response.status))
            data = await response.read()
            self.raise_for_error(data)
            return TrackerResponse(bencoding.Decoder(data).decode())
    
    def close(self):
        self._http_client.close()

    def raise_for_error(self, tracker_response):
        try:
            message = tracker_response.decode('utf-8')
            if 'failure' in message:
                raise ConnectionError('Unable to connect to the tracker: {}'.format(message))
        except UnicodeDecodeError:
            pass
    
    def _contruction_tracker_parameter(self):
        return {
            'info_hash': self._torrent.info_hash,
            'peer_id': self._peer_id,
            'port': 6881,
            'uploaded': 0,
            'downloaded': 0,
            'left': 0,
            'compact': 1
        }



# converts a 32-bit binary port to int using unpack
def _decode_port(port):
    return unpack(">H", port)[0]

'''
calculate and return a unique peer id

A 'peer id' is 20 characters(bytes) long identifier
'''
def _calculate_peer_id():
    return '-PC1000-' + ''.join([str(random.randint(0, 9)) for _ in range(12)])

