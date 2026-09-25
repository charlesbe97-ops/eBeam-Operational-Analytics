# ============================================================
# OEE ANALYSIS - PUBLIC / GITHUB DEMO VERSION
# ============================================================
# This version intentionally uses synthetic data and synthetic process
# parameters. It demonstrates the data-processing architecture only.
# No value in this repository should be interpreted as a real equipment
# setting, production parameter, calibration constant, or operating limit.
# ============================================================

#1_OEE_Analysis
import calendar
import pandas as pd
import numpy as np
import os
from pathlib import Path
import platform
import subprocess
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle, Frame, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ============================================================
# PUBLIC DEMO CONFIGURATION
# ============================================================
# All process constants and sample datasets in this repository are synthetic.
# They are provided only to demonstrate the analytics workflow and must not be
# interpreted as production settings, calibration data, or engineering limits.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR.mkdir(exist_ok=True)

PUBLIC_PARAMS = {
    "MODE_A": {"kfactor": 2.50, "current": 2.40, "gap_factor": 0.0600},
    "MODE_B": {"kfactor": 0.025, "current": 8.00, "gap_factor": 0.0045},
}
PUBLIC_PALLETS_MIN_A = -1.80
PUBLIC_PALLETS_MIN_B = 8.00
PUBLIC_TRANSPORT_DISTANCE = 5.00
PUBLIC_PALLET_SPACING = 1.00
PUBLIC_FITO_THRESHOLD = 0.50

Data = pd.read_csv(DATA_DIR / 'ProcesoDatos.csv', encoding='utf-8-sig')
TSecciones = pd.read_csv(DATA_DIR / 'SeccionesTiempo.csv', encoding='utf-8-sig')
Paros = pd.read_csv(DATA_DIR / 'Paros.csv', encoding='utf-8-sig')
BeamON = pd.read_csv(DATA_DIR / 'BEAMON.csv', sep=',', encoding='utf-8-sig')
Master = pd.read_csv(DATA_DIR / 'BitacoraMaster.csv', encoding='utf-8-sig')
# INFO PARA AUDITORIA DE CAPTURA
Data_Audit=Data.copy()
Paros_Audit=Paros.copy()
# PROCESO INICIO
# INICIO KPI
TSecciones['entra todo']=pd.Timedelta(TSecciones['entra todo'].iloc[0])
TSecciones['sale mitad']=pd.Timedelta(TSecciones['sale mitad'].iloc[0])
TSecciones['giro y centro']=pd.Timedelta(TSecciones['giro y centro'].iloc[0])
TSecciones['entra mitad']=pd.Timedelta(TSecciones['entra mitad'].iloc[0])
TSecciones['sale todo']=pd.Timedelta(TSecciones['sale todo'].iloc[0])
Data['Fecha']=pd.to_datetime(Data['Fecha'],format='%d/%m/%Y')
Data['Carga (h)'] = pd.to_datetime(Data['Carga (h)'].str.replace('.', '', regex=False).str.upper(), format='%I:%M:%S %p')
Data['Inicio de irradiación (h)'] = pd.to_datetime(Data['Inicio de irradiación (h)'].str.replace('.', '', regex=False).str.upper(), format='%I:%M:%S %p')
Data['Exit treatment zone (h)'] = pd.to_datetime(Data['Exit treatment zone (h)'].str.replace('.', '', regex=False).str.upper(), format='%I:%M:%S %p')
Data['Fin de proceso (h)'] = pd.to_datetime(Data['Fin de proceso (h)'].str.replace('.', '', regex=False).str.upper(), format='%I:%M:%S %p')
Data['Fecha fin']=pd.to_datetime(Data['Fecha fin'],format='%d/%m/%Y')
Data['Tiempo de paro programado'] = pd.to_timedelta(Data['Tiempo de paro programado'])
Data['Tiempo de paro programado'] = Data['Tiempo de paro programado'].fillna(pd.Timedelta(seconds=0))
Data['1. Retardo de brotes'] = Data['1. Retardo de brotes'].fillna(0)
Data['2. Desinfeccion'] = Data['2. Desinfeccion'].fillna(0)
Data['3. Fitosanitario (150 Gy)'] = Data['3. Fitosanitario (150 Gy)'].fillna(0)
Data['3. Fitosanitario (400 Gy)'] = Data['3. Fitosanitario (400 Gy)'].fillna(0)
Data['4. Vegetales'] = Data['4. Vegetales'].fillna(0)
Data['5. Chiles secos'] = Data['5. Chiles secos'].fillna(0)
Data['6. Alimentos mascotas'] = Data['6. Alimentos mascotas'].fillna(0)
Data['7. Otros'] = Data['7. Otros'].fillna(0)
Data['8. Cosmeticos'] = Data['8. Cosmeticos'].fillna(0)
Data['9. Esterilizacion'] = Data['9. Esterilizacion'].fillna(0)
Data['Desecho fitosanitario'] = Data['Desecho fitosanitario'].fillna(0)
Data['Pallets tratados mal/Reprocesados'] = Data['Pallets tratados mal/Reprocesados'].fillna(0)
Data['Pruebas'] = Data['Pruebas'].fillna(0)
Data['Registro'] = Data['Registro'].fillna('Desconocido')
Data['Total_tarimas'] = Data.loc[:, '1. Retardo de brotes':'Pruebas'].sum(axis=1)
Data['Dosis_fracc'] = Data['Dosis de proceso (kGy)']/Data['# de Fraccionamiento']
Data['Pallets_min'] = PUBLIC_PALLETS_MIN_A*np.log(Data['Dosis_fracc']) + PUBLIC_PALLETS_MIN_B
Data['Tarimas_calculo'] = np.where(Data['Total_tarimas'] <= 5, 1, Data['Total_tarimas'] - 5)
Data['kfactor'] = Data['Tipo de tratamiento'].map(lambda x: PUBLIC_PARAMS.get(x, PUBLIC_PARAMS['MODE_B'])['kfactor'])
Data['mA'] = Data['Tipo de tratamiento'].map(lambda x: PUBLIC_PARAMS.get(x, PUBLIC_PARAMS['MODE_B'])['current'])
Data['vUBC'] = (Data['mA']*Data['kfactor']/Data['Dosis_fracc']).round(3)
Data['TUBC'] = pd.to_timedelta(PUBLIC_TRANSPORT_DISTANCE/Data['vUBC']/60, unit='h').dt.ceil('s')
Data['FactorGAP'] = Data['Tipo de tratamiento'].map(lambda x: PUBLIC_PARAMS.get(x, PUBLIC_PARAMS['MODE_B'])['gap_factor'])
Data['TGAP'] = pd.to_timedelta(Data['Dosis_fracc']/Data['FactorGAP']/60/60, unit='h').dt.ceil('s')
T2S=TSecciones['entra todo'].iloc[0]+TSecciones['sale mitad'].iloc[0]+TSecciones['giro y centro'].iloc[0]+TSecciones['entra mitad'].iloc[0]+TSecciones['sale todo'].iloc[0]
T1S=TSecciones['entra todo'].iloc[0]+TSecciones['sale todo'].iloc[0]
Data['TPF'] = np.where(Data['No. de lados'] == 2,
                            T2S + 2*Data['TUBC'] + Data['TGAP']*(Data['Total_tarimas']+Data['Tarimas_calculo']+1),
                            T1S + Data['TUBC'] + Data['TGAP']*(Data['Tarimas_calculo'])
)
Data['TPT'] = (Data['TPF']*Data['# de Fraccionamiento'])-(Data['TGAP']*np.ceil(Data['Pallets_min'])*(Data['# de Fraccionamiento']-1))

