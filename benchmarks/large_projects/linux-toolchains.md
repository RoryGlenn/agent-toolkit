# Toolchain reproduction for the Linux verification

The curator adapter expects tools rather than replacing the host's toolchain. This
verification used private Go/Node roots and extracted Debian packages because the cloud
account is unprivileged and has no `sudo`. A normal Linux machine can instead supply its
installed C tools, Bison, Flex and M4, together with the pinned private Go/Node roots.
The generated receipts record the actual configure/build output.

The following archives were retrieved through the approved HTTPS proxy and their bytes
recorded with SHA-256. Go and Node hashes were also checked against the official release
manifests. Debian package digests below record these particular HTTPS downloads; no claim
of independent signature verification is made.

| Artifact | URL | SHA-256 |
| --- | --- | --- |
| Go 1.26.0 linux-amd64 | https://dl.google.com/go/go1.26.0.linux-amd64.tar.gz | `aac1b08a0fb0c4e0a7c1555beb7b59180b05dfc5a3d62e40e9de90cd42f88235` |
| Node 22.22.1 linux-x64 | https://nodejs.org/dist/v22.22.1/node-v22.22.1-linux-x64.tar.xz | `9a6bc82f9b491279147219f6a18add1e18424dce90d41d2a5fcd69d4924ba3aa` |
| Bison 3.8.2 | https://deb.debian.org/debian/pool/main/b/bison/bison_3.8.2+dfsg-1+b2_amd64.deb | `ce6eb1f7aad18850e32d223a68f54bcbe756d74f138c8ec5460ad9d220f4d335` |
| Flex 2.6.4 | https://deb.debian.org/debian/pool/main/f/flex/flex_2.6.4-8.2+b4_amd64.deb | `75f963765232c356d0a2fb70e780dfa9de2425aca036ec60eefb7fc98a2c905b` |
| M4 1.4.19 | https://deb.debian.org/debian/pool/main/m/m4/m4_1.4.19-8_amd64.deb | `221b3e224708c1da2a1a88b6824380593579b2254ae7d914afa14cbd5d343334` |

Extract Go/Node archives into a new private tools directory. Extract Debian packages with
`dpkg-deb -x PACKAGE PRIVATE/native`; pass `PRIVATE/native/usr` as another `--toolchain`.
The adapter sets `BISON_PKGDATADIR` when `share/bison` is present in a selected root.
Debian Bison embeds `/usr/bin/m4`. If M4 is also private, rename that private `bin/bison`
binary to `bin/bison.real`, then use this relocation wrapper as its `bin/bison`:

```sh
#!/bin/sh
bison_tools=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export M4="$bison_tools/m4"
exec "$bison_tools/bison.real" "$@"
```

Make only this private wrapper executable. No system binaries, PATH configuration, host
accounts or personal agent configuration are changed. npm 10.9.4 is bundled with the
selected Node archive. GCC 14.2.0, GNU Make 4.4.1, Perl and Bubblewrap 0.12.0 came from the
cloud image and remain platform-specific prerequisites, not portable binary pins.
