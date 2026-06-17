# CRFT — Corps Radiatif Fractal de Tristan

**Module:** `Omega-TFTS / radiative-body`  
**Status:** exploratory / simulation-ready  
**Claim strength:** geometric and electromagnetic architecture, not a thermodynamic free-energy claim.

## Thesis

A tunnelled fractal body whose voids are filled with selected dielectrics can act as a multi-scale electromagnetic radiator/absorber. The fractal maximizes internal surface-per-volume and creates a hierarchy of dielectric cavities, waveguide stubs, antennas, hot spots, and impedance-matching channels.

```text
fractal voids + dielectric loading + conductor/magnetic skin
-> multi-scale resonances
-> broadband absorption/emission shaping
-> possible gain in effective aperture, near-field density, and mode coupling
```

## OAK warning

A fractal surface can increase internal exchange area, local density of modes, absorption bandwidth, and coupling opportunities. It does **not** automatically create infinite far-field radiated power. In thermal equilibrium, far-field emission remains constrained by emissivity, aperture/projection, temperature, reciprocity, and energy conservation.

The correct research target is:

```text
maximize useful emissivity / absorptivity / coupling / bandwidth / Purcell-like enhancement
within thermodynamic and antenna bounds.
```

---

## 1. Geometry: surface-per-volume gain

For a unit Menger-type support after `n` substitutions:

```text
V_M(n) = (20/27)^n V_0
A_M(n) = 6 (4/3)^n
```

Therefore:

```text
(A/V)_M(n) = (A/V)_0 (9/5)^n
```

Define the surface-volume gain:

```text
G_SV^M(n) = (9/5)^n
```

For an isolated Cantor sparse cube assembly, if every surviving micro-cube surface is exposed:

```text
V_K(n) = (8/27)^n V_0
A_K(n) = 6 (8/9)^n
(A/V)_K(n) = (A/V)_0 3^n
```

So the Cantor skeleton has stronger surface-per-volume scaling, but weaker connectivity. The Menger body gives the better radiator body because it preserves channels, loops, and tunnel coupling.

Canonical design split:

```text
K_n = sparse high-S/V skeleton
M_n = connected high-S/V tunnel body
```

---

## 2. Dielectric-filled holes

Each hole or tunnel can be filled with a dielectric of complex permittivity:

```text
epsilon_r(omega) = epsilon'(omega) - i epsilon''(omega)
```

or loss tangent:

```text
tan(delta) = epsilon'' / epsilon'
```

Effects:

1. **Resonance compression**

```text
lambda_material = lambda_0 / sqrt(epsilon_eff)
f_res ~ c / (L_eff sqrt(epsilon_eff))
```

High permittivity lets smaller holes resonate at lower frequencies.

2. **Mode shaping**

Different dielectric fillings create different TE/TM/HEM-like resonances in the tunnel hierarchy.

3. **Impedance matching**

A dielectric gradient across scales can reduce reflection and push absorption/emission toward a designed band.

4. **Loss engineering**

Low-loss dielectric favors efficient radiation/resonance. Lossy dielectric favors absorption/thermalization.

---

## 3. Radiative law of the Tristan body

Define the effective spectral radiative output as:

```text
P(omega, T) = epsilon_eff(omega)
              A_eff(omega)
              M_BB(omega, T)
              eta_out(omega)
```

where:

```text
epsilon_eff(omega) = engineered emissivity/absorptivity
A_eff(omega)       = effective participating area/aperture
M_BB(omega,T)      = blackbody spectral exitance
eta_out(omega)     = outcoupling efficiency from internal tunnels to exterior
```

The total output is:

```text
P(T) = integral P(omega,T) d omega
```

The fractal advantage is not magical power multiplication. It is:

```text
A_eff(omega) increases where modes couple well
epsilon_eff(omega) can approach 1 across broader bands
eta_out(omega) can be tuned by aperture/tunnel geometry
```

---

## 4. Gain factors

Define a multiplicative design score:

