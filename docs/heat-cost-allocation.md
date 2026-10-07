# What the heat reading is

[English](heat-cost-allocation.md) · [Čeština](cs/heat-cost-allocation.md)

The number odecet.info shows for heat is not a quantity of energy. It is the raw counter of an **electronic heat cost allocator** mounted on a radiator, built to EN 834. This page follows that reading from the temperature impulse on the radiator through the allocation coefficients to joules and kilowatt-hours. Home Assistant only receives the first step, the raw scale units.

## 1. What a scale unit is

### The device

The device on the radiator is not a heat meter. A heat meter sits in the pipe. It measures the volume flow of the heating water, in cubic metres per hour, and the temperature difference between flow and return. It integrates energy and displays physical units such as GJ or kWh.

An electronic heat cost allocator is fixed to the radiator surface. It has no contact with the water and does not know the flow. It measures temperature. One sensor reads the radiator surface. Another reads the air in the room.

### What the raw scale unit means

The device integrates the difference between the radiator surface and the room air, using an approximation of how a radiator gives off heat:

$$
I = \int (T_{\text{surface}} - T_{\text{air}})^{m} \, dt
$$

$m$ is the radiator's temperature exponent, usually about $1.2$ to $1.3$.

A **scale unit** is a dimensionless step of that internal counter. It is a sum of heat flow from the radiator surface into the room over time. The device stays idle when the radiator is cold or the temperature difference is tiny, for example when summer sun warms the room. When heating water warms the radiator, the counter starts adding scale units.

One hundred scale units on a small bathroom rail release much less energy into the air than one hundred scale units on a three-metre triple-panel radiator in a living room. The raw number has no physical dimension.

## 2. Names

| Level | English name | Meaning |
| --- | --- | --- |
| Device | Electronic heat cost allocator | The device on the radiator |
| Raw value | Scale unit, raw reading, unweighted display value | The counter, before any coefficients |
| Weighted value | Cost allocation unit, weighted reading | The reading after the radiator and position coefficients |
| Building energy | Total heat energy consumed | The building's real energy, in GJ or MWh |

## 3. Static and dynamic quantities

Turning scale units into joules needs two kinds of parameters.

### Static quantities

These stay put until someone rebuilds, replaces windows, or replaces a radiator.

1. **Radiator rating coefficient ($K_v$).** The radiator's nominal heat output, in watts, at a standard temperature set (for example $75/65/20\ ^\circ\text{C}$), and how heat passes from the radiator to the allocator. It comes from the heating design and from type tests. A larger radiator has a higher $K_v$.
2. **Room position coefficient ($K_p$).** How exposed the room is. A north room with three outside walls under an unheated roof loses more heat than an internal room facing south. The coefficient comes from a room heat-loss calculation. In practice it is often below $1.0$, commonly about $0.4$ to $0.9$, and it reduces the scale units of a disadvantaged room so the occupants do not pay for the building's cold corner.
3. **Floor area ($A$).** The apartment area $A_{\text{apt}}$ and the heated area of the whole building $A_{\text{bldg}}$, in square metres.
4. **Basic and consumption split ($Z\% / S\%$).** How the building's bill is divided. Common splits are 40/60, 50/50, or 60/40.

### Dynamic quantities

These exist only after a billing period.

1. **Scale units of one radiator ($N_{\text{raw}}$).** Steps counted in the period.
2. **Building heat energy ($Q_{\text{bldg}}$).** Energy measured by the building heat meter in the basement, in GJ or MWh.
3. **Sum of the building's cost allocation units ($N_{\text{bldg}}$).** Every radiator in every apartment, for the year.

## 4. From scale units to joules

The calculation has a local normalisation and then a building-wide allocation.

```text
[ Raw radiator scale units: N_raw ]
               |
               v  × K_v (radiator rating) × K_p (room position)
[ Radiator cost allocation units: N_w ]
               |
               v  Sum across the apartment's radiators
[ Apartment cost allocation units: N_apt ]
               |
               v  × (Q_cons_bldg / N_bldg) = joules per cost allocation unit
[ Apartment consumption energy: Q_apt,cons ]
               |
               v  + Basic share of the apartment (by floor area)
[ Total energy attributed to the apartment: Q_apt,total ]
```

### Phase 1: scale units to cost allocation units

For each radiator:

$$
N_{w} = N_{\text{raw}} \times K_v \times K_p
$$

- Input: $N_{\text{raw}}$, scale units.
- Parameters: $K_v$ and $K_p$, both dimensionless.
- Output: $N_{w}$, cost allocation units.

