#!/usr/bin/env bash
# Boots the built image against a scratch tree and checks what the project
# promises at runtime: listings appear, the server rules hold, a host-side
# change is indexed without a restart, and generated files stay owned by the
# host user.
#
# Usage: tests/smoke.sh [image]   (default: site-filebrowser:ci)
set -euo pipefail

IMAGE=${1:-site-filebrowser:ci}
PORT=${PORT:-$(( 18000 + RANDOM % 2000 ))}
CONTAINER=site-filebrowser-smoke
BASE=$(mktemp -d)
CONTENT=$BASE/html

mkdir -p "$CONTENT/sub" "$CONTENT/hand-written"
printf 'x\n' > "$CONTENT/hello.txt"
printf 'x\n' > "$CONTENT/sub/inner.txt"
printf 'x\n' > "$CONTENT/notes.txt.bak"
printf 'body { color: red }\n' > "$CONTENT/style.css"
printf '<html>mine</html>\n' > "$CONTENT/hand-written/index.html"
ln -s /etc/hostname "$CONTENT/outside.txt"

cleanup() {
    docker logs "$CONTAINER" > "$BASE/container.log" 2>&1 || true
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
    rm -rf "$BASE"
}
trap cleanup EXIT

fail() {
    echo "smoke: FAIL: $*" >&2
    echo "--- last container log lines ---" >&2
    docker logs --tail 25 "$CONTAINER" >&2 || true
    exit 1
}

expect_code() {
    local url=$1 want=$2 got
    got=$(curl -s -o /dev/null -w '%{http_code}' --path-as-is "$url")
    [ "$got" = "$want" ] || fail "$url returned $got, expected $want"
}

listing_has() {
    curl -sf "$BASE_URL/" | grep -q "$1"
}

docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER" -p "127.0.0.1:$PORT:80" -v "$CONTENT:/var/www/html" "$IMAGE" >/dev/null
BASE_URL="http://127.0.0.1:$PORT"

code=
for _ in $(seq 1 30); do
    code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/" || true)
    [ "$code" = 200 ] && break
    sleep 1
done
[ "$code" = 200 ] || fail "the root listing never came up (last status $code)"

listing_has 'hello.txt' || fail 'hello.txt is missing from the listing'
listing_has 'outside.txt' && fail 'a symlink pointing outside the content root is listed'
curl -sf "$BASE_URL/hand-written/" | grep -q 'mine' || fail 'a hand-written index.html was replaced'
expect_code "$BASE_URL/hello.txt" 200
expect_code "$BASE_URL/notes.txt.bak" 403

headers=$(curl -sI "$BASE_URL/style.css")
grep -q 'X-Frame-Options' <<<"$headers" || fail 'the security headers are missing on style.css'
grep -q 'X-Content-Type-Options' <<<"$headers" || fail 'X-Content-Type-Options is missing on style.css'
grep -qi '^Server: nginx[[:space:]]*$' <<<"$headers" || fail 'the nginx version is advertised'
grep -qi 'immutable' <<<"$headers" && fail 'style.css is pinned in browsers for a year'

printf 'x\n' > "$CONTENT/added-later.txt"
for _ in $(seq 1 20); do
    listing_has 'added-later.txt' && break
    sleep 1
done
listing_has 'added-later.txt' || fail 'the watcher did not index a file added on the host'

owner=$(stat -c '%u' "$CONTENT/index.html")
[ "$owner" = "$(id -u)" ] || fail "the generated index.html is owned by uid $owner, not $(id -u)"

echo "smoke: ok (image $IMAGE on port $PORT)"
