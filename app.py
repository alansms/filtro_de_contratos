import streamlit as st
import pandas as pd
import csv
import io
import time
import re
from datetime import datetime
from dateutil import parser  # Parsing robusto de datas

st.set_page_config(page_title="Filtro de Contratos", layout="wide")

# ================== CSS ==================
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #1a1a1a;
    padding: 2rem 1rem;
}
[data-testid="stSidebar"] * {
    color: white;
    font-family: "Segoe UI", sans-serif;
}

[data-testid="stFileUploadDropzone"] {
    background-color: #2e2e2e !important;
    border: 2px dashed #555 !important;
    border-radius: 8px !important;
    color: #fff !important;
    padding: 20px !important;
    font-size: 1rem;
    text-align: center;
    width: 250px;
    position: absolute;
    top: 120px;
    right: 20px;
}

.stButton > button {
    background-color: #ff0000;
    color: #fff;
    font-weight: 600;
    padding: 0.6rem 1.2rem;
    border: none;
    border-radius: 8px;
    margin-top: 0.5rem;
    cursor: pointer;
}
.stButton > button:disabled {
    background-color: #888 !important;
}

h1 {
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ================== SIDEBAR ==================
with st.sidebar:
    st.image("logo_fiap.jpg", use_column_width=True)
    st.title("Filtro de Contratos")

    data_inicio = st.date_input("Data inicial", datetime(2025, 1, 1).date())
    data_fim = st.date_input("Data final", datetime(2025, 12, 31).date())
    num_preview = st.slider("Linhas para visualizar", 1, 100, 10)

    processar = st.button("Processar")
    debug = st.checkbox("Mostrar logs de debug")

# Uploader
uploaded_file = st.file_uploader("Arraste seu CSV ou clique para escolher", type=["csv"], key="upload")

st.title("Resultados do Filtro")


# ================== FUNÇÕES ==================
def is_valid_cpf(cpf):
    return re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf)


def is_valid_rg(rg):
    return re.fullmatch(r'\d{2}\.\d{3}\.\d{3}-\d', rg)


def parse_date(date_str, debug_logs):
    try:
        # Interpreta datas no formato dd/mm/yyyy
        parsed = parser.parse(date_str, dayfirst=True)
        if debug and len(debug_logs) < 15:
            debug_logs.append(f"Converted '{date_str}' to {parsed}")
        return parsed
    except Exception as e:
        if debug and len(debug_logs) < 15:
            debug_logs.append(f"Error converting '{date_str}': {e}")
        return None


# 1) Filtragem por sobreposição (PARCIAL):
#    O contrato aparece se houver qualquer interseção com o período.
def is_overlap(start_contract, end_contract, start_period, end_period):
    return start_contract <= end_period and start_period <= end_contract


# 2) Filtragem por período totalmente contido (COMPLETO):
#    O contrato só aparece se estiver totalmente dentro do período selecionado.
def is_fully_within_period(start_contract, end_contract, start_period, end_period):
    return start_contract >= start_period and end_contract <= end_period


def process_csv(file_bytes, period_start_dt, period_end_dt, debug):
    start_time = time.time()
    registros_lidos = 0
    registros_filtrados = 0
    filtered_rows = []
    debug_logs = []

    reader = csv.reader(io.StringIO(file_bytes.decode("utf-8")))
    for row in reader:
        registros_lidos += 1
        if len(row) != 6:
            if debug and len(debug_logs) < 15:
                debug_logs.append(f"Ignorado - Número de colunas inválido: {row}")
            continue

        nome, cpf, rg, endereco, data_ini_str, data_fim_str = row

        # Validação de CPF e RG
        if not (is_valid_cpf(cpf) and is_valid_rg(rg)):
            if debug and len(debug_logs) < 15:
                debug_logs.append(f"Ignorado - CPF/RG inválido: {cpf}, {rg}")
            continue

        # Conversão das datas
        data_ini = parse_date(data_ini_str, debug_logs)
        data_fim = parse_date(data_fim_str, debug_logs)
        if not (data_ini and data_fim):
            if debug and len(debug_logs) < 15:
                debug_logs.append(f"Ignorado - Data inválida: {data_ini_str}, {data_fim_str}")
            continue

        # ==============
        # Escolha a lógica desejada:
        #  A) Se você quiser qualquer sobreposição, use:
        #     if is_overlap(data_ini, data_fim, period_start_dt, period_end_dt):
        #
        #  B) Se quiser o contrato totalmente contido no período, use:
        #     if is_fully_within_period(data_ini, data_fim, period_start_dt, period_end_dt):
        # ==============

        # Lógica A) Sobreposição parcial:
        # if is_overlap(data_ini, data_fim, period_start_dt, period_end_dt):

        # Lógica B) Contrato totalmente dentro do período:
        if is_fully_within_period(data_ini, data_fim, period_start_dt, period_end_dt):
            filtered_rows.append(row)
            registros_filtrados += 1
            if debug and len(debug_logs) < 15:
                debug_logs.append(f"Incluído: {nome} ({data_ini_str} - {data_fim_str})")

    tempo = time.time() - start_time
    metrics = {
        "lidos": registros_lidos,
        "filtrados": registros_filtrados,
        "tempo": tempo
    }
    return filtered_rows, metrics, debug_logs


def convert_to_csv(data):
    output = io.StringIO()
    writer = csv.writer(output)
    for row in data:
        writer.writerow(row)
    return output.getvalue()


# ================== LÓGICA DE DATAS ==================
period_start = datetime.combine(data_inicio, datetime.min.time())
period_end = datetime.combine(data_fim, datetime.max.time())

# ================== PROCESSAMENTO ==================
if uploaded_file and processar:
    file_bytes = uploaded_file.getvalue()
    filtered_rows, metrics, debug_logs = process_csv(file_bytes, period_start, period_end, debug)

    # Logs de debug
    if debug:
        st.write("### Logs de Debug (máx. 15 mensagens):")
        for log in debug_logs:
            st.write(log)

    st.success("Processamento concluído.")
    st.write(f"Registros lidos: {metrics['lidos']}")
    st.write(f"Registros filtrados: {metrics['filtrados']}")
    st.write(f"Tempo de execução: {metrics['tempo']:.2f} segundos")

    if filtered_rows:
        df = pd.DataFrame(filtered_rows, columns=["Nome", "CPF", "RG", "Endereço", "Data Inicial", "Data Final"])
        st.dataframe(df.head(num_preview))
        csv_data = convert_to_csv(filtered_rows)
        st.download_button("Baixar CSV", csv_data, "contratos_filtrados.csv", "text/csv")
    else:
        st.warning("Nenhum registro encontrado para o período selecionado.")
else:
    st.info("Envie um arquivo e clique em 'Processar'.")
