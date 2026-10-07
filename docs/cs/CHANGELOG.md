# Seznam změn

<p align="center">
  <a href="../../CHANGELOG.md"><img alt="English" src="https://img.shields.io/badge/English-6e7681?style=for-the-badge"></a>
  <a href="CHANGELOG.md"><img alt="Čeština" src="https://img.shields.io/badge/%C4%8Ce%C5%A1tina-1f6feb?style=for-the-badge"></a>
</p>

Významné změny tohoto projektu. Formát sleduje [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) a verze [sémantické verzování](https://semver.org/spec/v2.0.0.html). Čísla patch a minor nejsou omezená na jednu číslici.

Před tímto vydáním žádný tag nebyl, takže práce, která přistála na `main`, je zapsaná jednou, jako 0.1.4, ne jako vymyšlené meziverze.

## [0.3.1] - 2026-10-07

Jména měřidel a formulář nastavení se řídí jazykem Home Assistantu. Hlášené hodnoty se nemění.

### Změněno

- Zařízení měřidla se anglicky jmenuje `Heat [S/N 39584888]` a česky `Teplo [číslo 39584888]`. Studená a teplá voda mají stejný tvar.
- Rozbalovací seznamy měřidel a historie a věta o typech, které účet nemá, použijí české popisky, když je Home Assistant česky.
- Každý uživatelský dokument má český protějšek a první řádek každé stránky odkazuje na druhý jazyk.

### Proč

Jméno zařízení a několik popisků nastavení zůstávalo anglicky i v českém Home Assistantu. Je to změna popisku, proto zůstává na 0.3.

## [0.3.0] - 2026-10-07

Prázdná jednotka u topení je surové počítadlo indikátoru na radiátoru, ne chybějící energie.

### Změněno

- Topení s prázdnou jednotkou se ukládá jako `scale units` (dílky). Na Energy dashboard nepatří. Oprava „nemá jednotku“ se u něj už nezakládá.
- Výběr měřidel upozorňuje, že topení často nemá smysl vybírat, a odkazuje na vysvětlení.
- Uživatelské stránky mají český protějšek v `docs/cs/`.

### Proč

Web u těchto řádků nepíše GJ ani kWh. Brát prázdnou buňku jako chybu schovávalo bezrozměrný dílek a žádalo opravu něčeho, co na stránce není.

## [0.2.1] - 2026-10-07

Graf historie na senzoru ukazuje stavy od přidání měřidla. Starší odečty už byly naimportované jako statistiky a to šlo snadno přehlédnout.

### Přidáno

- Diagnostika teď obsahuje nejstarší odečet, nejnovější odečet a kolik hodinových bodů statistik se naimportovalo.
- `dev/inspect_account.py` se přihlásí přes `.env` a umí zapsat odečty jako JSON nebo CSV.
- Tag `v*` publikuje svou část seznamu změn jako nejnovější vydání na GitHubu.
- Zelené pull requesty Dependabotu se sloučí squash commitem. Pull requesty od kohokoli jiného zůstanou být.

### Proč

Jednodenní graf historie vypadal, jako by stažení nemělo minulost. Rozsah je teď vidět a vydání ani aktualizace závislostí už nečekají na ruční kliknutí.

## [0.2.0] - 2026-10-07

Integrace teď sleduje publikovaná pravidla quality scale Home Assistantu až po platinum, v mezích přihlášení na web.

### Přidáno

- Vlastní relace přihlášení, takže cookies účtu nevisí na jiných integracích.
- Přeložená jména entit, ikona synchronizace a přeložené chyby.
- Odebrání zařízení měřidla, když to měřidlo z účtu zmizí.
- Kroky instalace v README, které sedí na současný tok HACS, banner značky a odkaz My Home Assistant.
- Noční kontrola hassfest a HACS, striktní typová kontrola a práh pokrytí 95 procent.
- Dependabot pro Python a GitHub Actions. Plovoucí odkazy akcí hassfest a HACS zůstávají nepřipnuté.

### Proč

Uživatelé dostanou spolehlivější instalaci a kód, který jde zkontrolovat proti quality scale. Home Assistant vlastní integrace neznámkuje, takže značka platinum je vlastní posouzení tohoto projektu. Přihlášení pořád čte web, takže integrace zůstává vlastní komponenta.

## [0.1.4] - 2026-10-07

První zapsané vydání neoficiální integrace odecet.info.

### Přidáno

- Config flow Home Assistantu pro účet odecet.info, s výběrem typů měřidel, které účet skutečně má.
- Parsery tabulky historie a CSV exportu, který web staví v prohlížeči.
- Jeden senzor stavu na měřidlo, tlačítko ruční synchronizace a minutová pauza zobrazená jako čas další povolené synchronizace.
- Denní synchronizace na pozadí s rozptylem a omezeným opakováním. Měřidla topení, která přišla bez jednotky, zůstala mimo statistiky a založila opravu.
- Místní kontrola Home Assistantu, která před pushem zkopíruje pracovní strom, protože HACS umí stáhnout jen commit, který už je na GitHubu.
- CI pro pytest, hassfest a HACS, plus odznaky README pro ten stav a pro publikované vydání.

### Proč

Uživatelé potřebují verzi, kterou jde nainstalovat přes HACS. Jeden zápis 0.1.4 se vyhýbá předstírání, že 0.1.1 až 0.1.3 vyšly.

[0.3.1]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.3.1
[0.3.0]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.3.0
[0.2.1]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.2.1
[0.2.0]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.2.0
[0.1.4]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.1.4
