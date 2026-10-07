# Odecet.info pro Home Assistant

[English](../../README.md) · [Čeština](README.md)

<img src="https://raw.githubusercontent.com/JustGetSchwifty/odecet-info-ha-integration/main/custom_components/odecet_info/brand/logo@2x.png" alt="odecet.info" width="512">

odecet.info je český web, na kterém domácí účet vidí historii studené vody, teplé vody a topení. Tato neoficiální integrace se tím účtem přihlásí a přenese stav každého měřidla do Home Assistantu. S provozovatelem webu není spojená. Web se může změnit nebo přístup zastavit.

Topení není energie. Prázdná jednotka u řádků Teplo je bezrozměrný **dílek** indikátoru na radiátoru. Často nemá smysl ho vybírat. [Co vlastně ukazuje topení](heat-cost-allocation.md).

## Co umí

- Jedno zařízení na měřidlo a senzor **Stav**.
- Tlačítko **Synchronizovat** a senzor **Další ruční synchronizace**.
- Voda s jednotkou `m3` se ukládá jako m³ a může jít na Energy dashboard.
- Topení s prázdnou jednotkou se ukládá jako `scale units`. Na Energy dashboard nepatří.
- Starší odečty jsou hodinové statistiky. Graf na stránce senzoru kreslí jen stavy od vzniku entity a otevírá se zhruba na poslední den. Minulost je v Energy dashboardu a v grafu statistik s obdobím hodina nebo delším.

Čtení probíhá jednou denně kolem 04:00 místního času, s náhodným zpožděním do 30 minut. Ruční i automatická synchronizace mají společný limit jednou za minutu.

## Instalace

Integrace není ve výchozím katalogu HACS. Home Assistant musí být **2025.11.0** nebo novější.

1. Nainstalujte [HACS](https://www.hacs.xyz/docs/use/download/download/) a dokončete jeho nastavení včetně přihlášení ke GitHubu.
2. V HACS otevřete nabídku vpravo nahoře a zvolte **Custom repositories**.
3. Přidejte `https://github.com/JustGetSchwifty/odecet-info-ha-integration` jako **Integration** a stiskněte **Add**. Samotné přidání adresy nic nestáhne.
4. Vyhledejte **Odecet.info**, otevřete ho a stiskněte **Download**. Nechte nejnovější vydání.
5. Restartujte Home Assistant, když HACS ukáže **Pending restart**.
6. V **Nastavení → Zařízení a služby → Přidat integraci** vyhledejte **Odecet.info**.

První obrazovka chce e-mail, heslo a adresu přihlášení. Druhá obrazovka chce měřidla, způsob čtení historie a datum, od kterého se má synchronizovat. U topení je upozornění s odkazem na vysvětlení dílků. Stejná tři pole se později mění přes **Konfigurovat**.

## Odebrat

**Nastavení → Zařízení a služby → Odecet.info**, nabídka, **Smazat**. Stažený repozitář odeberte ještě v HACS a restartujte Home Assistant.

Vývoj, testy a smlouva webu zůstávají v angličtině v kořeni repozitáře.
