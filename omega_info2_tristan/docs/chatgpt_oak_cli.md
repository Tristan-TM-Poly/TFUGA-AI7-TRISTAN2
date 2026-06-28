# ChatGPT OAK CLI

`omega-chatgpt-oak` evaluates whether a Tristan GitHub workflow is allowed to stop or must continue.

## Rule

For Tristan `Go @GitHub` workflows:

```text
CI green + mergeable + not merged = must merge
```

## Print rules

```bash
omega-chatgpt-oak --rules
```

## Evaluate context

```bash
cat > context.json <<'JSON'
{
  "requested_go_github": true,
  "pr_open": true,
  "ci_green": true,
  "mergeable": true,
  "merged": false,
  "used_fresh_head_sha": true
}
JSON

omega-chatgpt-oak --context context.json
```

Expected decision: gate fails and asks for merge.

## CI mode

```bash
omega-chatgpt-oak --context context.json --exit-nonzero-on-fail
```

This exits with code `2` when the gate catches a workflow mistake.

## OAK note

This CLI is a supervisor, not a GitHub connector. It does not merge by itself. It prevents summaries that stop before the real final state.
