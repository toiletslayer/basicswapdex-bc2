# BitcoinII Core Regtest Mining Blocker

BitcoinII / BC2 BasicSwap swap tests need predictable regtest block generation so test wallets can mature coinbase funds and confirm swap transactions.

## Observed Behavior

Tested against BitcoinII Core v29.1.0 Windows CLI release:

- `generatetoaddress 1 <address>` mines the first regtest block.
- Subsequent `generatetoaddress` calls return an empty block list.
- Raising `maxtries` to `100000000` still returns no additional blocks.
- `setgenerate` is not available.

This prevents maturing coinbase funds and blocks automated BasicSwap regtest swap validation.

## Reproduction Probe

This branch includes a standalone probe script:

```bash
python scripts/probe_bitcoinii_regtest.py --daemon /path/to/bitcoinIId --cli /path/to/bitcoinII-cli
```

The script checks:

- descriptor RPC availability.
- CSV, Segwit, and Taproot deployment visibility.
- descriptor import into a private-key-disabled watch wallet.
- three consecutive `generatetoaddress` attempts.

Expected result with the v29.1.0 release binary: descriptor/watch checks pass, the first mining attempt returns one block, later mining attempts return no blocks, and the script exits nonzero.

## Requirement Impact

The BasicSwap integration requirements are otherwise lining up:

- Descriptor RPCs are present.
- Watch-only descriptor import succeeds in a private-key-disabled wallet.
- `getdeploymentinfo` lists `csv`, `segwit`, and `taproot`.

The missing piece is practical local block generation for swap tests.

## Source Diagnosis

In `Bitcoin-II/BitcoinII-Core`, `src/kernel/chainparams.cpp`, regtest is configured as if it should be easy to mine:

- `powLimit = 7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff`
- `fPowAllowMinDifficultyBlocks = true`
- `fPowNoRetargeting = true`
- `m_is_mockable_chain = true`

However, the regtest genesis block is created with:

```cpp
genesis = CreateGenesisBlock(1750495460, 3948631054, 0x1d00ffff, 1, 50 * COIN);
```

Because retargeting is disabled, the hard `0x1d00ffff` target appears to carry forward after genesis, making later regtest blocks impractical to mine with normal test commands.

## Likely Fix Direction

BitcoinII Core probably needs a regtest-specific genesis setup with an easy `nBits` value, similar to Bitcoin Core-style regtest behavior, and updated expected regtest genesis hash assertions.

An initial source patch is included at:

```text
patches/bitcoinii-core-regtest-mining-fix.patch
```

That patch changes only regtest chain parameters:

- regtest genesis `nBits` from `0x1d00ffff` to `0x207fffff`.
- regtest genesis hash assertion to the resulting hash.
- regtest height-0 checkpoint to the resulting hash.

## Patched Build Validation

The patch was built locally on Windows with Visual Studio 2022, CMake, and vcpkg using a daemon/CLI-only configuration:

```powershell
$env:VCPKG_ROOT='C:\Program Files\Microsoft Visual Studio\2022\Community\VC\vcpkg'
cmake -S C:\bc2src -B C:\bcli -G 'Visual Studio 17 2022' -A x64 `
  -DCMAKE_TOOLCHAIN_FILE="$env:VCPKG_ROOT\scripts\buildsystems\vcpkg.cmake" `
  -DVCPKG_TARGET_TRIPLET=x64-windows-static `
  -DVCPKG_MANIFEST_NO_DEFAULT_FEATURES=ON `
  -DVCPKG_MANIFEST_FEATURES=wallet `
  -DBUILD_GUI=OFF -DBUILD_TESTS=OFF -DBUILD_BENCH=OFF `
  -DBUILD_FUZZ_BINARY=OFF -DBUILD_TX=OFF -DBUILD_UTIL=OFF `
  -DBUILD_WALLET_TOOL=OFF -DBUILD_CLI=ON -DBUILD_DAEMON=ON `
  -DENABLE_WALLET=ON -DWITH_BDB=ON -DWITH_SQLITE=ON -DWITH_ZMQ=OFF
cmake --build C:\bcli --config Release --target bitcoinIId bitcoinII-cli --parallel
```

The patched binaries passed the probe:

```bash
python scripts/probe_bitcoinii_regtest.py --daemon /path/to/patched/bitcoinIId --cli /path/to/patched/bitcoinII-cli
```

Observed result:

- `getdescriptorinfo` and `importdescriptors` are available.
- `getdeploymentinfo` lists `csv`, `segwit`, and `taproot`.
- descriptor import into a private-key-disabled watch wallet succeeds.
- three consecutive `generatetoaddress` calls mined blocks at heights 1, 2, and 3.
- `repeat_mining_ok: true`.

The optional funded watch-wallet check also passed:

```bash
python scripts/probe_bitcoinii_regtest.py --daemon /path/to/patched/bitcoinIId --cli /path/to/patched/bitcoinII-cli --mature-watch-funds
```

That run mined 100 additional blocks after the first three probe blocks. The watch wallet reported the watched coinbase outputs as mature and trusted:

- `watch_received_by_address_minconf_1: 150.00000000`
- `watch_balances.mine.trusted: 150.00000000`
- final chain height: `103`

This clears the Core-side blocker for automated BasicSwap regtest swap validation, assuming the patched BitcoinII Core binary or equivalent upstream fix is used.
