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

## Roadmap

### Done

- Confirmed the BasicSwap requirement set and matched BC2 against the BTC-like integration path.
- Added BC2 chain parameters and interface code.
- Added `basicswap-prepare` support for BitcoinII v29.1.0 binaries and config generation.
- Added runtime wiring for daemon arguments, wallet creation, descriptor wallets, and seed checks.
- Verified `bitcoinii` naming and avoided `BTC2` naming.
- Verified BitcoinII descriptor import into a private-key-disabled watch wallet:
  - `createwallet watch disable_private_keys=true blank=true descriptors=true`
  - `importdescriptors` returned success.
  - `getaddressinfo` on the imported address returned solvable descriptor data.
- Ran a manual equivalent of the old requirements script as far as the current repo/release allows:
  - UTXO/script behavior follows the Bitcoin Core-derived code path and BTC-like interface.
  - CSV and Segwit are present in `getdeploymentinfo`.
  - descriptor watch-only wallet RPCs are available and import succeeds.

### Next Verification

- Resolve BC2 regtest mining behavior before full swap tests. The v29.1.0 release binary mined the first regtest block with `generatetoaddress`, then returned an empty block list on later calls even with `maxtries=100000000`. The legacy `setgenerate` RPC is not available. Source review shows regtest is intended to be easy (`powLimit=7fff...`, `fPowAllowMinDifficultyBlocks=true`, `fPowNoRetargeting=true`), but the regtest genesis is created with `nBits=0x1d00ffff`. With no retargeting, that hard target appears to carry forward and prevents practical local mining. This likely needs a BitcoinII Core regtest fix or a dedicated testing binary before automated BasicSwap swap tests can run. Use `scripts/probe_bitcoinii_regtest.py` to retest future binaries.
- After mining is predictable, test funded watch-only balance tracking against `bitcoinIId` regtest. Descriptor import is verified, but a funded balance test needs spendable regtest coins.
- Run a full managed BasicSwap startup with Particl plus BC2. This requires Particl binaries in the test environment.
- Run a live regtest swap path using BC2 as the BTC-like side.

### Packaging And Upstream Readiness

- Find or request a signed checksum source for BitcoinII releases. Current prepare support logs the release SHA256 but cannot fully verify it against a signed upstream checksum file.
- Check whether upstream BasicSwap wants BC2 release downloads from `Bitcoin-II/BitcoinII-Core` or a separate binary-release repository.
- Add/update extended regtest tests if upstream maintainers want BC2 covered like Namecoin/Dogecoin.
- Decide whether upstream BasicSwap wants BitcoinII as a built-in coin or maintained as a downstream fork.