```text
G_CRFT(omega,n) =
  G_SV(n)
  G_eps(omega)
  G_modes(omega,n)
  G_match(omega)
  G_out(omega)
  G_QV(omega)
```

with:

```text
G_SV(n)      surface-per-volume gain
G_eps        dielectric resonance compression / field concentration
G_modes      number and usefulness of coupled modes
G_match      impedance-matching improvement
G_out        external radiation/outcoupling efficiency
G_QV         Q / mode-volume enhancement, bounded by loss and bandwidth
```

OAK requires reporting each factor separately, because a large internal field can still fail to radiate if the mode is trapped or lossy.

---

## 5. Fractal antenna interpretation

The conductive/magnetic skeleton acts as a multi-scale antenna body:

```text
small features -> high frequencies
large tunnels  -> low frequencies
self-similarity -> multiband response
space-filling paths -> long electrical length in compact volume
```

The dielectric-filled holes convert the body into a hybrid of:

```text
fractal antenna
frequency-selective surface
metamaterial absorber/emitter
dielectric resonator antenna array
near-field hot-spot lattice
```

---

## 6. Dielectric gradient canon

Instead of filling every hole with the same dielectric, define a scale-dependent map:

```text
epsilon_s = epsilon_base * r_epsilon^s
loss_s    = loss_base * r_loss^s
```

where `s` is the fractal scale.

Possible assignments:

```text
large tunnels: low-loss dielectric for outcoupling and broad channels
middle tunnels: moderate epsilon for impedance matching
small holes: high epsilon or lossy dielectric for absorption/hot spots
magnetic inclusions: selected scales for nonreciprocal or tunable response
```

This produces a fractal dielectric impedance transformer.

---

## 7. CRFT + TFTS fusion

The radiative body becomes a branch of Omega-TFTS:

```text
CRFT = radiative / dielectric / antenna / absorber-emitter layer
TFTS = superconducting / topological / hyper-loop layer
```

Fusion:

```text
Omega-TFTS-CRFT =
  Menger-Cantor geometry
  + dielectric-filled holes
  + conductive/magnetic surfaces
  + superconducting or normal-metal paths
  + hyper-loop flux network
  + radiative aperture / absorber-emitter spectrum
```

The same holes can serve three roles:

```text
geometry role: maximize surface-volume
EM role: create resonances and impedance matching
topological role: create loops, cavities, vortex/edge sites
```

---

## 8. Simulation ladder

### Level 0: geometry

```text
compute A(n), V(n), A/V, holes, graph cycles, tunnel sizes
```

### Level 1: circuit/radiation proxy

```text
assign LC/RLC resonators to loops and holes
compute modal density and impedance spectrum
```

### Level 2: full-wave EM

```text
FDTD / FEM / MoM
extract S11, S21, absorption, radiation efficiency, gain pattern
```

### Level 3: thermal radiation

```text
extract epsilon_eff(omega)
compute P(omega,T)
compare to blackbody and flat control samples
```

### Level 4: superconducting/topological extension

```text
add Delta, Josephson couplings, flux quantization, BdG invariant
```

---

## 9. OAK validation metrics

```text
A_over_V_gain(n)
absorptivity A(omega)
emissivity epsilon(omega)
radiation efficiency eta_rad(omega)
realized gain G_realized(theta,phi,omega)
quality factor Q
mode volume V_mode
Purcell proxy Q/V_mode
thermal conductivity and hot-spot stability
breakdown field / dielectric loss
comparison against non-fractal controls
```

Reject strong claims if:

```text
increased internal area does not increase measured absorptivity/emissivity
modes are trapped and do not outcouple
losses dominate before useful radiation
thermal gradients destroy stability
performance is not better than optimized non-fractal controls
```

---

## 10. Canonical slogan

```text
Les trous deviennent des cavites.
Les cavites deviennent des resonateurs.
Les resonateurs deviennent des antennes.
Les antennes deviennent un spectre fractal.
Le dielectrique accorde le spectre.
La surface par volume amplifie le couplage.
OAK decide ce qui rayonne vraiment.
```
