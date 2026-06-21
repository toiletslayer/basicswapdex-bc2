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

## Roadmap

### Done

- Confirmed the BasicSwap requirement set and matched BC2 against the BTC-like integration path.
- Added BC2 chain parameters and interface code.
- Added `basicswap-prepare` support for BitcoinII v29.1.0 binaries and config generation.
- Added runtime wiring for daemon arguments, wallet creation, descriptor wallets, and seed checks.
- Verified `bitcoinii` naming and avoided `BTC2` naming.

### Next Verification

- Explicitly test watch-only descriptor import/use against `bitcoinIId` regtest. The current code creates a descriptor watch wallet, but the watch-only requirement should be demonstrated directly.
- Run the equivalent of the old BasicSwap requirements script manually because the current BasicSwap repo no longer includes `scripts/requirements.python`.
- Run a full managed BasicSwap startup with Particl plus BC2.
- Run a live regtest swap path using BC2 as the BTC-like side.

### Packaging And Upstream Readiness

- Find or request a signed checksum source for BitcoinII releases. Current prepare support logs the release SHA256 but cannot fully verify it against a signed upstream checksum file.
- Check whether upstream BasicSwap wants BC2 release downloads from `Bitcoin-II/BitcoinII-Core` or a separate binary-release repository.
- Add/update extended regtest tests if upstream maintainers want BC2 covered like Namecoin/Dogecoin.
- Decide whether upstream BasicSwap wants BitcoinII as a built-in coin or maintained as a downstream fork.
