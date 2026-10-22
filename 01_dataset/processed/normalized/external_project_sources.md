# External Project Sources

The paper uses multiple historical versions of ten open-source C/C++ projects. The project source trees themselves are **not** copied into `heuristic_vs_LLM/` to avoid duplicating third-party repositories.

Configure the local source root with `--source-root <source-root>` when running
`02_heuristic/scripts/tracker.py`. The directories below are relative to that
root. Source trees are external inputs and are not included in this repository.

Observed project-version directory names referenced by the evaluation inputs:

- `curl-8.11.1`
- `curl-8.13.0`
- `curl-8.15.0`
- `curl-8.7.1`
- `curl-8.9.1`
- `curl-8_13_0`
- `curl-8_9_1`
- `ffmpeg-6.0`
- `ffmpeg-6.1.1`
- `ffmpeg-7.0.1`
- `ffmpeg-7.1`
- `ffmpeg-7.1.1`
- `git-2.44.0`
- `git-2.46.0`
- `git-2.47.1`
- `git-2.49.0`
- `git-2.50.1`
- `libuv-1.46.0`
- `musl-1.1.24`
- `musl-1.2.1`
- `musl-1.2.3`
- `musl-1.2.4`
- `nginx-1.25.4`
- `nginx-1.27.2`
- `openssl-3.2.1`
- `openssl-3.5.1`
- `openssl-openssl-3.3.1`
- `openssl-openssl-3.5.1`
- `redis-7.0.11`
- `redis-7.2.1`
- `redis-7.4.2`
- `redis-8.0.2`
- `tmux-3.0`
- `tmux-3.1`
- `tmux-3.2`
- `tmux-3.3`
- `tmux-3.4`
- `vim-9.1.0550`
- `vim-9.1.1040`
- `vim-9.1.1591`

Provide these project-version directories under the configured source root.
