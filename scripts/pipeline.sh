#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data scripts report
if ! command -v python3 >/dev/null; then echo 'Necesitas python3 (sudo apt install python3 python3-venv)' >&2; exit 1; fi
if ! command -v curl >/dev/null; then echo 'Necesitas curl (sudo apt install curl)' >&2; exit 1; fi
if ! command -v unzip >/dev/null; then echo 'Necesitas unzip (sudo apt install unzip)' >&2; exit 1; fi
if [ ! -d .venv ]; then python3 -m venv .venv; fi
. .venv/bin/activate
python -m pip install -q -r requirements.txt
if [ ! -s data/online_retail.zip ]; then
 echo '[1/8] Descargando archivo desde UCI...'
 curl --fail --location --retry 3 -o data/online_retail.zip 'https://archive.ics.uci.edu/static/public/352/online+retail.zip'
fi
if [ ! -s 'data/Online Retail.xlsx' ]; then
 echo '[2/8] Extrayendo planilla...'
 unzip -oq data/online_retail.zip -d data/
fi
if [ ! -s data/retail_raw.csv ]; then
 echo '[3/8] Convirtiendo Excel a CSV con in2csv...'
 in2csv 'data/Online Retail.xlsx' > data/retail_raw.csv
fi
echo '[4/8] Verificación original con wc -l y csvstat...'
wc -l data/retail_raw.csv | tee report/conteo_csv.txt
csvstat data/retail_raw.csv > report/csvstat_original.txt
python scripts/analisis.py
echo '[5/8] División reproducible de clientes con seed 42...'
head -n 1 data/clientes.csv > data/header.csv
tail -n +2 data/clientes.csv | LC_ALL=C sort -t, -k1,1n | shuf --random-source=<(yes 42) > data/clientes_shuf.csv
NTR=$(( $(wc -l < data/clientes_shuf.csv) * 7 / 10 ))
(cat data/header.csv; head -n "$NTR" data/clientes_shuf.csv) > data/train.csv
(cat data/header.csv; tail -n +$((NTR+1)) data/clientes_shuf.csv) > data/test.csv
echo '[6/8] Entrenando modelos...'
python scripts/modelos.py
echo '[7/8] Generando factura...'
python scripts/factura.py
echo '[8/8] Elaborando reporte Markdown y PDF...'
python scripts/reporte.py
printf '\nLISTO: report/reporte.md, report/reporte.pdf, report/factura.txt\n'
