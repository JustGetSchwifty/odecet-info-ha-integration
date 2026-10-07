# Testování

[![English](https://img.shields.io/badge/English-6e7681?style=for-the-badge)](../testing.md) [![Čeština](https://img.shields.io/badge/Čeština-1f6feb?style=for-the-badge)](testing.md)

Tier 1 je rychlý a odecet.info nekontaktuje. Před pushem tier 2 nahraje pracovní strom do místního Home Assistantu. Po pushi nebo vydání na GitHubu samostatný příkaz ověří, že HACS ten publikovaný odkaz stáhne.

## Tier 1

Spusťte to po větší změně, než tu změnu označíte za hotovou.

```bash
uv run ruff check custom_components tests
uv run mypy
uv run pytest
```

`mypy` je pro `custom_components/odecet_info` striktní. `pytest` selže, když pokrytí toho balíčku klesne pod 95 procent. CI pouští obojí, a taky každou noc a na vyžádání, aby se nové pravidlo hassfestu nebo HACS chytilo i bez pushe.

`tests/test_publish.py` kontroluje strom na chyby hassfestu a HACS, které GitHub nepotřebují: pořadí klíčů manifestu, závislost na recorderu, ikonu značky integrace a soubor LICENSE, který GitHub pozná jako MIT. Stejný obraz hassfestu jako v CI jde spustit místně:

```bash
docker run --rm -v "$PWD://github/workspace" ghcr.io/home-assistant/hassfest
```

V Actions `dev/check_github_metadata.py` kontroluje rozpoznanou licenci SPDX a to, že repozitář má téma, které HACS počítá. Obecná témata jako `home-assistant` a `hacs` se nepočítají. Tento repozitář používá `water`, `energy` a `metering`.

Sada pokrývá:

- Platné přihlášení (`True`) a honeypot, antiforgery token, špatné heslo, timeout, HTTP 429 a HTTP 503
- HTML a CSV se stejnými měřidly, včetně desetinné čárky, duplicitních řádků, chybějících sloupců, přihlašovací stránky vrácené jako CSV, neznámých typů, chybějících jednotek a klesajícího stavu
- Config flow, včetně účtu, který už je nastavený, a účtu bez měřidel
- Senzory, minutovou pauzu, řádky statistik a opravu, když jednotka chybí

Fixture v `tests/fixtures/` jsou syntetické. Živé zachycení zůstává v gitignorovaném `dev/capture/`.

`dev/inspect_account.py` je živý protějšek. Použije `.env`, vypíše rozsah každého měřidla a umí zapsat JSON nebo CSV. Jeho testy používají naskriptovanou relaci a web nevolají.

## Tier 2 před pushem

HACS stahuje GitHub. Commit, který je jen na tomto stroji, v tom stažení není, takže kontrola před pushem zkopíruje `custom_components/odecet_info` do konfigurace kontejneru a restartuje Home Assistant. Ta kopie je místní instalace, ne instalace přes HACS.

```bash
docker compose -f dev/docker-compose.yml up -d --build
uv run python dev/bootstrap_ha.py --local
```

## HACS po pushi nebo vydání

Spusťte to až potom, co commit nebo vydání už je na GitHubu. Ověří, že HACS stáhne to, co dostanou uživatelé. Po prvním vydání na GitHubu HACS instaluje nejnovější vydání místo `main` a tag bez vydání se nepočítá.

```bash
uv run python dev/bootstrap_ha.py --hacs --version vX.Y.Z
```

HACS se normálně zastaví a chce přihlášení k GitHubu přes zařízení. Bootstrap GitHub relaci nemá, takže uloží záznam HACS bez tokenu a tento veřejný repozitář stejně stáhne. GitHub můžete připojit později z panelu HACS, když neověřené API narazí na limit.

Kontejner drží konfiguraci v gitignorovaném `dev/ha-config/`. Ten adresář po bootstrapu obsahuje heslo odecet.info, takže se nesmí commitovat.

Místní Home Assistant:

| | |
| --- | --- |
| URL | http://127.0.0.1:8123 |
| Uživatel | `dev` |
| Heslo | `dev` |

Ty údaje existují jen pro tento kontejner. Nejsou to účet odecet.info.

Bootstrap je hotový, když senzory měřidel existují a jejich stavy jsou čísla. Kontejner zůstane běžet.
