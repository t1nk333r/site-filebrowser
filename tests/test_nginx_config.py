"""nginx.conf has to keep agreeing with the listings the generator writes."""
import re
import sys

from conftest import NGINX_CONF, REPO

CONFIG = NGINX_CONF.read_text(encoding='utf-8')


def location_blocks():
    blocks = []
    for match in re.finditer(r'location\s+([^{]*)\{', CONFIG):
        start = match.end()
        depth, index = 1, start
        while depth and index < len(CONFIG):
            if CONFIG[index] == '{':
                depth += 1
            elif CONFIG[index] == '}':
                depth -= 1
            index += 1
        blocks.append((match.group(1).strip(), CONFIG[start:index - 1]))
    return blocks


def block_matching(fragment):
    return next(body for header, body in location_blocks() if fragment in header)


SECURITY_HEADERS = ('X-Frame-Options', 'X-Content-Type-Options', 'Referrer-Policy',
                    'Permissions-Policy', 'Content-Security-Policy')


def header_names(text):
    return set(re.findall(r'add_header\s+(\S+)\s', text))


def csp_value():
    match = re.search(r'add_header\s+Content-Security-Policy\s+"([^"]+)"', CONFIG)
    assert match, 'nginx.conf sends no Content-Security-Policy'
    return match.group(1)


def csp_directives():
    directives = {}
    for part in csp_value().split(';'):
        part = part.strip()
        if part:
            name, _, rest = part.partition(' ')
            directives[name] = rest
    return directives


def test_security_headers_survive_add_header_inheritance():
    # nginx discards every inherited add_header as soon as a location defines
    # one, so such a location has to repeat the whole set
    configured = header_names(CONFIG)
    assert set(SECURITY_HEADERS) <= configured, sorted(set(SECURITY_HEADERS) - configured)

    for header, body in location_blocks():
        present = header_names(body)
        if present:
            missing = configured - present
            assert not missing, f'location {header!r} would drop inherited {sorted(missing)}'


def test_csp_is_strict_outside_inline_content():
    directives = csp_directives()
    assert directives['default-src'] == "'self'"
    for directive in ('object-src', 'base-uri', 'form-action', 'frame-ancestors'):
        assert directives[directive] == "'none'", directive
    assert directives['font-src'] == "'self'"
    assert directives['img-src'] == "'self' data:"
    assert "'unsafe-eval'" not in csp_value()


def test_health_endpoint_and_referrer_policy():
    assert re.search(r'Referrer-Policy\s+"no-referrer"', CONFIG)
    assert re.search(r'location\s*=\s*/healthz\s*\{[^}]*return\s+200', CONFIG, re.S), 'no /healthz route'


def test_csp_permits_what_the_pages_actually_use(page_artefacts):
    """A policy that blocked the theme toggle or the inline listing styles would
    be a silent breakage, so keep it honest against the real artefacts."""
    directives = csp_directives()

    for name, text in page_artefacts.items():
        if '<script>' in text or 'onclick=' in text:
            assert "'unsafe-inline'" in directives.get('script-src', ''), f'{name} uses inline script'
        if '<style' in text:
            assert "'unsafe-inline'" in directives.get('style-src', ''), f'{name} uses inline style'
        external = re.findall(r'(?:src|href)="(?:https?:)?//', text)
        assert not external, f'{name} loads {external}, which default-src blocks'


def test_cleans_up_obsolete_and_version_leaking_headers():
    assert 'X-XSS-Protection' not in CONFIG
    assert re.search(r'server_tokens\s+off;', CONFIG), 'the nginx version is advertised'


def test_static_asset_caching():
    assets = block_matching('jpg')
    assert 'expires 1y;' in assets

    styles = block_matching('css|js')
    assert 'expires 1h;' in styles
    assert 'immutable' not in styles, 'edited stylesheets would be pinned for a year'


def test_symlinks_and_dotfiles_are_restricted():
    assert re.search(r'disable_symlinks\s+if_not_owner', CONFIG)
    assert re.search(r'location ~ /\\\.', CONFIG), 'dotfiles are not denied'
    assert 'autoindex off;' in CONFIG


def test_backup_rule_matches_the_generator_exclusions():
    header, _ = next((h, b) for h, b in location_blocks() if 'bak' in h)
    assert re.search(r'\(\s*~\|', header) or '~|' in header, header

    sys.path.insert(0, str(REPO))
    import generator

    extensions = re.search(r'\\\.\(([a-z|]+)\)', header)
    assert extensions, header
    for extension in extensions.group(1).split('|'):
        name = f'notes.txt.{extension}'
        assert generator.should_exclude(name), f'{name} is denied by nginx but listed'
    assert generator.should_exclude('notes.txt~'), 'backup files ending in ~ are listed'
    assert not generator.should_exclude('notes.txt.BAK'), 'the rule is case-sensitive in both places'
