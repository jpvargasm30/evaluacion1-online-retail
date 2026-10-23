#!/usr/bin/env python3
"""Compara 5 alternativas en partición fija proporcionada por la evaluación."""
import csv,json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error,r2_score
R=Path('report');D=Path('data')
def load(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
train=load(D/'train.csv');test=load(D/'test.csv')
if not train or not test:raise ValueError('No hay clientes suficientes para entrenamiento y prueba')
ytr=np.array([float(r['Ingreso']) for r in train]); yte=np.array([float(r['Ingreso']) for r in test])
metrics=[]
def score(name,target,pred):
    pred=np.asarray(pred,dtype=float)
    metrics.append({'modelo':name,'objetivo':target,'MAE':float(mean_absolute_error(yte,pred)),
                    'R2':float(r2_score(yte,pred))})
score('Base: media de entrenamiento','Original',np.full_like(yte,ytr.mean()))
for name,features in [('A: Facturas + Productos',['Facturas','Productos']),
                      ('B: EsUK + MesPrimeraCompra',['EsUK','MesPrimeraCompra'])]:
    xtr=np.array([[float(r[c]) for c in features] for r in train]);
    xte=np.array([[float(r[c]) for c in features] for r in test]);
    lm=LinearRegression().fit(xtr,ytr)
    score(name,'Original',np.maximum(0,lm.predict(xte)))
    # El cero es límite económico natural de un ingreso de ventas válidas.
    lm_log=LinearRegression().fit(xtr,np.log1p(ytr))
    score(name,'log(1+Ingreso)',np.maximum(0,np.expm1(np.clip(lm_log.predict(xte),-30,30))))
(R/'modelos.json').write_text(json.dumps({'n_train':len(train),'n_test':len(test),
     'metrics':metrics,'test_max':float(yte.max()),'test_median':float(np.median(yte)),
     'test_mean':float(yte.mean()),
     'top1pct_test_income_share':float(yte[np.argsort(yte)[-max(1,round(len(yte)*.01)):]].sum()/yte.sum()*100)
      if yte.sum() else 0},ensure_ascii=False,indent=2),encoding='utf-8')
print('Métricas guardadas en report/modelos.json')
