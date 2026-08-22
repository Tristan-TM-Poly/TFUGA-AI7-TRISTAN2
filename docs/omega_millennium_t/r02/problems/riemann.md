# Riemann Hypothesis

Status: `open`

Every nontrivial zero of the Riemann zeta function has real part one half.

No solution is claimed.

## Ω-ZETA-SQUARE-T∞ research surface

The repository now includes an OAK-safe centered-square research toolkit at
`omega_zeta_square_t/` with documentation in `docs/omega_zeta_square_t/README.md`.

Canonical quotient coordinate:

\[
w=s-\frac12,\qquad u=w^2=(s-\tfrac12)^2.
\]

For a candidate zero \(\rho=\beta+i\gamma\),

\[
D_{RH}(u)=\frac{|u|+\Re u}{2}=(\beta-\tfrac12)^2.
\]

The toolkit explores quotient/parabolic geometry, the standard
\(\Theta(u)=\xi(1/2+\sqrt u)\) criterion, finite Stieltjes/Hankel diagnostics,
parabolic tomography, HGFM proof graphs, CVCD criterion compression, and OAK
negative-memory rules.

Important epistemic boundary: equivalent formulations, finite zero checks,
finite Hankel positivity, numerical spectral reconstruction, and pattern
recognition are research evidence only. They do not establish RH.

Machine-readable contract:
`specs/omega_zeta_square_t/research_contract.json`.

Initial proof/criterion hypergraph:
`specs/omega_zeta_square_t/proof_graph.json`.