The apartment total is the sum of its radiators:

$$
N_{\text{apt}} = \sum_{i=1}^{k} N_{w,i}
$$

### Phase 2: cost allocation units to joules

This step needs the whole building. The allocator only measures a share.

The consumption part of the building energy is:

$$
Q_{\text{cons}} = Q_{\text{bldg}} \times \frac{S\%}{100\%}
$$

One cost allocation unit is worth:

$$
e = \frac{Q_{\text{cons}}}{N_{\text{bldg}}}
$$

in GJ or joules per cost allocation unit.

The radiator's energy is:

$$
Q_{\text{radiator}} = N_{w} \times e = (N_{\text{raw}} \times K_v \times K_p) \times e
$$

The apartment's consumption energy is:

$$
Q_{\text{apt,cons}} = N_{\text{apt}} \times e
$$

### Phase 3: the basic share

Heat also enters through uninsulated risers and through walls from neighbouring rooms. Part of the bill is therefore split by floor area.

$$
Q_{\text{basic}} = Q_{\text{bldg}} \times \frac{Z\%}{100\%}
$$

$$
Q_{\text{apt,basic}} = Q_{\text{basic}} \times \frac{A_{\text{apt}}}{A_{\text{bldg}}}
$$

$$
Q_{\text{apt,total}} = Q_{\text{apt,basic}} + Q_{\text{apt,cons}}
$$

## 5. Energy units

- $1\ \text{J} = 1\ \text{W}\cdot\text{s}$
- $1\ \text{MJ} = 10^{6}\ \text{J}$
- $1\ \text{GJ} = 10^{9}\ \text{J} = 1000\ \text{MJ}$
- $1\ \text{kWh} = 3.6\ \text{MJ}$
- $1\ \text{MWh} = 1000\ \text{kWh} = 3.6\ \text{GJ}$
- $1\ \text{GJ} \approx 277.78\ \text{kWh} \approx 0.2778\ \text{MWh}$

## 6. A worked example

Building, for one year:

- Energy at the building meter, $Q_{\text{bldg}}$: $500\ \text{GJ}$
- Heated floor area, $A_{\text{bldg}}$: $2500\ \text{m}^{2}$
- Split: 40% basic, 60% consumption
- Sum of cost allocation units, $N_{\text{bldg}}$: $25000$

Derived:

- Consumption energy: $500 \times 0.60 = 300\ \text{GJ}$
- Basic energy: $500 \times 0.40 = 200\ \text{GJ}$
- One cost allocation unit:

$$
e = \frac{300\ \text{GJ}}{25000} = 0.012\ \text{GJ} = 12\ \text{MJ} \approx 3.333\ \text{kWh}
$$

An apartment of $60\ \text{m}^{2}$ with two radiators:

| Room | Scale units | $K_v$ | $K_p$ | Cost allocation units | Energy |
| --- | --- | --- | --- | --- | --- |
| Living room | 400 | 1.25 | 0.80 | $400 \times 1.25 \times 0.80 = 400$ | $400 \times 12 = 4800\ \text{MJ}$ (1333.3 kWh) |
| Bedroom | 150 | 1.00 | 0.60 | $150 \times 1.00 \times 0.60 = 90$ | $90 \times 12 = 1080\ \text{MJ}$ (300.0 kWh) |
| Consumption total | 550 |  |  | 490 | $5880\ \text{MJ}$ (5.88 GJ, 1633.3 kWh) |

The apartment is $60 / 2500 = 2.4\%$ of the floor area.

- Basic energy: $200\ \text{GJ} \times 0.024 = 4.80\ \text{GJ} = 4800\ \text{MJ}$ (1333.3 kWh)
- Total: $5.88 + 4.80 = 10.68\ \text{GJ} = 10680\ \text{MJ} \approx 2966.7\ \text{kWh} \approx 2.97\ \text{MWh}$

## What this integration can show

1. The number in the export is **scale units**: a dimensionless integral of the radiator-to-air temperature difference.
2. Turning scale units into cost allocation units is **static**. It depends on that radiator ($K_v$) and that room ($K_p$). The integration does not have those coefficients.
3. Turning cost allocation units into joules or kilowatt-hours is **dynamic**. It is a share of the building bill and changes every winter with the building meter and with every neighbour. The integration does not have that bill.

Home Assistant therefore stores the raw counter as `scale units`. It does not place that sensor on the Energy dashboard. Selecting heat is often not useful unless you only want to watch whether the counter is moving.
