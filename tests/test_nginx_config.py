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


def test_security_headers_survive_add_header_inheritance():
    # nginx discards every inherited add_header as soon as a location defines
    # one, so a location that sets a header has to repeat the security set
    for header, body in location_blocks():
        if 'add_header' in body:
            assert 'X-Frame-Options' in body, header
            assert 'X-Content-Type-Options' in body, header


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
