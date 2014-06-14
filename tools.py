import pt
import custom
from json import dumps as package, loads as unpackage
from collections import OrderedDict

#def pub2addr(pubkey): return pt.pubtoaddr(pubkey)


def sign(msg, privkey):
    return pt.ecdsa_sign(msg, privkey)


def verify(msg, sig, pubkey):
    return pt.ecdsa_verify(msg, sig, pubkey)


def privtopub(privkey):
    return pt.privtopub(privkey)


def det_hash(x):
    """Deterministically takes sha256 of dict, list, int, or string."""

    def det_list(l): return '[%s]' % ','.join(map(det, sorted(l)))

    def det_dict(x):
        list_=map(lambda p: det(p[0]) + ':' + det(p[1]), sorted(x.items()))
        return '{%s}' % ','.join(list_)

    def det(x): return {list: det_list, dict: det_dict}.get(type(x), str)(x)

    return custom.hash_(det(unpackage(package(x))))


def base58_encode(num):
    num = int(num, 16)
    alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
    base_count = len(alphabet)
    encode = ''
    if num < 0:
        return ''
    while (num >= base_count):
        mod = num % base_count
        encode = alphabet[mod] + encode
        num = num / base_count
    if num:
        encode = alphabet[num] + encode
    return encode


def make_address(pubkeys, n):
    """n is the number of pubkeys required to spend from this address."""
    return (str(len(pubkeys)) + str(n) +
            base58_encode(det_hash({str(n): pubkeys}))[0:29])


def buffer_(str_to_pad, size):
    if len(str_to_pad) < size:
        return buffer_('0' + str_to_pad, size)
    return str_to_pad
