#!/usr/bin/env python3
"""Auditoría del dataset Online Retail: limpieza excluyente y análisis exploratorio.
Todas las decisiones de negocio están documentadas en reporte.py y README.md.
"""
import csv, json, math, statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

D = Path('data'); R = Path('report')
FIELDS = ['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country']
EXTRA = ['Revenue','Month','Hour']
OUT = FIELDS + EXTRA
NON_PRODUCTS = {'POST','DOT','M','D','C2','BANK CHARGES','AMAZONFEE','S','B','CRUK','PADS'}
# Códigos especiales: POST envío, DOT comisión, M manual, D descuento,
# C2 porte, BANK CHARGES cargos bancarios, AMAZONFEE tarifa marketplace,
# S muestras, B ajuste, CRUK comisión, PADS ajustes.

def num(x):
    try: return float(str(x).strip().replace(',',''))
    except (ValueError, TypeError): return None

def parse_date(t):
    t = (t or '').strip()
    for fmt in ('%Y-%m-%d %H:%M:%S','%m/%d/%Y %H:%M','%Y-%m-%d %H:%M','%Y-%m-%d'):
        try: return datetime.strptime(t,fmt)
        except ValueError: pass
    try: return datetime.fromisoformat(t)
    except ValueError: return None

def clean_id(s):
    if not s or not s.strip(): return ''
    z=num(s)
    return str(int(z)) if z is not None and z.is_integer() else ''

def money(x): return f'{x:.2f}'

def quantile(data, q):
    if not data: return None
    a=sorted(data); p=(len(a)-1)*q; lo=int(p); hi=min(lo+1,len(a)-1)
    return a[lo]*(hi-p)+a[hi]*(p-lo)

with (D/'retail_raw.csv').open(newline='',encoding='utf-8-sig') as f:
    rr=csv.DictReader(f)
    if not set(FIELDS).issubset(rr.fieldnames or []):
        raise ValueError(f'Columnas inesperadas: {rr.fieldnames}')
    original=list(rr)
N=len(original)
missing={k:sum(not str(r.get(k,'') or '').strip() for r in original) for k in FIELDS}
qty=[z for r in original if (z:=num(r['Quantity'])) is not None]
prices=[z for r in original if (z:=num(r['UnitPrice'])) is not None]
bounds={}
for key,a in [('Quantity',qty),('UnitPrice',prices)]:
    q1,q3=quantile(a,.25),quantile(a,.75); spread=q3-q1
    bounds[key]={'q1':q1,'q3':q3,'lower':q1-1.5*spread,'upper':q3+1.5*spread}
outliers={k:sum(1 for z in a if z < bounds[k]['lower'] or z > bounds[k]['upper']) for k,a in [('Quantity',qty),('UnitPrice',prices)]}
raw_counts={
 'duplicados_exactos':N-len({tuple((r.get(k) or '') for k in FIELDS) for r in original}),
 'facturas_canceladas':sum(str(r['InvoiceNo']).strip().upper().startswith('C') for r in original),
 'cantidad_no_positiva':sum(num(r['Quantity']) is None or num(r['Quantity'])<=0 for r in original),
 'precio_no_positivo':sum(num(r['UnitPrice']) is None or num(r['UnitPrice'])<=0 for r in original),
 'codigos_no_producto':sum(str(r['StockCode']).strip().upper() in NON_PRODUCTS for r in original),
 'descripcion_vacia':missing['Description'],
 'cliente_no_identificado':missing['CustomerID'],
 'atipicos_quantity_IQR':outliers['Quantity'],
 'atipicos_unitprice_IQR':outliers['UnitPrice'],
}
seen=set(); counts=Counter(); stages=[]; valid=[]; excluded=[]
# Prioridad garantiza asignación de un solo motivo y contabilidad de filas inequívoca.
priority=['Duplicado exacto','Cancelación','Cantidad inválida o <= 0','Precio inválido o <= 0',
          'Código no comercial','Descripción faltante','Fecha inválida']
