[English](../challenges.md) | [Čeština](challenges.md)

# Obtížná místa

## Přihlášení je HTML formulář, ne API

Přihlašovací stránka posílá `multipart/form-data` a čeká tělo `True`. JSON klient by se nikdy nepřihlásil. Stejná odpověď musí nést dál antiforgery cookie. Honeypot pole `website` se snadno přehlédne a musí být prázdné.

## Export CSV vzniká v prohlížeči

Nabídka exportu je DataTables `csvHtml5` / `excelHtml5`. Adresa CSV neexistuje. Brát „CSV“ jako druhý parser pořád dává smysl: integrace serializuje tabulku tak, jak to dělá tlačítko, a použije skutečný soubor, když ho web přidá. `auto` tu cestu zkusí a spadne zpátky na HTML buňky.

## Historie vypadá stránkovaně, ale není

Snímek ukazuje stránky, protože DataTables stránkuje prohlížeč. Server pošle celou tabulku. Sledovat odkazy „další stránka“ by byl špatný klient.

## Řádky topení jsou dílky

Voda je označená `m3`. Buňky topení v `Jednotka` jsou prázdné a stránka neukazuje `kWh` ani `GJ`. Prázdná buňka je bezrozměrné počítadlo indikátoru na radiátoru. Integrace ukládá `scale units` a ten senzor nedává na Energy dashboard. Řádek vody s prázdnou jednotkou pořád založí opravu. Řádek topení, který opravdu obsahuje `GJ` nebo `kWh`, si tu jednotku energie nechá.

`m3` se normalizuje na `m³`, protože je to stejná jednotka bez horního indexu, ne odhad.

## Duplicitní řádky

Historie opakuje stejné číslo, čas a hodnotu. Složí se do jednoho odečtu. Pokles se nechá, protože výměna měřidla je platná a statistiky Home Assistantu `total_increasing` ji berou jako reset.

## Formulář období je měsíční a vázaný na účet

Formulář nástěnky potřebuje skrytou hodnotu `flat` ze stránky toho účtu. Integrace ji přečte, požádá o rozsah, který potřebuje, a zahodí dny před datem, které uživatel zvolil.

## Kontroly publikování

HACS hledá `custom_components/odecet_info/brand/icon.png`. Adresář `brand/` v kořeni repozitáře tu kontrolu nesplní.

Rozpoznání licence na GitHubu vrátí SPDX `NOASSERTION`, když má text MIT navíc část s upozorněním. HACS pak repozitář odmítne. Upozornění je v `NOTICE`. `LICENSE` zůstává text MIT.

HACS taky ignoruje obecná témata jako `home-assistant` a `hacs`. Repozitář potřebuje aspoň jedno konkrétní téma, třeba `water` nebo `energy`.

## HACS neumí vyzkoušet commit, který není na GitHubu

Kontrola před pushem dřív stahovala integraci přes HACS. To stažení je poslední commit už na GitHubu, takže změnu, která se teprve měla pushnout, nikdy nevidělo. Test před pushem teď kopíruje pracovní strom do konfigurace Home Assistantu. Stažení přes HACS běží po pushi a po vydání stáhne tag toho vydání.

## HACS chce přihlášení k GitHubu přes zařízení

HACS 2 nezaloží svůj záznam, dokud ho někdo neautorizuje na
`https://github.com/login/device`. Místní kontejner GitHub relaci nemá.
Bootstrap uloží záznam HACS s prázdným tokenem, takže stažení tohoto
veřejného repozitáře použije neověřené GitHub API. Na jednu instalaci to stačí.
Když GitHub odpoví 403, přihlaste se do HACS z rozhraní Home Assistantu.

Výchozí hostitel katalogu HACS (`data-v2.hacs.xyz`) z tohoto kontejneru nebyl
dostupný. Přidání repozitáře podle jména na GitHubu toho hostitele nepotřebuje.

## Zařízení měřidla musí ukazovat na existující zařízení účtu

Home Assistant odmítne `via_device`, když nadřazené zařízení ještě neexistuje,
a současná vydání chtějí `via_device_id` místo dvojice identifikátoru.
Zařízení účtu vznikne před senzory měřidel a vazba použije to pole, které
daná verze Home Assistantu deklaruje.

## Statistiky se nesmí importovat dvakrát

Import externí statistiky a zároveň záznam senzoru `total_increasing` by vodu nebo topení započítal dvakrát. Historie se importuje přes `async_import_statistics` na entitu senzoru (`source` `recorder`) a jen když je jednotka známá.
