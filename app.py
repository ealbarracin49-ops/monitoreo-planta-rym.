import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient
import plotly.express as px

# 1. Credenciales extraídas de tus imágenes (Imagen 2)
TOKEN = "DkpL6zznGwMgO5RwAhPXj2ZbZ3w2qsvWVTWotXivS3KKRZe56F5XsywwnK7l3_76FWpj2ZVWOeN1RQVlTydEWQ=="
ORG = "miguelcmo"
URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
BUCKET = "iot_telemetry_data"

# Configuración de la página de Streamlit
st.set_page_config(page_title="RYM Manufacturing", layout="wide")
st.title("📊 Digitalización de Planta: RYM Manufacturing")
st.markdown("---")

# 2. Función para conectar y consultar InfluxDB
def get_data(query):
    try:
        client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
        # Convertimos el resultado directamente a un DataFrame de Pandas
        df = client.query_api().query_data_frame(query)
        client.close()
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# 3. Consultas Flux (Basadas en los ejemplos de tus imágenes 3, 4 y 5)
query_environment = f'''
from(bucket: "{BUCKET}")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "environment")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

query_vibration = f'''
from(bucket: "{BUCKET}")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "mpu6050")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

# 4. Interfaz del Tablero
col1, col2 = st.columns(2)

# Sección de Temperatura y Humedad (Sensor DHT22)
with col1:
    st.header("🌡️ Ambiente (DHT22)")
    df_env = get_data(query_environment)
    if df_env is not None and not df_env.empty:
        # Mostrar métricas actuales
        last_temp = df_env['temperature'].iloc[-1]
        last_hum = df_env['humidity'].iloc[-1]
        
        m1, m2 = st.columns(2)
        m1.metric("Temperatura", f"{last_temp:.2f} °C")
        m2.metric("Humedad", f"{last_hum:.2f} %")
        
        # Gráfico histórico
        fig_temp = px.line(df_env, x="_time", y=["temperature", "humidity"], title="Histórico de Ambiente")
        st.plotly_chart(fig_temp, use_container_width=True)

# Sección de Vibración (Sensor MPU6050)
with col2:
    st.header("🫨 Vibración (MPU6050)")
    df_vib = get_data(query_vibration)
    if df_vib is not None and not df_vib.empty:
        # Calcular magnitud (Punto 7 de la Imagen 5)
        df_vib['magnitud'] = (df_vib['accel_x']**2 + df_vib['accel_y']**2 + df_vib['accel_z']**2)**0.5
        
        last_vib = df_vib['magnitud'].iloc[-1]
        st.metric("Magnitud de Vibración", f"{last_vib:.4f} g")
        
        # Gráfico de aceleración ejes X, Y, Z
        fig_vib = px.line(df_vib, x="_time", y=["accel_x", "accel_y", "accel_z"], title="Ejes de Aceleración")
        st.plotly_chart(fig_vib, use_container_width=True)
# --- MÉTODO ANALÍTICO ADICIONAL (Ambiente) ---
if df_env is not None and not df_env.empty:
    st.markdown("---")
    st.subheader("📊 Análisis Estadístico de Ambiente")
    
    # Promedio Móvil para suavizar temperatura
    df_env['temp_smooth'] = df_env['temperature'].rolling(window=5).mean()
    
    # Métricas en columnas
    m1, m2, m3 = st.columns(3)
    curr_temp = df_env['temperature'].iloc[-1]
    avg_temp = df_env['temperature'].mean()
    max_temp = df_env['temperature'].max()
    
    m1.metric("Temp. Actual", f"{curr_temp:.2f} °C")
    m2.metric("Promedio", f"{avg_temp:.2f} °C")
    m3.metric("Máxima", f"{max_temp:.2f} °C")

    # Gráfico del promedio móvil
    fig_smooth = px.line(df_env, x="_time", y="temp_smooth", title="Tendencia de Temperatura (Promedio Móvil)")
    st.plotly_chart(fig_smooth, use_container_width=True)
# 5. Detección de Anomalías (Requerimiento técnico)
st.markdown("---")
st.header("🚨 Alertas y Análisis")
if df_vib is not None and not df_vib.empty:
    umbral = 1.5  # Ejemplo básico de la imagen 4
    picos = df_vib[df_vib['accel_x'].abs() > umbral]
    if not picos.empty:
        st.warning(f"Se detectaron {len(picos)} picos de vibración por encima de {umbral}")
    else:
        st.success("Operación normal: Sin vibraciones anómalas.")
