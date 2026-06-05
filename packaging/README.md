# Package-manager distribution

Templates for shipping Auto-Rotate through OS package managers. These are **follow-ups to the
first GitHub release** — winget and Flathub both require a published, downloadable release to
point at, so wire them up once `v0.1.0` installers exist.

| Channel | File | Notes |
| --- | --- | --- |
| Homebrew (macOS) | `homebrew/auto-rotate.rb` | Cask pointing at the release `.dmg`. Host in a `homebrew-auto-rotate` tap repo. |
| winget (Windows) | `winget/` | Manifest stub; submit to `microsoft/winget-pkgs` after release. |
| Flathub (Linux) | `flatpak/dev.gedejong.autorotate.yaml` | Manifest stub; submit to Flathub after release. |

After each release, bump the version and SHA-256 in each manifest to match the new assets.
