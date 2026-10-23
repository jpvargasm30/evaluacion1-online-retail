#!/usr/bin/env python3
"""Construye reporte.md y su exportación PDF con los datos reales del pipeline."""
import json,html,re
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
R=Path('report');a=json.loads((R/'resultados.json').read_text()); m=json.loads((R/'modelos.json').read_text())
fmt=lambda x:f'{x:,.2f}'
md=[]
def add(t=''):md.append(t)
def table(head,rows):
    add('| '+' | '.join(map(str,head))+' |');add('|'+'|'.join(['---']*len(head))+'|')
    for row in rows:add('| '+' | '.join(str(x).replace('|','/') for x in row)+' |')
    add()
add('# Universidad del Bío-Bío')
add('## Facultad de Ciencias — Departamento de Estadística')
add('# Evaluación N°1: ¿Cuánto vende realmente una tienda en línea?')
add('**Auditoría de ventas reales desde la línea de comandos**  ')
add('**Asignatura:** Ciencia de Datos en la Terminal Linux  ')
add('**Profesor:** Luis Gómez  ')
add('**Analista:** Juan Pablo Vargas  ')
add('**Fecha:** 22 de octubre de 2026')
add('\n---\n')
add('## Índice')
add('1. Resumen ejecutivo  \n2. Fuente y metodología  \n3. Auditoría y limpieza  \n4. Análisis exploratorio  \n5. Modelación predictiva  \n6. Hallazgos y conclusiones  \n7. Reproducibilidad y referencias')
add('\n## 1. Resumen ejecutivo')
add(f'Se procesaron **{a["n_original"]:,}** registros del comercio electrónico británico Online Retail. '
    f'Tras una auditoría excluyente quedaron **{a["n_clean"]:,}** líneas de venta válidas y **{a["n_excluded"]:,}** observaciones separadas. '
    f'El ingreso comercial válido suma **£{fmt(a["net_income"])}**. '
    f'Las cancelaciones negativas registradas, en valor absoluto, suman **£{fmt(a["cancelled_abs"])}** '
    f'(**{a["pct_cancelled"]:.2f}%** del bruto operativo definido en esta auditoría).')
add('## 2. Fuente y metodología')
add('Fuente: Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository. '
    'https://archive.ics.uci.edu/dataset/352/online+retail. Registros entre el 01-12-2010 y el 09-12-2011. '
    'Se descargó ZIP con `curl -L`, se extrajo con `unzip`, se convirtió la planilla mediante `in2csv`, '
    'se verificaron dimensiones con `wc -l` y tipos/distribuciones con `csvstat`, y se procesó el CSV con '
    'un script invocado desde la terminal. Los gráficos fueron generados con matplotlib mediante Python.')
add('**Convenciones:** Revenue = Quantity × UnitPrice (libras esterlinas); Month = AAAA-MM; Hour = 0–23; '
    'CustomerID se normaliza a entero sin decimal; InvoiceDate conserva hora y segundos. '
    'Los duplicados se comparan antes de normalizar texto, para detectar duplicados exactos en la fuente. '
    'Se estandariza Description a mayúsculas y espacios simples, evitando diferencias de presentación.')
add('## 3. Auditoría y limpieza')
add('### 3.1 Faltantes en la fuente')
table(['Columna','Faltantes','% de filas'],[(k,v,f'{100*v/a["n_original"]:.2f}%') for k,v in a['missing'].items()])
add('**Contraste con UCI:** la ficha describe Description y CustomerID como atributos que pueden faltar. '
    'Los conteos anteriores se obtienen directamente del archivo descargado y permiten comprobar la magnitud. '
    'No se presupone que la ficha contenga los conteos exactos.')
