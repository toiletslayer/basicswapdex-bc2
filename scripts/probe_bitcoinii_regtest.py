#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 The Basicswap developers
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php.

"""Probe BitcoinII regtest behavior needed by BasicSwap tests.

This script is intentionally standalone so it can be run against a stock
BitcoinII Core release binary or a patched testing binary.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from decimal import Decimal
from pathlib import Path


def cli_call(cli_path, base_args, *args, wallet=None, json_out=True):
    cmd = [str(cli_path), *base_args]
    if wallet:
        cmd.append(f"-rpcwallet={wallet}")
    cmd.extend(str(a) for a in args)
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "RPC failed: {}\n{}".format(" ".join(cmd), exc.output)
        ) from exc
    return json.loads(out, parse_float=Decimal) if json_out else out.strip()


def json_ready(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    return value


def wait_for_rpc(cli_path, base_args, timeout_seconds):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            cli_call(cli_path, base_args, "getblockchaininfo")
            return
        except Exception:
            time.sleep(1)
    raise RuntimeError("bitcoinIId RPC did not become ready")


def mine_one(cli_path, base_args, address, maxtries):
    start = time.time()
    result = cli_call(cli_path, base_args, "generatetoaddress", 1, address, maxtries)
    info = cli_call(cli_path, base_args, "getblockchaininfo")
    return {
        "return_count": len(result),
        "hashes": result,
        "height": info.get("blocks"),
        "elapsed_seconds": round(time.time() - start, 3),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Probe BitcoinII Core regtest mining and descriptor support."
    )
    parser.add_argument("--daemon", required=True, help="Path to bitcoinIId")
    parser.add_argument("--cli", required=True, help="Path to bitcoinII-cli")
    parser.add_argument(
        "--datadir",
        default=None,
        help="Data directory to use. Defaults to a temporary directory.",
    )
    parser.add_argument("--rpcport", type=int, default=29547)
    parser.add_argument("--port", type=int, default=29548)
    parser.add_argument("--rpcuser", default="bc2probe")
    parser.add_argument("--rpcpassword", default="bc2probe")
    parser.add_argument("--maxtries", type=int, default=100000000)
    parser.add_argument("--startup-timeout", type=int, default=60)
    parser.add_argument(
        "--keep-datadir",
        action="store_true",
        help="Do not delete temporary datadir on exit.",
    )
    parser.add_argument(
        "--mature-watch-funds",
        action="store_true",
        help="Mine additional blocks after the repeat-mining probe so watched coinbase funds mature.",
    )
    args = parser.parse_args()

    daemon_path = Path(args.daemon).resolve()
    cli_path = Path(args.cli).resolve()
    if not daemon_path.exists():
        raise FileNotFoundError(daemon_path)
    if not cli_path.exists():
        raise FileNotFoundError(cli_path)

    temp_dir = None
    if args.datadir:
        data_dir = Path(args.datadir).resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
    else:
        temp_dir = tempfile.mkdtemp(prefix="bitcoinii-regtest-probe-")
        data_dir = Path(temp_dir)

    base_args = [
        "-regtest",
        f"-datadir={data_dir}",
        f"-rpcuser={args.rpcuser}",
        f"-rpcpassword={args.rpcpassword}",
        f"-rpcport={args.rpcport}",
    ]
    daemon_args = [
        str(daemon_path),
        "-regtest",
        f"-datadir={data_dir}",
        "-server=1",
        f"-rpcuser={args.rpcuser}",
        f"-rpcpassword={args.rpcpassword}",
        f"-rpcport={args.rpcport}",
        f"-port={args.port}",
        "-fallbackfee=0.0002",
    ]

    proc = subprocess.Popen(
        daemon_args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_for_rpc(cli_path, base_args, args.startup_timeout)

        chain_info = cli_call(cli_path, base_args, "getblockchaininfo")
        network_info = cli_call(cli_path, base_args, "getnetworkinfo")
        deployment_info = cli_call(cli_path, base_args, "getdeploymentinfo")
        help_import = cli_call(
            cli_path, base_args, "help", "importdescriptors", json_out=False
        )
        help_getdescriptor = cli_call(
            cli_path, base_args, "help", "getdescriptorinfo", json_out=False
        )

        cli_call(cli_path, base_args, "createwallet", "spend", "false", "false", "", "false", "true")
        cli_call(
            cli_path,
            base_args,
            "-named",
            "createwallet",
            "wallet_name=watch",
            "disable_private_keys=true",
            "blank=true",
            "descriptors=true",
        )
        watch_wallet_info = cli_call(cli_path, base_args, "getwalletinfo", wallet="watch")

        address = cli_call(
            cli_path, base_args, "getnewaddress", "", "bech32", wallet="spend", json_out=False
        )
        address_info = cli_call(cli_path, base_args, "getaddressinfo", address, wallet="spend")
        desc_info = cli_call(cli_path, base_args, "getdescriptorinfo", address_info["desc"])
        import_payload = json.dumps(
            [
                {
                    "desc": desc_info["descriptor"],
                    "timestamp": "now",
                    "active": False,
                    "label": "bc2-probe-watch",
                }
            ]
        )
        import_result = cli_call(
            cli_path, base_args, "importdescriptors", import_payload, wallet="watch"
        )
        watch_address_info = cli_call(
            cli_path, base_args, "getaddressinfo", address, wallet="watch"
        )

        first_mine = mine_one(cli_path, base_args, address, args.maxtries)
        second_mine = mine_one(cli_path, base_args, address, args.maxtries)
        third_mine = mine_one(cli_path, base_args, address, args.maxtries)
        watch_received = cli_call(
            cli_path,
            base_args,
            "getreceivedbyaddress",
            address,
            1,
            wallet="watch",
        )
        watch_balances = cli_call(cli_path, base_args, "getbalances", wallet="watch")
        repeat_mining_ok = (
            first_mine["return_count"] > 0
            and second_mine["return_count"] > 0
            and third_mine["return_count"] > 0
        )
        mature_watch_result = None
        if args.mature_watch_funds:
            if repeat_mining_ok:
                maturity_address = cli_call(
                    cli_path,
                    base_args,
                    "getnewaddress",
                    "",
                    "bech32",
                    wallet="spend",
                    json_out=False,
                )
                maturity_hashes = cli_call(
                    cli_path,
                    base_args,
                    "generatetoaddress",
                    100,
                    maturity_address,
                    args.maxtries,
                )
                mature_watch_result = {
                    "maturity_blocks_mined": len(maturity_hashes),
                    "watch_received_by_address_minconf_1": cli_call(
                        cli_path,
                        base_args,
                        "getreceivedbyaddress",
                        address,
                        1,
                        wallet="watch",
                    ),
                    "watch_balances": cli_call(
                        cli_path, base_args, "getbalances", wallet="watch"
                    ),
                    "chain_height": cli_call(
                        cli_path, base_args, "getblockchaininfo"
                    ).get("blocks"),
                }
            else:
                mature_watch_result = {
                    "skipped": "repeat mining failed before maturity check"
                }

        deployments = deployment_info.get("deployments", {})
        result = {
            "datadir": str(data_dir),
            "version": network_info.get("version"),
            "subversion": network_info.get("subversion"),
            "chain": chain_info.get("chain"),
            "descriptor_rpcs_available": {
                "getdescriptorinfo": "getdescriptorinfo" in help_getdescriptor,
                "importdescriptors": "importdescriptors" in help_import,
            },
            "deployments_present": {
                "csv": "csv" in deployments,
                "segwit": "segwit" in deployments,
                "taproot": "taproot" in deployments,
            },
            "watch_wallet_private_keys_enabled": watch_wallet_info.get(
                "private_keys_enabled"
            ),
            "watch_descriptor_import_success": bool(import_result[0].get("success")),
            "watch_address_solvable": watch_address_info.get("solvable"),
            "watch_received_by_address_minconf_1": watch_received,
            "watch_balances_after_mining": watch_balances,
            "mining": {
                "maxtries": args.maxtries,
                "first": first_mine,
                "second": second_mine,
                "third": third_mine,
                "repeat_mining_ok": repeat_mining_ok,
            },
        }
        if mature_watch_result is not None:
            result["mature_watch_funds"] = mature_watch_result
        print(json.dumps(json_ready(result), indent=2))
        return 0 if result["mining"]["repeat_mining_ok"] else 2
    finally:
        try:
            subprocess.run(
                [str(cli_path), *base_args, "stop"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
        finally:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            if temp_dir and not args.keep_datadir:
                shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
