import hashlib


def generate_key(g_id):
    return hashlib.md5((g_id + "griff").encode('utf-8')).hexdigest()