add('No se descartan ventas con **CustomerID faltante**: la venta y su ingreso se conocen incluso si no se conoce al comprador. '
    f'Se conservan {a["unidentified_sales"]:,} ventas válidas sin identificador, equivalentes a £{fmt(a["unidentified_revenue"])}; '
    'se excluyen únicamente del archivo de clientes para modelación. Los registros sin **Description** se separan '
    'del conjunto comercial para que los rankings de productos sean interpretables; esta es una decisión conservadora '
    'que puede subestimar el ingreso si hay transacciones genuinas sin descripción.')
add('### 3.2 Anomalías detectadas (conteo independiente; se superponen)')
labels={'duplicados_exactos':'Duplicados exactos','facturas_canceladas':'Facturas C (filas)',
'cantidad_no_positiva':'Quantity <= 0 o inválida','precio_no_positivo':'UnitPrice <= 0 o inválido',
'codigos_no_producto':'Códigos no comerciales','descripcion_vacia':'Description faltante',
'cliente_no_identificado':'CustomerID faltante','atipicos_quantity_IQR':'Valores atípicos Quantity (IQR)',
'atipicos_unitprice_IQR':'Valores atípicos UnitPrice (IQR)'}
table(['Detección','Filas'],[(labels[k],v) for k,v in a['raw_anomalies'].items()])
add('Outliers: regla descriptiva de Tukey (valores por debajo de Q1−1.5×IQR o por encima de Q3+1.5×IQR), '
    'calculada con la distribución cruda de cada variable. **No se excluyen por ser extremos**: una compra mayorista '
    'puede ser legítima; las magnitudes originales se conservan en el análisis de sensibilidad.')
for k,v in a['bounds'].items(): add(f'- **{k}:** umbral inferior {fmt(v["lower"])}; superior {fmt(v["upper"])}.')
add('### 3.3 Exclusión secuencial y rastreable')
add('Cada registro recibe **un único motivo prioritario**; los conteos de la siguiente tabla sí son aditivos. '
    'Se evita descontar dos veces una factura C con cantidad negativa.')
table(['Paso','Filas excluidas en este paso','Filas restantes'],[(x['criterio'],f'{x["excluidas"]:,}',f'{x["restantes"]:,}') for x in a['stages']])
add(f'**Resultado:** {a["n_clean"]:,} ventas comerciales; {a["n_excluded"]:,} excluidas guardadas '
    'en `data/retail_anulaciones.csv` con columna `ExclusionReason`.')
add('Criterios: duplicado exacto (evita facturación doble); factura que comienza en C (cancelación, nunca venta nueva); '
    'cantidad y precio no positivos o inválidos (no representan ventas comerciales positivas); códigos '
    '`POST`, `DOT`, `M`, `D`, `C2`, `BANK CHARGES`, `AMAZONFEE`, `S`, `B`, `CRUK`, `PADS` '
    '(portes, comisiones, descuentos, ajustes o líneas especiales no tratadas como producto comercial); '
    'descripción ausente (producto no interpretable) y fecha ilegible (impide desagregar por mes/hora). '
    '**Advertencia:** algunos códigos especiales pueden representar operaciones reales; su exclusión '
    'define estrictamente ingresos por productos, no ingresos contables totales.')
add('## 4. Análisis exploratorio')
add('### 4.1 Distribuciones y asimetría')
table(['Variable','Media','Mediana','DE','Mínimo','Q1','Q3','Máximo','Asimetría'],[
[k]+[fmt(a['stats'][k][z]) for z in ['media','mediana','sd','min','q1','q3','max','asimetria']]
for k in ['Quantity','UnitPrice','Revenue']])
add('Asimetría positiva: abundan compras de menor cuantía y algunas líneas muy grandes arrastran el promedio. '
    'La mediana permite describir la transacción típica sin el fuerte impacto de las colas. '
    'Los valores extremos no deben confundirse automáticamente con errores.')
