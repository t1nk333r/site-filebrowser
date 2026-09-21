"""The two page scaffolders must agree and must refuse what they promise to."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO, page_from_scaffolder


def created(result):
    """The path the scaffolder reported, or None when it refused."""
    if result.returncode != 0:
        return None
    marker = '\u2713 Created: '
    for line in result.stdout.splitlines():
        if line.startswith(marker):
            return line[len(marker):]
    return None


@pytest.mark.parametrize('title', [
    'Plain Title',
    'Q&A: Tom & Jerry',
    'slash/and\\back [x] 100%',
    '<script>alert(1)</script>',
    'Quote " and \' apostrophe',
])
def test_both_scaffolders_produce_the_same_page(tmp_path, title):
    sh_result, sh_root = page_from_scaffolder(tmp_path, title, 'posts/page.html', shell=True)
    py_result, py_root = page_from_scaffolder(tmp_path, title, 'posts/page.html', shell=False)

    assert sh_result.returncode == 0, sh_result.stderr
    assert py_result.returncode == 0, py_result.stderr
    assert (sh_root / 'html/posts/page.html').read_bytes() == (py_root / 'html/posts/page.html').read_bytes()


def test_title_is_escaped_for_the_markup(tmp_path):
    _, root = page_from_scaffolder(tmp_path, '<b>bold</b> & "quoted"', 'page.html', shell=True)
    text = (root / 'html/page.html').read_text(encoding='utf-8')

    assert '<title>&lt;b&gt;bold&lt;/b&gt; &amp; &quot;quoted&quot;</title>' in text
    assert '<h1>&lt;b&gt;bold&lt;/b&gt; &amp; &quot;quoted&quot;</h1>' in text
    assert '<b>bold</b>' not in text


@pytest.mark.parametrize('shell', [True, False])
def test_appends_the_html_extension(tmp_path, shell):
    result, root = page_from_scaffolder(tmp_path, 'No Extension', 'posts/noext', shell=shell)

    assert result.returncode == 0, result.stderr
    assert (root / 'html/posts/noext.html').exists()


@pytest.mark.parametrize('shell', [True, False])
def test_refuses_to_overwrite_an_existing_page(tmp_path, shell):
    first, root = page_from_scaffolder(tmp_path, 'First', 'page.html', shell=shell)
    assert first.returncode == 0, first.stderr
    before = (root / 'html/page.html').read_bytes()

    second, _ = page_from_scaffolder(tmp_path, 'Second', 'page.html', shell=shell)

    assert second.returncode == 1
    assert 'already exists' in second.stderr + second.stdout
    assert (root / 'html/page.html').read_bytes() == before


@pytest.mark.parametrize('path', ['../evil.html', 'posts/../../evil.html', '/tmp/evil.html'])
def test_refuses_paths_outside_the_content_directory(tmp_path, path):
    work = tmp_path / 'work'
    work.mkdir()
    for command in ([sys.executable, str(REPO / 'new-page.py'), 'T', path],
                    ['bash', str(REPO / 'new-page.sh'), 'T', path]):
        result = subprocess.run(command, cwd=work, capture_output=True, text=True, timeout=60)
        assert result.returncode == 1, result.stdout + result.stderr
        assert 'ERROR' in result.stderr + result.stdout
    assert not list(tmp_path.glob('evil.html'))
    assert not Path('/tmp/evil.html').exists()


def test_shell_scaffolder_refuses_a_symlinked_directory(tmp_path):
    work = tmp_path / 'work'
    (work / 'html').mkdir(parents=True)
    os.symlink(tmp_path, work / 'html' / 'link')

    result = subprocess.run(['bash', str(REPO / 'new-page.sh'), 'T', 'link/evil.html'],
                            cwd=work, capture_output=True, text=True, timeout=60)

    assert result.returncode == 1
    assert 'symlinked path' in result.stderr
    assert not (tmp_path / 'evil.html').exists()


def test_python_scaffolder_refuses_a_symlinked_directory(tmp_path):
    work = tmp_path / 'work'
    (work / 'html').mkdir(parents=True)
    os.symlink(tmp_path, work / 'html' / 'link')

    result = subprocess.run([sys.executable, str(REPO / 'new-page.py'), 'T', 'link/evil.html'],
                            cwd=work, capture_output=True, text=True, timeout=60)

    assert result.returncode == 1
    assert 'outside' in result.stderr
    assert not (tmp_path / 'evil.html').exists()
