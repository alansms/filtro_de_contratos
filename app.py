import streamlit as st
import pandas as pd
import csv
import io
import time
import re
from datetime import datetime

st.set_page_config(page_title="Filtro de Contratos", layout="wide")

# CSS para personalizar o visual da sidebar e do file_uploader
st.markdown("""
<style>
/* Sidebar com fundo escuro e fonte branca */
[data-testid="stSidebar"] {
    background-color: #1a1a1a;
    padding: 2rem 1rem;
}
[data-testid="stSidebar"] * {
    color: white;
    font-family: "Segoe UI", sans-serif;
}

/* Personaliza a área do file uploader (que suporta drag and drop) */
[data-testid="stFileUploadDropzone"] {
    background-color: #2e2e2e !important;
    border: 2px dashed #555 !important;
    border-radius: 8px !important;
    color: #fff !important;
    padding: 20px !important;
    font-size: 1rem;
    text-align: center;
    width: 250px; /* Ajuste de largura */
    position: absolute; /* Para mover para o lado direito */
    top: 120px; /* Ajuste da posição na tela */
    right: 20px; /* Alinha ao lado direito */
}

/* Botão de processar em vermelho */
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

/* Ajuste do título principal */
h1 {
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# Layout da sidebar
with st.sidebar:
    st.image("logo_fiap.jpg", use_column_width=True)
    st.title("Filtro de Contratos")
    data_inicio = st.date_input("Data inicial", datetime(2025, 1, 1).date())
    data_fim = st.date_input("Data final", datetime(2025, 12, 31).date())
    num_preview = st.slider("Linhas para visualizar", 1, 100, 10)
    processar = st.button("Processar")

# Uploader de arquivo no lado direito da tela
uploaded_file = st.file_uploader("Arraste seu CSV ou clique para escolher", type=["csv"], key="upload")

st.title("Resultados do Filtro")

def is_valid_cpf(cpf):
    return re.fullmatch(r'\d{3}\.\d{3}\.\d{3}-\d{2}', cpf)

def is_valid_rg(rg):
    return re.fullmatch(r'\d{2}\.\d{3}\.\d{3}-\d', rg)

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except:
        return None

def is_overlap(start_contract, end_contract, start_period, end_period):
    return start_contract <= end_period and start_period <= end_contract

def process_csv(file_bytes, period_start_dt, period_end_dt):
    start_time = time.time()
    registros_lidos, registros_filtrados = 0, 0
    filtered_rows = []
    reader = csv.reader(io.StringIO(file_bytes.decode("utf-8")))
    for row in reader:
        registros_lidos += 1
        if len(row) != 6:
            continue
        nome, cpf, rg, endereco, data_ini_str, data_fim_str = row
        if not (is_valid_cpf(cpf) and is_valid_rg(rg)):
            continue
        data_ini, data_fim = parse_date(data_ini_str), parse_date(data_fim_str)
        if not (data_ini and data_fim):
            continue
        if is_overlap(data_ini, data_fim, period_start_dt, period_end_dt):
            filtered_rows.append(row)
            registros_filtrados += 1
    tempo = time.time() - start_time
    return filtered_rows, {"lidos": registros_lidos, "filtrados": registros_filtrados, "tempo": tempo}

def convert_to_csv(data):
    output = io.StringIO()
    writer = csv.writer(output)
    for row in data:
        writer.writerow(row)
    return output.getvalue()

# Lógica de data
period_start = datetime.combine(data_inicio, datetime.min.time())
period_end = datetime.combine(data_fim, datetime.max.time())

# Condicional para carregar o arquivo
if uploaded_file and processar:
    file_bytes = uploaded_file.getvalue()
    filtered_rows, metrics = process_csv(file_bytes, period_start, period_end)
    resultado_csv = convert_to_csv(filtered_rows)
    st.success("Processamento concluído.")
    st.write(f"Registros lidos: {metrics['lidos']}")
    st.write(f"Registros filtrados: {metrics['filtrados']}")
    st.write(f"Tempo de execução: {metrics['tempo']:.2f} segundos")
    if filtered_rows:
        # Exibindo a quantidade de linhas com base no slider
        df = pd.DataFrame(filtered_rows, columns=["Nome", "CPF", "RG", "Endereço", "Data Inicial", "Data Final"])
        st.dataframe(df.head(num_preview))  # Atualização automática com o slider
        st.download_button("Baixar CSV", resultado_csv, "contratos_filtrados.csv", "text/csv")
    else:
        st.warning("Nenhum registro encontrado.")
else:
    st.info("Envie um arquivo e clique em 'Processar'.")