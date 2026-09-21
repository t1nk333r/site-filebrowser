#!/usr/bin/env python3

import sys
from datetime import datetime
from html import escape
from pathlib import Path

CONTENT_ROOT = Path('html')

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITLE_PLACEHOLDER</title>
<link rel="stylesheet" href="/style.css">
<script>
// The theme is applied from the head, before anything is painted, so a dark
// page never flashes light while the parser walks a long listing. The footer
// button cycles light -> dark -> ember, the choice is remembered in
// localStorage, and #dark or #ember can be linked directly.
var THEMES = ['light', 'dark', 'ember'];

function currentTheme() {
  var index = THEMES.indexOf(location.hash.replace('#', ''));
  if (index > -1) return THEMES[index];
  try {
    var stored = localStorage.getItem('theme');
    if (THEMES.indexOf(stored) > -1) return stored;
  } catch (e) {}
  return 'light';
}

function storeTheme(name) {
  try {
    localStorage.setItem('theme', name);
  } catch (e) {}
}

function applyTheme() {
  var name = currentTheme();
  for (var i = 0; i < THEMES.length; i++) {
    document.documentElement.classList.toggle(THEMES[i], name === THEMES[i]);
  }
}

function toggleTheme() {
  var next = THEMES[(THEMES.indexOf(currentTheme()) + 1) % THEMES.length];
  storeTheme(next);
  location.hash = next === 'light' ? '' : '#' + next;
  applyTheme();
}

window.addEventListener('hashchange', function () {
  storeTheme(currentTheme());
  applyTheme();
});

storeTheme(currentTheme());
applyTheme();
</script>
</head>
<body>
<main>
<h1>TITLE_PLACEHOLDER</h1>
<p>-</p>

<p>Start writing your content here...</p>

<time>DATE_PLACEHOLDER</time>

</main>
<footer>
<p><a href="../"><i>../</i></a></p>
<button class="theme-toggle" onclick="toggleTheme()">◐</button>
</footer>
</body>
</html>
"""

def create_page(title, filepath):
    """Create a new HTML page from template"""

    # Ensure .html extension
    if not filepath.endswith('.html'):
        filepath += '.html'

    # Full path, refused if it would land outside the content directory
    full_path = CONTENT_ROOT / filepath
    try:
        inside = full_path.resolve().is_relative_to(CONTENT_ROOT.resolve())
    except (OSError, RuntimeError):
        sys.exit(f"ERROR: cannot resolve {filepath}")
    if not inside:
        sys.exit(f"ERROR: {filepath} is outside {CONTENT_ROOT}/")

    if full_path.exists():
        sys.exit(f"ERROR: {full_path} already exists, refusing to overwrite it")

    # Create parent directories
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Get current date
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Generate HTML content; the title is escaped for the <title> and <h1> it is
    # interpolated into. Substituted by name rather than str.format(): the page
    # contains JS braces, which format() would read as fields.
    html_content = (TEMPLATE
                    .replace('TITLE_PLACEHOLDER', escape(title))
                    .replace('DATE_PLACEHOLDER', current_date))

    # Write file
    full_path.write_text(html_content, encoding='utf-8')

    print(f"✓ Created: {full_path}")
    print(f"  Title: {title}")
    print(f"  Date: {current_date}")
    print(f"\nEdit with: nano {full_path}")

    return full_path

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 new-page.py \"Page Title\" path/to/file.html")
        print("\nExamples:")
        print("  python3 new-page.py \"My Blog Post\" posts/my-post.html")
        print("  python3 new-page.py \"About Me\" about.html")
        print("  python3 new-page.py \"Deep Page\" projects/web/deep/page.html")
        sys.exit(1)
    
    title = sys.argv[1]
    filepath = sys.argv[2]
    
    create_page(title, filepath)

if __name__ == '__main__':
    main()
