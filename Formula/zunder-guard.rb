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
  version "1.0.0-rc.11"
  # Source-available, not open source: Elastic License 2.0.
  license "Elastic-2.0"

  on_macos do
    on_arm do
      url "https://github.com/zunderlabs/zunder-guard/releases/download/v1.0.0-rc.11/zunder-guard-v1.0.0-rc.11-darwin-arm64.tar.gz"
      sha256 "5e884671c095af8361626780aa77a9583c34262b0c19bd6c9a47a18ca2f476f1"
    end
    on_intel do
      url "https://github.com/zunderlabs/zunder-guard/releases/download/v1.0.0-rc.11/zunder-guard-v1.0.0-rc.11-darwin-amd64.tar.gz"
      sha256 "3763ee65e74785ff0df4765302eb9f636111df7b68e5a994d11d29e8ddfb5848"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/zunderlabs/zunder-guard/releases/download/v1.0.0-rc.11/zunder-guard-v1.0.0-rc.11-linux-arm64.tar.gz"
      sha256 "e5102ce7cc9f5003fb69937fc10d69f5196022745c19e26e3c6f958ebf56036b"
    end
    on_intel do
      url "https://github.com/zunderlabs/zunder-guard/releases/download/v1.0.0-rc.11/zunder-guard-v1.0.0-rc.11-linux-amd64.tar.gz"
      sha256 "76ac90113d399d3ab458a8bd728ed79db2be263c76d78952e760737433e9f851"
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
