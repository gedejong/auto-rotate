# Package-manager distribution

| Channel | Status | Notes |
| --- | --- | --- |
| PyPI | **live** | Published on tag via Trusted Publishing (`release.yml` → `pypi` job). |
| Homebrew (macOS) | **live** | Tap [`gedejong/homebrew-auto-rotate`](https://github.com/gedejong/homebrew-auto-rotate); cask auto-bumped on each release (see below). `homebrew/auto-rotate.rb` here is the original template. |
| winget (Windows) | template | `winget/` stub; submit to `microsoft/winget-pkgs` after a release. |
| Flathub (Linux) | template | `flatpak/dev.gedejong.autorotate.yaml` stub; submit to Flathub after a release. |

## macOS signing & notarization

See [`macos-signing.md`](macos-signing.md). When the `MACOS_*` secrets are set, the release
job signs with a Developer ID and notarizes via Briefcase; otherwise it ad-hoc signs.

## Homebrew cask auto-bump

The `homebrew` job in `release.yml` updates the tap's `Casks/auto-rotate.rb` (version +
SHA-256 of the published `.dmg`) on every `v*` tag and pushes it to the tap.

It is **inert until** a repository secret named **`HOMEBREW_TAP_TOKEN`** is set:

- Create a fine-grained PAT scoped to **`gedejong/homebrew-auto-rotate`** with
  **Contents: Read and write**.
- Add it as `HOMEBREW_TAP_TOKEN` under the `auto-rotate` repo's Actions secrets.

Without the secret the job runs but does nothing (so releases never fail on it).

winget/Flathub still need a manual version + SHA-256 bump in their manifests per release.
