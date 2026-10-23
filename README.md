# Evaluación N°1 — Online Retail

Proyecto **reproducible** para la evaluación de Ciencia de Datos en la Terminal Linux (Universidad del Bío-Bío, octubre de 2026).

## Ejecutar en Ubuntu 24.04 (WSL 2)

En la terminal **Ubuntu** (no dentro del contenedor, donde solo aparece `$`):

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl unzip
cd ruta/a/evaluacion1_online_retail
bash scripts/pipeline.sh
```

El script descarga `Online Retail.xlsx` de UCI, hace la conversión con `in2csv`, calcula faltantes y anomalías, separa ventas válidas y anulaciones, agrega clientes, divide según las **líneas exactas solicitadas** con `sort`/`shuf`, compara cinco configuraciones de modelos y crea **`report/reporte.md`, `report/reporte.pdf`, `report/factura.txt`** y visualizaciones.

* Requiere Internet la primera vez, espacio libre y Python instalado en Ubuntu.
* No requiere Docker porque la pauta acepta terminal Linux; es más sencillo instalar librerías en un entorno virtual local.
* Si la descarga ya existe en `data/online_retail.zip`, se reutiliza.
* Modifica el marcador **`[COMPLETAR NOMBRE]`** del reporte y el rótulo del analista en el script de factura para personalizar, y vuelve a ejecutar el pipeline para generar el PDF actualizado. Evita editar solo el PDF pues se regenera.
* Debes revisar/interpretar todos los resultados, decisiones de exclusión y posibles limitaciones antes de entregar como trabajo propio.

## Organización

- `scripts/pipeline.sh`: orquestación integral desde cero.
- `scripts/analisis.py`: auditoría, limpieza, agregaciones y figuras.
- `scripts/modelos.py`: regresiones sklearn, objetivo original y logarítmico.
- `scripts/factura.py`: factura calculada desde los archivos CSV.
- `scripts/reporte.py`: informe Markdown y PDF generado con cifras medidas.
- `requirements.txt`: dependencias fijadas por intervalos de versiones mayores.
- `data/`: entrada/salidas CSV; `report/`: entregables.

## Definiciones de auditoría importantes

1. Se retienen ventas válidas sin CustomerID para **ingresos** y se excluyen solamente de la base para **modelos por cliente**.
2. Se excluyen duplicados exactos, facturas `C`, Quantity y UnitPrice no positivos, códigos especiales, descripción vacía y fecha ilegible. La prioridad de exclusión es secuencial para no contar filas dos veces.
3. Los valores extremos IQR se **cuentan, pero no se descartan automáticamente** porque un mayorista puede hacer compras legítimas grandes.
4. **Cancelaciones** = valor absoluto de las líneas negativas con InvoiceNo empezando en C (tras prioridad por duplicados). La tasa es cancelaciones/(ventas válidas + cancelaciones). Esta es una medida de magnitud de cancelaciones y **no** necesariamente una pérdida económica neta.
5. El predictor `Facturas`/`Productos` se calcula sobre el mismo período que Ingreso. La comparación sirve como ejercicio de modelación explicativa, **no** como pronóstico de gasto futuro sin fuga de información.
6. El reporte contiene código fuente regenerable y un PDF, portada e índice textual. No se inventan cifras: todos los resultados se completan al ejecutar el pipeline con el dataset real.

## Subir a GitHub

En la carpeta del proyecto, luego de comprobar los archivos:

```bash
git init
git add README.md requirements.txt .gitignore scripts report
# también agrega data/*.csv si corresponde según instrucciones del docente y límites de GitHub
# git add data/*.csv
git commit -m "Evaluacion 1: auditoria reproducible Online Retail"
# crea un repositorio vacío en GitHub, luego:
# git branch -M main
# git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
# git push -u origin main
```

El dataset original puede mantenerse fuera del repositorio y descargarse desde el pipeline. Comprobar tamaño de CSV antes de subirlos a GitHub.

**Referencia:** Chen, D. (2015). *Online Retail*. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33

## Informe final de la evaluación

**Estudiante:** Juan Pablo Vargas

**Informe PDF definitivo:** `report/reporte_Juan_Pablo_Vargas.pdf`

Este documento contiene la portada, el índice independiente,
los resultados del análisis, las visualizaciones y las conclusiones.

El archivo `report/reporte.md` es generado automáticamente por
`scripts/reporte.py` y contiene los resultados y la metodología
en formato Markdown.

El PDF definitivo presenta esos resultados con una maquetación
académica personalizada. La ejecución de `scripts/pipeline.sh`
regenera el informe automático, pero no reproduce exactamente
el diseño del PDF definitivo.
