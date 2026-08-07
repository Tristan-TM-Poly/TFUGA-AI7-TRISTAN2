# R0.9 signature limitations

R0.9 validates the **receipt contract** for signatures:

- signature method is allowlisted;
- signer ID and role are present;
- signer is not an author where independence is required;
- signed timestamp is timezone-aware;
- payload digest matches the exact R0.9 request, evidence, checks and M-minus history;
- signature reference is preserved.

R0.9 does **not** invoke GPG, Sigstore, Fulcio, Rekor, a certificate authority,
a hardware token or an institutional identity provider.

Therefore:

```text
method = pgp or sigstore
```

means that a signature receipt was supplied in that declared format. It does
not mean that R0.9 independently proved the signer's legal identity, key
ownership, certificate validity, revocation state or institutional authority.

Before any real external action, a qualified human process must verify the
signature with the appropriate external trust system and preserve that
verification as new evidence.

The deterministic `sha256_detached` method only proves payload equality. It is
not identity authentication and is rejected for public destinations.
