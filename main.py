#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import config
import logging
import time
import threading
import binascii
import decimal

import tornado.ioloop
import tornado.web
import tornado.options
from tornado import gen
from platform import system as os_type
from concurrent.futures import ThreadPoolExecutor

from freetx.crypto import ECPrivateKey, ripemd160_sha256
from freetx.base58 import BASE58_ALPHABET, b58encode_check

import FEIP9

logging.basicConfig(level=logging.INFO)

def decode_opreturn_msg(tx, block):
	for t in tx["vin"]:
		if "scriptSig" in t and "asm" in t["scriptSig"]:
			public_key = t["scriptSig"]["asm"].split("[ALL|FORKID] ")[-1]
			public_key = ripemd160_sha256(bytes.fromhex(public_key))
			address = b58encode_check(b'\x23' + public_key)
			break
	for t in tx["vout"]:
		if t["scriptPubKey"]["type"] != 'nulldata':
			continue
		FEIP9.set_db_by_asm(t["scriptPubKey"]['asm'], tx["txid"], address, block)

def block_updater():
	logger = logging.getLogger('Block Updater')
	logger.setLevel(logging.INFO)
	while 1:
		rpc_connection = AuthServiceProxy(config.config["rpc_server_uri"])
		block = rpc_connection.getblock(config.config["current_block"])
		logger.info(f"Update Tip: Block={config.config['current_block']},Height={block['height']}")
		if "confirmations" in block and "nextblockhash" in block:
			config.config["current_block"] = block["nextblockhash"]
			config.save_config()
			for i in block["tx"]:
				tx = rpc_connection.decoderawtransaction(rpc_connection.getrawtransaction(i))
				decode_opreturn_msg(tx, block)
		else:
			time.sleep(6)

def run_api_server():
    app = tornado.web.Application([
        (r"/get_base_by_utxo", FEIP9.GetBaseByUtxo),
		(r"/get_all_tx", FEIP9.GetAllTx)
    ], autoreload=False)
    app.listen(int(config.config["api_port"]), address=config.config["api_url"])

    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
	threading.Thread(target=block_updater).start()
	run_api_server()



