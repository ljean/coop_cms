# -*- coding: utf-8 -*-

import base64
import os.path


def make_dir(*args):
    base_dir = args[0]
    for elt in args[1:]:
        base_dir = os.path.join(base_dir, elt)
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)
    return base_dir


def encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return base64.urlsafe_b64encode("".join(enc).encode()).decode()


def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


def get_db_password_filename(secret_dir):
    return os.path.join(make_dir(secret_dir, 'secrets'), 'db_password.txt')


def get_db_password(secret_dir, secret_key):
    try:
        with open(get_db_password_filename(secret_dir), 'rt') as file:
            password = decode(secret_key, file.read())
    except FileNotFoundError:
        password = ''
    if not password:
        print("*" * 20)
        print("Warning no database password defined")
        print("*" * 20)
    return password


def set_db_password(secret_dir, secret_key, password):
    with open(get_db_password_filename(secret_dir), 'wt') as file:
        file.write(encode(secret_key, password))
