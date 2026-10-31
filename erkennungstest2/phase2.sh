#!/bin/bash
# Erkennungstest 2, Teil 2: neue Orte ohne Sturm, Schlafzimmer, Sonderfälle
cd /tmp/claude-0/erkt2/tools
while pgrep -f "driver.py camping,wald,stellplatz" > /dev/null; do sleep 15; done
LEERWIND=12 NOBLIND=1 python3 driver.py festival:tag+nacht,garten:tag+nachtregen,baustelle:nacht,wild:tag+nacht,camping:dunkel,schlafzimmer
python3 extra.py diag,blend,kopf,linse
