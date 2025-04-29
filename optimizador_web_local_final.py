import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import matplotlib.pyplot as plt

st.set_page_config(page_title="Optimizador de Tiempo & Estrés", layout="wide")

# ------------------------ TÍTULO Y GUÍA ------------------------ #
st.title("🧠 Optimizador de Tiempo & Estrés")
st.subheader("Una solución inteligente para armonizar tus prioridades y reducir el estrés")

with st.expander("📚 Guía de Uso", expanded=True):
    st.markdown("""
    Esta aplicación te ayuda a asignar mejor tu tiempo diario, priorizar tus actividades importantes y reducir tu nivel de estrés.

    **¿Cómo usarla?**
    1. Ingresá tu nombre o email en el panel izquierdo.
    2. Cargá o editá tus actividades (Tema, Tiempo, Estrés, etc.).
    3. Guardá tus datos.
    4. Presioná "Optimizar mi tiempo".
    5. Visualizá tu plan optimizado y descargalo si querés.

    **Campos esperados:**
    - **Tema**: Nombre de la actividad.
    - **Tiempo**: Horas asignadas (0 a 24).
    - **Estrés**: Valor de 0 a 10.
    - **Obligatorio**: 1 si es obligatorio, 0 si es optativo.
    - **Peso**: Importancia (0 a 10).
    - **Mínimo**: Tiempo mínimo deseado (0 a 24).

    **Reglas clave:**
    - Los temas obligatorios reciben el tiempo exacto indicado.
    - El resto se optimiza sin superar las 24 horas en total.
    """)

# ------------------------ IDENTIFICACIÓN DE USUARIO ------------------------ #
st.sidebar.header("Identificación del Usuario")
usuario = st.sidebar.text_input("Ingresá tu nombre o email").strip().replace(" ", "_")

# Archivos personalizados por usuario
file_input2 = f"Input2_{usuario}.xlsx" if usuario else None
file_output = f"datos_optimizados_{usuario}.xlsx" if usuario else None

# ------------------------ CARGA DE DATOS ------------------------ #
if usuario and os.path.exists(file_input2):
    df = pd.read_excel(file_input2)
elif usuario:
    df = pd.DataFrame(columns=["Tema", "Tiempo", "Estrés", "Obligatorio", "Peso", "Mínimo"])
else:
    df = pd.DataFrame()

# ------------------------ EDICIÓN DE DATOS ------------------------ #
st.header("1. Cargar o editar tus actividades")
if usuario:
    df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    if st.button("Guardar Input2 actualizado"):
        errores = []

        try:
            for col in ["Tiempo", "Estrés", "Obligatorio", "Peso", "Mínimo"]:
                df_editado[col] = pd.to_numeric(df_editado[col], errors="coerce")

            if (df_editado["Tiempo"] > 24).any(): errores.append("Tiempo > 24")
            if (df_editado["Mínimo"] > 24).any(): errores.append("Mínimo > 24")
            if (df_editado["Estrés"] < 0).any() or (df_editado["Estrés"] > 10).any(): errores.append("Estrés fuera de rango")
            if (df_editado["Peso"] < 0).any() or (df_editado["Peso"] > 10).any(): errores.append("Peso fuera de rango")
            if not df_editado["Obligatorio"].isin([0, 1]).all(): errores.append("Obligatorio debe ser 0 o 1")
            if (df_editado["Mínimo"] > df_editado["Tiempo"]).any(): errores.append("Mínimo > Tiempo")
            if df_editado["Tiempo"].sum() > 24: errores.append("Suma de Tiempos > 24")

            if errores:
                st.error("Errores detectados:")
                for e in errores:
                    st.write("- ", e)
            else:
                df_editado.to_excel(file_input2, index=False)
                st.success("Archivo Input2 guardado correctamente.")

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df_editado.to_excel(writer, index=False)
                st.download_button("Descargar Input2", data=buffer.getvalue(), file_name=file_input2)

        except Exception as e:
            st.error(f"Error al guardar: {e}")
else:
    st.info("Ingresá tu nombre o email para comenzar.")

# ------------------------ OPTIMIZACIÓN ------------------------ #
st.header("2. Optimizar mi tiempo")
if usuario and st.button("Optimizar mi tiempo"):
    df = pd.read_excel(file_input2)
    n = len(df)
    tiempo_total = 24
    tiempo_disponible = tiempo_total
    tiempo_opt = np.zeros(n)
    obligatorio = df["Obligatorio"].values == 1
    tiempo = df["Tiempo"].values
    minimo = df["Mínimo"].values
    estres = df["Estrés"].values
    peso = df["Peso"].values

    # Paso 1: Asignar tiempo a temas obligatorios
    for i in range(n):
        if obligatorio[i]:
            tiempo_opt[i] = tiempo[i]
            tiempo_disponible -= tiempo[i]

    # Paso 2: Ordenar optativos por menor estrés y mayor peso
    opt_idx = [i for i in range(n) if not obligatorio[i]]
    opt_prioridad = sorted(opt_idx, key=lambda i: (estres[i], -peso[i]))

    for i in opt_prioridad:
        if tiempo_disponible >= tiempo[i]:
            tiempo_opt[i] = tiempo[i]
            tiempo_disponible -= tiempo[i]
        elif tiempo_disponible >= minimo[i]:
            tiempo_opt[i] = minimo[i]
            tiempo_disponible -= minimo[i]
        elif tiempo_disponible > 0:
            tiempo_opt[i] = tiempo_disponible
            tiempo_disponible = 0
        else:
            tiempo_opt[i] = 0

    df["Tiempo_Optimizado"] = tiempo_opt
    df.to_excel(file_output, index=False)
    st.success("Optimización completada y guardada.")

    buffer2 = io.BytesIO()
    with pd.ExcelWriter(buffer2, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    st.download_button("Descargar resultados optimizados", data=buffer2.getvalue(), file_name=file_output)

# ------------------------ VISUALIZACIÓN ------------------------ #
st.header("3. Visualizar resultados")
if usuario and os.path.exists(file_output):
    df_result = pd.read_excel(file_output)
    st.dataframe(df_result)

    st.subheader("Gráfico de tiempo optimizado")
    fig, ax = plt.subplots()
    ax.barh(df_result["Tema"], df_result["Tiempo_Optimizado"])
    ax.set_xlabel("Horas")
    ax.set_ylabel("Temas")
    ax.invert_yaxis()
    st.pyplot(fig)

# ------------------------ PIE LEGAL ------------------------ #
st.markdown("""
---
**Aviso de responsabilidad:** Esta aplicación se ofrece con fines informativos. No se garantiza la precisión de las recomendaciones. El uso es bajo responsabilidad del usuario.
""")