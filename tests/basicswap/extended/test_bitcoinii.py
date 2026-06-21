#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 The Basicswap developers
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php.

"""
basicswap]$ BITCOINII_BINDIR=/path/to/patched/bitcoinii/bin python tests/basicswap/extended/test_bitcoinii.py

BitcoinII Core v29.1.0 needs the regtest mining patch in
patches/bitcoinii-core-regtest-mining-fix.patch for repeat block generation.
"""

import logging
import os
import random
import sys
import unittest

import basicswap.config as cfg
from basicswap.basicswap import Coins
from basicswap.util import toBool
from basicswap.bin.run import startDaemon
from basicswap.contrib.rpcauth import generate_salt, password_to_hmac
from tests.basicswap.common import (
    stopDaemons,
    waitForRPC,
    make_rpc_func,
)
from tests.basicswap.test_btc_xmr import BasicSwapTest, test_delay_event
from tests.basicswap.test_xmr import NUM_NODES
from tests.basicswap.extended.test_dcr import (
    run_test_success_path,
    run_test_bad_ptx,
    run_test_itx_refund,
)

logger = logging.getLogger("BSX Tests")

if not len(logger.handlers):
    logger.addHandler(logging.StreamHandler(sys.stdout))


BITCOINII_BINDIR = os.path.expanduser(
    os.getenv("BITCOINII_BINDIR", os.path.join(cfg.DEFAULT_TEST_BINDIR, "bitcoinii"))
)
BITCOINIID = os.getenv("BITCOINIID", "bitcoinIId" + cfg.bin_suffix)

BC2_USE_DESCRIPTORS = toBool(os.getenv("BC2_USE_DESCRIPTORS", True))

BC2_BASE_PORT = 8436
BC2_BASE_RPC_PORT = 8446


def prepareBC2DataDir(datadir, nodeId, conf_file="bitcoinii.conf"):
    node_dir = os.path.join(datadir, "bc2_" + str(nodeId))
    if not os.path.exists(node_dir):
        os.makedirs(node_dir)
    filePath = os.path.join(node_dir, conf_file)

    with open(filePath, "w+") as fp:
        fp.write("regtest=1\n")
        fp.write("[regtest]\n")

        fp.write("port=" + str(BC2_BASE_PORT + nodeId) + "\n")
        fp.write("rpcport=" + str(BC2_BASE_RPC_PORT + nodeId) + "\n")
        salt = generate_salt(16)
        fp.write(
            "rpcauth={}:{}${}\n".format(
                "test" + str(nodeId),
                salt,
                password_to_hmac(salt, "test_pass" + str(nodeId)),
            )
        )

        fp.write("daemon=0\n")
        fp.write("printtoconsole=0\n")
        fp.write("server=1\n")
        fp.write("discover=0\n")
        fp.write("listenonion=0\n")
        fp.write("bind=127.0.0.1\n")
        fp.write("debug=1\n")
        fp.write("debugexclude=libevent\n")

        fp.write("fallbackfee=0.0002\n")
        fp.write("acceptnonstdtxn=0\n")
        fp.write("addresstype=bech32\n")
        fp.write("changetype=bech32\n")

        for i in range(0, NUM_NODES):
            if nodeId == i:
                continue
            fp.write("addnode=127.0.0.1:{}\n".format(BC2_BASE_PORT + i))


