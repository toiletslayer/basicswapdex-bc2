# BitcoinII Core Upstream Issue Draft

Use this draft to open an issue at:

`https://github.com/Bitcoin-II/BitcoinII-Core/issues/new`

## Title

```text
Regtest generatetoaddress stops after first block
```

## Body

````markdown
## Summary

BitcoinII Core v29.1.0 appears unable to repeatedly mine regtest blocks with `generatetoaddress`. The first block mines successfully, but later `generatetoaddress` calls return an empty block list even with a very high `maxtries` value.

This blocks automated BasicSwap DEX regtest swap validation for BitcoinII / BC2 because test wallets cannot reliably mature coinbase funds or confirm swap transactions.

## Observed behavior

Tested against the BitcoinII Core v29.1.0 Windows CLI release:

- `generatetoaddress 1 <address>` mines the first regtest block.
- Subsequent `generatetoaddress` calls return `[]`.
- Raising `maxtries` to `100000000` still returns `[]`.
- `setgenerate` is not available.

## Expected behavior

On regtest, repeated `generatetoaddress` calls should mine blocks predictably, similar to Bitcoin Core regtest behavior.

## Diagnosis

In `src/kernel/chainparams.cpp`, regtest appears configured for easy mining:

- `powLimit = 7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff`
- `fPowAllowMinDifficultyBlocks = true`
- `fPowNoRetargeting = true`
- `m_is_mockable_chain = true`

However, regtest genesis is created with the harder mainnet-style compact target:

```cpp
genesis = CreateGenesisBlock(1750495460, 3948631054, 0x1d00ffff, 1, 50 * COIN);
```

Because retargeting is disabled, the hard `0x1d00ffff` target appears to carry forward after genesis, making later regtest blocks impractical to mine with normal test commands.

## Candidate fix

A regtest-only patch that changes the regtest genesis `nBits` to `0x207fffff` and updates the resulting regtest genesis hash/checkpoint passed local validation.

Patch and validation notes are here:

- Patch: https://github.com/toiletslayer/basicswapdex-bc2/blob/main/patches/bitcoinii-core-regtest-mining-fix.patch
- Reproduction/validation doc: https://github.com/toiletslayer/basicswapdex-bc2/blob/main/docs/bitcoinii-core-regtest-mining.md
- Probe script: https://github.com/toiletslayer/basicswapdex-bc2/blob/main/scripts/probe_bitcoinii_regtest.py

## Validation with candidate fix

A patched Windows build mined repeated regtest blocks successfully:

- `getdescriptorinfo` and `importdescriptors` available.
- `getdeploymentinfo` lists `csv`, `segwit`, and `taproot`.
- descriptor import into a private-key-disabled watch wallet succeeds.
- three consecutive `generatetoaddress` calls mined blocks at heights 1, 2, and 3.
- optional funded watch-wallet probe mined 100 additional blocks and observed mature trusted watch-only funds.

Would you prefer this regtest genesis target/checkpoint update as a PR, or is there another preferred fix direction for BitcoinII regtest mining?
````
