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

The patch has not yet been compiled in this environment because CMake/Ninja/MSVC build tools are not installed on the current PC. After building a patched `bitcoinIId`, rerun:

```bash
python scripts/probe_bitcoinii_regtest.py --daemon /path/to/patched/bitcoinIId --cli /path/to/patched/bitcoinII-cli
```

The expected patched result is `repeat_mining_ok: true`.

Until that is fixed or a dedicated testing binary is provided, BasicSwap can start and configure BC2, but full automated regtest swap tests cannot be completed reliably.
