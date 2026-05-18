# Full Inventory and Sharding

Use this reference before any large first scan.

The goal is to avoid missing files, avoid duplicate processing, and decide whether parallel subagent sharding is justified.

## Core Rule

Do not begin full classification immediately.

First create a **full inventory baseline** of the folder, then decide:

1. single-agent or parallel-subagent
2. how to shard the work
3. how to verify no file was missed

## Step 1 — Build the inventory baseline

The coordinator should first collect:

- total file count
- total directory count
- top-level directories
- file count per top-level directory
- extension distribution
- root-level loose files
- hidden/system-file count

This gives the team a stable baseline before any worker starts analysis.

## Inventory Output

The inventory should allow the coordinator to answer:

- how big is the folder
- where the biggest clusters are
- whether the folder is clean or mixed
- whether the problem is large enough to justify parallel workers

At minimum, keep:

- `total_files`
- `total_dirs`
- `files_by_top_level_dir`
- `files_by_extension`
- `root_level_file_count`
- `hidden_or_system_file_count`

## Why this matters

Without a baseline, workers can:

- miss entire branches
- duplicate work on the same paths
- over-focus on obvious keyword-heavy directories
- under-cover quiet but important folders

## Step 2 — Decide single-agent vs parallel-subagent

### Prefer single-agent when

- file count is modest
- role is obvious
- folder structure is already clean
- refresh-only work is needed

### Prefer parallel subagent mode when

- file count is large
- top-level branches are numerous
- the folder mixes internal and client/project materials
- role is ambiguous
- compliance, assets, and business materials are mixed

## Mandatory Thresholds

These are execution gates for this skill:

- `total_files > 3000` → parallel subagent mode required
- `meaningful_top_level_branches > 8` → parallel subagent mode required
- mixed customer/project + compliance + asset signals → parallel subagent mode required
- low or medium role confidence after inventory triage → parallel subagent mode required

Below those thresholds, single-agent mode is allowed but not required.

## Step 3 — Shard by directory, not by keyword

For first coverage, shard by **directory slices**, not semantic keyword slices.

Good sharding:

- Worker A owns a top-level subtree
- Worker B owns a different subtree
- Worker C owns another subtree

Bad sharding:

- one worker scans “PRD”
- one worker scans “合同”
- one worker scans “风险”

Keyword sharding is useful later for focused checks, but it is weak as the primary coverage strategy.

## Recommended Sharding Strategy

### First layer

Coordinator groups by top-level or near-top-level directories.

### Second layer

Balance shards roughly by:

- file count
- business complexity
- obvious risk

### Third layer

Assign workers bounded ownership, for example:

- Worker A: product / project / delivery folders
- Worker B: customer / sales / external project folders
- Worker C: finance / HR / legal / admin folders
- Worker D: historical archive / mixed legacy folders

## Worker Ownership Rule

Each worker should receive:

- owned paths
- excluded paths
- target questions
- required output format

This prevents overlap and improves coverage accounting.

## Step 4 — Coverage accounting

At the end, the coordinator must compare:

- `inventory_total`
- `processed_unique_total`
- `skipped_total`
- `unassigned_total`
- `duplicate_total`

Target:

- `inventory_total = processed_unique_total + skipped_total`
- `unassigned_total = 0`
- `duplicate_total = 0`

## Coverage Checklist

Before synthesis, verify:

- every top-level branch was assigned
- root-level loose files were not forgotten
- hidden/system files were intentionally skipped, not accidentally ignored
- no worker reported paths outside its assigned slice
- no top-level branch has zero ownership

## Suggested Internal State Files

These do not need to be delivered to the end user. They are coordinator working state.

### `scan.summary.json`

Holds:

- total file count
- total directory count
- shard candidates
- extension distribution

### `scan.assignment.json`

Holds:

- worker name
- owned paths
- excluded paths
- expected file count per shard

### `scan.coverage.json`

Holds:

- processed file count
- skipped file count
- duplicate count
- unassigned count

## Required Team Flow

1. coordinator builds inventory baseline
2. coordinator decides single-agent or parallel-subagent mode
3. if parallel-subagent mode, coordinator shards by directory
4. subagents inspect only their slices
5. coordinator merges results
6. coordinator runs coverage check
7. only then ask the user and generate outputs

## Important Rule

Coverage comes before elegance.

It is better to have a slightly rough early classification with full coverage than a polished but incomplete classification that missed a whole branch of files.

## Important Prohibition

If the mandatory thresholds are hit, the coordinator must not:

- stop after a single inventory worker
- ask the user immediately after inventory
- generate HTML immediately after inventory
- skip sharding and coverage accounting
