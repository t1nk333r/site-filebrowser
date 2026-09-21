"""The theme script lives in every page-producing artefact, so these tests both
keep the copies identical and pin the behaviour a visitor sees."""
import os
import re

import pytest

from conftest import REPO, canonical_script, generate, normalise_script, script_blocks


def test_every_copy_of_the_theme_script_is_identical(page_artefacts):
    canonical = canonical_script()
    for name, text in page_artefacts.items():
        blocks = script_blocks(text)
        assert blocks, f'{name} carries no inline script'
        for block in blocks:
            assert normalise_script(block) == canonical, f'{name} has drifted'


def test_script_runs_from_the_head_and_scopes_dark_to_the_root(page_artefacts):
    canonical = canonical_script()
    assert 'document.documentElement.classList' in canonical
    assert 'document.body.classList' not in canonical
    assert 'localStorage' in canonical

    for name, text in page_artefacts.items():
        assert text.index('<script>') < text.index('</head>'), f'{name}: script is not in the head'


def theme_rules(text):
    """Theme selector -> declarations, normalised, multi-selectors split."""
    rules = {}
    for match in re.finditer(r'(html\.(?:dark|ember)[^{}]*)\{([^{}]*)\}', text):
        declarations = ' '.join(match.group(2).split())
        for selector in match.group(1).split(','):
            rules[' '.join(selector.split())] = declarations
    return rules


def test_theme_rules_target_the_root_element(tmp_path):
    root = tmp_path / 'html'
    root.mkdir()
    (root / 'page.txt').write_text('x')
    generate(root)
    generated = (root / 'index.html').read_text(encoding='utf-8')
    style = (REPO / 'html' / 'style.css').read_text(encoding='utf-8')

    for name, text in (('html/style.css', style), ('generated listing', generated)):
        assert 'body.dark' not in text and 'body.ember' not in text, name
        assert 'html.dark body' in text and 'html.ember body' in text, name

    # the listing carries a subset of the stylesheet and never contradicts it
    style_rules = theme_rules(style)
    for selector, declarations in theme_rules(generated).items():
        assert selector in style_rules, f'{selector} is styled in a listing but not in style.css'
        assert style_rules[selector] == declarations, f'{selector} differs between the copies'

    # the ember palette also reaches what a listing never uses
    for selector in ('html.ember h2', 'html.ember blockquote', 'html.ember code', 'html.ember pre'):
        assert selector in style_rules, selector


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


THEME_BACKGROUNDS = {
    'light': 'rgb(242, 242, 242)',
    'dark': 'rgb(26, 26, 26)',
    'ember': 'rgb(23, 23, 23)',
}


def state(tab):
    return tab.evaluate("""() => ({
        theme: ['light', 'dark', 'ember'].filter(t => document.documentElement.classList.contains(t))[0] || 'none',
        classes: document.documentElement.className,
        background: getComputedStyle(document.body).backgroundColor,
        hash: location.hash,
        stored: (() => { try { return localStorage.getItem('theme'); } catch (e) { return 'n/a'; } })(),
    })""")


def toggle(tab):
    tab.click('.theme-toggle')
    tab.wait_for_timeout(150)


@pytest.mark.browser
def test_toggle_cycles_light_dark_ember(site, page):
    page.goto(f'{site}/template.html')
    assert state(page)['theme'] == 'light'

    for expected in ('dark', 'ember', 'light'):
        toggle(page)
        current = state(page)
        assert current['theme'] == expected, current
        assert current['background'] == THEME_BACKGROUNDS[expected], current
        assert current['classes'] == expected, f'only one theme class at a time: {current}'
        assert current['stored'] == expected, current
        expected_hash = '' if expected == 'light' else f'#{expected}'
        assert current['hash'] == expected_hash, current


@pytest.mark.browser
def test_theme_survives_navigation_and_toggles_from_storage(site, page):
    page.goto(f'{site}/')
    toggle(page)                      # dark
    toggle(page)                      # ember
    assert state(page)['theme'] == 'ember'

    page.click('a[href="sub/"]')
    page.wait_for_url(f'{site}/sub/')
    arrived = state(page)
    assert arrived['theme'] == 'ember' and arrived['hash'] == ''
    assert arrived['background'] == THEME_BACKGROUNDS['ember']

    # the theme came from storage, not the hash: the button must still advance it
    toggle(page)
    assert state(page)['theme'] == 'light'
    assert state(page)['stored'] == 'light'


@pytest.mark.browser
@pytest.mark.parametrize('name', ['dark', 'ember'])
def test_deep_links_apply_on_load_and_advance_from_there(site, page, name):
    page.goto(f'{site}/sub/#{name}', wait_until='domcontentloaded')
    loaded = state(page)
    assert loaded['theme'] == name, loaded
    assert loaded['background'] == THEME_BACKGROUNDS[name], loaded
    assert loaded['classes'] == name, loaded

    toggle(page)
    assert state(page)['theme'] == ('light' if name == 'ember' else 'ember')
