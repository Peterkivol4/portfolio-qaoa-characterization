# J2 Resolution Example

This note records the concrete parameter-resolution example used in the top-level README.

## Setup

- `n_spins = 8`
- open boundary conditions
- `J1 = 1.0`
- `h = 1.0`
- disorder strength `= 0.0`
- optimizer: `spsa`
- evaluation budget: `60`
- seeds: `11, 17, 23, 31`
- comparison: `J2 = 0.3` versus `J2 = 0.5`

## Per-seed comparison

### `p = 1`

| seed | angle distance | `J2=0.3` energy error | `J2=0.5` energy error | `J2=0.3` NNN corr. error | `J2=0.5` NNN corr. error | `J2=0.3` fidelity | `J2=0.5` fidelity |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 11 | 0.7026 | 10.7990 | 10.1519 | 0.7148 | 0.7960 | 0.0355 | 0.0267 |
| 17 | 0.6455 | 10.8000 | 10.1751 | 0.7217 | 0.7776 | 0.0226 | 0.0350 |
| 23 | 0.2821 | 9.0970 | 11.4157 | 0.8955 | 0.8588 | 0.0034 | 0.0215 |
| 31 | 0.5483 | 10.5661 | 10.1457 | 0.5445 | 0.7912 | 0.0592 | 0.0309 |
| mean | 0.5446 | 10.3155 | 10.4721 | 0.7191 | 0.8059 | 0.0302 | 0.0285 |

### `p = 3`

| seed | angle distance | `J2=0.3` energy error | `J2=0.5` energy error | `J2=0.3` NNN corr. error | `J2=0.5` NNN corr. error | `J2=0.3` fidelity | `J2=0.5` fidelity |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 11 | 1.7786 | 8.4028 | 8.9730 | 0.7955 | 0.5555 | 0.0346 | 0.0479 |
| 17 | 1.9882 | 5.9715 | 3.0402 | 0.6354 | 0.4692 | 0.1039 | 0.4272 |
| 23 | 2.7797 | 9.4946 | 5.6251 | 0.4166 | 0.7891 | 0.0004 | 0.1096 |
| 31 | 0.9979 | 6.2263 | 6.5196 | 0.5483 | 0.6209 | 0.1240 | 0.2031 |
| mean | 1.8861 | 7.5238 | 6.0395 | 0.5989 | 0.6087 | 0.0657 | 0.1970 |

## Interpretation

At `p = 1`, the two frustration settings remain poorly resolved: the mean angle distance is only `0.5446`, both fidelities stay around `3e-2`, and both next-nearest-neighbor correlation errors remain large. By `p = 3`, the mean angle distance rises to `1.8861`, the `J2 = 0.5` mean fidelity rises to `0.1970`, and the optimized responses are no longer clustered near the same shallow-angle manifold.
