#!/bin/bash

# Usage: ./new-page.sh "Page Title" path/to/file.html

if [ $# -lt 2 ]; then
    echo "Usage: ./new-page.sh \"Page Title\" path/to/file.html"
    echo "Example: ./new-page.sh \"My Blog Post\" posts/my-post.html"
    exit 1
fi

TITLE="$1"
FILEPATH="html/$2"
CURRENT_DATE=$(date +%Y-%m-%d)

# bash 5.2+ replaces & in a ${var//pat/replacement} with the matched text, which
# would corrupt both the escaping below and the substitution of the title
shopt -u patsub_replacement 2>/dev/null || true

# Ensure .html extension
case "$FILEPATH" in
    *.html) ;;
    *) FILEPATH="$FILEPATH.html" ;;
esac

# The title is interpolated into <title> and <h1>, so escape it for HTML
ESCAPED_TITLE=${TITLE//&/&amp;}
ESCAPED_TITLE=${ESCAPED_TITLE//</&lt;}
ESCAPED_TITLE=${ESCAPED_TITLE//>/&gt;}
ESCAPED_TITLE=${ESCAPED_TITLE//\"/&quot;}
ESCAPED_TITLE=${ESCAPED_TITLE//\'/&#x27;}

# Refuse anything that leaves html/: '..' elements outright, and no component may
# be a symlink, which mkdir and the redirect would otherwise follow
case "/$FILEPATH/" in
    */../*)
        echo "ERROR: refusing path containing a '..' element: $FILEPATH" >&2
        exit 1
        ;;
esac

CHECK="html"
IFS='/' read -ra PARTS <<<"$2"
for PART in "${PARTS[@]}"; do
    CHECK="$CHECK/$PART"
    if [ -L "$CHECK" ]; then
        echo "ERROR: refusing symlinked path: $CHECK" >&2
        exit 1
    fi
done

if [ -e "$FILEPATH" ]; then
    echo "ERROR: $FILEPATH already exists, refusing to overwrite it" >&2
    exit 1
fi

# Create directory if it doesn't exist
mkdir -p "$(dirname "$FILEPATH")" || exit 1

read -r -d '' TEMPLATE <<'EOF' || true
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITLE_PLACEHOLDER</title>
<link rel="stylesheet" href="/style.css">
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
<script>
function toggleTheme() {
  location.hash = location.hash === '#dark' ? '' : '#dark';
}
if (location.hash === '#dark') document.body.classList.add('dark');
</script>
</body>
</html>
EOF

# Substitute with parameter expansion rather than sed: a title containing &, /
# or \ breaks a sed replacement, and & silently expands to the matched text
CONTENT=${TEMPLATE//TITLE_PLACEHOLDER/$ESCAPED_TITLE}
CONTENT=${CONTENT//DATE_PLACEHOLDER/$CURRENT_DATE}

printf '%s\n' "$CONTENT" > "$FILEPATH" || exit 1

echo "✓ Created: $FILEPATH"
echo "  Title: $TITLE"
echo "  Date: $CURRENT_DATE"
echo ""
echo "Edit with: nano $FILEPATH"
