"""Read a bounded regular local UTF-8 JSON metadata file."""

import json
import os
import stat
from .core import InputError

LIMIT = 32768


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise InputError('duplicate JSON object key')
        value[key] = item
    return value


def _constant(_):
    raise InputError('non-finite JSON value')


def load(path):
    try:
        if stat.S_ISLNK(os.lstat(path).st_mode):
            raise InputError('input must not be a symlink')
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > LIMIT:
                raise InputError('input must be a regular file of at most 32768 bytes')
            data = stream.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise InputError('input exceeds 32768 bytes')
        return json.loads(data.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
    except InputError:
        raise
    except (OSError, ValueError, RecursionError) as exc:
        raise InputError('cannot read bounded UTF-8 JSON metadata') from exc
