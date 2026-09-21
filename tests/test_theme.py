"""The theme script lives in every page-producing artefact, so these tests both
keep the copies identical and pin the behaviour a visitor sees."""
import os

import pytest

from conftest import (REPO, canonical_script, generate, normalise_script,
                      page_from_scaffolder, script_blocks, serve, snippet_page)


def artefacts(tmp_path):
    """Every artefact that carries the theme script."""
    root = tmp_path / 'html'
    root.mkdir()
    (root / 'page.txt').write_text('x')
    generate(root)
    _, sh_root = page_from_scaffolder(tmp_path, 'T', 'page.html', shell=True)
    _, py_root = page_from_scaffolder(tmp_path, 'T', 'page.html', shell=False)

    return {
        'html/template.html': (REPO / 'html' / 'template.html').read_text(encoding='utf-8'),
        'generated listing': (root / 'index.html').read_text(encoding='utf-8'),
        'new-page.sh': (sh_root / 'html/page.html').read_text(encoding='utf-8'),
        'new-page.py': (py_root / 'html/page.html').read_text(encoding='utf-8'),
        'html.json': snippet_page(REPO / 'html.json'),
        'README.md': (REPO / 'README.md').read_text(encoding='utf-8'),
    }


def test_every_copy_of_the_theme_script_is_identical(tmp_path):
    canonical = canonical_script()
    for name, text in artefacts(tmp_path).items():
        blocks = script_blocks(text)
        assert blocks, f'{name} carries no inline script'
        for block in blocks:
            assert normalise_script(block) == canonical, f'{name} has drifted'


def test_script_runs_from_the_head_and_scopes_dark_to_the_root(tmp_path):
    canonical = canonical_script()
    assert 'document.documentElement.classList' in canonical
    assert 'document.body.classList' not in canonical
    assert 'localStorage' in canonical

    for name, text in artefacts(tmp_path).items():
        if name.endswith('.md'):
            continue
        assert text.index('<script>') < text.index('</head>'), f'{name}: script is not in the head'


def test_dark_rules_target_the_root_element(tmp_path):
    root = tmp_path / 'html'
    root.mkdir()
    (root / 'page.txt').write_text('x')
    generate(root)

    for path in (REPO / 'html' / 'style.css', root / 'index.html'):
        text = path.read_text(encoding='utf-8')
        assert 'body.dark' not in text, f'{path} still scopes dark to body'

    assert 'html.dark body' in (root / 'index.html').read_text(encoding='utf-8')
    style = (REPO / 'html' / 'style.css').read_text(encoding='utf-8')
    for selector in ('html.dark body', 'html.dark pre', 'html.dark code', 'html.dark blockquote', 'html.dark table'):
        assert selector in style, selector


def _playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if os.environ.get('REQUIRE_BROWSER_TESTS'):
            pytest.fail('REQUIRE_BROWSER_TESTS is set but playwright is not installed')
        pytest.skip('playwright is not installed')
    return sync_playwright


@pytest.fixture
def page():
    sync_playwright = _playwright()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        tab = context.new_page()
        yield tab
        context.close()
        browser.close()


def state(tab):
    return tab.evaluate("""() => ({
        dark: document.documentElement.classList.contains('dark'),
        background: getComputedStyle(document.body).backgroundColor,
        hash: location.hash,
        stored: (() => { try { return localStorage.getItem('theme'); } catch (e) { return 'n/a'; } })(),
    })""")


def toggle(tab):
    tab.click('.theme-toggle')
    tab.wait_for_timeout(150)


@pytest.mark.browser
def test_toggle_switches_both_ways(site, page):
    page.goto(f'{site}/template.html')
    assert state(page)['dark'] is False

    toggle(page)
    dark = state(page)
    assert dark['dark'] is True and dark['background'] == 'rgb(26, 26, 26)'
    assert dark['hash'] == '#dark' and dark['stored'] == 'dark'

    toggle(page)
    light = state(page)
    assert light['dark'] is False and light['background'] == 'rgb(242, 242, 242)'
    assert light['stored'] == 'light'


@pytest.mark.browser
def test_theme_survives_navigation_and_can_be_toggled_from_storage(site, page):
    page.goto(f'{site}/')
    toggle(page)
    assert state(page)['dark'] is True

    page.click('a[href="sub/"]')
    page.wait_for_url(f'{site}/sub/')
    arrived = state(page)
    assert arrived['dark'] is True and arrived['hash'] == ''

    # the theme came from storage, not the hash: the toggle must still flip it
    toggle(page)
    assert state(page)['dark'] is False
    assert state(page)['stored'] == 'light'


@pytest.mark.browser
def test_dark_deep_link_wins_and_is_applied_on_load(site, page):
    page.goto(f'{site}/sub/#dark', wait_until='domcontentloaded')
    assert state(page)['dark'] is True

    toggle(page)
    cleared = state(page)
    assert cleared['dark'] is False and cleared['hash'] == '' and cleared['stored'] == 'light'
