#!/bin/bash
set -e

echo "🍎 Creating macOS App Bundle for AWSF"
echo "====================================="

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# App details
APP_NAME="AWSF"
APP_DIR="/Applications/${APP_NAME}.app"
BUNDLE_ID="com.awsf.app"

print_status "Creating app bundle structure..."

# Remove existing app if it exists
if [[ -d "$APP_DIR" ]]; then
    print_status "Removing existing app bundle..."
    rm -rf "$APP_DIR"
fi

# Create app bundle structure
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>awsf</string>
    <key>CFBundleIdentifier</key>
    <string>${BUNDLE_ID}</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.developer-tools</string>
</dict>
</plist>
EOF

# Create launcher script
cat > "$APP_DIR/Contents/MacOS/awsf" << EOF
#!/bin/bash

# Get the app bundle directory
APP_DIR="\$(dirname "\$(dirname "\$0")")"
PROJECT_ROOT="$PROJECT_ROOT"

# Set up terminal profile for better appearance
osascript -e 'tell application "Terminal"
    activate
    set newTab to do script "cd \\"\\$PROJECT_ROOT\\"; echo \\"🔍 AWSF\\"; echo \\"============\\"; python3 src/awsf.py"
    set current settings of newTab to (first settings set whose name is "AWS Resource Search")
end tell' 2>/dev/null || \\
osascript -e 'tell application "Terminal"
    activate
    do script "cd \\"$PROJECT_ROOT\\"; echo \\"🔍 AWSF\\"; echo \\"============\\"; python3 src/awsf.py"
end tell'
EOF

# Make the launcher executable
chmod +x "$APP_DIR/Contents/MacOS/awsf"

print_success "App bundle created at: $APP_DIR"

# Try to create a better terminal profile
print_status "Setting up terminal profile..."

osascript << 'APPLESCRIPT'
tell application "Terminal"
    -- Create a new profile if it doesn't exist
    try
        set profileName to "AWS Fuzzy Finder"
        
        -- Create new profile based on default
        set newProfile to (duplicate (first settings set whose name is "Basic")) with properties {name:profileName}
        
        -- Customize the profile
        set properties of newProfile to {
            font name:"SF Mono", 
            font size:14, 
            background color:{8738, 10794, 15677}, 
            normal text color:{65535, 65535, 65535},
            cursor color:{65535, 65535, 65535},
            number of columns:120,
            number of rows:40
        }
        
        log "✅ Terminal profile created: " & profileName
    on error e
        log "⚠️  Could not create terminal profile: " & e
    end try
end tell
APPLESCRIPT

# Update Spotlight index
print_status "Updating Spotlight index..."
sudo mdutil -E /Applications >/dev/null 2>&1 || true

print_success "macOS app bundle setup complete!"
echo ""
echo "🎉 You can now:"
echo "• Find 'AWS Fuzzy Finder' in Spotlight"
echo "• Open from Applications folder"
echo "• Add to Dock for quick access"
echo ""
echo "💡 The app will open in Terminal with a custom profile for better appearance."