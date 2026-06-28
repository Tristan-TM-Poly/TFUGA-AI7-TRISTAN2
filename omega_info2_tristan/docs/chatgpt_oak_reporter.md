# ChatGPT OAK Reporter

`chatgpt_oak_reporter.py` prevents premature final summaries for Tristan `Go @GitHub` workflows.

## Core rule

```text
Do not produce a final successful GitHub summary before merge.
```

If CI is green and the PR is mergeable but not merged, the reporter raises an error. This encodes the negative memory from the earlier failure: PR open and green is not the final state.

## Valid final states

- `MERGED`: successful post-merge report.
- `BLOCKED_REAL`: report a real blocker such as missing permission, failed CI, safety issue, or legal/IP risk.

## Example

```python
from omega_info2 import GitHubRunContext, build_post_merge_report

context = GitHubRunContext(
    requested_go_github=True,
    pr_open=True,
    ci_green=True,
    mergeable=True,
    merged=True,
    used_fresh_head_sha=True,
    summary_after_merge=True,
)

report = build_post_merge_report(
    context,
    pr_number=140,
    merge_sha="abc123",
    files_changed=["src/module.py", "tests/test_module.py"],
)
print(report.body)
```

## OAK note

This module is a final-answer guard. It does not call GitHub by itself; it prevents ChatGPT from claiming completion too early.
