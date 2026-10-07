# Architektura

<p align="center">
  <a href="../architecture.md"><img alt="English" src="https://img.shields.io/badge/English-6e7681?style=for-the-badge"></a>
  <a href="architecture.md"><img alt="Čeština" src="https://img.shields.io/badge/%C4%8Ce%C5%A1tina-1f6feb?style=for-the-badge"></a>
</p>

Integrace je jeden záznam Home Assistantu na jeden účet odecet.info. Kód, který mluví s webem, Home Assistant neimportuje, takže testy parseru běží bez něj.

```text
config flow  -> dedicated session -> OdecetClient.async_fetch
coordinator  -> dedicated session -> OdecetClient.async_fetch -> ReadingSet
sensors      -> latest register, and hourly statistics when the unit is known
button       -> coordinator refresh, blocked for 60 seconds after the last attempt
```

## Moduly

| Modul | Role |
| --- | --- |
| `client.py` | Přihlášení, formulář období, stažení CSV nebo HTML |
| `parse.py` | Tabulka a CSV na odečty. Špatné řádky jsou problémy |
| `html_extract.py` | Formuláře a tabulky ze serverového HTML |
| `statistics.py` | Hodinový `state` a spotřeba `sum` |
| `config_flow.py` | Účet a pak typy měřidel, které se skutečně našly |
| `coordinator.py` | Denní plán, zpomalení po chybě, opravy |
| `sensor.py` | Jeden stav na měřidlo a čas další ruční synchronizace |
| `button.py` | Synchronizovat |

## Relace

Klient přijme relaci `aiohttp` a sám si ji nezakládá. Koordinátor ji vytvoří přes `async_create_clientsession` při nastavování záznamu, takže ji Home Assistant při odebrání zavře. Zkoušky při nastavení a v možnostech vytvoří relaci s `auto_cleanup=False` a zavřou ji před návratem kroku. Cookies přihlášení nikdy nejdou na sdílenou relaci Home Assistantu.

## Quality scale

`quality_scale.yaml` má každé publikované pravidlo jako `done` nebo `exempt`. Manifest říká `platinum`, protože ten soubor je úplný. Home Assistant vlastní integrace nehodnotí, takže značka je posouzení tohoto repozitáře proti publikovaným pravidlům.

## Plánování

Krátký interval dotazování není. Úspěšná synchronizace naplánuje 04:00 místního času plus až 30 minut rozptylu. Selhání naplánuje exponenciální zpomalení, které není kratší než 60 sekund. Po pěti selháních se otevře oprava a další pokus je následující denní slot. Selhání přihlášení místo toho spustí tok opětovného přihlášení.

Ruční tlačítko a plán sdílejí `last_attempt`. Dokud je ta značka mladší než minuta, tlačítko je nedostupné a `sensor.<účet>_next_manual_sync` je v budoucnosti. Home Assistant ten čas ukáže jako odpočet.

## Entity

Zařízení účtu vznikne dřív než zařízení měřidla. Každé měřidlo je vlastní zařízení, navázané přes `via_device`, protože měřidlo ukazující na chybějící zařízení se odmítne. Jméno zařízení měřidla se překládá: anglicky `Heat [S/N {serial}]`, česky `Teplo [číslo {serial}]`. Zařízení účtu si nechá e-mail.

Voda s `m³` nebo `L` má `device_class: water` a `state_class: total_increasing`. Topení s prázdnou jednotkou je `scale units` a `total_increasing`, bez energetické třídy, takže zůstane mimo Energy dashboard. Jeho hodinová historie se přesto importuje. Topení, které přijde s `kWh` nebo `GJ`, má `device_class: energy`. Vodní měřidlo bez jednotky zůstane holé číslo a založí opravu.

Statistiky používají `async_import_statistics` se `source: recorder` a identifikátorem entity senzoru. To je stejná řada, kterou čte Energy dashboard. Druhá externí statistika se nezakládá.

## Možnosti

Přihlašovací údaje a adresa přihlášení jsou data záznamu. Zapnutá média, způsob čtení a datum začátku jsou možnosti. Změna možností záznam znovu načte. Média, která v posledním přihlášení nebyla, se z výběru vynechají a jmenují se v popisu formuláře. Home Assistant neumí v jednom výběru jednu položku zešedivit.
