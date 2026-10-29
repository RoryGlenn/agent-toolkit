`native-seccomp.json` derives from Moby profiles commit
`4b8214fc4971e06172938a1f1554ccff6647ee80`, `seccomp/default.json`.
The original profile's SHA-256 is
`6416b47770785a41ac59073cdc77d9fe98517df2799dc83ef207e622de3053f6`.
Its Apache 2.0 license is retained in `MOBY-LICENSE`.

The only additional allowed syscalls are `clone`, `clone3`, `unshare`, `setns`,
`mount`, `umount2`, `pivot_root` and `chroot`, needed by Codex's nested command
sandbox and the evaluator's Bubblewrap launcher. No Linux capabilities are added.
Both actor and evaluator cells use this extended profile and require filesystem budget = memory.max,
zero swap, exclusively tmpfs writable data and in-cgroup data materialization:
payloads can create another private tmpfs, so the sum of initial mount sizes alone
is not an aggregate filesystem bound. Cgroup memory enforces the total allocated
memory-backed storage even across such nested mounts.
