#!/usr/bin/env python3
"""Genera factura desde CSV LIMPIOS, no desde cifras introducidas manualmente."""
import csv
from collections import defaultdict
from pathlib import Path
D=Path('data');R=Path('report')
def reader(f):
    with (D/f).open(newline='',encoding='utf-8') as fp:return list(csv.DictReader(fp))
clean=reader('retail_clean.csv');excluded=reader('retail_anulaciones.csv')
net=sum(float(r['Revenue']) for r in clean)
top=defaultdict(float)
for r in clean:top[r['Country']]+=float(r['Revenue'])
top_country=max(top,key=top.get)
cancel=sum(abs(float(r['Revenue'])) for r in excluded if r['ExclusionReason']=='Cancelación' and r['Revenue'] and float(r['Revenue'])<0)
pct=100*cancel/(cancel+net) if cancel+net else 0
text=f'''ONLINE RETAIL - FACTURA DE AUDITORÍA
==================================
Analista: Juan Pablo Vargas
Fuente: UCI Online Retail (Chen, 2015)
Ingreso neto por ventas válidas: £{net:,.2f}
País con mayor ingreso: {top_country} (£{top[top_country]:,.2f})
Monto absoluto de cancelaciones: £{cancel:,.2f}
Cancelaciones sobre ingreso bruto operativo: {pct:.2f}%
Definición: bruto operativo = ventas válidas + valor absoluto de facturas C negativas.
Las exclusiones no comerciales no se consideran cancelaciones.
'''
(R/'factura.txt').write_text(text,encoding='utf-8');print(text)