add('### 4.2 Magnitud de ventas y cancelaciones')
add(f'- Ingreso de ventas válidas: **£{fmt(a["net_income"])}**.\n- Valor absoluto de cancelaciones negativas: **£{fmt(a["cancelled_abs"])}**. '
    f'\n- Bruto operativo definido = ventas válidas + cancelaciones absolutas: **£{fmt(a["gross_operational"])}**. '
    f'\n- Porcentaje anulado = |cancelaciones C negativas| / bruto operativo: **{a["pct_cancelled"]:.2f}%**. '
    f'\n- Facturas distintas: **{a["invoices"]:,}**; clientes identificados: **{a["customers"]:,}**; '
    f'códigos de producto distintos: **{a["products"]:,}**.')
add('**Alcance del indicador:** no es una pérdida causal ni financiera auditada: una factura C puede devolver una '
    'venta anterior al período; las cancelaciones pueden tener precios o productos distintos. No se deduce que '
    'todo lo cancelado equivalga a ingreso recuperable.')
add('### 4.3 Productos líderes')
table(['Posición','Código','Descripción','Ingreso £'],[(i+1,x['code'],x['description'],fmt(x['revenue'])) for i,x in enumerate(a['top_revenue'])])
add('**Top 10 por unidades:**')
table(['Posición','Código','Descripción','Unidades'],[(i+1,x['code'],x['description'],fmt(x['units'])) for i,x in enumerate(a['top_quantity'])])
add(f'Los dos top 10 comparten **{a["products_intersection"]}** códigos; mayor volumen no garantiza mayor ingreso: '
    'el precio unitario cambia la posición de un producto.')
add('### 4.4 Distribución geográfica y temporal')
add('**Ingreso por país (todos los países):**')
table(['País','Ingreso (£)','% de total'],[(k,fmt(v),f'{100*v/a["net_income"]:.2f}%') for k,v in a['country_income']])
add('**Ingreso por mes:**')
table(['Mes','Ingreso (£)'],[(k,fmt(v)) for k,v in sorted(a['month_income'])])
add('![Ingresos mensuales](ingresos_mes.png)')
add('**Ingreso por hora:**')
table(['Hora','Ingreso (£)'],[(k,fmt(v)) for k,v in a['hour_income']])
add('![Ingresos por hora](ingresos_hora.png)')
if a['country_income']:
    country,total=a['country_income'][0]
    add(f'**Dominio geográfico:** {country} lidera con {100*total/a["net_income"]:.2f}% del ingreso válido. '
        'Este peso afecta la representatividad de comparaciones internacionales.')
add('### 4.5 Facturas, concentración y correlaciones')
s=a['invoice_stats']
add(f'Ingreso por factura: mediana **£{fmt(s["mediana"])}**, media **£{fmt(s["media"])}**, '
    f'Q1 **£{fmt(s["q1"])}**, Q3 **£{fmt(s["q3"])}** y máximo **£{fmt(s["max"])}**. '
    f'Los 10 clientes identificados de mayor ingreso aportan **{a["top10_customer_contribution"]:.2f}%** '
    'del ingreso comercial total (incluidas las líneas de clientes sin ID en el denominador).')
add('![Distribución de facturas](facturas_distribucion.png)')
cs=a['correlation'];fs=['Quantity','UnitPrice','Revenue']
table(['Variable']+fs,[[f]+[f'{z:.4f}' for z in cs[i]] for i,f in enumerate(fs)])
add('Son correlaciones lineales sobre filas de venta; Revenue es producto de Quantity y UnitPrice, '
    'de modo que la interpretación no es causal y los atípicos pueden dominar el coeficiente.')
add('## 5. Modelación predictiva por cliente')
add(f'Se agregaron exactamente **{a["customer_count"]:,}** clientes con identificador en '
    '`data/clientes.csv`, con columnas `CustomerID, Facturas, Productos, EsUK, MesPrimeraCompra, Ingreso`. '
    '`Facturas` y `Productos` cuentan valores distintos; `EsUK` es 1 para UK y 0 para otros; '
    'la primera compra se determina con la menor fecha-hora. Ante países múltiples se usa el país modal. '
    'La partición 70/30 reproduce la instrucción de la pauta: orden numérico, `shuf --random-source=<(yes 42)` '
    f'y corte exacto por líneas: **{m["n_train"]:,}** entrenamiento / **{m["n_test"]:,}** prueba.')
