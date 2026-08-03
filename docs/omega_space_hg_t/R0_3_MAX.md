# Ω-SPACE-HG-T∞ R0.3 MAX — Physical and Information Networks

## Scope

R0.3 couples the R0.2 perturbed orbit to four explicit mission networks:

1. a multi-node lumped thermal graph;
2. an electrical-power and battery flow model;
3. an RF link and rotating-Earth ground-contact model;
4. a finite onboard data queue.

The integrated fixture connects orbit, illumination, operating modes, loads,
heat, storage and downlink rather than optimizing each subsystem in isolation.
It remains reduced-order research software and is not an operational network,
licensed radio design, flight product or qualification artifact.

## Thermal network

Each thermal node carries heat capacity, temperature, radiator area, emissivity
and declared limits. Conductive edges exchange heat symmetrically. External heat
and radiation to a sink close the node balance. Every step reports:

- node net heat;
- conductive exchange;
- radiated heat;
- internal-energy change;
- external-energy input;
- energy-balance residual;
- limit violations.

The OAK fixture uses a closed two-node conductive system and verifies total
energy conservation to `1e-8 J`.

## Electrical power system

The battery baseline tracks stored energy, SOC, charge/discharge throughput,
current limits, efficiencies, ohmic losses, curtailed generation, served load
and unmet load. The solver explicitly reports impossible loads rather than
silently violating SOC or current limits.

This is not an electrochemical cell model. Temperature dependence, capacity
fade, state-of-health estimation, cell imbalance and validated equivalent-
circuit parameters remain future work.

## Communications and ground contact

The link engine calculates wavelength, free-space path loss, received power,
noise power, carrier-to-noise, `C/N0`, a theoretical bitrate ceiling and margin.
The first OAK invariant verifies that doubling range adds
`6.020599913 dB` of path loss.

Ground contact uses a spherical rotating body, station latitude/longitude,
minimum elevation and sampled orbit states. Contact windows preserve start,
end, duration and maximum elevation.

The model does not include regulatory allocation, atmospheric attenuation,
polarization mismatch, antenna patterns, implementation losses, coding gain,
interference, Doppler acquisition or real ground-station availability.

## Data network

The finite queue accounts exactly for:

```text
available = prior storage + generated data
transmitted = min(available, link capacity)
stored = min(capacity, available - transmitted)
dropped = overflow beyond capacity
```

The integrated canonical fixture produces payload data outside ground contacts,
downlinks during visible passes and records both delivered and dropped volume.

## Integrated fixture

The default `omega-space-hg-r03 simulate` run uses:

- the R0.2 550 km inclined J2 orbit;
- a Montreal ground station;
- cylindrical binary eclipse;
- a three-node bus/payload/battery thermal graph;
- a 420 Wh, 28 V bounded battery;
- a 2.2 GHz free-space link;
- a 256 GB data store;
- deterministic payload/contact modes.

Its OAK gate requires:

- no thermal or power violations;
- SOC above the declared floor;
- at least one contact window;
- positive delivered data;
- zero data loss;
- storage below 95 percent;
- exact deterministic replay.

Passing this gate certifies only the stated software fixture.

## Commands

```bash
omega-space-hg-r03 manifest
omega-space-hg-r03 simulate --duration-orbits 8 --step-s 20
omega-space-hg-r03 oak
```

## Validation

```bash
pytest -q \
  tests/test_omega_space_hg_t.py \
  tests/test_omega_space_hg_r02.py \
  tests/test_omega_space_hg_r03.py
python -m omega_space_hg_t.r03_cli simulate --duration-orbits 8 --step-s 20
python -m omega_space_hg_t.r03_cli oak
python examples/omega_space_hg_r03_demo.py
```

## M-minus registry

- `M⁻-SPACE-R03-001`: explicit-Euler thermal networks require step-size checks.
- `M⁻-SPACE-R03-002`: thermal conductances and capacities are inputs, not inferred
  qualified properties.
- `M⁻-SPACE-R03-003`: battery energy accounting is not electrochemical validation.
- `M⁻-SPACE-R03-004`: a free-space-positive link margin does not grant spectrum,
  legal operation or reliable communications.
- `M⁻-SPACE-R03-005`: sampled contact windows may miss short threshold crossings.
- `M⁻-SPACE-R03-006`: a binary cylindrical eclipse is not precision illumination.
- `M⁻-SPACE-R03-007`: no loss in the canonical queue does not prove capacity for
  another orbit, payload, station network or operational schedule.

## Next frontier

R0.4 should add reliability distributions, fault trees, common-cause failures,
radiation-event ledgers, watchdog/safe-mode state machines, bounded FDIR,
Monte-Carlo campaigns and promotion of real failure witnesses into M-minus
regression assets.