Data['TPR'] = ((pd.to_datetime(Data['Fecha fin'].dt.strftime('%Y-%m-%d') + ' ' + Data['Exit treatment zone (h)'].dt.strftime('%H:%M:%S')) + TSecciones['sale todo'].iloc[0]) - 
            pd.to_datetime(Data['Fecha'].dt.strftime('%Y-%m-%d') + ' ' + Data['Inicio de irradiación (h)'].dt.strftime('%H:%M:%S')) + TSecciones['entra todo'].iloc[0] + 
            (Data['TGAP']/2)-Data['Tiempo de paro programado']
).dt.ceil('s')
Data['Rendimiento'] = np.clip(
    (1- (Data['TPR']-Data['TPT'])/Data['TPT'])*100,
    0,
    100
).round(2)
Data['Diferencia_Pallets'] = np.where(Data['Total_tarimas'] > Data['Pallets_min'], 
                                      0,
                                      Data['Pallets_min'] - Data['Total_tarimas']
)
Data['Dist_hueca'] = Data['Diferencia_Pallets'] * PUBLIC_PALLET_SPACING
Data['Tiempo_hueco'] = pd.to_timedelta(Data['Dist_hueca']/Data['vUBC']/60, unit='h').dt.ceil('s')
Data['Aprovechamiento'] = np.clip(
    100 * (1 - (Data['Tiempo_hueco'] * ((Data['# de Fraccionamiento'] * Data['No. de lados']) - 1)) / Data['TPR']),
    0,
    100
).round(2)
Data['Calidad'] = np.where(
    Data['Total_tarimas'] > 0,
    ((Data['Total_tarimas']-Data['Pallets tratados mal/Reprocesados'])/Data['Total_tarimas'])*100,
    0
)
Data['IGE'] = (Data['Rendimiento']*Data['Aprovechamiento']*Data['Calidad']/10000).round(2)
# KPI FIN
# TIEMPOS POR SERVICIO INICIO
Retardo_brotes =  np.where(
    Data['Total_tarimas'] > 0,
    (Data['1. Retardo de brotes']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Desinfeccion = np.where(
    Data['Total_tarimas'] > 0,
    (Data['2. Desinfeccion']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Fitosanitario_150 = np.where(
    Data['Total_tarimas'] > 0,
    (Data['3. Fitosanitario (150 Gy)']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Fitosanitario_400 = np.where(
    Data['Total_tarimas'] > 0,
    (Data['3. Fitosanitario (400 Gy)']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Vegetales = np.where(
    Data['Total_tarimas'] > 0,
    (Data['4. Vegetales']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Chiles_secos = np.where(
    Data['Total_tarimas'] > 0,
    (Data['5. Chiles secos']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Alimentos_mascotas = np.where(
    Data['Total_tarimas'] > 0,
    (Data['6. Alimentos mascotas']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Otros = np.where(
    Data['Total_tarimas'] > 0,
    (Data['7. Otros']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Cosmeticos = np.where(
    Data['Total_tarimas'] > 0,
    (Data['8. Cosmeticos']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Esterilizacion = np.where(
    Data['Total_tarimas'] > 0,
    (Data['9. Esterilizacion']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Desecho_Fito = np.where(
    Data['Total_tarimas'] > 0,
    (Data['Desecho fitosanitario']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Reprocesos = np.where(
    Data['Total_tarimas'] > 0,
    (Data['Pallets tratados mal/Reprocesados']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Pruebas_Tiempo = np.where(
    Data['Total_tarimas'] > 0,
    (Data['Pruebas']/Data['Total_tarimas'])*Data['TPR'],
    0
)
Tiempos_Servicio = pd.DataFrame({
    'Retardo_brotes': Retardo_brotes,
    'Desinfeccion': Desinfeccion,
    'Fitosanitario_150': Fitosanitario_150,
    'Fitosanitario_400': Fitosanitario_400,
    'Vegetales': Vegetales,
    'Chiles_secos': Chiles_secos,
    'Alimentos_mascotas': Alimentos_mascotas,
    'Otros': Otros,
    'Cosmeticos': Cosmeticos,
    'Esterilizacion': Esterilizacion,
    'Desecho Fito': Desecho_Fito,
    'Reprocesos': Reprocesos,
    'Pruebas Tiempo': Pruebas_Tiempo
}).astype('timedelta64[s]')
# TIEMPOS POR SERVICIO FIN
fecha_inicio = Data['Fecha'].min()
fecha_fin = Data['Fecha'].max()
anio_evaluacion = Data['Fecha'].iloc[0].year
mes_evaluacion=(Data['Fecha'].iloc[0]).strftime("%m")
# PROCESO FIN
# PAROS INICIO 
Paros['Fecha'] = pd.to_datetime(Paros['Fecha'], format='%d/%m/%Y')
Paros['Hora de Paro'] = pd.to_datetime(Paros['Hora de Paro'].str.replace('a.m.', 'AM', regex=False).str.replace('p.m.', 'PM', regex=False), format='%I:%M:%S %p').pipe(lambda x: x - pd.to_datetime(x.dt.date))
Paros['Fecha Reinicio'] = pd.to_datetime(Paros['Fecha Reinicio'], format='%d/%m/%Y')
Paros['Hora Reinicio'] = pd.to_datetime(Paros['Hora Reinicio'].str.replace('a.m.', 'AM', regex=False).str.replace('p.m.', 'PM', regex=False), format='%I:%M:%S %p').pipe(lambda x: x - pd.to_datetime(x.dt.date))
Paros['Interlock'] = Paros['Interlock'].fillna('No registrado')
Paros['Motivo del paro'] = Paros['Motivo del paro'].fillna('N/A')
Paros['Registro'] = Paros['Registro'].fillna('No Registrado')
Paros['Observaciones'] = Paros['Observaciones'].fillna('Sin Observaciones')
Paros['Tiempo de Paro'] = (Paros['Fecha Reinicio'] + Paros['Hora Reinicio'])-(Paros['Fecha']+ Paros['Hora de Paro'])
Paros['InicioParo']=Paros['Fecha']+ Paros['Hora de Paro'] #COLUMNA AUXILIAR PARA CONTEO DE PAROS POR PROCESO
# PAROS FIN
# CONTEO DE PAROS (PROCESO)
ConteoParos = []
for i in range(len(Data)):
    inicio = pd.to_datetime(Data['Fecha'].iloc[i].strftime('%Y-%m-%d') + ' ' + Data['Inicio de irradiación (h)'].iloc[i].strftime('%H:%M:%S'))
    fin = pd.to_datetime(Data['Fecha fin'].iloc[i].strftime('%Y-%m-%d') + ' ' + Data['Exit treatment zone (h)'].iloc[i].strftime('%H:%M:%S'))

    cantidad = Paros[
        (Paros['InicioParo'] >= inicio) &
        (Paros['InicioParo'] <= fin)
    ].shape[0]

    ConteoParos.append(cantidad)
Data['ConteoParos'] = ConteoParos
# FIN CONTEO DE PAROS
# TABLA RESULTADO FINAL
resultado = pd.concat([Data, Tiempos_Servicio], axis=1)
# INICIO Manejo datos BeamON
BeamON[['Date/Time', 'System.BEAM_ON']] = BeamON['Date/Time,System.BEAM_ON'].str.split(",", expand=True)
BeamON = BeamON.drop(columns=['Date/Time,System.BEAM_ON'])
BeamON = BeamON.drop_duplicates(subset=["Date/Time"])
BeamON = BeamON[BeamON["Date/Time"] != "Date/Time"]
BeamON['Date/Time']=pd.to_datetime(BeamON['Date/Time'],format='%m/%d/%Y %I:%M:%S %p')
BeamON['System.BEAM_ON']=np.ceil([float(x) for x in BeamON['System.BEAM_ON']])
BeamON_Time=BeamON['Date/Time'].iloc[1]-BeamON['Date/Time'].iloc[0]
# FIN Manejo datos BeamON
# INICIO Analisis Bitacora Maestra
# Leer el archivo
# Diccionario para asegurar que los meses en español se conviertan correctamente
meses_es = {
    'ene': 'Jan',
    'feb': 'Feb',
    'mar': 'Mar',
    'abr': 'Apr',
    'may': 'May',
    'jun': 'Jun',
    'jul': 'Jul',
    'ago': 'Aug',
    'sep': 'Sep',
    'oct': 'Oct',
    'nov': 'Nov',
    'dic': 'Dec',
}

# Reemplazar los meses en español a inglés para que Pandas los procese de golpe de forma nativa
fecha_en_ingles = Master['Fecha de Proceso'].str.lower().replace(
    meses_es, regex=True
)

# Convertir directamente a datetime de Pandas
Master['Fecha de Proceso'] = pd.to_datetime(fecha_en_ingles, format='%d-%b-%y').fillna(pd.to_datetime(0))
Master['Operador'] = Master['Operador'].fillna('Sin registro')
Master['Estatus'] = Master['Estatus'].fillna('Sin estatus')
Master['P. Run'] = Master['P. Run'].fillna(-1)
Master['P. Run'] = [int(x) for x in Master['P. Run']]
Master['TIN'] = Master['TIN'].fillna('Sin TIN')
Master['Folio TIN'] = Master['Folio TIN'].fillna(0)
Master['Folio TIN'] = [int(x) for x in Master['Folio TIN']]
Master['Folio Logistica'] = Master['Folio Logistica'].fillna(0)
Master['Folio Logistica'] = [0 if x == 'Falta captura' else x for x in Master['Folio Logistica']]
Master['Folio Logistica'] = [float(x) for x in Master['Folio Logistica']]
Master['Folio calidad'] = Master['Folio calidad'].fillna(-1) 
Master['Cliente'] = Master['Cliente'].fillna('Sin Cliente')
Master['Codigo cliente'] = Master['Codigo cliente'].fillna('Sin Codigo Cliente')
Master['Producto'] = Master['Producto'].fillna('Sin Producto')
Master['Configuracion (Fito) prod'] = Master['Configuracion (Fito) prod'].fillna('Error registro')
Master['No de configuracion'] = Master['No de configuracion'].fillna(0)
Master['Tipo de servicio'] = Master['Tipo de servicio'].fillna('Sin Tipo de Servicio')
Master['Dosis de proceso solicitada (kGy)'] = Master['Dosis de proceso solicitada (kGy)'].fillna(0)
Master['Numero de tarima de TIN'] = Master['Numero de tarima de TIN'].fillna(0)
Master['Carrier'] = Master['Carrier'].fillna(0)
Master['Etiqueta sistema'] = Master['Etiqueta sistema'].fillna('Sin etiqueta sistema')
Master['Etiqueta interna'] = Master['Etiqueta interna'].fillna('Sin etiqueta interna')
Master['Tarimas por TIN'] = Master['Tarimas por TIN'].fillna(0)
Master['Tratamiento'] = Master['Tratamiento'].fillna('Sin Tratamiento')
Master['Dosis proceso'] = Master['Dosis proceso'].fillna(0)
Master['N° Lados'] = Master['N° Lados'].fillna(0)
Master['N° pases'] = Master['N° pases'].fillna(0)
Master['kGy por pase'] = Master['kGy por pase'].fillna(0)
Master['Factor K'] = Master['Factor K'].fillna(0)
Master['Corriente (A)'] = Master['Corriente (A)'].fillna(0)
Master['Velocidad UBC'] = Master['Velocidad UBC'].fillna(0)
Master['Inicio carga conveyor'] = pd.to_datetime(Master['Inicio carga conveyor'].str.replace('.', '', regex=False).str.upper(),format='%I:%M:%S %p').fillna(pd.to_datetime(0))
Master['Fin descarga conveyor'] = pd.to_datetime(Master['Fin descarga conveyor'].str.replace('.', '', regex=False).str.upper(),format='%I:%M:%S %p').fillna(pd.to_datetime(0))
Master['Tiempo proceso'] = pd.to_timedelta(Master['Tiempo proceso'], errors='coerce').fillna(pd.Timedelta(seconds=0))
Master['Desviaciones'] = Master['Desviaciones'].fillna('Sin Desviaciones')
Master['Registro'] = Master['Registro'].fillna('Sin Registro')
ConteoDeDesviaciones = Master['Desviaciones'].value_counts()
Master2=Master.drop_duplicates(subset=['P. Run'])
Master2=Master2[Master2['Fecha de Proceso'].between(fecha_inicio, fecha_fin)]
# TARIMAS TRATADAS POR Tipo de servicio
# Filtrar Bitácora Master
Master_TIN_Base = Master[
    Master['Fecha de Proceso'].between(fecha_inicio, fecha_fin)
].copy()
# Excluir registros que no tienen un TIN válido
Master_TIN_Base = Master_TIN_Base[
    Master_TIN_Base['TIN'] != 'Sin TIN'
].copy()
# FUNCIÓN PARA OBTENER EL TIPO DE SERVICIO REPRESENTATIVO
# Valores que no queremos considerar como un servicio válido
servicios_invalidos = {
    '-',
    '#REF!',
    'Sin Tipo de Servicio'
}
def obtener_servicio_representativo(serie):
    # Conservamos solamente servicios válidos
    servicios_validos = [
        servicio.strip()
        for servicio in serie.dropna().astype(str)
        if servicio.strip() not in servicios_invalidos
    ]
    # Si el TIN no tiene ningún servicio válido
    if len(servicios_validos) == 0:
        return 'Sin Tipo de Servicio'
    # Si existen varias capturas para un TIN,
    # usamos el servicio que aparece con mayor frecuencia
    return pd.Series(servicios_validos).mode().iloc[0]

# DEJAR UN SOLO REGISTRO POR TIN
Master_TIN = (
    Master_TIN_Base
    .groupby('TIN', as_index=False)
    .agg(
        # Primera fecha registrada para ese TIN
        Fecha=('Fecha de Proceso', 'min'),

        # Si hay distintos valores registrados,
        # tomamos el máximo, como acordamos
        Tarimas=('Tarimas por TIN', 'max'),

        # Para clasificar Fitosanitario usamos la dosis solicitada
        Dosis_Solicitada=(
            'Dosis de proceso solicitada (kGy)',
            'max'
        ),

        # Tipo de servicio representativo del TIN
        Tipo_Servicio=(
            'Tipo de servicio',
            obtener_servicio_representativo
        )
    )
)
# CLASIFICACIÓN DEL TIPO DE SERVICIO
def clasificar_servicio(row):

    tipo = str(row['Tipo_Servicio']).strip()
    dosis = row['Dosis_Solicitada']
    # FITOSANITARIO
    if tipo.startswith('Fitosanitario'):
        if dosis >= PUBLIC_FITO_THRESHOLD:
            return 'Fitosanitario_400Gy'
        else:
            return 'Fitosanitario_150Gy'
    # DESBACTERIZACIÓN
    mapa_servicios = {
        'Desbacterizacion (Chiles secos)':
            'Chiles_secos',
        'Desbacterizacion (Alimento mascotas)':
            'Alimentos_mascotas',
        'Desbacterizacion (Vegetales)':
            'Vegetales',
        'Desbacterizacion (Otros Y protocolos)':
            'Otros'
    }
    # Si está en el diccionario, cambia el nombre.
    # Si no, conserva el nombre original.
    return mapa_servicios.get(tipo, tipo)
# Aplicar clasificación a cada TIN
Master_TIN['Tipo de Servicio'] = Master_TIN.apply(
    clasificar_servicio,
    axis=1
)
# TOTAL DE TARIMAS TRATADAS EN EL MES
Total_Tarimas_Mes = int(
    Master_TIN['Tarimas'].sum()
)
# TARIMAS TRATADAS POR TIPO DE SERVICIO
TarimasPorServicio = (
    Master_TIN
    .groupby(
        'Tipo de Servicio',
        as_index=False
    )['Tarimas']
    .sum()
)
# Agregar Año y Mes para utilizar posteriormente en Power BI
TarimasPorServicio.insert(
    0,
    'Mes',
    mes_evaluacion
)
TarimasPorServicio.insert(
    0,
    'Año',
    anio_evaluacion
)
# # Crear llave AñoMes
# TarimasPorServicio['AñoMesKey'] = (
#     TarimasPorServicio['Año'] * 100
#     + TarimasPorServicio['Mes']
# )
# Convertir número de tarimas a entero
TarimasPorServicio['Tarimas'] = (
    TarimasPorServicio['Tarimas']
    .round()
    .astype(int)
)
# RESULTADOS DE CONTROL
print('\n' + '=' * 50)
print(
    f'TARIMAS TRATADAS - '
    f'{Data["Fecha"].iloc[0].strftime("%B %Y").upper()}'
)
print('=' * 50)
print(
    f'Total de TIN únicos procesados: '
    f'{len(Master_TIN)}'
)
print(
    f'Total de tarimas tratadas: '
    f'{Total_Tarimas_Mes}'
)
print('\nTarimas por tipo de servicio:')
print(TarimasPorServicio)
print('=' * 50)
# FIN Analisis Bitacora Maestra
# FIN

# INICIO Calculo KPI
_, dias_del_mes = calendar.monthrange(Data['Fecha'].iloc[0].year, Data['Fecha'].iloc[0].month)
TiempoTotalMes=pd.to_timedelta(dias_del_mes*24,unit='h')
HorasProcesoTotales=Data['TPR'].sum()
BeamON_Mes=BeamON_Time*BeamON['System.BEAM_ON'].sum()
BeamOFF_Mes=TiempoTotalMes-BeamON_Mes
Uso_operativo = (BeamON_Mes/TiempoTotalMes)*100
ContParosMes = Paros['Interlock'].count()
HorasParoMes = Paros['Tiempo de Paro'].sum()
PorcTiempoParo = round((HorasParoMes/TiempoTotalMes)*100,2)
Disponibilidad = (100-PorcTiempoParo)
Rendimiento = Data['Rendimiento'].mean()
Aprovechamiento = Data['Aprovechamiento'].mean()
Calidad = Data['Calidad'].mean()
IGE = Data['IGE'].mean()
OEE = Disponibilidad*Rendimiento*Calidad/10000
ParosporProceso = Data['ConteoParos'].sum()/Data['Fecha'].count()
No_TIN_Mes=len(Master2[Master2['TIN'] != 'Sin TIN']['TIN'].unique())
PRun_Mes=(Master2['P. Run'] != -1).sum()
FTR = (1 - (Master2['Desviaciones'] != 'Sin Desviaciones').sum() / (Master2['P. Run'] != -1).sum()) * 100
KPI_Mensual = {
    "Año":anio_evaluacion,
    "Mes":mes_evaluacion,
    "Rendimiento":Rendimiento,
    "Aprovechamiento":Aprovechamiento,
    "Calidad":Calidad,
    "First Time Right":FTR,
    "% Tiempo de paro":PorcTiempoParo,
    "Disponibilidad":Disponibilidad,
    "IGE":IGE,
    "OEE":OEE,
    "Horas totales del mes":TiempoTotalMes,
    "Horas Proceso agendadas":HorasProcesoTotales,
    "Horas Beam ON":BeamON_Mes,
    "Horas Beam OFF":BeamOFF_Mes,
    "No. TIN tratados":No_TIN_Mes,
    "No. Process Run ejecutadas":PRun_Mes
}
KPI_Mes=pd.DataFrame([KPI_Mensual])
# INICIO Calculos por servicio
TPS = [
    {"Tipo de Servicio":'Retardo_brotes',"Horas de proceso":Retardo_brotes.sum(),"% Horas de Proceso":100*Retardo_brotes.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['1. Retardo de brotes'].sum()},
    {"Tipo de Servicio":'Desinfeccion',"Horas de proceso":Desinfeccion.sum(),"% Horas de Proceso":100*Desinfeccion.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['2. Desinfeccion'].sum()},
    {"Tipo de Servicio":'Fitosanitario_150',"Horas de proceso":Fitosanitario_150.sum(),"% Horas de Proceso":100*Fitosanitario_150.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['3. Fitosanitario (150 Gy)'].sum()},
    {"Tipo de Servicio":'Fitosanitario_400',"Horas de proceso":Fitosanitario_400.sum(),"% Horas de Proceso":100*Fitosanitario_400.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['3. Fitosanitario (400 Gy)'].sum()},
    {"Tipo de Servicio":'Vegetales',"Horas de proceso":Vegetales.sum(),"% Horas de Proceso":100*Vegetales.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['4. Vegetales'].sum()},
    {"Tipo de Servicio":'Chiles_secos',"Horas de proceso":Chiles_secos.sum(),"% Horas de Proceso":100*Chiles_secos.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['5. Chiles secos'].sum()},
    {"Tipo de Servicio":'Alimentos_mascotas',"Horas de proceso":Alimentos_mascotas.sum(),"% Horas de Proceso":100*Alimentos_mascotas.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['6. Alimentos mascotas'].sum()},
    {"Tipo de Servicio":'Otros',"Horas de proceso":Otros.sum(),"% Horas de Proceso":100*Otros.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['7. Otros'].sum()},
    {"Tipo de Servicio":'Cosmeticos',"Horas de proceso":Cosmeticos.sum(),"% Horas de Proceso":100*Cosmeticos.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['8. Cosmeticos'].sum()},
    {"Tipo de Servicio":'Esterilizacion',"Horas de proceso":Esterilizacion.sum(),"% Horas de Proceso":100*Esterilizacion.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['9. Esterilizacion'].sum()},
    {"Tipo de Servicio":'Desecho_Fito',"Horas de proceso":Desecho_Fito.sum(),"% Horas de Proceso":100*Desecho_Fito.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['Desecho fitosanitario'].sum()},
    {"Tipo de Servicio":'Reprocesos',"Horas de proceso":Reprocesos.sum(),"% Horas de Proceso":100*Reprocesos.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['Pallets tratados mal/Reprocesados'].sum()},
    {"Tipo de Servicio":'Pruebas Tiempo',"Horas de proceso":Pruebas_Tiempo.sum(),"% Horas de Proceso":100*Pruebas_Tiempo.sum()/HorasProcesoTotales,"Posiciones Tratadas":Data['Pruebas'].sum()},
]
TiemposPorServicio = pd.DataFrame(TPS)
TiemposPorServicio.insert(4, 'Mes', mes_evaluacion)
TiemposPorServicio.insert(5, 'Año', anio_evaluacion)
print(f'El tiempo de paro es: {Paros["Tiempo de Paro"].sum()}')
print(f'El rendimiento es: {Rendimiento}')
print(f'El aprovechamiento es: {Aprovechamiento}')
print(f'La calidad es: {Calidad}')
print(f'El indice global es: {IGE}')
print(f'El FTR es: {FTR}')
print(TiemposPorServicio['Horas de proceso'].sum())
print(HorasProcesoTotales)
print(TiemposPorServicio['% Horas de Proceso'].sum())
print(TiemposPorServicio['Posiciones Tratadas'].sum())
print(HorasProcesoTotales-TiemposPorServicio['Horas de proceso'].sum())
print(f'El uso operativo es {Uso_operativo}')
print(f'La disponibildad es: {Disponibilidad}')
print(f'El OEE es: {OEE}')
print('\n\n')
# INICIO AUDITORIA OEE
# Resumen global
Data_Audit['Total_tarimas'] = Data_Audit.loc[:, '1. Retardo de brotes':'Pruebas'].sum(axis=1)
Operadores=Data_Audit['Registro'].unique()
print(Operadores)
FaltasRegistro= {
    "Mes": mes_evaluacion,
    "Fecha":len(Data_Audit[Data_Audit['Fecha'].isna()]),
    "Carga":len(Data_Audit[Data_Audit['Carga (h)'].isna()]),
    "Inicio de Irradiacion":len(Data_Audit[Data_Audit['Inicio de irradiación (h)'].isna()]),
    "Exit Treatment Zone":len(Data_Audit[Data_Audit['Exit treatment zone (h)'].isna()]),
    "Fin Proceso":len(Data_Audit[Data_Audit['Fin de proceso (h)'].isna()]),
    "Fecha fin":len(Data_Audit[Data_Audit['Fecha fin'].isna()]),
    "Dosis Proceso":len(Data_Audit[Data_Audit['Dosis de proceso (kGy)'].isna()]),
    "# de Fraccionamiento":len(Data_Audit[Data_Audit['# de Fraccionamiento'].isna()]),
    "Tipo de tratamiento":len(Data_Audit[Data_Audit['Tipo de tratamiento'].isna()]),
    "No. de lados":len(Data_Audit[Data_Audit['No. de lados'].isna()]),
    "Registro":len(Data_Audit[Data_Audit['Registro'].isna()]),
    "Sin registro de tarimas":len(Data_Audit[Data_Audit['Total_tarimas']==0])
}
FaltasRegistro["Total Faltas"] = sum(v for k, v in FaltasRegistro.items() if k != "Mes")
FaltasRegistroTotal = pd.DataFrame([FaltasRegistro])
# Resumen por operador
resumen_operadores = []

for operador in Operadores:
    if pd.isna(operador):
        continue
    
    sub_data = Data_Audit[Data_Audit['Registro'] == operador]
    
    # Calculamos el conteo de cada tipo de falta
    f_fecha = sub_data['Fecha'].isna().sum()
    f_carga = sub_data['Carga (h)'].isna().sum()
    f_inicio = sub_data['Inicio de irradiación (h)'].isna().sum()
    f_exit = sub_data['Exit treatment zone (h)'].isna().sum()
    f_fin = sub_data['Fin de proceso (h)'].isna().sum()
    f_fecha_fin = sub_data['Fecha fin'].isna().sum()
    f_dosis = sub_data['Dosis de proceso (kGy)'].isna().sum()
    f_fracc = sub_data['# de Fraccionamiento'].isna().sum()
    f_tipo = sub_data['Tipo de tratamiento'].isna().sum()
    f_lados = sub_data['No. de lados'].isna().sum()
    f_tarimas = (sub_data['Total_tarimas'] == 0).sum()
    
    # Suma total de faltas para este operador
    total_faltas = (f_fecha + f_carga + f_inicio + f_exit + f_fin + 
                    f_fecha_fin + f_dosis + f_fracc + f_tipo + f_lados + f_tarimas)
    
    resumen_operadores.append({
        "Mes":mes_evaluacion,
        "Operador": operador,
        "Total Registros": len(sub_data),
        "Total Faltas": total_faltas,  # Columna agregada
        "Fecha": f_fecha,
        "Carga": f_carga,
        "Inicio de Irradiacion": f_inicio,
        "Exit Treatment Zone": f_exit,
        "Fin Proceso": f_fin,
        "Fecha fin": f_fecha_fin,
        "Dosis Proceso": f_dosis,
        "# de Fraccionamiento": f_fracc,
        "Tipo de tratamiento": f_tipo,
        "No. de lados": f_lados,
        "Sin registro de tarimas": f_tarimas
    })

FaltasPorOperador = pd.DataFrame(resumen_operadores)
# FIN AUDITORIA OEE
# INICIO AUDITORIA PAROS
# Resumen global
Paros_Audit['Fecha'] = pd.to_datetime(Paros_Audit['Fecha'], format='%d/%m/%Y')
Paros_Audit['Fecha'] = Paros_Audit['Fecha'].fillna(pd.to_datetime(-1))
Paros_Audit['Hora de Paro'] = pd.to_datetime(Paros_Audit['Hora de Paro'].str.replace('a.m.', 'AM', regex=False).str.replace('p.m.', 'PM', regex=False), format='%I:%M:%S %p').pipe(lambda x: x - pd.to_datetime(x.dt.date))
Paros_Audit['Hora de Paro'] = Paros_Audit['Hora de Paro'].fillna(pd.Timedelta(-1))
Paros_Audit['Fecha Reinicio'] = pd.to_datetime(Paros_Audit['Fecha Reinicio'], format='%d/%m/%Y')
Paros_Audit['Fecha Reinicio'] = Paros_Audit['Fecha Reinicio'].fillna(pd.to_datetime(-1))
Paros_Audit['Hora Reinicio'] = pd.to_datetime(Paros_Audit['Hora Reinicio'].str.replace('a.m.', 'AM', regex=False).str.replace('p.m.', 'PM', regex=False), format='%I:%M:%S %p').pipe(lambda x: x - pd.to_datetime(x.dt.date))
Paros_Audit['Hora Reinicio'] = Paros_Audit['Hora Reinicio'].fillna(pd.Timedelta(-1))
Paros_Audit['Tiempo de Paro'] = (Paros_Audit['Fecha Reinicio'] + Paros_Audit['Hora Reinicio'])-(Paros_Audit['Fecha']+ Paros_Audit['Hora de Paro'])
OperadoresParos=Paros_Audit['Registro'].unique()
print(OperadoresParos)
FaltasRegistroParos= {
    "Mes": mes_evaluacion,
    "Fecha":len(Paros_Audit[Paros_Audit['Fecha']==pd.to_datetime(-1)]),
    "Hora de Paro":len(Paros_Audit[Paros_Audit['Hora de Paro']==pd.Timedelta(-1)]),
    "Fecha Reinicio":len(Paros_Audit[Paros_Audit['Fecha Reinicio']==pd.to_datetime(-1)]),
    "Hora Reinicio":len(Paros_Audit[Paros_Audit['Hora Reinicio']==pd.Timedelta(-1)]),
    "Interruption ID":len(Paros_Audit[Paros_Audit['Interruption ID'].isna()]),
    "Interlock":len(Paros_Audit[Paros_Audit['Interlock'].isna()]),
    "Motivo del paro":len(Paros_Audit[(Paros_Audit['Motivo del paro'].isna()) & (Paros_Audit['Interlock']=='Process -OFF -Button')]),
    "Registro":len(Paros_Audit[Paros_Audit['Registro'].isna()]),
    "Tiempo de Paro":len(Paros_Audit[Paros_Audit['Tiempo de Paro']<=pd.Timedelta(0)])
}
FaltasRegistroParos["Total Faltas"] = sum(v for k, v in FaltasRegistroParos.items() if k != "Mes")
FaltasRegistroParosTotal = pd.DataFrame([FaltasRegistroParos])
# Resumen por operador
# Resumen por operador en Paros
resumen_operadores_paros = []

for operador in OperadoresParos:
    # Omitimos valores nulos
    if pd.isna(operador):
        continue
    
    sub_paros = Paros_Audit[Paros_Audit['Registro'] == operador]
    
    # Conteo de faltas para el operador
    f_fecha = (sub_paros['Fecha'] == pd.to_datetime(-1)).sum()
    f_hora_paro = (sub_paros['Hora de Paro'] == pd.Timedelta(-1)).sum()
    f_fecha_reinicio = (sub_paros['Fecha Reinicio'] == pd.to_datetime(-1)).sum()
    f_hora_reinicio = (sub_paros['Hora Reinicio'] == pd.Timedelta(-1)).sum()
    f_interruption = sub_paros['Interruption ID'].isna().sum()
    f_interlock = sub_paros['Interlock'].isna().sum()
    f_motivo = ((sub_paros['Motivo del paro'].isna()) & (sub_paros['Interlock'] == 'Process -OFF -Button')).sum()
    f_tiempo = (sub_paros['Tiempo de Paro'] <= pd.Timedelta(0)).sum()
    
    # Total de faltas por operador
    total_faltas_paros = (f_fecha + f_hora_paro + f_fecha_reinicio + f_hora_reinicio + 
                          f_interruption + f_interlock + f_motivo + f_tiempo)
    
    resumen_operadores_paros.append({
        "Mes": mes_evaluacion,
        "Operador": operador,
        "Total Registros Paros": len(sub_paros),
        "Total Faltas": total_faltas_paros,
        "Fecha": f_fecha,
        "Hora de Paro": f_hora_paro,
        "Fecha Reinicio": f_fecha_reinicio,
        "Hora Reinicio": f_hora_reinicio,
        "Interruption ID": f_interruption,
        "Interlock": f_interlock,
        "Motivo del paro": f_motivo,
        "Tiempo de Paro": f_tiempo
    })

FaltasParosPorOperador = pd.DataFrame(resumen_operadores_paros)
# FIN AUDITORIA PAROS
# INICIO AUDITORIA MASTER
# Resumen global
Master_Audit = Master[Master['Fecha de Proceso'].between(fecha_inicio, fecha_fin)]
OperadoresMaster=Master_Audit['Operador'].unique()
print(OperadoresMaster)
FaltasRegistroMaster= {
    "Mes": mes_evaluacion,
    "Fecha de Proceso":len(Master_Audit[Master_Audit['Fecha de Proceso']==pd.to_datetime(0)]),
    "Operador":len(Master_Audit[Master_Audit['Operador']=='Sin registro']),
    "Estatus":len(Master_Audit[Master_Audit['Estatus']=='Sin estatus']),
    "P. Run":len(Master_Audit[Master_Audit['P. Run']==-1]),
    "TIN":len(Master_Audit[Master_Audit['TIN']=='Sin TIN']),
    "Folio TIN":len(Master_Audit[Master_Audit['Folio TIN']==0]),
    "Folio Logistica":len(Master_Audit[Master_Audit['Folio Logistica']==0]),
    "Folio calidad":len(Master_Audit[Master_Audit['Folio calidad']==-1]),
    "Cliente":len(Master_Audit[Master_Audit['Cliente']=='Sin Cliente']),
    "Codigo cliente":len(Master_Audit[Master_Audit['Codigo cliente']=='Sin Codigo Cliente']),
    "Producto":len(Master_Audit[Master_Audit['Producto']=='Sin Producto']),
    "Configuracion (Fito) prod":len(Master_Audit[Master_Audit['Configuracion (Fito) prod']=='Error registro']),
    # "No de configuracion":len(Master_Audit[
    #     (Master_Audit['No de configuracion']==0) & 
    #     (Master_Audit['Tipo de servicio']!='Fitosanitario 150 Gy') &
    #     (Master_Audit['Tipo de servicio']!='Fitosanitario 400 Gy')
    #     ]
    #     ),
    "Tipo de servicio":len(Master_Audit[Master_Audit['Tipo de servicio']=='Sin Tipo de Servicio']),
    "Dosis de proceso solicitada (kGy)":len(Master_Audit[Master_Audit['Dosis de proceso solicitada (kGy)']==0]),
    "Numero de tarima de TIN":len(Master_Audit[Master_Audit['Numero de tarima de TIN']==0]),
    "Carrier":len(Master_Audit[Master_Audit['Carrier']==0]),
    "Etiqueta sistema":len(Master_Audit[Master_Audit['Etiqueta sistema']=='Sin etiqueta sistema']),
    "Etiqueta interna":len(Master_Audit[Master_Audit['Etiqueta interna']=='Sin etiqueta interna']),
    "Tarimas por TIN":len(Master_Audit[Master_Audit['Tarimas por TIN']==0]),
    "Tratamiento":len(Master_Audit[Master_Audit['Tratamiento']=='Sin Tratamiento']),
    "Dosis proceso":len(Master_Audit[Master_Audit['Dosis proceso']==0]),
    "N° Lados":len(Master_Audit[Master_Audit['N° Lados']==0]),
    "N° pases":len(Master_Audit[Master_Audit['N° pases']==0]),
    "kGy por pase":len(Master_Audit[Master_Audit['kGy por pase']==0]),
    "Factor K":len(Master_Audit[Master_Audit['Factor K']==0]),
    "Corriente (A)":len(Master_Audit[Master_Audit['Corriente (A)']==0]),
    "Velocidad UBC":len(Master_Audit[Master_Audit['Velocidad UBC']==0]),
    "Inicio carga conveyor":len(Master_Audit[Master_Audit['Inicio carga conveyor']==pd.to_datetime(0)]),
    "Fin descarga conveyor":len(Master_Audit[Master_Audit['Fin descarga conveyor']==pd.to_datetime(0)]),
    "Tiempo proceso":len(Master_Audit[Master_Audit['Tiempo proceso']==pd.Timedelta(seconds=0)]),
    "Registro":len(Master_Audit[Master_Audit['Registro']=='Sin Registro'])
}
FaltasRegistroMaster["Total Faltas"] = sum(v for k, v in FaltasRegistroMaster.items() if k != "Mes")
FaltasRegistroMasterTotal = pd.DataFrame([FaltasRegistroMaster])
# Resumen por operador
resumen_operadores_master = []

for operador in OperadoresMaster:
    if pd.isna(operador):
        continue
    
    sub_master = Master_Audit[Master_Audit['Operador'] == operador]
    
    # Conteo de faltas por variable según reglas de imputation previas
    f_fecha = (sub_master['Fecha de Proceso'] == pd.to_datetime(0)).sum()
    f_operador = (sub_master['Operador'] == 'Sin registro').sum()
    f_estatus = (sub_master['Estatus'] == 'Sin estatus').sum()
    f_prun = (sub_master['P. Run'] == -1).sum()
    f_tin = (sub_master['TIN'] == 'Sin TIN').sum()
    f_folio_tin = (sub_master['Folio TIN'] == 0).sum()
    f_folio_logistica = (sub_master['Folio Logistica'] == 0).sum()
    f_folio_calidad = (sub_master['Folio calidad'] == -1).sum()
    f_cliente = (sub_master['Cliente'] == 'Sin Cliente').sum()
    f_codigo_cliente = (sub_master['Codigo cliente'] == 'Sin Codigo Cliente').sum()
    f_producto = (sub_master['Producto'] == 'Sin Producto').sum()
    f_config_fito = (sub_master['Configuracion (Fito) prod'] == 'Error registro').sum()
    f_tipo_servicio = (sub_master['Tipo de servicio'] == 'Sin Tipo de Servicio').sum()
    f_dosis_solicitada = (sub_master['Dosis de proceso solicitada (kGy)'] == 0).sum()
    f_num_tarima_tin = (sub_master['Numero de tarima de TIN'] == 0).sum()
    f_carrier = (sub_master['Carrier'] == 0).sum()
    f_etiqueta_kt = (sub_master['Etiqueta sistema'] == 'Sin etiqueta sistema').sum()
    f_etiqueta_eb = (sub_master['Etiqueta interna'] == 'Sin etiqueta interna').sum()
    f_tarimas_tin = (sub_master['Tarimas por TIN'] == 0).sum()
    f_tratamiento = (sub_master['Tratamiento'] == 'Sin Tratamiento').sum()
    f_dosis_proceso = (sub_master['Dosis proceso'] == 0).sum()
    f_lados = (sub_master['N° Lados'] == 0).sum()
    f_pases = (sub_master['N° pases'] == 0).sum()
    f_kgy_pase = (sub_master['kGy por pase'] == 0).sum()
    f_factor_k = (sub_master['Factor K'] == 0).sum()
    f_corriente = (sub_master['Corriente (A)'] == 0).sum()
    f_velocidad = (sub_master['Velocidad UBC'] == 0).sum()
    f_inicio_carga = (sub_master['Inicio carga conveyor'] == pd.to_datetime(0)).sum()
    f_fin_descarga = (sub_master['Fin descarga conveyor'] == pd.to_datetime(0)).sum()
    f_tiempo_proceso = (sub_master['Tiempo proceso'] == pd.Timedelta(seconds=0)).sum()
    f_registro = (sub_master['Registro'] == 'Sin Registro').sum()
    
    # Suma total de campos omitidos/erróneos
    total_faltas_master = (
        f_fecha + f_operador + f_estatus + f_prun + f_tin + f_folio_tin + 
        f_folio_logistica + f_folio_calidad + f_cliente + f_codigo_cliente + 
        f_producto + f_config_fito + f_tipo_servicio + f_dosis_solicitada + 
        f_num_tarima_tin + f_carrier + f_etiqueta_kt + f_etiqueta_eb + 
        f_tarimas_tin + f_tratamiento + f_dosis_proceso + f_lados + f_pases + 
        f_kgy_pase + f_factor_k + f_corriente + f_velocidad + f_inicio_carga + 
        f_fin_descarga + f_tiempo_proceso + f_registro
    )
    
    resumen_operadores_master.append({
        "Mes": mes_evaluacion,
        "Operador": operador,
        "Total Registros Master": len(sub_master),
        "Total Faltas": total_faltas_master,
        "Fecha de Proceso": f_fecha,
        "Estatus": f_estatus,
        "P. Run": f_prun,
        "TIN": f_tin,
        "Folio TIN": f_folio_tin,
        "Folio Logistica": f_folio_logistica,
        "Folio calidad": f_folio_calidad,
        "Cliente": f_cliente,
        "Codigo cliente": f_codigo_cliente,
        "Producto": f_producto,
        "Configuracion (Fito) prod": f_config_fito,
        "Tipo de servicio": f_tipo_servicio,
        "Dosis solicitada": f_dosis_solicitada,
        "Numero de tarima": f_num_tarima_tin,
        "Carrier": f_carrier,
        "Etiqueta sistema": f_etiqueta_kt,
        "Etiqueta interna": f_etiqueta_eb,
        "Tarimas por TIN": f_tarimas_tin,
        "Tratamiento": f_tratamiento,
        "Dosis proceso": f_dosis_proceso,
        "N° Lados": f_lados,
        "N° pases": f_pases,
        "kGy por pase": f_kgy_pase,
        "Factor K": f_factor_k,
        "Corriente": f_corriente,
        "Velocidad UBC": f_velocidad,
        "Inicio carga": f_inicio_carga,
        "Fin descarga": f_fin_descarga,
        "Tiempo proceso": f_tiempo_proceso,
        "Registro": f_registro
    })

FaltasMasterPorOperador = pd.DataFrame(resumen_operadores_master)
# FIN AUDITORIA MASTER
import os
from pathlib import Path
# Funcion para duracion a segundos
def convertir_duraciones_a_segundos(df):
    df = df.copy()

    for columna in df.columns:
        if pd.api.types.is_timedelta64_dtype(df[columna]):
            df[columna] = (
                df[columna]
                .dt.total_seconds()
                .round()
                .astype("Int64")
            )

    return df
# INICIO MENÚ DE EXPORTACIÓN
print("\n" + "="*40)
print("     MENÚ DE EXPORTACIÓN DE DATOS")
print("="*40)
print("1. NO guardar resultados")
print("2. Guardar en una carpeta/nombre personalizado")
print("3. Guardar en el histórico SIN sobreescribir (anexar)")
print("="*40)

opcion = input("Selecciona una opción (1, 2 o 3): ").strip()

# Consolidación de Auditorías
f_oee = FaltasPorOperador.copy()
f_oee.insert(0, 'Modulo', 'Proceso_OEE')

f_paros = FaltasParosPorOperador.copy()
f_paros.insert(0, 'Modulo', 'Paros')

f_master = FaltasMasterPorOperador.copy()
f_master.insert(0, 'Modulo', 'Master')

Historico_Auditoria = pd.concat([f_oee, f_paros, f_master], ignore_index=True).fillna(0)

# Diccionario de tablas a exportar
tablas_historicas = {
    'Historico_Proceso.csv': convertir_duraciones_a_segundos(resultado),
    'Historico_Paros.csv': convertir_duraciones_a_segundos(Paros),
    'Historico_BeamON.csv': convertir_duraciones_a_segundos(BeamON),
    'Historico_Master.csv': convertir_duraciones_a_segundos(Master),
    'Historico_Auditoria.csv': convertir_duraciones_a_segundos(Historico_Auditoria),
    'KPI_Mensual.csv': convertir_duraciones_a_segundos(KPI_Mes),
    'Tiempos_por_Servicio.csv': convertir_duraciones_a_segundos(TiemposPorServicio),
    'Tarimas_por_Servicio.csv': convertir_duraciones_a_segundos(TarimasPorServicio)
}

if opcion == '1':
    print("\nProceso finalizado sin guardar resultados.")

elif opcion == '2':
    # Permite al usuario definir el nombre de la carpeta de destino
    nombre_destino = input("\nIngresa el nombre de la carpeta personalizada (ej. Reporte_Agosto_2026): ").strip()
    if not nombre_destino:
        nombre_destino = "PowerBI_Data_Custom"
        
    nombre_destino = OUTPUT_DIR / nombre_destino
    os.makedirs(nombre_destino, exist_ok=True)
    
    print(f"\nGuardando archivos en '{nombre_destino}'...")
    for nombre_archivo, df in tablas_historicas.items():
        ruta = os.path.join(nombre_destino, nombre_archivo)
        df.to_csv(ruta, index=False, encoding='utf-8-sig')
        print(f"  ✓ Archivo guardado: {ruta}")
        
    print(f"\n¡Archivos guardados con éxito en la carpeta '{nombre_destino}'!")

elif opcion == '3':
    # Anexa filas a los CSV existentes dentro de PowerBI_Data
    carpeta_destino = OUTPUT_DIR / 'PowerBI_Data'
    os.makedirs(carpeta_destino, exist_ok=True)
    
    print(f"\nAnexando datos en '{carpeta_destino}'...")
    for nombre_archivo, df in tablas_historicas.items():
        ruta = os.path.join(carpeta_destino, nombre_archivo)
        archivo_existe = os.path.exists(ruta)
        
        # mode='a' anexa los datos; header=False evita duplicar encabezados
        df.to_csv(
            ruta, 
            mode='a', 
            index=False, 
            header=not archivo_existe, 
            encoding='utf-8-sig'
        )
        
        if archivo_existe:
            print(f"  ✓ Registros anexados en: {ruta}")
        else:
            print(f"  ✓ Archivo creado por primera vez: {ruta}")
            
    print("\n¡Datos acumulados exitosamente en el registro histórico!")

else:
    print("\nOpción no válida. El programa finalizó sin guardar cambios.")
# FIN MENÚ DE EXPORTACIÓN
# REPORTE #

# ============================================================
# CONFIGURACIÓN DEL REPORTE PDF
# ============================================================

LOGO_PATH = ASSETS_DIR / "logo.png"  # optional
PDF_PATH = OUTPUT_DIR / "Reporte.pdf"
MODO = "PDF"  # Opciones: "PDF" o "IMPRESORA"


def df_a_tabla(df, ancho_disponible):
    """Convierte un DataFrame de pandas en una tabla formateada para ReportLab con ajuste automático de ancho."""
    num_cols = len(df.columns)
    
    # Calcular padding dinámico según la cantidad de columnas
    if num_cols > 20:
        padding_h = 1
        font_sz = 4.5
    elif num_cols > 10:
        padding_h = 2
        font_sz = 6
    else:
        padding_h = 4
        font_sz = 7

    estilos = getSampleStyleSheet()
    estilo_encabezado = ParagraphStyle(
        'HeaderStyle', parent=estilos['Normal'], fontName='Helvetica-Bold',
        textColor=colors.whitesmoke, fontSize=font_sz, leading=font_sz + 1, alignment=1
    )
    estilo_celda = ParagraphStyle(
        'CeldaStyle', parent=estilos['Normal'], fontName='Helvetica',
        fontSize=font_sz, leading=font_sz + 1, alignment=1
    )

    datos = []
    headers = [Paragraph(str(col), estilo_encabezado) for col in df.columns]
    datos.append(headers)

    for row in df.itertuples(index=False):
        fila = [Paragraph(str(val), estilo_celda) for val in row]
        datos.append(fila)

    # Ancho uniforme por columna para no sobrepasar el frame
    col_width = ancho_disponible / float(num_cols)
    col_widths = [col_width] * num_cols

    tabla = Table(datos, colWidths=col_widths, hAlign='LEFT')
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#D3D3D3')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), padding_h),
        ('RIGHTPADDING', (0, 0), (-1, -1), padding_h),
    ]))
    return tabla


def generar_pdf_reporte(f_registro_total, f_paros_total, f_master_total):
    """Crea y guarda el documento PDF con los DataFrames consolidados."""
    ANCHO_HOJA, ALTO_HOJA = letter
    MARGEN = 1.0 * cm
    LOGO_ALTO = 2.0 * cm

    c = canvas.Canvas(str(PDF_PATH), pagesize=letter)

    # Logo optional: public repo works even when assets/logo.png is absent.
    if LOGO_PATH.exists():
        logo = ImageReader(str(LOGO_PATH))
        ancho_orig, alto_orig = logo.getSize()
        logo_ancho = LOGO_ALTO * (ancho_orig / alto_orig)
        y_logo = ALTO_HOJA - MARGEN - LOGO_ALTO
        c.drawImage(
            str(LOGO_PATH), MARGEN, y_logo,
            width=logo_ancho, height=LOGO_ALTO,
            preserveAspectRatio=True, mask="auto"
        )
        contenido_y = y_logo - 0.3 * cm
    else:
        contenido_y = ALTO_HOJA - MARGEN
    ancho_disponible = ANCHO_HOJA - (2 * MARGEN)
    alto_disponible = contenido_y - MARGEN

    frame = Frame(
        MARGEN, MARGEN, ancho_disponible, alto_disponible,
        id='FrameContenido', topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0
    )

    estilos = getSampleStyleSheet()
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo', parent=estilos['Heading2'], fontName='Helvetica-Bold',
        fontSize=9, textColor=colors.HexColor('#1F4E78'), spaceAfter=2
    )

    elementos = []
    dfs = [
        ("Auditoría OEE - Faltas Registro Total", f_registro_total),
        ("Auditoría Paros - Faltas Registro Total", f_paros_total),
        ("Auditoría Master - Faltas Registro Total", f_master_total),
    ]

    for titulo, df in dfs:
        if not df.empty:
            elementos.append(Paragraph(f"<b>{titulo}</b>", estilo_subtitulo))
            elementos.append(df_a_tabla(df, ancho_disponible))
            elementos.append(Spacer(1, 0.3 * cm))

    frame.addFromList(elementos, c)
    c.save()
    print(f"✓ PDF generado exitosamente en: {PDF_PATH}")

def imprimir_pdf():
    """Envía el PDF generado a la impresora del sistema."""
    if platform.system() == "Windows":
        os.startfile(str(PDF_PATH), "print")
    elif platform.system() in ["Linux", "Darwin"]:
        subprocess.run(["lp", str(PDF_PATH)], check=True)


# ============================================================
# EJECUCIÓN DEL REPORTE PDF
# ============================================================

# Generar DataFrames consolidados para las tablas del PDF
FaltasRegistroTotal = pd.DataFrame([FaltasPorOperador.sum(numeric_only=True).to_dict()])
FaltasRegistroTotal['Mes'] = mes_evaluacion

FaltasRegistroParosTotal = pd.DataFrame([FaltasParosPorOperador.sum(numeric_only=True).to_dict()])
FaltasRegistroParosTotal['Mes'] = mes_evaluacion

FaltasRegistroMasterTotal = pd.DataFrame([FaltasMasterPorOperador.sum(numeric_only=True).to_dict()])
FaltasRegistroMasterTotal['Mes'] = mes_evaluacion

# Llamada para crear el archivo PDF
generar_pdf_reporte(FaltasRegistroTotal, FaltasRegistroParosTotal, FaltasRegistroMasterTotal)

# Enviar a la impresora en caso de que MODO esté configurado en "IMPRESORA"
if MODO.upper() == "IMPRESORA":
    imprimir_pdf()

# ============================================================
# GENERACIÓN DE REPORTES INDIVIDUALES POR OPERADOR
# ============================================================

def crear_tabla_firmas(ancho_disponible):
    """Crea un bloque de firmas alineado con dos líneas y sus cargos."""
    datos_firma = [
        ["-------------------------------------------------", "", "-------------------------------------------------"],
        ["Operador", "", "Gerente de operaciones"]
    ]
    
    # Ancho: 40% firma 1, 20% espacio central, 40% firma 2
    col_widths = [ancho_disponible * 0.42, ancho_disponible * 0.16, ancho_disponible * 0.42]
    
    tabla_firmas = Table(datos_firma, colWidths=col_widths, hAlign='CENTER')
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))
    return tabla_firmas


def generar_reportes_individuales(df_oee, df_paros, df_master):
    """Genera un archivo PDF individual para cada operador encontrado en los DataFrames."""
    
    # Obtener el universo único de operadores en los 3 dataframes
    ops_oee = set(df_oee['Operador'].dropna().unique()) if 'Operador' in df_oee.columns else set()
    ops_paros = set(df_paros['Operador'].dropna().unique()) if 'Operador' in df_paros.columns else set()
    ops_master = set(df_master['Operador'].dropna().unique()) if 'Operador' in df_master.columns else set()
    
    operadores_unicos = sorted(list(ops_oee.union(ops_paros).union(ops_master)))

    if not operadores_unicos:
        print("⚠ No se encontraron operadores para generar reportes individuales.")
        return

    # Carpeta donde se guardarán los PDFs individuales
    carpeta_salida = OUTPUT_DIR / 'Reportes_Operadores'
    os.makedirs(carpeta_salida, exist_ok=True)

    ANCHO_HOJA, ALTO_HOJA = letter
    MARGEN = 1.0 * cm
    LOGO_ALTO = 1.8 * cm

    estilos = getSampleStyleSheet()
    estilo_titulo_op = ParagraphStyle(
        'TituloOperador', parent=estilos['Heading1'], fontName='Helvetica-Bold',
        fontSize=12, textColor=colors.HexColor('#1F4E78'), spaceAfter=4
    )
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo', parent=estilos['Heading2'], fontName='Helvetica-Bold',
        fontSize=8.5, textColor=colors.HexColor('#1F4E78'), spaceAfter=2
    )

    print(f"\nGenerando {len(operadores_unicos)} reportes individuales por operador...")

    for operador in operadores_unicos:
        # Sanitizar nombre para el archivo
        nombre_archivo_clean = "".join(c for c in str(operador) if c.isalnum() or c in (' ', '_', '-')).strip()
        ruta_pdf = os.path.join(carpeta_salida, f"Reporte_Operador_{nombre_archivo_clean}.pdf")

        c = canvas.Canvas(str(ruta_pdf), pagesize=letter)

        # 1. Header / Logo
        if os.path.exists(LOGO_PATH):
            logo = ImageReader(str(LOGO_PATH))
            ancho_orig, alto_orig = logo.getSize()
            logo_ancho = LOGO_ALTO * (ancho_orig / alto_orig)
            y_logo = ALTO_HOJA - MARGEN - LOGO_ALTO
            c.drawImage(str(LOGO_PATH), MARGEN, y_logo, width=logo_ancho, height=LOGO_ALTO, preserveAspectRatio=True, mask="auto")
            contenido_y = y_logo - 0.3 * cm
        else:
            contenido_y = ALTO_HOJA - MARGEN

        ancho_disponible = ANCHO_HOJA - (2 * MARGEN)
        alto_disponible = contenido_y - MARGEN

        frame = Frame(
            MARGEN, MARGEN, ancho_disponible, alto_disponible,
            id='FrameOperador', topPadding=0, bottomPadding=0, leftPadding=0, rightPadding=0
        )

        elementos = []
        elementos.append(Paragraph(f"<b>Reporte de Auditoría de Registro - Operador: {operador}</b>", estilo_titulo_op))
        elementos.append(Spacer(1, 0.2 * cm))

        # 2. Filtrar DataFrames por operador
        sub_oee = df_oee[df_oee['Operador'] == operador] if 'Operador' in df_oee.columns else pd.DataFrame()
        sub_paros = df_paros[df_paros['Operador'] == operador] if 'Operador' in df_paros.columns else pd.DataFrame()
        sub_master = df_master[df_master['Operador'] == operador] if 'Operador' in df_master.columns else pd.DataFrame()

        dfs = [
            ("Faltas por Registro - Proceso OEE", sub_oee),
            ("Faltas por Registro - Paros", sub_paros),
            ("Faltas por Registro - Master", sub_master),
        ]

        # 3. Agregar tablas al reporte
        for titulo, df in dfs:
            if not df.empty:
                elementos.append(Paragraph(f"<b>{titulo}</b>", estilo_subtitulo))
                elementos.append(df_a_tabla(df, ancho_disponible))
                elementos.append(Spacer(1, 0.3 * cm))

        # 4. Bloque de Firmas al final
        elementos.append(Spacer(1, 1.2 * cm))
        elementos.append(crear_tabla_firmas(ancho_disponible))

        # Generar PDF
        frame.addFromList(elementos, c)
        c.save()
        print(f"  ✓ Generado: Reporte_Operador_{nombre_archivo_clean}.pdf")

    print(f"\n¡Todos los reportes por operador fueron guardados en:\n{carpeta_salida}")


# ============================================================
# LLAMADA DE EJECUCIÓN (Agregar al final de tu código)
# ============================================================

generar_reportes_individuales(
    df_oee=FaltasPorOperador,
    df_paros=FaltasParosPorOperador,
    df_master=FaltasMasterPorOperador
)
