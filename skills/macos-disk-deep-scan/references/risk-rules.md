# Developer disk audit rules

## Classify by evidence

| Location or artifact | Starting judgment | Required qualification |
| --- | --- | --- |
| npm `_cacache`, pip cache, Homebrew download cache | Regenerable candidate | Check downloads/installers and actual configured location; the preset uses common paths, not effective config. |
| npm `_npx` | Per-entry conditional candidate | MCP servers and long-running CLIs execute here; inspect each exact child, including process argument references. Never suggest clearing all npx while tools are running. |
| npm global modules, Bun global packages, runtime managers | Installed software | Not cache. Preserve unless the user separately chooses to uninstall a known tool/version. |
| uv cache | Conditional candidate | A held `.lock` means active use. Do not delete/recreate locks. Cached environments may host live processes. Preserve `.venv` separately from download caches. |
| pnpm store, Cargo/Maven/Gradle/Go module caches | Conditional candidate | Hardlinks, offline/private dependencies, active builds and rebuild/download costs matter. Do not call a store's whole size unused. Do not execute package-manager cleanup commands. |
| `node_modules`, `.next`, `.build`, `.derivedData`, Xcode DerivedData | Generated-output candidate | Check tracked files, owning repo, working directories, servers, builds and signed/benchmark evidence requirements. Keep source and lockfiles. |
| Python `.venv` | Reinstallable environment candidate | Check interpreter/tool use and whether dependencies are recoverable. Do not equate it with a wheel cache. |
| `target` beside `Cargo.toml` | Rust output candidate | Inspect repo and processes. An unrelated directory named `target` remains unknown. |
| Generic `build`, `dist`, `tmp`, temporary source copies | Unknown until investigated | Names alone do not prove generated content. Temporary paths may contain the only copy of code, captures, reports or research. |
| Git worktrees | Preserve the tree initially | Enumerate through read-only Git evidence; separate ignored build/dependency outputs. Dirty state or untracked files prohibit a whole-tree recommendation. Clean does not mean merged or unused. |
| IDE `CachedData`, `CachedExtensionVSIXs` | Conditional cache | Retain active versions/downloads. Preserve installed extensions, `User`, workspace databases, agent sessions, file history and recovery backups. |
| Application log directories | Conditional, file-level | Separate old closed logs from open/recent logs and evidence. Age alone is not authorization. Never delete whole live log roots. |
| Application update staging | Conditional | A pending update marker, incomplete download or running updater blocks the recommendation until clarified. No open files is insufficient. |
| Browser ordinary cache | Conditional | Require browser-specific scope; preserve active use. Do not conflate profile data with ordinary cache. |
| Browser `CacheStorage`, Service Worker resources | Offline application data | May contain app-managed offline content; discuss offline loss and refetch cost. Preserve adjacent IndexedDB, Local Storage, cookies, credentials and profile directories. |
| Browser local models, automation browsers, tool runtimes | Optional installed resources | Check live use and redownload/feature impact. They may recreate immediately. |
| Docker/OrbStack/Claude/other VM disks | Preserve | Report allocated and logical sizes separately. Do not remove raw disks or start engines/remote contexts. Internal reclaimable image/layer data requires a separate scoped investigation. |
| Agent sessions, archives, backups, screenshots, generated media, packet captures | User data / evidence | Do not include in a routine cache tier even when stored under hidden or temporary directories. |
| `/private/var/folders`, `/private/tmp` | Mixed-use | Select proven child artifacts only; preserve sockets, live test/IPC directories, system runtime content and unknown artifacts. |
| VM/swap, Preboot, OS snapshots, Recovery | System-managed | Never manually clear. Suggest saving work and a voluntary normal restart only as advice, with no promised savings. |

## Interpret uncertainty

- **Measured allocation:** `st_blocks * 512`, with same-root hardlinks counted once. It is not exclusive APFS extent ownership. Never promise its full value will return as free space.
- **Partial scan:** display the reason alongside every derived estimate. A timeout can yield no size; show unknown, not zero. Ranking omission is not proof that another directory is small.
- **Activity:** positive open-file/cwd/argument evidence blocks a current cleanup suggestion. Negative evidence remains limited to visibility and observation time. macOS privacy and ownership restrictions can hide processes/files.
- **Identity:** device/inode/mtime/owner observations help notice change, but are neither an immutable snapshot nor an execution authorization. Directory mtime does not seal every descendant.
- **Deleted-but-open files:** if separately investigated, explain that only normal process exit may release them. Never print raw command arguments, and never kill unrelated processes to reclaim bytes.
- **Sparse/clone/shared storage:** distinguish logical size, allocated size and actually reclaimed free space. Avoid double counting nested worktrees, repeated scans, shared hardlinks and APFS containers.
- **TCC/network/storage extensions:** do not bypass permissions, follow cloud placeholders, or retry hung file providers indefinitely. Bound each root and report it unscanned. Read-only scanning does not justify changing system permissions.
- **Sensitive diagnostics:** emit only needed paths and process IDs. Never include command-line API keys, cookies, database contents, or environment values in reports or repository fixtures.

## Handle dialogue without executing

Use a question such as: “Which exact entries should I put on a proposed cleanup list: developer caches, inactive build outputs, or selected application caches? Which applications and evidence must be excluded?”

Carry forward scope by exact paths and exclusions, not broad globs. Include expected rebuild/redownload/offline effects, activity observations, coverage gaps and timestamps. If a user authorizes deletion, state that execution is outside this v1 skill; stop after the proposed list. Do not silently continue with a shell deletion, package-manager prune, worktree removal, app termination, or permission change.