for r in original:
    rawkey=tuple((r.get(k) or '') for k in FIELDS)
    q=num(r['Quantity']); p=num(r['UnitPrice']); dt=parse_date(r['InvoiceDate'])
    code=str(r['StockCode']).strip().upper()
    desc=str(r['Description'] or '').strip()
    if rawkey in seen: reason='Duplicado exacto'
    elif str(r['InvoiceNo']).strip().upper().startswith('C'): reason='Cancelación'
    elif q is None or q<=0: reason='Cantidad inválida o <= 0'
    elif p is None or p<=0: reason='Precio inválido o <= 0'
    elif code in NON_PRODUCTS: reason='Código no comercial'
    elif not desc: reason='Descripción faltante'
    elif dt is None: reason='Fecha inválida'
    else: reason=''
    seen.add(rawkey)
    obj={k:str(r.get(k,'') or '').strip() for k in FIELDS}
    obj['CustomerID']=clean_id(obj['CustomerID'])
    # La descripción se normaliza para presentación; no se altera la definición del duplicado exacto.
    obj['Description']=' '.join(desc.split()).upper() if desc else ''
    obj['Quantity']=f'{q:g}' if q is not None else ''
    obj['UnitPrice']=f'{p:.4f}' if p is not None else ''
    obj['InvoiceDate']=dt.strftime('%Y-%m-%d %H:%M:%S') if dt else obj['InvoiceDate']
    obj['Revenue']=money(q*p) if q is not None and p is not None else ''
    obj['Month']=dt.strftime('%Y-%m') if dt else ''
    obj['Hour']=str(dt.hour) if dt else ''
    if reason:
        counts[reason]+=1; obj['ExclusionReason']=reason; excluded.append(obj)
    else: valid.append(obj)
for reason in priority:
    stages.append({'criterio':reason,'excluidas':counts[reason], 'restantes':N-sum(counts[k] for k in priority[:priority.index(reason)+1])})
assert len(valid)+len(excluded)==N

def write_csv(path,fieldnames,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,fieldnames=fieldnames,extrasaction='ignore');wr.writeheader();wr.writerows(rows)
write_csv(D/'retail_clean.csv',OUT,valid)
write_csv(D/'retail_anulaciones.csv',OUT+['ExclusionReason'],excluded)

# Ventas válidas sin CustomerID se incluyen en ingresos, pero no en datos de clientes.
rev=lambda r:float(r['Revenue']) if r['Revenue'] else 0
income=sum(map(rev,valid))
# Cancelación en valor absoluto exclusivamente de facturas C negativas; no equivale a pérdida neta.
cancel_abs=sum(abs(rev(r)) for r in excluded if r['ExclusionReason']=='Cancelación' and rev(r)<0)
gross_operational=income+cancel_abs
ratio_cancel=100*cancel_abs/gross_operational if gross_operational else 0

def agg(field):
    d=defaultdict(float)
    for r in valid:d[r[field]]+=rev(r)
    return sorted(d.items(),key=lambda z:-z[1])
country=agg('Country');month=agg('Month');hour=sorted(agg('Hour'),key=lambda z:int(z[0]))
prod_income=defaultdict(float);prod_qty=defaultdict(float);descs={}
for r in valid:
    c=r['StockCode']; prod_income[c]+=rev(r);prod_qty[c]+=float(r['Quantity']);descs[c]=r['Description']
top_rev=sorted(prod_income.items(),key=lambda z:-z[1])[:10]
top_qty=sorted(prod_qty.items(),key=lambda z:-z[1])[:10]
by_invoice=defaultdict(float);by_customer=defaultdict(float);cust_rows=defaultdict(list)
for r in valid:
    by_invoice[r['InvoiceNo']]+=rev(r)
    if r['CustomerID']:
        by_customer[r['CustomerID']]+=rev(r)
        cust_rows[r['CustomerID']].append(r)
