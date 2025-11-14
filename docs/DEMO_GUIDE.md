# Creating the Demo GIF

## Tools for Recording

### macOS
- **Kap** (Recommended): https://getkap.co/
  - Free, open-source screen recorder
  - Built-in GIF export
  - `brew install --cask kap`

- **Gifox**: https://gifox.io/
  - Paid ($14.99)
  - Professional quality GIFs
  - `brew install --cask gifox`

- **LICEcap**: https://www.cockos.com/licecap/
  - Free, lightweight
  - Simple GIF recording

### Terminal Recording (Alternative)
```bash
# Install asciinema for terminal recording
brew install asciinema

# Install agg to convert to GIF
cargo install --git https://github.com/asciinema/agg

# Record session
asciinema rec demo.cast

# Convert to GIF
agg demo.cast docs/demo.gif
```

## Demo Script

### Scenario 1: Interactive Search (15-20 seconds)
```bash
# Start with interactive mode
awsf

# Type "payment" to filter
# Show results appearing
# Navigate with arrows
# Press Enter to open in console
```

### Scenario 2: Service-Specific Search (10-15 seconds)
```bash
# Search Lambda functions
awsf lambda auth

# Show filtered results
# Select one and open
```

### Scenario 3: Quick Direct Search (10 seconds)
```bash
# Direct search with term
awsf s3 media

# Show match and open
```

## Recording Tips

1. **Terminal Setup**:
   - Use a clean terminal window
   - Font size: 14-16pt (readable in GIF)
   - Theme: Dark theme with good contrast
   - Window size: 1200x800px (or similar 16:10 ratio)

2. **Recording Settings**:
   - Frame rate: 15-20 fps (smooth but small file)
   - Format: GIF (max 10MB for GitHub)
   - Quality: Medium-High (balance size vs clarity)
   - Duration: 20-30 seconds total

3. **Before Recording**:
   - Clear terminal: `clear`
   - Ensure AWS resources are populated: `python3 scripts/populate_resources.py`
   - Test your commands
   - Close unnecessary windows

4. **During Recording**:
   - Type at a moderate, readable pace
   - Pause briefly after each command
   - Show the interactive features (arrow navigation, Enter to open)
   - Demonstrate 2-3 different use cases

5. **After Recording**:
   - Trim any dead time at start/end
   - Optimize GIF size if needed
   - Test playback in README locally

## Example Recording Flow

1. **Start Recording**
2. Clear screen: `clear`
3. Show help: `awsf -h` (scroll briefly)
4. Interactive search: `awsf` → type "payment" → navigate → select
5. Service search: `awsf lambda auth` → select result
6. **Stop Recording**
7. Export to `docs/demo.gif`

## File Location

Save the final GIF as:
```
docs/demo.gif
```

## Optimization

If the GIF is too large (>10MB):

```bash
# Install gifsicle
brew install gifsicle

# Optimize the GIF
gifsicle -O3 --lossy=80 -o docs/demo.gif docs/demo-original.gif
```

## Preview Before Commit

Test locally:
```bash
# View in browser
open README.md  # If you have a Markdown viewer

# Or commit to a branch and view on GitHub
git checkout -b add-demo
git add docs/demo.gif README.md
git commit -m "Add demo GIF"
git push -u origin add-demo
```
