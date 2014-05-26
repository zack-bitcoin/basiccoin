import pt
import custom
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
    if isinstance(x, list):
        return custom.hash_(str(sorted(x)))
    elif isinstance(x, dict):
        return custom.hash_(str(OrderedDict(sorted(x.items(),
                                                   key=lambda t: t[0]))))
    else:
        return custom.hash_(x)


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
