# macOS code signing & notarization

The `release.yml` macOS job signs and notarizes the app automatically **when the secrets
below are present**. Without them it falls back to ad-hoc signing (the app runs, but
Gatekeeper warns on first launch). Briefcase does the signing, notarization, and stapling
itself — `package macOS --identity …` notarizes by default; CI just has to put the
certificate and the notarization credentials where Briefcase/codesign can find them.

## Required repository secrets

Add these under the **`auto-rotate`** repo → Settings → Secrets and variables → Actions:

| Secret | What it is |
| --- | --- |
| `MACOS_SIGNING_IDENTITY` | The identity name, e.g. `Developer ID Application: Edwin de Jong (TEAMID)`. Presence of this secret is what switches CI from ad-hoc to signed. |
| `MACOS_CERTIFICATE` | Base64 of your exported **Developer ID Application** certificate (`.p12`). |
| `MACOS_CERTIFICATE_PASSWORD` | The password you set when exporting the `.p12`. |
| `MACOS_TEAM_ID` | Your 10-character Apple Developer Team ID. |
| `MACOS_APPLE_ID` | The Apple ID email used for notarization. |
| `MACOS_APPLE_ID_PASSWORD` | An **app-specific password** for that Apple ID (not your login password). |

## Getting each value (one-time, on a Mac)

1. **Developer ID Application certificate.** In Xcode → Settings → Accounts → your team →
   *Manage Certificates* → `+` → **Developer ID Application** (or create it at
   developer.apple.com → Certificates). Then in **Keychain Access**, find
   *"Developer ID Application: … (TEAMID)"*, right-click → **Export** → `.p12`, set a
   password. Base64 it for the secret:

   ```bash
   base64 -i DeveloperID.p12 | pbcopy   # paste into MACOS_CERTIFICATE
   ```

2. **Identity string + Team ID.** Run:

   ```bash
   security find-identity -p codesigning -v
   ```

   Copy the full `Developer ID Application: … (TEAMID)` string into `MACOS_SIGNING_IDENTITY`;
   the parenthesised 10-char `TEAMID` is `MACOS_TEAM_ID`.

3. **App-specific password.** Sign in at <https://appleid.apple.com> → *Sign-In and Security*
   → *App-Specific Passwords* → generate one (label it e.g. "notarytool"). That value is
   `MACOS_APPLE_ID_PASSWORD`; the Apple ID email is `MACOS_APPLE_ID`.

## How CI uses them

The `Set up signing keychain + notarization profile` step:

- imports the `.p12` into a dedicated, default keychain so `codesign` finds the identity;
- runs `xcrun notarytool store-credentials briefcase-macOS-<TEAM_ID> …` — the **exact profile
  name Briefcase looks for** — so notarization runs without prompting.

Then `briefcase package macOS --identity "$MACOS_SIGNING_IDENTITY"` signs → submits to Apple →
waits → staples. Expect the job to take a few extra minutes while Apple notarizes.

## After the first notarized release

Update the Homebrew cask in `gedejong/homebrew-auto-rotate` to drop the
"not notarized / right-click to open" caveat — notarized builds open normally.

## Notes

- 0.1.0 ships an Apple-Silicon-only build (`min_os_version = 14.0`). Notarization is
  arch-independent; an Intel/universal build is a separate change (universal2 wheels).
- App Store Connect API keys can replace the app-specific password (swap the
  `store-credentials` flags to `--key/--key-id/--issuer`) if you prefer key-based auth.
