# Odecet.info pro Home Assistant

[![English](https://img.shields.io/badge/English-6e7681?style=for-the-badge)](../../README.md) [![Čeština](https://img.shields.io/badge/Čeština-1f6feb?style=for-the-badge)](README.md)

<img src="https://raw.githubusercontent.com/JustGetSchwifty/odecet-info-ha-integration/main/custom_components/odecet_info/brand/logo@2x.png" alt="odecet.info" width="512">

[![CI](https://github.com/JustGetSchwifty/odecet-info-ha-integration/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/JustGetSchwifty/odecet-info-ha-integration/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/JustGetSchwifty/odecet-info-ha-integration?display_name=tag)](https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases)
[![Stars](https://img.shields.io/github/stars/JustGetSchwifty/odecet-info-ha-integration)](https://github.com/JustGetSchwifty/odecet-info-ha-integration/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](../../LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.11%2B-blue)](https://www.home-assistant.io/)

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=JustGetSchwifty&repository=odecet-info-ha-integration&category=integration"><img alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." src="https://my.home-assistant.io/badges/hacs_repository.svg"></a>
</p>

odecet.info je český web, na kterém domácí účet vidí historii studené vody, teplé vody a topení. Tato neoficiální integrace se tím účtem přihlásí a přenese stav každého měřidla do Home Assistantu. S provozovatelem webu není spojená. Web se může změnit nebo přístup zastavit. Viz [LICENSE](../../LICENSE) a [NOTICE](../../NOTICE).

Uživatelská dokumentace i obrazovky Home Assistantu se udržují anglicky a česky zároveň. Změna v jednom jazyce není hotová, dokud není stejná změna i ve druhém.

Integrace se řídí publikovanými pravidly [Home Assistant quality scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/) až po platinum. Výjimky jsou v `custom_components/odecet_info/quality_scale.yaml`. Home Assistant vlastní integrace nehodnotí, takže ta značka je naše posouzení proti těm pravidlům, ne známka od týmu jádra.

## Podporovaná měřidla

Měřidlo je podporované, když ho přihlášený účet vrátí. Samostatný seznam hardwaru není.

- Studená voda. Jednotka `m3` se ukládá jako metry krychlové.
- Teplá voda. Stejně.
- Topení. Web nechává jednotku prázdnou, protože číslo je bezrozměrný **dílek** indikátoru na radiátoru, ne kilowatthodiny. Často nemá smysl ho vybírat. [Co vlastně ukazuje topení](heat-cost-allocation.md).

Měřidlo, které z účtu později zmizí, se z Home Assistantu odebere.

## Co dostanete

- Jedno zařízení na měřidlo, navázané na zařízení účtu. V češtině se jmenuje `Teplo [číslo 39584888]`. Anglický Home Assistant ukáže `Heat [S/N 39584888]`. Studená a teplá voda mají stejný tvar.
- Senzor **Stav** s posledním odečtem. V angličtině je to **Reading**.
- Tlačítko **Synchronizovat** na zařízení účtu.
- Senzor **Další ruční synchronizace**, který ukáže, kdy je tlačítko znovu povolené.
- Importovanou historii u senzorů se známou jednotkou, takže voda může jít na Energy dashboard.

## Jak se odečty aktualizují

Integrace čte web jednou denně, kolem 04:00 místního času, plus náhodné zpoždění do 30 minut. Každou minutu se neptá. Neúspěšné čtení se opakuje se zpomalením a nikdy častěji než jednou za minutu. Po pěti selháních otevře opravu a počká do dalšího dne. **Synchronizovat** má stejný minutový limit.

Číslo na senzoru je poslední stav. Graf historie na stránce entity kreslí stavy, které Home Assistant viděl od vzniku entity, a otevírá se zhruba na poslední den. Starší odečty jsou hodinové dlouhodobé statistiky. Energy dashboard a graf statistik s obdobím hodina nebo delším čtou tu řadu. Diagnostika u každého měřidla uvádí `oldest_at`, `latest_at` a `statistic_points`, tedy rozsah, který se naimportoval. Dílky topení v tom rozsahu jsou. Energie to pořád není.

## Instalace

Integrace není ve výchozím katalogu HACS. Home Assistant musí být **2025.11.0** nebo novější. Na starší verzi HACS vydání odmítne.

1. Nainstalujte [HACS](https://www.hacs.xyz/docs/use/download/download/) a dokončete jeho nastavení včetně přihlášení ke GitHubu, aby se HACS objevil v postranní liště.
2. Otevřete HACS. V nabídce vpravo nahoře zvolte **Custom repositories**.
3. Přidejte `https://github.com/JustGetSchwifty/odecet-info-ha-integration`, typ nastavte na **Integration** a stiskněte **Add**. Samotné přidání adresy nic nestáhne.
4. Vyhledejte **Odecet.info**, otevřete ho a stiskněte **Download**. Nechte vybrané nejnovější vydání.
5. Restartujte Home Assistant, když HACS ukáže **Pending restart**. Aktualizace ten restart potřebuje. První stažení se často načte i bez něj.
6. Jděte do **Nastavení → Zařízení a služby → Přidat integraci**, vyhledejte **Odecet.info** a zadejte účet.

Tento repozitář v HACS otevře i odznak nahoře.

## Nastavení

První obrazovka se ptá na:

| Pole | Účel |
| --- | --- |
| E-mail | Adresa z přihlašovací stránky odecet.info. |
| Heslo | Uloží se do záznamu Home Assistantu. Do logu se nezapisuje. |
| Adresa přihlášení | Stránka s přihlašovacím formulářem. Výchozí je `https://odecet.info/signin`. |

Druhá obrazovka se ptá na:

| Pole | Účel |
| --- | --- |
| Měřidla | Studená voda, teplá voda a topení. Vybrat lze jen typy, které účet má. Typy, které necháte vypnuté, se ignorují. |
| Jak číst historii | **Automaticky (CSV, potom tabulka)** zkusí nejdřív CSV export a pak tabulku historie. **Export CSV** nebo **Tabulka historie** vynutí jednu cestu. |
| Synchronizovat od | Odečty před tímto datem se ignorují. Prázdné pole znamená historii, kterou web vrátí. |

Stejná tři pole jdou změnit později: **Nastavení → Zařízení a služby → Odecet.info → Konfigurovat**.

Po nastavení ukazuje zařízení účtu **Synchronizovat** a **Další ruční synchronizace**. Každé měřidlo je vlastní zařízení, pojmenované médiem a číslem v závorce, a senzor **Stav**.

Voda označená `m3` se ukládá jako metry krychlové a může jít na Energy dashboard jako voda. Topení s prázdnou jednotkou se ukládá jako `scale units`. Je to průběžné počítadlo, není to energie a na Energy dashboard se nepřidává. Řádek vody bez jednotky pořád založí opravu. Integrace si `kWh` ani `GJ` nevymýšlí.

## Použití

Sledujte stavy vody bytu v Home Assistantu a na Energy dashboardu. Oprava se otevře, když denní čtení pořád selhává, nebo když voda přijde bez jednotky.

Upozorněte, když je měřidlo hodinu nedostupné. Identifikátor entity nahraďte senzorem ze svého účtu.

```yaml
alias: Odecet.info meter unavailable
triggers:
  - trigger: state
    entity_id: sensor.cold_water_s_n_SERIAL_reading
    to: unavailable
    for:
      hours: 1
actions:
  - action: notify.persistent_notification
    data:
      title: odecet.info
      message: A meter has been unavailable for an hour.
```

## Omezení

- Integrace je neoficiální.
- Změna přihlášení nebo stránky historie na webu může synchronizaci rozbít, dokud se integrace neaktualizuje.
- Topení s prázdnou jednotkou se ukládá jako `scale units`. Není to energie a na Energy dashboard se nepřidává. Integrace si `kWh` ani `GJ` nevymýšlí. Řádek vody bez jednotky pořád založí opravu.
- Automatická i ruční synchronizace mají společný limit jednoho požadavku za minutu.
- Odečty před **Synchronizovat od** se ignorují. Web taky omezuje, kolik historie vrátí.
- K měřidlu není místní spojení. Účet se musí umět přihlásit na web.

## Odebrání

**Nastavení → Zařízení a služby → Odecet.info**, otevřete nabídku a zvolte **Smazat**. Chcete-li smazat i stažení, odeberte repozitář v HACS a restartujte Home Assistant.

## Ladění

- **Nastavení → Systém → Protokoly**, filtr `odecet_info`. Neúspěšné čtení se zapíše jednou na začátku a jednou při obnovení. Heslo se nezapisuje.
- Oprava se založí, když měřidlo nemá rozpoznatelnou jednotku, nebo když denní synchronizace pořád selhává.
- **Nastavení → Zařízení a služby → Odecet.info → Stáhnout diagnostiku** vypíše měřidla, varování a výsledek poslední synchronizace. Heslo ani cookies relace tam nejsou.
- Když se rozložení webu změní, stabilnější je cesta CSV. V **Konfigurovat** přepněte **Jak číst historii** a synchronizujte znovu.

## Vývoj

Místní kontroly jsou v [testing.md](testing.md). Pro objevování a pro místní kontejner Home Assistantu zkopírujte [.env.example](../../.env.example) na `.env`. `.env` necommitujte.

```bash
uv run pytest
docker compose -f dev/docker-compose.yml up -d --build
uv run python dev/bootstrap_ha.py --local
```

`dev/inspect_account.py` se přihlásí přes `.env` a stáhne odečty bez spuštění Home Assistantu. Vypíše rozsah každého měřidla. Heslo nevypisuje.

```bash
uv run python dev/inspect_account.py login
uv run python dev/inspect_account.py fetch --method auto
uv run python dev/inspect_account.py fetch --method csv --sync-from 2024-01-01 --json /tmp/odecet.json --csv /tmp/odecet.csv
```

`--method` je `auto`, `csv` nebo `table`. Soubory JSON a CSV jsou pro vás. Necommitujte je.

## Licence

[MIT](../../LICENSE). Upozornění, že jde o neoficiální projekt, je v [NOTICE](../../NOTICE). Samotný soubor licence zůstává čisté MIT, aby ho GitHub a HACS poznaly.
