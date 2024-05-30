'''
connect is an experimental bittorrent clint

Created By : Anisujjaman Shohan
Starting date : 31 May 2024
End Date : 

'''

from collections import OrderedDict

# starting of an integer
TOKEN_INTEGER = b'i'

# starting of a list
TOKEN_LIST = b'l'

# staring of a dictionary
TOKEN_DICT = b'd'

# indecates end of any token values i.e. integer, list, dict
TOKEN_END = b'e'

# string separator to delimite string size
TOKEN_STRING_SEPARATOR = b':'

class Decoder:
    '''
    decodes a dencided sequence of bytes
    '''
    def __init__(self, data: bytes):
        if isinstance(data, bytes):
            raise TypeError('Argument "data" must be of type bytes')
        
        self._data = data
        self._index = 0

    '''
    decodes a bencoded data and returns a matching python object type
    '''
    def decode(self):
        t = self._peek
        if t == None:
            raise EOFError('Unexpected End-of-File')
        elif t == TOKEN_INTEGER:
            return self._decode_int()
        elif t == TOKEN_LIST:
            return self._decode_list()
        elif t == TOKEN_DICT:
            return self._decode_dict()
        elif t == TOKEN_END:
            return None
        elif t in b'0123456789':
            return self._decode_string()
        else:
            raise RuntimeError('Invalid Token Read at {0}'.format(str(self._index)))
    
    '''
    returns next character from the bencoded data or none
    '''
    def _peek(self):
        if self._index >= len(self._data) - 1:
            return None
        return self._data[self._index:self._index + 1]
    
    '''
    read or consume the next character from the data
    '''
    def _consume(self) -> bytes:
        self._index += 1
    
    '''
    read the length number of bytes from the data and returns the result
    '''
    def _read(self, length:int) -> bytes:
        if self._index + length > len(self._data):
            raise IndexError('Cannot read {0} bytes from the index {1}'.format(str(length), str(self._index)))
        res = self._data[self._index:self._index + length]
        self._index += length
        return res
    
    '''
    read the bencoded data until the given token is found and return the character read
    '''
    def _read_until(self, token:bytes) -> bytes:
        try:
            occurence = self._data.index(token, self._index)
            result = self._data[self._index:occurence]
            self._index = occurence + 1
            return result
        except ValueError:
            raise RuntimeError('Unable to find token {0}'.format(str(token)))
        
    # decoding data types one by one
    def _decode_int(self):
        return int(self._read_until(TOKEN_END))
    
    def _decode_list(self):
        result = []
        while self._data[self._index:self._index + 1] != TOKEN_END:
            result.append(self.decode())
        self._consume()
        return result
    
    def _decode_dict(self):
        result = OrderedDict()
        while self._data[self._index:self._index + 1] != TOKEN_END:
            key = self.decode()
            val = self.decode()
            result[key] = val
        self._consume()
        return result
    
    def _decode_string(self):
        bytes_to_read = int(self._read_until(TOKEN_STRING_SEPARATOR))
        data = self._read(bytes_to_read)
        return data
    
class Encoder:
    '''
    encodes a python object to a bencoded sequence

    The types are supported -
        - int
        - list
        - dict
        - string
        - bytes 
    Any other types are ignored
    '''
    def __init__(self, data):
        self._data = data
    
    '''
    encodes a python object to bencoded binary string; returns a binary data
    '''
    def encode(self):
        return self.encode_next(self._data)
    
    '''
    encode the next character from the data
    '''
    def encode_next(self, data):
        if type(data) == str:
            return self._encode_string(data)
        elif type(data) == int:
            return self._encode_int(data)
        elif type(data) == list:
            return self._encode_list(data)
        elif type(data) == dict or type(data) == OrderedDict:
            return self._encode_dict(data)
        elif type(data) == bytes:
            return self._encode_bytes(data)
        else:
            return None

    def _encode_string(self, data: str):
        result = str(len(data)) + ':' + data
        return self.encode(result)
    
    def _encode_int(self, data):
        return self.encode('i' + str(data) + 'e')
    
    def _encode_list(self, data):
        result = bytearray('l', 'uft-8')
        result += b''.join([self.encode_next(item) for item in data])
        result += b'e'
        return result
    
    def _encode_dict(self, data: dict) -> bytes:
        result = bytearray('d', 'uft-8')
        for k, v in data:
            key = self.encode_next(k)
            val = self.encode_next(v)
            if key and val:
                result += key
                result += val
            else:
                raise RuntimeError('Bad Dict')
        result += b'e'
        return result
    
    def _encode_bytes(self, data: str):
        result = bytearray()
        result += str.encode(str(len(data)))
        result += b':'
        result += data
        return result
