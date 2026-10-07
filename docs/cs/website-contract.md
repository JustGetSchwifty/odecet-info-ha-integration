[English](../website-contract.md) | [Čeština](website-contract.md)

# Smlouva webu odecet.info

Pozorováno 6. října 2026 na živém webu. Zachycení, kterým se to potvrdilo, je v gitignorovaném `dev/capture/`. Fixture v `tests/fixtures/` kopírují tvar s vymyšlenými hodnotami.

## Přihlášení

`GET https://odecet.info/signin` vrátí HTML formulář.

| Položka | Hodnota |
| --- | --- |
| Id formuláře | `kt_sign_in_form` |
| Akce formuláře | `signin` (stejná adresa) |
| Kontrola úspěchu | Tělo POST je přesně `True` |
| Antiforgery pole | `__RequestVerificationToken`, zkopírované z formuláře |
| Pole účtu | `email` |
| Tajné pole | `password` |
| Honeypot | `website`, musí se poslat prázdné |
| Cookies | Nechat jen pro toto přihlášení, včetně `ARRAffinity` |

`ARRAffinity` přilepí prohlížeč k jednomu serveru. Není to přihlášení na měsíce. Formulář nemá pole zapamatovat si mě, takže export Netscape `cookies.txt` vyprší s relací prohlížeče. Cookie přihlášení nepřidávejte, dokud pozdější zachycení neukáže autentizační cookie s dlouhým `Expires` nebo `Max-Age`.

Jakékoli jiné tělo 200 jsou neplatné údaje. HTTP 429 je omezení tempa. Timeouty a HTTP 5xx jsou chyby přenosu. Chybějící token znamená, že se změnila struktura stránky.

Prohlížeč posílá `multipart/form-data` přes axios. Klient dělá totéž.

## Nástěnka

Po přihlášení je `GET /` nástěnka. Je to HTML vykreslené na serveru, ne JSON API.

Formulář `GET` na `/` vybírá období:

| Pole | Význam |
| --- | --- |
| `flat` | Skrytý klíč účtu. Přečtěte ho ze stránky. Do kódu ho natvrdo nezadávejte. |
| `fromMonth`, `fromYear` | Začátek období. Měsíce jsou `1`–`12`. |
| `toMonth`, `toYear` | Konec období. |

Výchozí období je asi dvanáct měsíců. Integrace formulář znovu požádá od měsíce začátku synchronizace, nebo od nejstaršího roku ve formuláři, když začátek není, až po aktuální měsíc. Odečty se pak oříznou na přesné počáteční datum, protože formulář je měsíční.

## Tabulka historie

Historie stavů je tabulka `kt_ecommerce_report_customer_orders_table`. DataTables ji stránkuje v prohlížeči. Řádky už v HTML jsou, takže klient stránky neprochází.

Když to id zmizí, parser použije tabulku, jejíž hlavička obsahuje sloupce typu a stavu.

| Sloupec | Vnitřní pole | Poznámka |
| --- | --- | --- |
| Typ měřiče | medium | Často zabalené v odznaku `div`. Čtěte text. |
| Výrobní číslo | serial | Totožnost fyzického měřidla. |
| Výrobní číslo modulu | module serial | Atribut. Měřidlo nerozděluje. |
| Datum | timestamp | `DD.MM.YYYY`, `Europe/Prague`, uloženo ve 12:00 místního času. |
| Stav | value | Registr. Tečka nebo čárka. `Decimal`. |
| Jednotka | unit | Viz níže. |

Známé popisky typů:

| Popisek | Médium |
| --- | --- |
| Studená voda | `cold_water` |
| Teplá voda | `hot_water` |
| Teplo | `heat` |

Porovnání nerozlišuje velikost písmen a bere i stejná slova bez diakritiky, plus `cold water`, `hot water` a `heat`.

## Jednotky

| Text na webu | Uložená jednotka | Třída zařízení Home Assistantu |
| --- | --- | --- |
| `m3`, `m³`, `m^3` | `m³` | `water` pro studenou a teplou vodu |
| `L`, `l` | `L` | `water` |
| `kWh`, `GJ`, `MJ`, `Wh`, `MWh` | kanonická jednotka energie | `energy` pro topení |

Na pozorovaném účtu mají řádky vody `m3` a každý řádek topení má prázdnou buňku `Jednotka`. Ta prázdná buňka topení se ukládá jako `scale units`. Nepřevádí se na `kWh` ani `GJ`. Řádek vody s prázdnou jednotkou zůstane chybějící a založí opravu. Řádek topení, který skutečně obsahuje jednotku energie, si tu jednotku nechá.

## Export CSV

Tlačítko **Exportovat do CSV** je tlačítko DataTables `csvHtml5` v `meter-tables.js`. Soubor ze serveru nežádá. Serializuje tabulku historie.

Způsoby čtení:

| Způsob | Chování |
| --- | --- |
| `table` | Parsuje HTML buňky. |
| `csv` | Když existuje skutečný odkaz na CSV, stáhne ho. Jinak serializuje tabulku historie do CSV a parsuje ten text. |
| `auto` | Nejdřív cesta CSV, potom HTML tabulka. |

Odpověď, která je přihlašovací stránka, je neúspěšné čtení, ne prázdná historie.

## Řádky, které parser zahodí nebo nechá

| Situace | Výsledek |
| --- | --- |
| Přesný duplikát čísla, modulu, času a hodnoty | Jeden řádek plus varování |
| Stejné číslo a čas, jiná hodnota | Nechá pozdější řádek plus varování |
| Nečitelné datum nebo hodnota | Řádek přeskočí |
| Datum víc než dva dny v budoucnosti | Řádek přeskočí |
| Neznámý typ měřidla | Řádek přeskočí |
| Chybějící jednotka | Řádek nechá |
| Stav nižší než předchozí odečet | Řádek nechá a varuje |

Měsíční souhrnná tabulka (`kt_seznam_meraku_table`) a JSON grafu jsou součty spotřeby pro nástěnku. Nejsou to historie stavů a integrace je neparsuje.
