#!/bin/bash

# Regenerates the directory indexes whenever the content tree changes.
#
# inotifywait runs in monitor mode (-m) so its watches stay established while
# the generator runs. Without -m, inotifywait exits after the first event and
# the tree stays unwatched until the generator has finished, so every change
# landing in that window is dropped and the listing stays stale until some
# unrelated change arrives.

ROOT=/var/www/html
GENERATOR=/app/generator.py

# Paths a generation produces itself, and paths the listing never shows, must
# not wake the watcher: the first would loop forever, the second is invisible
# in the output either way.
ignored() {
    local rel=${1#"$ROOT"/}
    case "$rel" in
        .*|*/.*) return 0 ;;
        index.html|*/index.html) [ -e "$1" ] && return 0 ;;
    esac
    return 1
}

echo "Starting file watcher..."

while true; do
    inotifywait -m -r -q -e modify,create,delete,move --format '%w%f' "$ROOT" |
    {
        # Let the watches come up before the first pass: a change made before
        # that point is still on disk when the pass reads the tree, anything
        # after it is queued as an event. Without the gap a change can fall
        # between the two and be missed by both.
        sleep 1
        python3 -u "$GENERATOR" || echo "ERROR: index generation failed" >&2

        while read -r changed; do
            ignored "$changed" && continue
            echo "Change detected: $changed"

            # Coalesce a burst (rsync, git checkout, an editor writing several
            # files) into one regeneration, but never defer it for more than a
            # few seconds while events keep arriving.
            drain_until=$((SECONDS + 5))
            while [ "$SECONDS" -lt "$drain_until" ] && read -r -t 1 extra; do
                ignored "$extra" || echo "  changed too: $extra"
            done

            python3 -u "$GENERATOR" || echo "ERROR: index generation failed" >&2
        done
    }

    # inotifywait is gone (watch limit, content unmounted, watch removed). Bail
    # out of the loop instead of serving a frozen listing for good.
    echo "ERROR: file watcher stopped, restarting in 5s" >&2
    sleep 5
done
