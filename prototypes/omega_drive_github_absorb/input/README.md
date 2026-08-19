# Local Drive links input

This folder is intentionally ignored except for this README and `.gitignore`.

Real Google Drive links can be sensitive because a folder or file ID may grant access, reveal private project structure, or expose unpublished IP. Do not commit real links to this public repository.

## Local workflow

Create a local-only file:

```bash
cat > prototypes/omega_drive_github_absorb/input/drive_links.local.txt <<'EOF'
https://drive.google.com/drive/folders/YOUR_PRIVATE_FOLDER_ID
EOF
```

Run inventory-only mode:

```bash
PYTHONPATH=prototypes/omega_drive_github_absorb \
python -m omega_drive_github_absorb \
  prototypes/omega_drive_github_absorb/input/drive_links.local.txt \
  --repo Tristan-TM-Poly/TFUGA-AI7-TRISTAN2 \
  --level L1 \
  --max-level L1 \
  --out generated/omega_drive_github_absorb
```

The local file and generated outputs must stay local unless an OAK/IP/security review explicitly permits a redacted artifact to be committed.

## OAK rule

```text
Real Drive links stay local.
Public GitHub gets only code, schemas, redacted examples, and safe reports.
```
