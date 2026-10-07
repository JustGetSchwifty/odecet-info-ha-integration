# Co vlastně ukazuje topení

[![English](https://img.shields.io/badge/English-6e7681?style=for-the-badge)](../heat-cost-allocation.md) [![Čeština](https://img.shields.io/badge/Čeština-1f6feb?style=for-the-badge)](heat-cost-allocation.md)

Tento přehled přináší ucelený technický a matematický popis celého řetězce rozúčtování tepla v bytových domech s centrální otopnou soustavou – od fyzikálního vzniku impulsu na radiátoru přes normalizační koeficienty až po finální přepočet na jouly a kilowatthodiny. Home Assistant z odecet.info dostane jen první krok, surové dílky.

## 1. Co je to dílek a jak funguje měření na tělese

### Technická podstata zařízení

Zařízení osazené na radiátoru není kalorimetr (fyzikální měřič tepla), nýbrž **indikátor topných nákladů (ITN)**, v moderní podobě **elektronický indikátor topných nákladů (EITN)**, konstruovaný dle evropské technické normy ČSN EN 834.

Rozdíl oproti kalorimetru:

- **Fyzikální kalorimetr** se vkládá do potrubí, měří objemový průtok teplonosné látky (v $\text{m}^3/\text{h}$) a teplotní spád mezi přívodem a zpátečkou ($\Delta T$). Přímo integruje energii a zobrazuje fyzikální jednotky (GJ, kWh).
- **Indikátor (EITN)** je připevněn na povrchu radiátoru. Nemá žádný kontakt s protékající vodou a nezná její průtok. Měří pouze teplotu. Obvykle disponuje dvěma snímači: jedno čidlo měří povrchovou teplotu radiátoru, druhé čidlo měří teplotu vzduchu v místnosti.

### Co vyjadřuje surový dílek

Přístroj vyhodnocuje rozdíl teplot mezi povrchem radiátoru a vzduchem v místnosti. V čase tento rozdíl sčítá (integruje) podle aproximace fyzikálního zákona sdílení tepla:

$$
I = \int (T_{\text{telesa}} - T_{\text{vzduchu}})^{m} \, dt
$$

Kde $m$ je teplotní exponent otopného tělesa (obvykle $m \approx 1{,}2$ až $1{,}3$).

**Dílek je bezrozměrný krok vnitřního počítadla.** Představuje určitou sumu tepelného toku z povrchu radiátoru do vzduchu v čase. Přístroj má v sobě zabudované prahové podmínky (tzv. letní blokování) – pokud je povrch radiátoru chladný nebo je rozdíl teplot minimální (např. v létě při ohřátí bytu sluncem), počítadlo stojí. Jakmile začne otopná voda těleso ohřívat, čítač začne načítat impulsy – dílky.

Dílek sám o sobě nemá žádný fyzikální rozměr, protože 100 dílků na malém koupelnovém žebříku uvolní do vzduchu podstatně méně energie než 100 dílků na třímetrovém trojdeskovém radiátoru v obývacím pokoji.

## 2. Názvosloví

| Úroveň veličiny | Český název | Význam |
| --- | --- | --- |
| Přístroj | Indikátor topných nákladů (EITN / ITN) | Zařízení na otopném tělese |
| Surová hodnota | Odečtený dílek, dílek, odečtený náměr | Přímý stav počítadla bez úprav |
| Přepočtená hodnota | Nákladová jednotka (nj), přepočtený náměr | Hodnota po aplikaci koeficientů tělesa a polohy |
| Globální energie | Množství tepla (fakturační náměr domu) | Reálná energie budovy (GJ, MWh) |

## 3. Statické a dynamické veličiny

Aby bylo možné ze surových dílků získat jouly, kombinují se dva druhy parametrů.

### Statické veličiny

Tyto hodnoty jsou dlouhodobě stálé a mění se pouze při stavební rekonstrukci, výměně oken nebo výměně radiátoru.

1. **Koeficient výkonu otopného tělesa ($K_v$).** Jmenovitý tepelný výkon radiátoru (ve wattech) při standardním teplotním spádu (např. $75/65/20\ ^\circ\text{C}$) a způsob přestupu tepla mezi tělesem a indikátorem. Bere se z projektové dokumentace vytápění a z typových zkoušek. Větší těleso znamená vyšší $K_v$.
2. **Polohový koeficient místnosti ($K_p$).** Zohlednění tepelně-technické polohy místnosti v budově. Místnost na severu s třemi ochlazovanými stěnami pod nevytápěnou střechou má mnohem vyšší přirozenou tepelnou ztrátu než vnitřní místnost obklopená vytápěnými byty orientovaná na jih. Koeficient bývá menší než $1{,}0$ (často $0{,}4$ až $0{,}9$) a snižuje naměřené dílky u znevýhodněných místností.
3. **Započitatelná podlahová plocha ($A$).** Podlahová plocha bytu ($A_{\text{byt}}$) a celková plocha všech vytápěných prostor v domě ($A_{\text{dum}}$) v $\text{m}^2$.
4. **Poměr základní a spotřební složky ($Z\% / S\%$).** Poměr rozdělení nákladů domu, obvykle 40 % / 60 %, 50 % / 50 % nebo 60 % / 40 %.

### Dynamické veličiny

Tyto hodnoty vznikají až provozem a vyhodnocují se po skončení zúčtovacího období.

1. **Odečtené dílky tělesa ($N_{\text{od}}$).** Počet kroků načtených indikátorem za sledované období.
2. **Celková fyzikální energie budovy ($Q_{\text{dum}}$).** Skutečná energie naměřená fakturačním měřičem tepla na patě domu, v GJ nebo MWh.
3. **Celkový součet přepočtených jednotek domu ($N_{\text{dum}}$).** Součet všech nákladových jednotek ze všech radiátorů v domě za celý rok.

## 4. Z dílků na jouly

Výpočet probíhá ve dvou fázích: lokální normalizace a globální energetická alokace.

```text
[ Surové dílky radiátoru: N_od ]
               |
               v  × K_v (výkon radiátoru) × K_p (poloha místnosti)
[ Nákladové jednotky radiátoru: N_prep (nj) ]
               |
               v  Součet přes všechny radiátory v bytě
[ Nákladové jednotky bytu: N_byt (nj) ]
               |
               v  × (Q_spotr_dum / N_celk_dum) = hodnota 1 nj v joulech
[ Spotřební energie bytu: Q_byt,spotr ]
               |
               v  + Základní složka bytu (dle podlahové plochy)
[ Celková energie odebraná bytem: Q_byt,celk ]
```

### Fáze 1: dílky na nákladové jednotky

$$
N_{\text{prep}} = N_{\text{od}} \times K_v \times K_p
$$

- Vstup: $N_{\text{od}}$, dílky.
- Parametry: $K_v$ a $K_p$.
- Výstup: $N_{\text{prep}}$, nákladová jednotka (nj).

Za celý byt:

$$
N_{\text{byt}} = \sum_{i=1}^{k} N_{\text{prep},i}
$$

### Fáze 2: nákladové jednotky na jouly

Tento krok nelze provést bez dat za celou budovu.

$$
Q_{\text{spotr}} = Q_{\text{dum}} \times \frac{S\%}{100\%}
$$

$$
e_{\text{nj}} = \frac{Q_{\text{spotr}}}{N_{\text{dum}}}
$$

$$
Q_{\text{radiator}} = N_{\text{prep}} \times e_{\text{nj}} = (N_{\text{od}} \times K_v \times K_p) \times e_{\text{nj}}
$$

$$
Q_{\text{byt,spotr}} = N_{\text{byt}} \times e_{\text{nj}}
$$

### Fáze 3: základní složka

$$
Q_{\text{zakl}} = Q_{\text{dum}} \times \frac{Z\%}{100\%}
$$

$$
Q_{\text{byt,zakl}} = Q_{\text{zakl}} \times \frac{A_{\text{byt}}}{A_{\text{dum}}}
$$

$$
Q_{\text{byt,celk}} = Q_{\text{byt,zakl}} + Q_{\text{byt,spotr}}
$$

## 5. Převod jednotek

- $1\ \text{J} = 1\ \text{W}\cdot\text{s}$
- $1\ \text{MJ} = 10^{6}\ \text{J}$
- $1\ \text{GJ} = 10^{9}\ \text{J} = 1000\ \text{MJ}$
- $1\ \text{kWh} = 3{,}6\ \text{MJ}$
- $1\ \text{MWh} = 1000\ \text{kWh} = 3{,}6\ \text{GJ}$
- $1\ \text{GJ} \approx 277{,}78\ \text{kWh} \approx 0{,}2778\ \text{MWh}$

## 6. Modelový příklad

Budova za rok:

- Celková dodaná energie ($Q_{\text{dum}}$): $500\ \text{GJ}$
- Celková plocha ($A_{\text{dum}}$): $2500\ \text{m}^2$
- Rozdělení: 40 % základní, 60 % spotřební
- Součet nákladových jednotek ($N_{\text{dum}}$): $25\,000\ \text{nj}$

Odvozeně:

- Spotřební energie: $500 \times 0{,}60 = 300\ \text{GJ}$
- Základní energie: $500 \times 0{,}40 = 200\ \text{GJ}$

$$
e_{\text{nj}} = \frac{300\ \text{GJ}}{25\,000\ \text{nj}} = 0{,}012\ \text{GJ/nj} = 12\ \text{MJ/nj} \approx 3{,}333\ \text{kWh/nj}
$$

Byt $60\ \text{m}^2$ se dvěma tělesy:

| Místnost | Náměr | $K_v$ | $K_p$ | Nákladové jednotky | Energie |
| --- | --- | --- | --- | --- | --- |
| Obývací pokoj | 400 dílků | 1,25 | 0,80 | $400 \times 1{,}25 \times 0{,}80 = 400\ \text{nj}$ | $4800\ \text{MJ}$ (1333,3 kWh) |
| Ložnice | 150 dílků | 1,00 | 0,60 | $150 \times 1{,}00 \times 0{,}60 = 90\ \text{nj}$ | $1080\ \text{MJ}$ (300,0 kWh) |
| Spotřební složka | 550 dílků |  |  | 490 nj | $5880\ \text{MJ}$ (5,88 GJ, 1633,3 kWh) |

Podíl plochy je $60 / 2500 = 2{,}4\ \%$.

- Základní energie bytu: $200\ \text{GJ} \times 0{,}024 = 4{,}80\ \text{GJ} = 4800\ \text{MJ}$ (1333,3 kWh)
- Celkem: $5{,}88 + 4{,}80 = 10{,}68\ \text{GJ} = 10\,680\ \text{MJ} \approx 2966{,}7\ \text{kWh} \approx 2{,}97\ \text{MWh}$

## Co z toho umí tato integrace

1. Surové číslo v exportu jsou **dílky**. Jde o bezrozměrný časový integrál teplotního rozdílu radiátoru a vzduchu.
2. Přepočet dílků na nákladové jednotky je statický a závisí na radiátoru a poloze místnosti. Ty koeficienty integrace nemá.
3. Přepočet nákladových jednotek na jouly nebo kilowatthodiny je podíl z účtu celého domu a každoročně se mění. Ani ten integrace nemá.

Home Assistant proto ukládá surový stav jako `scale units` a nedává ho na Energy dashboard. Topení má smysl vybrat jen tehdy, když chcete sledovat, jestli se počítadlo hýbe.
