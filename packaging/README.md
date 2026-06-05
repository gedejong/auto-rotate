# Package-manager distribution

| Channel | Status | Notes |
| --- | --- | --- |
| PyPI | **live** | Published on tag via Trusted Publishing (`release.yml` → `pypi` job). |
| Homebrew (macOS) | **live** | Tap [`gedejong/homebrew-auto-rotate`](https://github.com/gedejong/homebrew-auto-rotate); cask auto-bumped on each release (see below). `homebrew/auto-rotate.rb` here is the original template. |
| winget (Windows) | ready to submit | `winget/` holds the three 0.1.0 manifests (schema-validated, real SHA-256 + ProductCode). See "winget submission" below. |
| Flathub (Linux) | not started | Needs an offline-from-source Flatpak build of the full native stack + AppStream metadata; only build-testable on Linux. Bigger effort — see notes below. |

## winget submission

`packaging/winget/` contains the three manifests winget requires (`version`, `installer`,
`locale`), already validated against the v1.6.0 JSON schemas, with the real installer
SHA-256 and the MSI's ProductCode/UpgradeCode. To publish to the public index, submit them
to [`microsoft/winget-pkgs`](https://github.com/microsoft/winget-pkgs) under
`manifests/g/gedejong/AutoRotate/0.1.0/` — either:

- **`wingetcreate`** (Windows): `wingetcreate update gedejong.AutoRotate` or
  `wingetcreate new <msi-url>` then `--submit` (auto-forks + opens the PR), or
- a manual fork + PR placing the three files at that path.

Microsoft's validation bot installs the MSI in a sandbox; unsigned installers are accepted
but may draw extra moderator review. On each new release, bump `PackageVersion`, the
`InstallerUrl`, and `InstallerSha256`, then resubmit.

## Homebrew cask auto-bump

The `homebrew` job in `release.yml` updates the tap's `Casks/auto-rotate.rb` (version +
SHA-256 of the published `.dmg`) on every `v*` tag and pushes it to the tap.

It is **inert until** a repository secret named **`HOMEBREW_TAP_TOKEN`** is set:

- Create a fine-grained PAT scoped to **`gedejong/homebrew-auto-rotate`** with
  **Contents: Read and write**.
- Add it as `HOMEBREW_TAP_TOKEN` under the `auto-rotate` repo's Actions secrets.

Without the secret the job runs but does nothing (so releases never fail on it).

winget/Flathub still need a manual version + SHA-256 bump in their manifests per release.
