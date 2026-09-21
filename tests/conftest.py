"""Shared helpers for the site-filebrowser test suite.

The tests drive the real artefacts: generator.py is executed as a program,
watcher.sh is run as the shipped script with only its two paths rewritten, and
the pages are served over HTTP so the checks see what a visitor would.
"""
import contextlib
import functools
import http.server
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from html.parser import HTMLParser
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
GENERATOR = REPO / 'generator.py'
WATCHER = REPO / 'watcher.sh'
NGINX_CONF = REPO / 'nginx.conf'


class _LinkParser(HTMLParser):
    """Collect every (href, text) pair, with character references decoded."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self._href = dict(attrs).get('href')
            self._text = []

    def handle_endtag(self, tag):
        if tag == 'a' and self._href is not None:
            self.links.append((self._href, ''.join(self._text)))
            self._href = None

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)


def links(index):
    """(href, text) for every link in an index file, last one is ../."""
    parser = _LinkParser()
    parser.feed(Path(index).read_text(encoding='utf-8'))
    return parser.links


def run_generator(root, *args, cwd=None):
    """Run generator.py as a program, the way the container does."""
    return subprocess.run(
        [sys.executable, '-u', str(GENERATOR), str(root), *args],
        capture_output=True, text=True, timeout=120, cwd=cwd or REPO,
    )


def generate(root):
    """Generate indexes and return the completed process."""
    result = run_generator(root)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def script_blocks(text):
    """Every inline <script> block in a file, in order.

    Snippets carry the script as one quoted string per line, so the surrounding
    quotes come along to keep normalise_script's string extraction aligned.
    """
    return re.findall(r'"?<script>.*?</script>"?', text, re.S)


def normalise_script(block):
    """Compare scripts that may be embedded as quoted snippet lines.

    README and html.json carry the script either verbatim or as one quoted
    string per line, so pull the strings back out before comparing.
    """
    strings = re.findall(r'"((?:[^"\\]|\\.)*)"', block)
    if strings:
        text = '\n'.join(s.replace('\\"', '"').replace('\\\\', '\\') for s in strings)
    else:
        text = block
    return '\n'.join(line.rstrip() for line in text.splitlines()).strip()


def canonical_script():
    """The theme script as html/template.html carries it."""
    blocks = script_blocks((REPO / 'html' / 'template.html').read_text(encoding='utf-8'))
    assert len(blocks) == 1, 'template.html should carry exactly one inline script'
    return normalise_script(blocks[0])


def snippet_page(path):
    """The page text a snippet file (html.json) expands to."""
    import json
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    entry = next(iter(data.values()))
    return '\n'.join(entry['body'])


def page_from_scaffolder(tmp_path, title, rel_path, shell=True):
    """Build a page with new-page.sh or new-page.py and return its path."""
    work = tmp_path / ('sh' if shell else 'py')
    work.mkdir(parents=True, exist_ok=True)
    if shell:
        cmd = ['bash', str(REPO / 'new-page.sh'), title, rel_path]
    else:
        cmd = [sys.executable, str(REPO / 'new-page.py'), title, rel_path]
    result = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=60)
    return result, work


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextlib.contextmanager
def serve(directory):
    """Serve a directory on a free port and yield its base URL."""
    handler = functools.partial(_QuietHandler, directory=str(directory))
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{httpd.server_address[1]}'
    finally:
        httpd.shutdown()
        httpd.server_close()


def watcher_for(base, root, generator):
    """The shipped watcher.sh with only its two paths pointed elsewhere.

    In the container the generator picks up its default root; against a test
    tree it has to be handed the root explicitly.
    """
    text = WATCHER.read_text(encoding='utf-8')
    assert text.count('ROOT=/var/www/html') == 1
    assert text.count('GENERATOR=/app/generator.py') == 1
    assert text.count('python3 -u "$GENERATOR"') == 2
    path = base / 'watcher.sh'
    path.write_text(
        text.replace('ROOT=/var/www/html', f'ROOT={root}')
            .replace('GENERATOR=/app/generator.py', f'GENERATOR={generator}')
            .replace('python3 -u "$GENERATOR"', 'python3 -u "$GENERATOR" "$ROOT"'),
        encoding='utf-8',
    )
    path.chmod(0o755)
    return path


@contextlib.contextmanager
def running_watcher(base, root, generator):
    """Start the watcher in the background, stop it and its watches afterwards."""
    script = watcher_for(base, root, generator)
    log = base / 'watch.log'
    with log.open('wb') as handle:
        process = subprocess.Popen([str(script)], stdout=handle, stderr=subprocess.STDOUT)
    try:
        yield log
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        subprocess.run(['pkill', '-f', f'inotifywait.*{root}'], capture_output=True)


def wait_until(predicate, timeout=20, interval=0.2):
    """Poll until predicate() is true, then return it; fail on timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    return None


def count(path, needle):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace').count(needle)
    except FileNotFoundError:
        return 0


@pytest.fixture
def content(tmp_path):
    """A content tree with the awkward names that used to break the index."""
    root = tmp_path / 'html'
    (root / 'sub dir').mkdir(parents=True)
    (root / 'plain.txt').write_text('x')
    (root / 'space name.txt').write_text('x')
    (root / 'a&b.txt').write_text('x')
    (root / 'g#h.txt').write_text('x')
    (root / 'i?j.txt').write_text('x')
    (root / '50%.txt').write_text('x')
    (root / 'c<d>.txt').write_text('x')
    (root / '"q".txt').write_text('x')
    (root / 'caf\u00e9.txt').write_text('x')
    (root / 'sub dir' / 'inner.txt').write_text('x')
    generate(root)
    return root


@pytest.fixture
def site(tmp_path):
    """A served tree: a generated listing plus a template page."""
    root = tmp_path / 'site'
    (root / 'sub').mkdir(parents=True)
    (root / 'sub' / 'inner.txt').write_text('x')
    shutil.copy(REPO / 'html' / 'style.css', root / 'style.css')
    shutil.copy(REPO / 'html' / 'template.html', root / 'template.html')
    generate(root)
    with serve(root) as base_url:
        yield base_url
