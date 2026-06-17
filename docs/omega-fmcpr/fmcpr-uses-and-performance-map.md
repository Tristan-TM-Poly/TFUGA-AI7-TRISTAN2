# Omega-FMCPR — Uses and Performance Map

**Status:** application atlas / OAK-gated.  
**Scope:** other uses and performance dimensions for fractal mycelial cooling, catalysis, purification, and Raman feedback.

## 1. Performance axes

```text
thermal:       DeltaT, heat flux, cooling stability, radiative/convective exchange
electrical:    DeltaV, DeltaI, P_load, P_net, sensor autonomy
field:         E/B localization, frequency selectivity, field cost, safety
chemical:      eta_purif, k_eff, selectivity, byproducts
spectral:      Raman SNR, DeltaR, baseline robustness, detection limit
hydraulic:     flow, pressure drop, residence time distribution
materials:     catalyst lifetime, adsorbent capacity, regeneration
system:        purification per watt, purification per volume, OAK score
```

## 2. Top use cases beyond basic purification

### 2.1 Autonomous environmental sensing

The reactor can run as a sensing node even when net energy generation is small:

```text
DeltaT -> DeltaV -> low-power Raman / conductivity / pH sampling
```

OAK gate:

```text
sensor uptime or sample throughput improves against battery-only control
```

### 2.2 Raman/SERS lab-on-chip

The fractal branches concentrate molecules and create hot-spot-like sampling points:

```text
fractal branch + Raman before/after = local spectral transformation proof
```

OAK gate:

```text
SNR and quantification error improve against flat/reference substrate
```

### 2.3 Catalytic screening platform

Different branches can carry different catalysts:

```text
branch_i = catalyst_i + field_i + flow_i + Raman delta_i
```

OAK gate:

```text
ranked catalyst performance is reproducible and not explained by flow or heating artifact
```

### 2.4 Smart membranes

Branches act as selective gates:

```text
adsorption + E/B bias + flow geometry = directional capture/release
```

OAK gate:

```text
selectivity and throughput beat passive membrane control
```

### 2.5 Anti-fouling adaptive filters

AC fields, pulsed flow, and branch switching can reduce fouling:

```text
fouling sensor -> field pulse -> branch regeneration
```

OAK gate:

```text
long-term flux and performance decay improve against control
```

### 2.6 Gas cleanup and sensing

Dry branches can become catalytic/adsorptive gas channels:

```text
gas in -> catalytic branch -> Raman/IR/electrical readout -> gas out
```

OAK gate:

```text
conversion or detection limit improves at matched energy and catalyst mass
```

### 2.7 Thermoelectric self-powered microreactors

A stable gradient can power local sensors or switches:

```text
DeltaT -> DeltaV -> local measurement / gate actuation
```

OAK gate:

```text
P_signal covers sensor/control budget or reduces external power requirement
```

### 2.8 Electrochemical synthesis and selectivity exploration

Instead of only cleaning, the system can tune reactions:

```text
field waveform + catalyst branch + Raman feedback = synthesis parameter scanner
```

OAK gate:

```text
product selectivity improves and byproducts remain acceptable
```

### 2.9 Magnetic capture and release

Magnetic particles or coatings can capture species and release them under changed fields:

```text
B_DC capture -> B_AC release/regenerate -> Raman verification
```

OAK gate:

```text
capture/release cycles stay stable and outperform passive magnetic filter
```

### 2.10 Dataset generator for AI/OAK design loops

Each branch run creates a tuple:

```text
geometry + fields + materials + spectra + chemistry + OAK outcome
```

OAK gate:

```text
dataset is reproducible, controlled, and contains negative memory cases
```

## 3. Best near-term performance targets

```text
1. Raman SNR gain > control
2. target removal > control at matched flow and catalyst mass
3. byproduct score acceptable
4. field energy does not dominate benefit
5. fouling slower than control
6. DeltaT stable enough for sensing or TE readout
7. CVCD captures both success and failure modes
```

## 4. Best first experiments

```text
E0: passive fractal channel vs straight channel, Raman in/out
E1: add adsorbent patches and compare removal
E2: add catalyst patches and compare conversion
E3: add DC field and measure energy per removed mass
E4: add AC frequency sweep and find selective branches
E5: add magnetic particles and capture/release cycles
E6: add thermal gradient and TE readout
E7: close the loop with Raman-driven parameter selection
```

## 5. FMCPR performance mantra

```text
Not maximum field: maximum useful chemistry per watt.
Not maximum Raman brightness: maximum truthful spectral evidence.
Not maximum fractality: maximum validated function.
Not maximum removal: safe removal without worse byproducts.
OAK decides.
```