add('**Importante:** el objetivo Ingreso y los predictores de actividad se calculan sobre el mismo horizonte anual. '
    'Esto mide asociación explicativa y no predicción anticipada a la primera compra; para predicción futura '
    'se deben construir predictores usando solo información anterior al período objetivo.')
add('### 5.1 Comparación de cinco configuraciones')
table(['Modelo','Objetivo al entrenar','MAE (£)','R² prueba'],[(x['modelo'],x['objetivo'],fmt(x['MAE']),f'{x["R2"]:.4f}') for x in m['metrics']])
chosen=min(m['metrics'],key=lambda x:x['MAE'])
add(f'**Mejor MAE de prueba:** {chosen["modelo"]}, objetivo **{chosen["objetivo"]}**, '
    f'MAE **£{fmt(chosen["MAE"])}**; su R² es **{chosen["R2"]:.4f}**. '
    'El MAE calcula errores en libras y siempre en escala original. '
    'Predicciones negativas se truncan a cero tanto con objetivo original como logarítmico.')
add('**Interpretación de los errores:** el gasto está concentrado en pocos clientes; '
    f'el 1% superior de clientes en prueba concentra {m["top1pct_test_income_share"]:.2f}% de su ingreso. '
    'Esos casos elevan el MAE y pueden deteriorar mucho el R². Entrenar con `log(1+Ingreso)` '
    'reduce la influencia de valores extremos en el ajuste; volver con `exp(pred)−1` prioriza típicamente '
    'el gasto central, pero puede subestimar compradores de gran volumen. '
    'El desempeño de B cuantifica cuánta señal contienen país y primer mes sin variables de actividad; '
    'si es peor que A, por sí solos resultan menos informativos. Un R² calculado una sola vez es frágil '
    'por el peso desproporcionado de pocos compradores grandes y la variabilidad de la muestra de prueba; '
    'sería preferible contrastarlo con múltiples particiones o validación cruzada.')
add('## 6. Tres hallazgos y recomendación')
if a['country_income']:
    k,v=a['country_income'][0]; add(f'1. **Concentración geográfica:** {k} aporta {100*v/a["net_income"]:.2f}% del ingreso de líneas válidas.')
add(f'2. **Importancia de cancelaciones:** £{fmt(a["cancelled_abs"])} se registran como cancelaciones '
    f'negativas ({a["pct_cancelled"]:.2f}% del bruto operativo definido).')
add(f'3. **Concentración por cliente:** los 10 clientes más grandes explican '
    f'{a["top10_customer_contribution"]:.2f}% del ingreso comercial registrado.')
add('**Recomendación a la tienda:** monitorear mensualmente cancelaciones por motivo, ventas de los '
    'principales productos y concentración de clientes; separar operaciones no comerciales de ventas de artículos. '
    'Antes de desplegar pronósticos operativos, separar temporalmente las compras para evitar fuga de información '
    'y validar modelos de manera repetida, especialmente en clientes de gasto alto.')
add('## 7. Reproducibilidad y referencias')
add('En una terminal Ubuntu: `sudo apt install -y python3 python3-venv python3-pip curl unzip` '
    'y desde la raíz del repositorio ejecutar `bash scripts/pipeline.sh`. '
    'Se descargan los datos desde UCI, se corre `in2csv`, `csvstat`, el script de limpieza, '
    'la división exacta con `shuf`, los modelos, la factura y este reporte en Markdown y PDF. '
    'Se requieren conexión a Internet y paquetes `requirements.txt` en la primera ejecución.')
add('**Archivos:** `data/retail_clean.csv`, `data/retail_anulaciones.csv`, `data/clientes.csv`, '
    '`data/train.csv`, `data/test.csv`, `report/modelos.json`, `report/resultados.json`, '
    '`report/factura.txt`, `report/reporte.md`, `report/reporte.pdf` y tres figuras PNG.')
