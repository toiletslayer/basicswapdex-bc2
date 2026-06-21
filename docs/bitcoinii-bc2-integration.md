# BitcoinII / BC2 BasicSwap Integration

This branch adds initial BasicSwap support for BitcoinII / BC2 as a Bitcoin Core-like SHA-256 PoW chain.

## Integration Checklist

BasicSwap's published coin integration guidance says each coin is case-by-case, but the readily integrated path requires:

- UTXO scripts.
- CLTV or CSV.
- Segwit enabled.
- Watch-only address support.
- Comparison against similar existing BasicSwap coin integrations.

Source: Particl Academy, "Integrate a Coin", `https://academy.particl.io/en/latest/basicswap-guides/basicswapguides_apply.html`.

The Academy page notes this requirement list was current for BasicSwap v0.13.4. This branch is based on BasicSwap v0.16.5, so the checklist is treated as the official baseline while the implementation is verified against the current repository patterns.

BitcoinII / BC2 is a Bitcoin Core-derived chain, so this branch follows the existing BTC-like integration pattern used by coins such as Dogecoin and Namecoin: add chain parameters, add a small `BTCInterface` subclass, wire interface creation and wallet seed checks, add prepare/download/config support, and then validate with daemon and swap tests.

## Added

- `Coins.BC2` chain parameters for mainnet, testnet4, and regtest.
- `BitcoinIIInterface`, derived from `BTCInterface`.
- BasicSwap interface selection, seed ID handling, wallet creation, and daemon argument wiring for BC2.
- `basicswap-prepare` support for `--withcoins=bitcoinii`.
- BitcoinII v29.1.0 release download and extraction support.
- Test coverage for BC2 chain parameter lookup and interface coin type.

## BitcoinII Details Used

- Coin name: `bitcoinii`
- Ticker: `BC2`
- Display name: `BitcoinII`
- Daemon: `bitcoinIId`
- CLI: `bitcoinII-cli`
- Mainnet RPC port: `8337`
- Mainnet P2P port: `8338`
- Testnet name: `testnet4`
- Testnet RPC port: `48337`
- Regtest RPC port: `18447`
- Message magic: `BitcoinII Signed Message:\n`

## Verified Locally

- Python syntax checks for changed modules.
- BC2 chain parameter/interface unit test.
- `basicswap-prepare` dry-runs for regtest and testnet with `--nocores`.
- BitcoinII v29.1.0 Windows CLI archive download and extraction.
- `bitcoinIId` regtest RPC smoke test.
- Watch-only descriptor import against a private-key-disabled `bitcoinIId` regtest wallet.
- Manual requirement probe against `bitcoinIId` v29.1.0:
  - descriptor RPCs `getdescriptorinfo` and `importdescriptors` are available.
  - `getdeploymentinfo` lists `csv`, `segwit`, and `taproot`.
  - the daemon reports `/Satoshi:29.1.0/`.
- Patched BitcoinII Core regtest build from `patches/bitcoinii-core-regtest-mining-fix.patch`:
  - built `bitcoinIId.exe` and `bitcoinII-cli.exe` with wallet support and without GUI/tests/ZMQ.
  - mined three consecutive regtest blocks with `generatetoaddress`.
  - passed the descriptor/watch-only/mining probe with `repeat_mining_ok: true`.
  - mined 100 additional blocks and verified the watch wallet saw `150.00000000` trusted mature BC2.
- Managed regtest setup with Particl plus BC2:
  - downloaded and extracted Particl Core v27.2.3.0.
  - prepared a wallet-initialized `--regtest` BasicSwap datadir with `particl` and `bitcoinii`.
  - created BC2 `bsx_wallet` and descriptor watch wallet `bsx_watch`.
  - started full `basicswap-run` and confirmed the UI returned HTTP 200.
  - confirmed BasicSwap detected `BitcoinII Core version 290100`.
  - confirmed the BC2 wallet seed check passed without the "not derived from swap seed" warning.

## Roadmap

### Done

- Confirmed the BasicSwap requirement set and matched BC2 against the BTC-like integration path.
- Added BC2 chain parameters and interface code.
- Added `basicswap-prepare` support for BitcoinII v29.1.0 binaries and config generation.
- Added runtime wiring for daemon arguments, wallet creation, descriptor wallets, and seed checks.
- Verified project naming uses `bitcoinii`, `BitcoinII`, and `BC2` consistently.
- Verified BitcoinII descriptor import into a private-key-disabled watch wallet:
  - `createwallet watch disable_private_keys=true blank=true descriptors=true`
  - `importdescriptors` returned success.
  - `getaddressinfo` on the imported address returned solvable descriptor data.
- Ran a manual equivalent of the old requirements script as far as the current repo/release allows:
  - UTXO/script behavior follows the Bitcoin Core-derived code path and BTC-like interface.
  - CSV and Segwit are present in `getdeploymentinfo`.
  - descriptor watch-only wallet RPCs are available and import succeeds.
- Prepared an initial BitcoinII Core regtest mining patch at `patches/bitcoinii-core-regtest-mining-fix.patch`.
- Built the patched BitcoinII Core daemon/CLI locally and verified repeat regtest mining works.
- Verified funded watch-only balance tracking against the patched regtest daemon.
- Verified managed Particl plus BC2 regtest startup through BasicSwap's runner.

### Next Verification

- Run a live regtest swap path using BC2 as the BTC-like side.

### Packaging And Upstream Readiness

- Find or request a signed checksum source for BitcoinII releases. Current prepare support logs the release SHA256 but cannot fully verify it against a signed upstream checksum file.
- Check whether upstream BasicSwap wants BC2 release downloads from `Bitcoin-II/BitcoinII-Core` or a separate binary-release repository.
- Add/update extended regtest tests if upstream maintainers want BC2 covered like Namecoin/Dogecoin.
- Decide whether upstream BasicSwap wants BitcoinII as a built-in coin or maintained as a downstream fork.

### Local Test Notes

- The local Particl binary download hash matched the downloaded Particl assert file. Signature verification was skipped for that one local download because Git for Windows `gpg.exe` was available but failed under the Python/GPG path handling in this environment.
- The local managed tests use patched BC2 binaries built from `patches/bitcoinii-core-regtest-mining-fix.patch`; the stock BC2 v29.1.0 release binary still cannot repeatedly mine regtest blocks.
