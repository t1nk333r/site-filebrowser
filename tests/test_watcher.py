"""The watcher must not lose a change that lands while the generator runs, and
must not wake itself."""
import shutil
import time

import pytest

from conftest import GENERATOR, count, generate, links, running_watcher, wait_until

pytestmark = pytest.mark.skipif(shutil.which('inotifywait') is None,
                                reason='inotify-tools is required')


def listed(root):
    index = root / 'index.html'
    if not index.exists():
        return set()
    return {text for _, text in links(index)[:-1]}


def test_regenerates_on_real_changes_only(tmp_path):
    root = tmp_path / 'html'
    (root / 'sub').mkdir(parents=True)
    (root / 'sub' / 'inner.txt').write_text('x')

    with running_watcher(tmp_path, root, GENERATOR) as log:
        assert wait_until(lambda: count(log, 'Generation complete') == 1, timeout=30), log.read_text()
        time.sleep(2)
        assert count(log, 'Generation complete') == 1, 'the generator woke itself'
        assert count(log, 'Change detected') == 0

        (root / '.hidden').write_text('x')
        (root / 'sub' / '.hidden').write_text('x')
        time.sleep(3)
        assert count(log, 'Generation complete') == 1, 'hidden paths are never listed'

        (root / 'new.txt').write_text('x')
        assert wait_until(lambda: count(log, 'Generation complete') == 2, timeout=20), log.read_text()
        assert 'new.txt' in listed(root)

        (root / 'sub' / 'index.html').unlink()
        assert wait_until(lambda: count(log, 'Generation complete') == 3, timeout=20), log.read_text()
        assert (root / 'sub' / 'index.html').exists()


def test_change_during_a_generation_is_not_dropped(tmp_path):
    """The old loop let inotifywait exit before generating, so the tree was
    unwatched for the whole run and anything landing in that window was lost."""
    root = tmp_path / 'html'
    root.mkdir()
    for i in range(20000):
        (root / f'd{i:05d}').mkdir()
    (root / 'plain.txt').write_text('x')
    generate(root)

    with running_watcher(tmp_path, root, GENERATOR) as log:
        assert wait_until(lambda: count(log, 'Generation complete') == 1, timeout=60), log.read_text()

        (root / 'trigger.txt').write_text('x')
        assert wait_until(lambda: 'Change detected' in log.read_text(), timeout=30), log.read_text()

        # let the running generation get past the listing it writes first
        assert wait_until(lambda: count(log, 'Generating directory indexes...') >= 2, timeout=30)
        time.sleep(0.3)
        (root / 'late.txt').write_text('x')

        assert wait_until(lambda: 'late.txt' in listed(root), timeout=30), log.read_text()
        assert 'late.txt' in log.read_text()
