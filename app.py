import streamlit as st
import pandas as pd
from influxdb_client import InfluxDBClient
import plotly.express as px

# =========================
# CONFIGURACIÓN INFLUXDB
# =========================
URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "EJwrNIOrygCc52EJm-H0NVuHwUapDRTUdEiJ4rCwz3H_cwi_APdfpViMMc9bmzfzcfg9dub8uibJw0fpekAIVQ=="
ORG = "miguelcmo"
BUCKET = "iot_telemetry_data"

st.set_page_config(page_title="IoT Dashboard", layout="wide")
st.title("📡 IoT Telemetry Dashboard")

st.sidebar.header("⏱️ Configuración de Tiempo")
start_time = st.sidebar.text_input("Start", value="-1h")
stop_time = st.sidebar.text_input("Stop", value="now()")

client = InfluxDBClient(url=URL, token=TOKEN, org=ORG)
query_api = client.query_api()

query = f'from(bucket: "{BUCKET}") |> range(start: {start_time}, stop: {stop_time})'

try:
    tables = query_api.query_data_frame(query)
    df = pd.concat(tables) if isinstance(tables, list) else tables

    if df.empty:
        st.warning("No hay datos disponibles.")
    else:
        # Limpieza de datos
        columns_to_remove = ["result", "table", "_start", "_stop"]
        for col in columns_to_remove:
            if col in df.columns:
                df = df.drop(columns=[col])
        if "_time" in df.columns:
            df["_time"] = pd.to_datetime(df["_time"])

        # MÉTRICAS
        st.subheader("📊 Métricas Estadísticas")
        temp_df = df[df["_field"] == "temperature"]
        hum_df = df[df["_field"] == "humidity"]

        col1, col2 = st.columns(2)
        if not temp_df.empty:
            col1.metric("🌡️ Temp Promedio", f"{round(temp_df['_value'].mean(), 2)} °C")
        if not hum_df.empty:
            col2.metric("💧 Humedad Promedio", f"{round(hum_df['_value'].mean(), 2)} %")

        # GRÁFICAS LINEALES
        st.subheader("📈 Historial de Sensores")
        st.plotly_chart(px.line(temp_df, x="_time", y="_value", title="Temperatura"), use_container_width=True)
        st.plotly_chart(px.line(hum_df, x="_time", y="_value", title="Humedad"), use_container_width=True)

        # ==========================================
        # NUEVA GRÁFICA DE CORRELACIÓN (LO QUE PIDIÓ EL PROFE)
        # ==========================================
        st.subheader("🔍 Análisis de Correlación: Vibración vs Temperatura")
        
        # Unimos datos de temperatura y acelerómetro en una sola tabla
        df_pivot = df[df["_field"].isin(["temperature", "accel_x"])].pivot(
            index="_time", columns="_field", values="_value"
        ).dropna()

        if not df_pivot.empty:
            fig_scatter = px.scatter(
                df_pivot, x="temperature", y="accel_x", 
                trendline="ols", title="¿Afecta el calor a la vibración?",
                labels={"temperature": "Temp (°C)", "accel_x": "Vibración (g)"}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.info("💡 Esta gráfica analiza si el calor causa fallas mecánicas.")
        else:
            st.warning("Faltan datos para la correlación.")

except Exception as e:
    st.error(f"Error: {e}")
