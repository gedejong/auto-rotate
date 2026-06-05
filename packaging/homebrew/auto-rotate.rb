# Homebrew Cask for Auto-Rotate. Host in a tap repo (e.g. gedejong/homebrew-auto-rotate),
# then: `brew install --cask gedejong/auto-rotate/auto-rotate`.
# Update `version` and `sha256` from each GitHub release's .dmg asset.
cask "auto-rotate" do
  version "0.1.0"
  sha256 :no_check # replace with the release .dmg SHA-256

  url "https://github.com/gedejong/auto-rotate/releases/download/v#{version}/Auto-Rotate-#{version}.dmg"
  name "Auto-Rotate"
  desc "Deskew and turn upright every page of a PDF"
  homepage "https://github.com/gedejong/auto-rotate"

  depends_on macos: ">= :big_sur"

  app "Auto-Rotate.app"

  # Optional features need Tesseract / OCRmyPDF on PATH.
  # depends_on formula: "tesseract"
  # depends_on formula: "ocrmypdf"

  zap trash: [
    "~/Library/Application Support/Auto-Rotate",
    "~/Library/Preferences/dev.gedejong.autorotate.plist",
  ]
end
