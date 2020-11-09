#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from peewee import *
import config
import logging
import time
import binascii
import decimal
import json
import tornado.ioloop
import tornado.web
import tornado.options
from tornado import gen
from concurrent.futures import ThreadPoolExecutor

db = SqliteDatabase('db.sqlite3')
class BaseModel(Model):
	class Meta:
		database = db

class Base(BaseModel):
	freecash_txid = CharField(max_length=64)
	freecash_address = CharField(max_length=34)
	freecash_height = CharField(max_length=8)
	freecash_time = CharField(max_length=20)
	freecash_utxo = CharField(max_length=64)
	freecash_vote = CharField(max_length=32)
	freecash_percent = CharField(max_length=8)
	freecash_tag = CharField(max_length=128)
	freecash_note = CharField(max_length=128)
	class Meta:
		order_by = ('freecash_address',)
		db_table = 'feip9'


def asm_decode(script_asm):
	op_return_msg = None
	script_asm = script_asm[10:]
	if len(script_asm) < 4:
		return None
	try:
		op_return_msg = binascii.a2b_hex(script_asm).decode("UTF-8")
		if op_return_msg == None:
			return None
	except:
		return None
	return op_return_msg

def check_format(op_return_msg):
	if op_return_msg == None:
		return None
	opreturn = op_return_msg.split("|")
	if opreturn[0] != "FEIP":
		return None
	if opreturn[1] != "9":
		return None
	if len(opreturn)!=8:
		return None
	return opreturn
	
def asm_type(base):
	return {
		"txid" : base.freecash_txid,
		"address" : base.freecash_address,
		"height" : base.freecash_height,
		"time" : base.freecash_time,
		"utxo" : base.freecash_utxo,
		"vote" : base.freecash_vote,
		"percent" : base.freecash_percent,
		"tag" : base.freecash_tag,
		"note" : base.freecash_note
	}

def set_database(txid, address, height, local_time, utxo, vote, percent, tag, note):
	Base.create_table()
	Base.create(
		freecash_txid = txid,
		freecash_address = address,
		freecash_height = height,
		freecash_time = local_time,
		freecash_utxo = utxo,
		freecash_vote = vote,
		freecash_percent = percent,
		freecash_tag = tag,
		freecash_note = note
	)


def set_db_by_asm(asm, txid, address, block):
	code = asm_decode(asm)
	if code is not None:
		data = check_format(code)
		if data is not None:
			set_database(txid, address, block['height'], block['mediantime'], 
				data[3], data[4], data[5], data[6], data[7])

def get_db_by_utxo(utxo):
	freers = {}
	count = 0
	for i in Base.select().where(Base.freecash_utxo == utxo):
		freers[count] = asm_type(i)
		count = count + 1
	return freers

class GetBaseByUtxo(tornado.web.RequestHandler):
	executor = ThreadPoolExecutor(10)
	logger = logging.getLogger('API.GetFreers')

	def get(self):
		utxo = self.get_argument("utxo")
		result = get_db_by_utxo(utxo)
		print(result, type(result))
		if result:
			result["result"] = True
		else:
			result = {"result":False}
			
		self.write(result)
		self.finish()

def get_all_tx(start, end):
	ids = Base.select().count()
	end = ids if end < 0 else end if end < ids else ids
	start = 1 if start <= 0 else start if start < end else end
	datas = {}
	for i in range(start, end + 1):
		base = Base.get_by_id(i)
		datas[i] = asm_type(base)
	print(datas, type(datas))
	return datas

class GetAllTx(tornado.web.RequestHandler):
	executor = ThreadPoolExecutor(10)
	logger = logging.getLogger('API.GetAllOfFreers')

	def get(self):
		result = get_all_tx(0,-1)
		if result:
			result["result"] = True
		else:
			result = {"result":False}
		self.write(result)
		self.finish()