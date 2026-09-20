# Site FileBrowser

A beautiful, minimalist file browser with automatic directory indexing and dark/light theme support. Perfect for showcasing files, documents, images, and content with a clean, retro-inspired aesthetic.

![Docker Build](https://github.com/d7eeem/site-filebrowser/actions/workflows/docker-publish.yml/badge.svg)

> **⚡ Vibe Coded**  
> This project was entirely vibe-coded through an AI conversation - from concept to deployment. No traditional coding session, just pure conversational development. The power of Claude + human imagination! 🤖✨

## ✨ Features

- 🎨 **Minimal Aesthetic** - Clean, monospace design inspired by classic directory listings
- 🌓 **Dark/Light Themes** - Toggle between themes with persistent preference (URL hash)
- 🔄 **Auto-Regeneration** - Automatically detects file changes and updates indexes
- 📁 **Recursive Indexing** - Generates beautiful listings for all directories
- 📊 **File Metadata** - Displays file sizes and modification dates
- 🚫 **Smart Exclusions** - Automatically hides system files and build artifacts
- 🐳 **Fully Dockerized** - One command to run anywhere
- 🚀 **CI/CD Ready** - Automatic builds via GitHub Actions
- 📱 **Responsive** - Works beautifully on mobile and desktop
- ⚡ **Lightweight** - Minimal dependencies, fast performance

## 🚀 Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/d7eeem/site-filebrowser.git
cd site-filebrowser

# Create content directory and add files
mkdir -p html/posts html/images
echo "Hello World" > html/posts/welcome.txt

# Start the server
docker-compose up -d

# Access at http://localhost:8800
```

### Using Docker Run

```bash
docker run -d \
  -p 8800:80 \
  -v $(pwd)/html:/var/www/html \
  --name site-filebrowser \
  ghcr.io/d7eeem/site-filebrowser:latest
```

### From Source

```bash
# Build the image
docker build -t site-filebrowser .

# Run
docker run -d -p 8800:80 -v $(pwd)/html:/var/www/html site-filebrowser
```

## 📁 Directory Structure

```
site-filebrowser/
├── .github/
│   └── workflows/
│       └── docker-publish.yml    # CI/CD pipeline
├── html/                          # Your content goes here
│   ├── style.css                  # Global stylesheet
│   ├── template.html              # Page template
│   ├── posts/                     # Blog posts, articles
│   ├── images/                    # Images, photos
│   └── projects/                  # Project files
├── Dockerfile                     # Container definition
├── compose.yml                    # Docker Compose config
├── generator.py                   # Index generator
├── watcher.sh                     # File watcher
├── nginx.conf                     # Nginx configuration
├── new-page.sh                    # Page creation script (Bash)
├── new-page.py                    # Page creation script (Python)
├── html.json                      # VS Code snippet (optional)
└── README.md                      # This file
```

## 📝 Creating Content

### Adding Files

Simply add files to the `html/` directory:

```bash
# Add a document
cp ~/document.pdf html/documents/

# Add an image
cp ~/photo.png html/images/

# Indexes regenerate automatically!
```

> **Content rules.** Symlinks are followed only inside the content directory: a
> link pointing outside it is left out of the listing rather than shown as a dead
> entry, and nginx refuses to follow a symlink owned by another user. An
> `index.html` you write by hand is never replaced — the generator stamps its own
> listings and only rewrites those.

### Creating HTML Pages

#### Using the Scripts

**Bash:**
```bash
./new-page.sh "My Blog Post" posts/my-post.html
```

**Python:**
```bash
python3 new-page.py "About Me" about.html
```

#### Manual Method

```bash
# Copy template
cp html/template.html html/posts/my-new-post.html

# Edit content
nano html/posts/my-new-post.html
```

Update the title, heading, and content between the `<main>` tags.

### VS Code Snippet (Fastest)

For frequent page creation, install a custom snippet:

1. **Open VS Code**
2. **File → Preferences → Configure User Snippets**
3. **Select "html.json"** (or create it)
4. **Copy the snippet from `html.json` in the repo**
5. **Save the file**

Now in any `.html` file:
- Type `minpage`
- Press `Tab`
- Instantly get a complete page template!

The snippet auto-fills:
- Current date
- Page title (type once, appears in `<title>` and `<h1>`)
- Cursor positioned for content

This is the **fastest way** to create new pages!

### Page Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Your Title</title>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<main>
<h1>Your Title</h1>
<p>-</p>

<!-- Your content here -->

<time>2026-01-18</time>
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
```

## 🎨 Theming

### Toggle Theme

Click the **◐** button in the footer to switch between light and dark themes.

### Theme Persistence

The theme preference is stored in the URL hash:
- Light mode: `http://localhost:8800/`
- Dark mode: `http://localhost:8800/#dark`

Share links with `#dark` to open directly in dark mode!

### Customizing Styles

Edit `html/style.css` to customize:
- Colors and backgrounds
- Fonts and spacing
- Layout and grid
- Mobile breakpoints

## ⚙️ Configuration

### Change Port

Edit `compose.yml`:
```yaml
ports:
  - "8080:80"  # Change 8800 to your desired port
```

### Exclude Additional Files

Edit `generator.py` and modify `EXCLUDE_PATTERNS`:
```python
EXCLUDE_PATTERNS = {
    '.git', 'node_modules', '.DS_Store', 
    '__pycache__', '.env',
    'index.html',
    'style.css', 'template.html',
    'new-page.sh', 'new-page.py',
    '.gitignore', 'README.md',
    'YOUR_PATTERN_HERE'  # Add your exclusions
}
```

### Custom Timezone

Edit `compose.yml`:
```yaml
environment:
  - TZ=America/New_York  # Change timezone
```

## 🐳 Docker Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build

# Force regenerate indexes
docker-compose exec file-browser python3 /app/generator.py

# Shell access
docker-compose exec file-browser sh
```

## 🚀 Deployment

### GitHub Container Registry

The project includes automated CI/CD via GitHub Actions. Every push to `main`/`master` automatically builds and publishes to GitHub Container Registry.

```bash
# Pull from registry
docker pull ghcr.io/d7eeem/site-filebrowser:latest

# Run
docker-compose pull
docker-compose up -d
```

See [`.github/workflows/docker-publish.yml`](.github/workflows/docker-publish.yml) for the pipeline itself: pull requests only build the image, pushes to `main`/`master` also publish it.

### Production Deployment

1. **Clone repository on server:**
```bash
git clone https://github.com/d7eeem/site-filebrowser.git
cd site-filebrowser
```

2. **Add your content:**
```bash
# Upload files via SCP, rsync, or git
rsync -avz ~/my-content/ html/
```

3. **Start container:**
```bash
docker-compose up -d
```

4. **Update content:**
```bash
# Add files to html/ directory
# Indexes regenerate automatically
```

5. **Update to latest version:**
```bash
git pull
docker-compose pull
docker-compose up -d
```

### Reverse Proxy (Nginx/Caddy)

**Nginx:**
```nginx
server {
    listen 80;
    server_name files.example.com;
    
    location / {
        proxy_pass http://localhost:8800;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Caddy:**
```
files.example.com {
    reverse_proxy localhost:8800
}
```

## 🛠️ Development

### IDE Setup

#### VS Code

For the best development experience, install the VS Code snippet:

```bash
# The html.json file is included in the repo
# Copy it to your VS Code snippets folder:

# macOS/Linux
mkdir -p ~/.config/Code/User/snippets/
cp html.json ~/.config/Code/User/snippets/html.json

# Windows
copy html.json %APPDATA%\Code\User\snippets\html.json

# Or manually via VS Code:
# File → Preferences → Configure User Snippets → html.json
# Then paste the content from the repo's html.json
```

Now type `minpage` + Tab in any HTML file for instant page creation!

#### Neovim/Vim (UltiSnips)

For Neovim/Vim users with UltiSnips:

```bash
# Create snippets directory if it doesn't exist
mkdir -p ~/.config/nvim/UltiSnips

# Create HTML snippets file
nvim ~/.config/nvim/UltiSnips/html.snippets
```

Add this snippet:

```snippets
snippet minpage "Minimal page template"
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${1:Page Title}</title>
<link rel="stylesheet" href="/style.css">
</head>
<body>
<main>
<h1>$1</h1>
<p>-</p>

<p>${2:Content here...}</p>

<time>`date +%Y-%m-%d`</time>

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
$0
endsnippet
```

Usage: Type `minpage` + Tab in any HTML file!

#### Neovim (LuaSnip)

For Neovim users with LuaSnip:

```bash
# Create snippets directory
mkdir -p ~/.config/nvim/luasnippets
nvim ~/.config/nvim/luasnippets/html.lua
```

Add this snippet:

```lua
local ls = require("luasnip")
local s = ls.snippet
local t = ls.text_node
local i = ls.insert_node
local f = ls.function_node

return {
  s("minpage", {
    t({"<!DOCTYPE html>", "<html lang=\"en\">", "<head>", "<meta charset=\"utf-8\">", 
       "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">", "<title>"}),
    i(1, "Page Title"),
    t({"</title>", "<link rel=\"stylesheet\" href=\"/style.css\">", "</head>", "<body>", "<main>", "<h1>"}),
    f(function(args) return args[1][1] end, {1}),
    t({"</h1>", "<p>-</p>", "", "<p>"}),
    i(2, "Content here..."),
    t({"</p>", "", "<time>"}),
    f(function() return os.date("%Y-%m-%d") end),
    t({"</time>", "", "</main>", "<footer>", "<p><a href=\"../\"><i>../</i></a></p>",
       "<button class=\"theme-toggle\" onclick=\"toggleTheme()\">◐</button>", "</footer>",
       "<script>", "function toggleTheme() {", "  location.hash = location.hash === '#dark' ? '' : '#dark';",
       "}", "if (location.hash === '#dark') document.body.classList.add('dark');",
       "</script>", "</body>", "</html>"}),
    i(0)
  })
}
```

Usage: Type `minpage` + Tab in any HTML file!

### Project Structure

- **generator.py** - Scans directories and generates HTML indexes
- **watcher.sh** - Monitors filesystem changes using inotify
- **nginx.conf** - Web server configuration
- **Dockerfile** - Multi-layer container build
- **compose.yml** - Docker Compose orchestration

### Local Development

```bash
# Make changes to generator.py
vim generator.py

# Rebuild container
docker-compose up -d --build

# Test changes
curl http://localhost:8800
```

### Running Generator Manually

```bash
# Inside container
docker-compose exec file-browser python3 /app/generator.py

# Outside container (requires Python 3); the optional argument points it at a
# different content root than /var/www/html
python3 generator.py html
```

## 🧪 Testing

```bash
# Test file creation
echo "test" > html/test.txt
sleep 2
curl http://localhost:8800 | grep "test.txt"

# Test directory creation
mkdir html/test-dir
sleep 2
curl http://localhost:8800 | grep "test-dir"

# Test index generation
docker-compose exec file-browser python3 /app/generator.py
ls html/index.html
```

## 📊 Performance

- **Build time:** ~30 seconds
- **Index generation:** <1 second for 100 files
- **Memory usage:** ~50MB
- **Image size:** ~50MB (Alpine-based)
- **Response time:** <10ms (static files)

## 🐛 Troubleshooting

### Files not appearing?

```bash
# Check file permissions
ls -la html/

# Verify exclusion patterns
grep EXCLUDE_PATTERNS generator.py

# Check container logs
docker-compose logs -f

# Manually regenerate
docker-compose exec file-browser python3 /app/generator.py
```

### Theme toggle not working?

- Clear browser cache
- Check JavaScript console for errors
- Verify `style.css` is loaded
- Ensure URL hash is preserved

### Port already in use?

```bash
# Check what's using the port
lsof -i :8800

# Change port in compose.yml
vim compose.yml  # Edit ports section
```

### Everything returns 403?

The container serves as the unprivileged `nginx` user (uid 101) and deliberately
never re-owns the mounted content directory, so that directory has to be readable
and traversable by that user:

```bash
chmod -R a+rX html
```

Generated `index.html` files are given the ownership of the directory they are
written into, so they stay yours to delete on the host.

### Container won't start?

```bash
# Check Docker status
docker ps -a

# View container logs
docker logs site-filebrowser

# Rebuild from scratch
docker-compose down
docker-compose up -d --build
```

## 🔒 Security

### Built-in Protections

✅ **Path Traversal Prevention**
- Nginx normalises request paths, so `..` cannot escape the content directory
- Generator validates all paths against allowed root
- Container isolation prevents filesystem escape

✅ **Hidden File Protection**
- All dotfiles (`.git`, `.env`, etc.) are blocked
- Backup files (`~`, `.bak`) are denied
- System files are never exposed

✅ **Security Headers**
- `X-Frame-Options: SAMEORIGIN` (prevents clickjacking)
- `X-Content-Type-Options: nosniff` (prevents MIME sniffing)
- No server version is advertised (`server_tokens off`)

✅ **Read-Only Operation**
- No file upload capability
- No modification through web interface
- Static file serving only

### Best Practices

**1. Mount Only What You Need**

❌ **DANGEROUS:**
```yaml
volumes:
  - /:/var/www/html  # Exposes entire system!
  - /home:/var/www/html  # Exposes all user files!
```

✅ **SAFE:**
```yaml
volumes:
  - ./html:/var/www/html  # Only your content directory
  - /path/to/specific/folder:/var/www/html
```

**2. Use Read-Only Mounts (Optional)**

For extra security, mount volumes as read-only:

```yaml
volumes:
  - ./html:/var/www/html:ro  # Read-only mount
```

Note: This prevents auto-generation. You'd need to generate indexes outside the container.

**3. Run Behind Reverse Proxy**

Add HTTPS and additional security with Nginx/Caddy:

```nginx
# Nginx reverse proxy with SSL
server {
    listen 443 ssl http2;
    server_name files.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Additional security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    
    location / {
        proxy_pass http://localhost:8800;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**4. Restrict Network Access**

Limit who can access the service:

```yaml
# compose.yml
services:
  file-browser:
    ports:
      - "127.0.0.1:8800:80"  # Only accessible from localhost
```

Then use SSH tunnel or VPN for remote access.

**5. Regular Updates**

```bash
# Pull latest security updates
docker-compose pull
docker-compose up -d

# Or rebuild from source
git pull
docker-compose up -d --build
```

### What's NOT Protected

⚠️ **No Authentication** - Anyone with access can view files
⚠️ **No Encryption** - Use HTTPS via reverse proxy for sensitive data
⚠️ **Volume Mount Security** - Your responsibility to mount safely
⚠️ **DoS Protection** - No rate limiting (add via reverse proxy)

### Production Deployment Checklist

- [ ] Mount only necessary directories
- [ ] Set up HTTPS via reverse proxy
- [ ] Restrict network access (firewall/IP whitelist)
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Don't expose sensitive files
- [ ] Use strong file permissions on host
- [ ] Consider authentication (Authelia, OAuth2 Proxy, etc.)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Design inspired by classic Unix directory listings
- Aesthetic inspired by [williamjansson.com](https://williamjansson.com)
- Built with minimal dependencies for maximum simplicity
- **100% vibe-coded** - Developed entirely through conversational AI without writing code manually
- Powered by Claude (Anthropic) - Proof that good vibes make good code ✨

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/d7eeem/site-filebrowser/issues)
- **Discussions:** [GitHub Discussions](https://github.com/d7eeem/site-filebrowser/discussions)

## 🔗 Links

- **GitHub:** https://github.com/d7eeem/site-filebrowser
- **Container Registry:** https://ghcr.io/d7eeem/site-filebrowser
- **Pipeline:** [.github/workflows/docker-publish.yml](.github/workflows/docker-publish.yml)

---

**Built with ❤️ for simplicity and minimalism**
