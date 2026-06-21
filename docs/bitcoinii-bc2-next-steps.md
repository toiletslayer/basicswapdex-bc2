# BitcoinII / BC2 Next Steps

This repo contains a work-in-progress BasicSwap DEX integration for BitcoinII / BC2.

The implementation is already pushed to `main` and includes chain parameters, a BTC-like interface, prepare/download/config support, descriptor wallet support, managed regtest startup fixes, validation docs, and an extended BC2 regtest harness.

## Immediate Tasks

### 1. Run the full BC2 extended regtest suite

Tracking issue: `https://github.com/toiletslayer/basicswapdex-bc2/issues/1`

Run:

```bash
BITCOINII_BINDIR=/path/to/patched/bitcoinii/bin python tests/basicswap/extended/test_bitcoinii.py
```

Current status:

- `tests/basicswap/extended/test_bitcoinii.py` exists and syntax validation passes.
- Managed Particl plus BC2 regtest startup has been validated.
- BC2 descriptor spend/watch wallets have been validated.
- Repeat BC2 regtest mining has been validated with patched BitcoinII Core.
- `TestBC2.test_02_sh_part_coin` passed with Monero startup disabled:
  - local Particl, Bitcoin Core, and patched BitcoinII Core regtest daemons started.
  - a seller-first PART to BC2 offer/bid completed.
  - both swap clients reached `SWAP_COMPLETED`.

Requirements:

- Patched BitcoinII Core binaries from `patches/bitcoinii-core-regtest-mining-fix.patch`.
- Standard BasicSwap extended-test daemon dependencies.
- Enough runtime to execute daemon-backed swap tests.
- On this Windows PC, `monero-wallet-rpc.exe` was blocked by Windows security, so XMR-dependent inherited tests cannot run here unless that executable is allowed or the BC2 tests are split into a smaller PART/BC2-only smoke suite.

Acceptance criteria:

- BC2 extended test setup starts all required daemons. Partial: PART, Bitcoin Core, and BC2 start locally; Monero wallet RPC is blocked by Windows security on this PC.
- PART/BC2 seller-first success path completes. Done for `TestBC2.test_02_sh_part_coin`.
- Refund/error-path checks complete, or any BC2-specific failures are documented with logs.
- Results are copied into `docs/bitcoinii-bc2-integration.md`.

### 2. Upstream the BitcoinII Core regtest mining fix

Tracking issue: `https://github.com/toiletslayer/basicswapdex-bc2/issues/2`

Stock BitcoinII Core v29.1.0 can mine the first regtest block, but later `generatetoaddress` calls return an empty block list. This blocks automated BasicSwap regtest swap validation.

This repo includes:

- `patches/bitcoinii-core-regtest-mining-fix.patch`
- `docs/bitcoinii-core-regtest-mining.md`
- `docs/bitcoinii-core-upstream-issue-draft.md`
- `scripts/probe_bitcoinii_regtest.py`

Acceptance criteria:

- Open an issue or PR against `Bitcoin-II/BitcoinII-Core` with the reproduction, diagnosis, and patch.
- Confirm upstream maintainers agree with the regtest-only target/genesis change or request their preferred fix.
- Update this BasicSwap branch once an upstream BC2 Core release or commit contains the fix.

### 3. Decide the BasicSwap upstream packaging path

Tracking issue: `https://github.com/toiletslayer/basicswapdex-bc2/issues/3`

Options:

- Upstream BC2 as a built-in BasicSwap coin.
- Keep this as a downstream BasicSwap fork until BC2 Core release/signature and regtest issues are settled.
- Split the work into smaller PRs: chain params/interface, prepare support, docs/tests.

Open questions:

- Does BasicSwap require signed release checksum support for BC2 binary downloads?
- Should `basicswap-prepare` download from `Bitcoin-II/BitcoinII-Core` releases or a separate BC2 binary-release repository?
- Should the extended test be the full BTC-like inherited suite or a smaller BC2 smoke test?

Acceptance criteria:

- Pick an upstream strategy.
- Prepare the PR body/checklist using `docs/bitcoinii-bc2-integration.md` as the source of truth.
- If submitting upstream, link the BC2 Core regtest mining issue or PR.
