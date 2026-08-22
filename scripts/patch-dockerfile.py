"""Insert the nftables-napi binary swap into an upstream Node Dockerfile.

The node image installs nftables-napi from npm itself; the only thing that has
to change for RouterOS is the prebuilt binary inside it. That is one step at the
end of the build stage, after upstream has assembled `dist/` and pruned the
prebuilds down to the target architecture.

The version guard is the important part: when upstream bumps nftables-napi to a
release the patch has not been rebuilt against, the build fails here instead of
publishing an image whose binary silently predates the API the node calls.

Usage: python3 scripts/patch-dockerfile.py <path to upstream Dockerfile>
"""

import sys
from pathlib import Path

ANCHOR = "    && chmod +x dist/cli.js\n"

BLOCK = """
RUN --mount=type=bind,source=nftprebuilds,target=/tmp/nftprebuilds \\
    ARCH=$([ "$(uname -m)" = aarch64 ] && echo linux-arm64 || echo linux-x64) \\
    && EXPECTED="$(cat /tmp/nftprebuilds/VERSION)" \\
    && ACTUAL="$(node -p "require('/opt/app/dist/node_modules/nftables-napi/package.json').version")" \\
    && { [ "$ACTUAL" = "$EXPECTED" ] || { \\
           echo "nftables-napi is $ACTUAL, the RouterOS patch was built for $EXPECTED"; \\
           exit 1; \\
       }; } \\
    && cp "/tmp/nftprebuilds/$ARCH/nftables-napi.glibc.node" \\
          "/opt/app/dist/node_modules/nftables-napi/prebuilds/$ARCH/nftables-napi.glibc.node"
"""


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    text = path.read_text()

    if text.count(ANCHOR) != 1:
        raise SystemExit(
            f"expected exactly one {ANCHOR.strip()!r} in {path}; upstream's build "
            "stage changed and the insertion point has to be revisited"
        )

    path.write_text(text.replace(ANCHOR, ANCHOR + BLOCK))
    print(f"patched {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