add('**Referencia:** Chen, D. (2015). Online Retail. UCI Machine Learning Repository. '
    'https://doi.org/10.24432/C5BW33. Ficha: https://archive.ics.uci.edu/dataset/352/online+retail.')
content='\n'.join(md)+'\n'
(R/'reporte.md').write_text(content,encoding='utf-8')

# PDF exportado desde el mismo Markdown con estilo consistente, portada e índice.
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyUser',parent=styles['BodyText'],fontName='Helvetica',fontSize=8.5,leading=13,spaceAfter=6))
styles.add(ParagraphStyle(name='H1User',parent=styles['Heading1'],fontSize=14,leading=17,spaceBefore=14,spaceAfter=8,textColor=colors.HexColor('#193c5a')))
styles.add(ParagraphStyle(name='H2User',parent=styles['Heading2'],fontSize=10.5,leading=13,spaceBefore=10,spaceAfter=5))
styles.add(ParagraphStyle(name='SmallUser',parent=styles['BodyText'],fontSize=7.2,leading=10))
styles.add(ParagraphStyle(name='CoverUser',parent=styles['Title'],fontSize=19,leading=25,spaceAfter=12))
doc=SimpleDocTemplate(str(R/'reporte.pdf'),pagesize=A4,rightMargin=1.65*cm,leftMargin=1.65*cm,topMargin=1.7*cm,bottomMargin=1.5*cm)
flow=[];lines=content.splitlines();i=0

def mark(text):
    esc=html.escape(text)
    esc=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',esc)
    esc=re.sub(r'`([^`]+)`',r'<font name="Courier" size="7">\1</font>',esc)
    return esc.replace('  ',' ')
while i<len(lines):
    s=lines[i].strip()
    if not s or s=='---':flow.append(Spacer(1,5));i+=1;continue
    if s.startswith('|') and i+1<len(lines) and lines[i+1].startswith('|---'):
        head=[z.strip() for z in s.strip('|').split('|')]; i+=2; rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            rows.append([z.strip() for z in lines[i].strip('|').split('|')]);i+=1
        dat=[head]+rows
        colcount=len(head)
        # tablas amplias pueden ser más densas y dividirse entre páginas.
        cellfont=5.6 if colcount>=8 else 6.6
        dat=[[Paragraph(mark(v),ParagraphStyle('TCell',parent=styles['SmallUser'],fontSize=cellfont,leading=cellfont+2)) for v in row] for row in dat]
        usable=A4[0]-3.3*cm
        widths=[usable/colcount]*colcount
        t=Table(dat,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbe6ec')),('GRID',(0,0),(-1,-1),.25,colors.HexColor('#b9c8d3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        flow.append(t);flow.append(Spacer(1,8));continue
    if s.startswith('!['):
        mm=re.match(r'!\[.*?\]\((.*?)\)',s)
        if mm:
            p=R/mm.group(1)
            if p.exists():
                im=Image(str(p));ratio=im.imageHeight/im.imageWidth;im.drawWidth=16.2*cm;im.drawHeight=16.2*cm*ratio;flow.append(im)
        i+=1;continue
    if s.startswith('# '):
        flow.append(Paragraph(mark(s[2:]),styles['CoverUser'] if i<10 else styles['H1User']))
    elif s.startswith('## '):flow.append(Paragraph(mark(s[3:]),styles['H1User']))
    elif s.startswith('### '):flow.append(Paragraph(mark(s[4:]),styles['H2User']))
    else:flow.append(Paragraph(mark(s),styles['BodyUser']))
    i+=1

def page(canvas,doc):
    canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#687887'))
    canvas.drawString(1.65*cm,1*cm,'Universidad del Bío-Bío | Evaluación N°1')
    canvas.drawRightString(A4[0]-1.65*cm,1*cm,str(doc.page));canvas.restoreState()
doc.build(flow,onFirstPage=page,onLaterPages=page)
print('Reportes guardados en',R)