clients=[]
for cid, rows in cust_rows.items():
    earliest=min(rows,key=lambda r:r['InvoiceDate'])
    # Si un cliente tiene más de un país, prevalece el país modal, con desempate alfabético.
    cts=Counter(r['Country'] for r in rows)
    country_client=sorted(cts.items(),key=lambda z:(-z[1],z[0]))[0][0]
    clients.append({'CustomerID':cid, 'Facturas':len({r['InvoiceNo'] for r in rows}),
                    'Productos':len({r['StockCode'] for r in rows}),
                    'EsUK':int(country_client=='United Kingdom'),
                    'MesPrimeraCompra':int(earliest['Month'].split('-')[1]),
                    'Ingreso':money(by_customer[cid])})
clients.sort(key=lambda r:int(r['CustomerID']))
write_csv(D/'clientes.csv',['CustomerID','Facturas','Productos','EsUK','MesPrimeraCompra','Ingreso'],clients)

def descriptive(a):
    if not a:return {}
    a=sorted(a);n=len(a);mean=statistics.fmean(a)
    m2=sum((x-mean)**2 for x in a)/n
    skew=sum((x-mean)**3 for x in a)/n/m2**1.5 if m2 else 0
    return {'n':n,'media':mean,'mediana':quantile(a,.5),'sd':math.sqrt(m2),
           'min':a[0],'q1':quantile(a,.25),'q3':quantile(a,.75),'max':a[-1],'asimetria':skew}
nums={k:[float(r[k]) for r in valid] for k in ['Quantity','UnitPrice','Revenue']}

import numpy as np
corr=np.corrcoef([nums[k] for k in ('Quantity','UnitPrice','Revenue')]).tolist()

# Gráficas hechas desde consola, reproducibles, sin interfaces interactivas.
plt.figure(figsize=(10,5))
plt.bar([k for k,v in sorted(month)], [v for k,v in sorted(month)])
plt.xticks(rotation=60,ha='right',fontsize=8)
plt.ylabel('Ingreso comercial (£)');plt.xlabel('Mes');plt.title('Online Retail: ingreso mensual de ventas válidas')
plt.tight_layout();plt.savefig(R/'ingresos_mes.png',dpi=160);plt.close()
plt.figure(figsize=(9,4.5))
plt.bar([str(k) for k,v in hour],[v for k,v in hour]);plt.ylabel('Ingreso comercial (£)');plt.xlabel('Hora (0-23)')
plt.title('Online Retail: ingresos por hora');plt.tight_layout();plt.savefig(R/'ingresos_hora.png',dpi=160);plt.close()
plt.figure(figsize=(9,5))
values=sorted(by_invoice.values())
plt.hist(values,bins=80);plt.yscale('log');plt.xlabel('Ingreso por factura (£)');plt.ylabel('Facturas (escala log)')
plt.title('Distribución de ingreso por factura');plt.tight_layout();plt.savefig(R/'facturas_distribucion.png',dpi=160);plt.close()

result={'n_original':N,'n_clean':len(valid),'n_excluded':len(excluded),'missing':missing,'raw_anomalies':raw_counts,
 'bounds':bounds,'stages':stages,'net_income':income,'cancelled_abs':cancel_abs,
 'gross_operational':gross_operational,'pct_cancelled':ratio_cancel,
 'invoices':len(by_invoice),'customers':len(cust_rows),'products':len(prod_income),
 'unidentified_sales':sum(1 for r in valid if not r['CustomerID']),
 'unidentified_revenue':sum(rev(r) for r in valid if not r['CustomerID']),
 'country_income':country,'month_income':month,'hour_income':hour,
 'top_revenue':[{'code':k,'description':descs[k],'revenue':v} for k,v in top_rev],
 'top_quantity':[{'code':k,'description':descs[k],'units':v} for k,v in top_qty],
 'products_intersection':len(set(k for k,v in top_rev)&set(k for k,v in top_qty)),
 'top10_customer_contribution':100*sum(sorted(by_customer.values(),reverse=True)[:10])/income if income else 0,
 'stats':{k:descriptive(v) for k,v in nums.items()},
 'invoice_stats':descriptive(list(by_invoice.values())), 'correlation':corr,
 'customer_count':len(clients),
 'customer_max_revenue':max(by_customer.values()) if by_customer else 0}
(R/'resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Filas originales',N,'| válidas',len(valid),'| anuladas',len(excluded))
