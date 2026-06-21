# BitcoinII / BC2 BasicSwap Integration

This branch adds initial BasicSwap support for BitcoinII / BC2 as a Bitcoin Core-like SHA-256 PoW chain.

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

## Remaining Before Upstream Submission

- Find or request a signed checksum source for BitcoinII releases. Current prepare support logs the release SHA256 but cannot fully verify it against a signed upstream checksum file.
- Run a full managed BasicSwap startup with Particl plus BC2.
- Run a live regtest swap path using BC2 as the BTC-like side.
- Decide whether upstream BasicSwap wants BitcoinII as a built-in coin or maintained as a downstream fork.
