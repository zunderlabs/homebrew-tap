# Zunder Guard Homebrew tap

This is the Homebrew tap for [Zunder Guard](https://github.com/zunderlabs/zunder-guard), a self-hosted risk firewall for trading bots and AI agents using Hyperliquid.

The tap is being prepared. **No formula is published yet.** Installation becomes available after the first verified formula PR is reviewed and merged. Do not copy the unrendered formula template into this repository.

Once published:

```sh
brew install zunderlabs/tap/zunder-guard
export ZUNDER_GUARD_HOME="$(brew --prefix)/var/zunder-guard"
zunder-guard init --interactive
```

Run Homebrew as your normal user. Follow the [installation and lifecycle guide](https://zunderlabs.com/docs/deploy/packages/) for pairing, licence activation, explicit network selection, upgrades and removal. `brew services` runs paper mode only. Mainnet foreground operation requires account confirmation, the configured risk limits and equity cap, journal initialization and the API-wallet key on standard input. Unattended mainnet uses the separately verified protected installer on Linux or macOS; never run a user-writable Homebrew Cellar executable as root.

## How formula updates are verified

The product release workflow opens a PR containing the exact `zunder-guard.rb` asset from a signed release. Before executing it, this tap's CI verifies the checksum manifest with Sigstore, checks the exact formula hash and requires the latest stable upstream release. Native jobs cover macOS and Linux on ARM64 and x86-64, including paper-service restart and state preservation through reinstall and removal.

Every PR runs the four required jobs, including documentation changes. When neither the base nor candidate contains a formula, each job explicitly reports bootstrap documentation only: no formula installation was tested. Removing an existing formula fails. Once a formula exists, every PR runs its signature verification and native lifecycle checks. Paper CI does not prove mainnet credential handling, host reboot or licence activation: separate release and Homebrew channel observations are required before publication.

See the upstream [distribution documentation](https://github.com/zunderlabs/zunder-guard/blob/main/deploy/guard/README.md) for installation and verification guidance. Update this README's preparation status when the first verified formula is merged.

## Licence

Zunder Guard is source-available under the [Elastic License 2.0](LICENSE), not open source. [NOTICE](NOTICE) preserves the product's licensing and trademark notices; source-file references in that notice refer to the upstream repository. Each binary archive supplies its own `THIRD_PARTY_LICENSES.md` alongside `LICENSE` and `NOTICE`.
