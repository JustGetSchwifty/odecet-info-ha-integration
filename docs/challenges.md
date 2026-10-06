# Challenges

## Sign-in is an HTML form, not an API

The sign-in page posts `multipart/form-data` and expects the body `True`. A JSON client would never log in. The same response also has to carry the antiforgery cookie forward. The honeypot field `website` is easy to miss and must be empty.

## CSV export is generated in the browser

The export menu is DataTables `csvHtml5` / `excelHtml5`. There is no CSV URL. Treating "CSV" as a second parser still matters: the integration serializes the table the way the button does, and it will use a real file if the site adds one. `auto` tries that path and falls back to the HTML cells.

## The history looks paged, but it is not

The screenshot shows pages because DataTables pages the browser. The server sends the whole table. Following "next page" links would be the wrong client.

## Heat rows have no unit

Water is labeled `m3`. Heat cells in `Jednotka` are empty, and the page does not show `kWh` or `GJ` next to the register. Inventing a unit would put the wrong quantity on the energy dashboard. The integration shows the raw register and raises a repair until the site provides a unit.

`m3` is normalized to `m³` because that is the same unit written without the superscript, not a guess.

## Duplicate rows

The history repeats identical serial, timestamp, and value rows. They collapse to one reading. A decrease is kept, because a meter replacement is valid, and Home Assistant `total_increasing` statistics treat it as a reset.

## The period form is monthly and account-specific

The dashboard form needs the hidden `flat` value from that account's page. The integration reads it and requests the range it needs, then drops days before the user's start date.

## Statistics must not be imported twice

Importing an external statistic and also letting the sensor record `total_increasing` would double-count water or heat. History is imported with `async_import_statistics` onto the sensor entity (`source` `recorder`) and only when the unit is known.
