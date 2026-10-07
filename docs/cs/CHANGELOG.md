# Seznam změn

[English](../../CHANGELOG.md) · [Čeština](CHANGELOG.md)

Významné změny tohoto projektu. Verze jsou sémantické. Text v angličtině je [CHANGELOG.md](../../CHANGELOG.md). Tento soubor se aktualizuje ve stejném commitu.

## [0.3.0] - 2026-10-07

Prázdná jednotka u topení je surové počítadlo indikátoru na radiátoru, ne chybějící energie.

### Změněno

- Topení s prázdnou jednotkou se ukládá jako `scale units` (dílky). Na Energy dashboard nepatří. Oprava „nemá jednotku“ se u něj už nezakládá.
- Výběr měřidel upozorňuje, že topení často nemá smysl vybírat, a odkazuje na vysvětlení.
- Uživatelské stránky mají český protějšek v `docs/cs/`.

### Proč

Web u těchto řádků nepíše GJ ani kWh. Brát prázdnou buňku jako chybu schovávalo bezrozměrný dílek a žádalo opravu něčeho, co na stránce není.

## [0.2.1] - 2026-10-07

Graf historie na senzoru ukazuje stavy od vzniku entity. Starší odečty jsou hodinové statistiky.

## [0.2.0] - 2026-10-07

Integrace sleduje publikovaná pravidla quality scale až po platinum, v mezích přihlášení na web.

## [0.1.4] - 2026-10-07

První označené vydání. Předtím žádný tag nebyl, proto neexistují verze 0.1.1 až 0.1.3.

[0.3.0]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.3.0
[0.2.1]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.2.1
[0.2.0]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.2.0
[0.1.4]: https://github.com/JustGetSchwifty/odecet-info-ha-integration/releases/tag/v0.1.4
