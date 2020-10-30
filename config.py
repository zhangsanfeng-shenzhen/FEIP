#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import decimal
import json

config = {}

def save_config():
	with open("config.json", mode='w', encoding='utf-8') as fp:
		json.dump(config, fp, ensure_ascii=False, indent=2)


def load_config():
	global config
	with open("config.json", mode='r', encoding='utf-8') as fp:
		config = json.load(fp)

load_config()