class TestBC2(BasicSwapTest):
    __test__ = True
    test_coin = Coins.BC2
    test_coin_from = Coins.BC2
    bc2_daemons = []
    start_ltc_nodes = False
    base_rpc_port = BC2_BASE_RPC_PORT
    bc2_addr = None
    max_fee: int = 200000
    test_fee_rate: int = 100000  # sats/kvB

    def mineBlock(self, num_blocks: int = 1) -> None:
        self.callnoderpc("generatetoaddress", [num_blocks, self.bc2_addr])

    @classmethod
    def tearDownClass(cls):
        logging.info("Finalising BitcoinII Test")
        stopDaemons(cls.bc2_daemons)
        cls.bc2_daemons.clear()

        super(TestBC2, cls).tearDownClass()

    @classmethod
    def coins_loop(cls):
        super(TestBC2, cls).coins_loop()
        ci0 = cls.swap_clients[0].ci(cls.test_coin)
        try:
            if cls.bc2_addr is not None:
                ci0.rpc_wallet("generatetoaddress", [1, cls.bc2_addr])
        except Exception as e:
            logging.warning(f"coins_loop generate {e}")

    @classmethod
    def prepareExtraDataDir(cls, i: int) -> None:
        if not cls.restore_instance:
            prepareBC2DataDir(cfg.TEST_DATADIRS, i)

        cls.bc2_daemons.append(
            startDaemon(
                os.path.join(cfg.TEST_DATADIRS, "bc2_" + str(i)),
                BITCOINII_BINDIR,
                BITCOINIID,
            )
        )
        logging.info("Started {} {}".format(BITCOINIID, cls.bc2_daemons[-1].handle.pid))

        bc2_rpc = make_rpc_func(i, base_rpc_port=BC2_BASE_RPC_PORT)
        waitForRPC(
            bc2_rpc,
            test_delay_event,
            rpc_command="getnetworkinfo",
            max_tries=12,
        )
        waitForRPC(bc2_rpc, test_delay_event, rpc_command="getblockchaininfo")
        if len(bc2_rpc("listwallets")) < 1:
            bc2_rpc(
                "createwallet",
                ["bsx_wallet", False, True, "", False, BC2_USE_DESCRIPTORS],
            )
            if BC2_USE_DESCRIPTORS:
                bc2_rpc(
                    "createwallet",
                    ["bsx_watch", True, True, "", False, True],
                )

    @classmethod
    def addPIDInfo(cls, sc, i):
        sc.setDaemonPID(Coins.BC2, cls.bc2_daemons[i].handle.pid)

    @classmethod
    def addCoinSettings(cls, settings, datadir, node_id):
        settings["chainclients"]["bitcoinii"] = {
            "connection_type": "rpc",
            "manage_daemon": False,
            "rpcport": BC2_BASE_RPC_PORT + node_id,
            "rpcuser": "test" + str(node_id),
            "rpcpassword": "test_pass" + str(node_id),
            "datadir": os.path.join(datadir, "bc2_" + str(node_id)),
            "bindir": BITCOINII_BINDIR,
            "use_csv": True,
            "use_segwit": True,
            "blocks_confirmed": 1,
            "use_descriptors": BC2_USE_DESCRIPTORS,
            "wallet_name": "bsx_wallet",
        }
        if BC2_USE_DESCRIPTORS:
            settings["chainclients"]["bitcoinii"]["watch_wallet_name"] = "bsx_watch"

    @classmethod
    def prepareExtraCoins(cls):
        ci0 = cls.swap_clients[0].ci(cls.test_coin)
        if not cls.restore_instance:
            for sc in cls.swap_clients:
                ci = sc.ci(cls.test_coin)
                ci.initialiseWallet(ci.getNewRandomKey())
            cls.bc2_addr = ci0.rpc_wallet("getnewaddress", ["mining_addr", "bech32"])
        else:
            addrs = ci0.rpc_wallet("getaddressesbylabel", ["mining_addr"])
            cls.bc2_addr = next(iter(addrs))

        num_blocks: int = 500
        if ci0.rpc("getblockcount") < num_blocks:
            logging.info(f"Mining {num_blocks} BitcoinII blocks to {cls.bc2_addr}")
            ci0.rpc("generatetoaddress", [num_blocks, cls.bc2_addr])
        logging.info("BC2 blocks: {}".format(ci0.rpc("getblockcount")))

    def test_007_hdwallet(self):
        logging.info("---------- Test {} hdwallet".format(self.test_coin_from.name))

        test_seed = "8e54a313e6df8918df6d758fafdbf127a115175fdd2238d0e908dd8093c9ac3b"
        test_wif = (
            self.swap_clients[0]
            .ci(self.test_coin_from)
            .encodeKey(bytes.fromhex(test_seed))
        )
        new_wallet_name = random.randbytes(10).hex()
        self.callnoderpc(
            "createwallet",
            [new_wallet_name, False, False, "", False, BC2_USE_DESCRIPTORS],
        )
        self.callnoderpc("sethdseed", [True, test_wif], wallet=new_wallet_name)
        addr = self.callnoderpc(
            "getnewaddress", ["add test", "bech32"], wallet=new_wallet_name
        )
        self.callnoderpc("unloadwallet", [new_wallet_name])
        assert addr.startswith("bcrt1")

    def test_012_p2sh_p2wsh(self):
        # Fee rate
        pass

    def test_02_sh_part_coin(self):
        self.prepare_balance(self.test_coin, 200.0, 1801, 1800)
        run_test_success_path(self, Coins.PART, self.test_coin)

    def test_03_sh_coin_part(self):
        run_test_success_path(self, self.test_coin, Coins.PART)

    def test_04_sh_part_coin_bad_ptx(self):
        self.prepare_balance(self.test_coin, 200.0, 1801, 1800)
        run_test_bad_ptx(self, Coins.PART, self.test_coin)

    def test_05_sh_coin_part_bad_ptx(self):
        self.prepare_balance(self.test_coin, 200.0, 1801, 1800)
        run_test_bad_ptx(self, self.test_coin, Coins.PART)

    def test_06_sh_part_coin_itx_refund(self):
        run_test_itx_refund(self, Coins.PART, self.test_coin)

    def test_07_sh_coin_part_itx_refund(self):
        self.prepare_balance(self.test_coin, 200.0, 1801, 1800)
        run_test_itx_refund(self, self.test_coin, Coins.PART)

    def test_01_b_full_swap_reverse(self):
        self.prepare_balance(self.test_coin, 100.0, 1801, 1800)
        self.do_test_01_full_swap(Coins.XMR, self.test_coin_from)


if __name__ == "__main__":
    unittest.main()
