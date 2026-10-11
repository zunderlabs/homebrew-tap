# Homebrew formula for Zunder Guard. Rendered by deploy/guard/packaging/render.sh for each
# release (version and checksums filled in) and committed to github.com/zunderlabs/homebrew-tap
# as Formula/zunder-guard.rb:
#
#   brew install zunderlabs/tap/zunder-guard
#
# Homebrew checks the SHA-256 below, which the release workflow took from the signed release.
# To check the Sigstore signature as well, follow "Verify this release" in the README.
class ZunderGuard < Formula
  desc "Self-hosted risk firewall between trading bots or AI agents and Hyperliquid"
  homepage "https://zunderlabs.com"
  version "1.0.0-rc.5"
  # Source-available, not open source: Elastic License 2.0.
  license "Elastic-2.0"

  on_macos do
    on_arm do
      url "https://github.com/zunderlabs/zunder-guard/releases/download/v1.0.0-rc.5/zunder-guard-v1.0.0-rc.5-darwin-arm64.tar.gz"
      sha256 "f8b19d57a7aabbfd10a5d2d5912486cd0e8cdb23dec80ac9cb8e0b64db030dbe"
    end
    on_intel do
      url "https://github.com/zunderlabs/zunder-guard/releases/download/v1.0.0-rc.5/zunder-guard-v1.0.0-rc.5-darwin-amd64.tar.gz"
      sha256 "21ea1a660f8959c117b3caf10926ee009d92d41e80f2e498697e757362a03002"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/zunderlabs/zunder-guard/releases/download/v1.0.0-rc.5/zunder-guard-v1.0.0-rc.5-linux-arm64.tar.gz"
      sha256 "dc8f0aedd310f2af8a615efb9a72c3a84ea9a46c8f21d062684d5f6edf5463d0"
    end
    on_intel do
      url "https://github.com/zunderlabs/zunder-guard/releases/download/v1.0.0-rc.5/zunder-guard-v1.0.0-rc.5-linux-amd64.tar.gz"
      sha256 "eeb12fd06ce2b5184e4b3936339d78a1bdce14d2e524b4cbe3e808b0c09f0552"
    end
  end

  def install
    bin.install "zunder-guard"
    pkgshare.install "LICENSE", "NOTICE", "THIRD_PARTY_LICENSES.md"
  end

  # Paper mode on 127.0.0.1 (unless `init` chose another address). `run` sends only where
  # --network says and only when that is the mode init recorded, so a testnet or mainnet setup
  # refuses this service. Sending modes use an explicit foreground start (caveats).
  service do
    run [opt_bin/"zunder-guard", "run", "--network", "paper"]
    environment_variables ZUNDER_GUARD_HOME: var/"zunder-guard"
    # launchd uses SuccessfulExit=false; systemd needs crashed=true for on-failure.
    keep_alive successful_exit: false, crashed: true
    log_path var/"log/zunder-guard.log"
    error_log_path var/"log/zunder-guard.log"
  end

  def caveats
    <<~EOS
      Use the same home for setup, pairing, licence commands and every start:
        export ZUNDER_GUARD_HOME="#{var}/zunder-guard"
        zunder-guard init --interactive
      Init creates your first client key and pairing code. To add another bot:
        zunder-guard pair
      Restart Guard after adding a client. Keep pairing output private.

      Paper mode only:
        brew services start zunder-guard
      For a testnet config, stop the service and run explicitly:
        brew services stop zunder-guard
        zunder-guard run --network testnet

      Mainnet works in the foreground on macOS and Linux. Guided init asks you to
      type mainnet, confirm the account and choose the equity cap; it checks the
      API wallet key without storing it. At your go-ahead, initialize the mainnet
      journal with journal-init --mode mainnet --note, then start with
      run --network mainnet --key-stdin. Both commands require
      ZUNDER_MAINNET_CONFIRM naming the configured account; run needs the key
      from your secret manager on standard input at every start.
      brew services cannot provide that credential and remains paper-only.
      For unattended mainnet use the separately verified protected installer:
      Linux uses systemd-creds; macOS uses System Keychain and launchd.
      Never elevate a user-writable Homebrew Cellar executable for that setup.

      Setup, licence activation, restart, upgrades and removal:
        https://zunderlabs.com/docs/deploy/packages/
      Guard's default listen address is 127.0.0.1:8547.
    EOS
  end

  test do
    assert_match "zunder-guard", shell_output("#{bin}/zunder-guard --version")
    %w[LICENSE NOTICE THIRD_PARTY_LICENSES.md].each do |notice|
      assert_path_exists pkgshare/notice
    end
  end
end
