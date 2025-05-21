import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from io import BytesIO

st.set_page_config(page_title="🔍 Correspondência de Nomes", layout="centered")

st.title("🔍 Correspondência de Nomes entre Arquivos")

st.sidebar.title("ℹ️ Instruções")
st.sidebar.markdown("""
Este aplicativo permite encontrar **nomes semelhantes** entre dois arquivos de texto com valores separados por quebra de linha (`.txt`, com separador `\\n`).  
Você deve preparar seus arquivos da seguinte forma:

- O **arquivo de referência** deve conter uma **coluna chamada `REFERENCIA`** com os nomes que servirão como base de comparação.
- O **arquivo de consulta** deve conter uma **coluna chamada `CONSULTA`** com os nomes que você deseja buscar correspondência.

Exemplo de conteúdo (`.txt` com `\\n`):

**arquivo de `referência.txt`:**
\nREFERENCIA
\nEmpresa A
\nEmpresa B
\nEmpresa C

**arquivo de `consulta.txt`:**         
\nCONSULTA
\nEmpresa B Ltda
\nEmpreza C
\nEMPRESA A

O resultado será um arquivo Excel com duas colunas:
- `entrada_consulta`
- `correspondencia_encontrada`
""")

arquivo_referencia = st.file_uploader("📄 Envie o arquivo de referência", type=["txt"])
arquivo_consulta = st.file_uploader("🔎 Envie o arquivo de consulta", type=["txt"])

def encontrar_correspondencia(nome, lista_referencia):
    nome_proc = str(nome).strip().lower()
    lista_proc = [n.lower() for n in lista_referencia]

    if nome_proc in lista_proc:
        idx = lista_proc.index(nome_proc)
        return lista_referencia[idx]

    resultados = process.extract(nome_proc, lista_proc, scorer=fuzz.ratio, limit=20)
    melhor_match = None
    maior_score = 0

    for nome_encontrado, score, _ in resultados:
        if score >= 90 and score > maior_score:
            idx = lista_proc.index(nome_encontrado)
            melhor_match = lista_referencia[idx]
            maior_score = score

    if melhor_match:
        return melhor_match

    for ref in lista_referencia:
        if f" {nome_proc} " in f" {ref.lower()} ":
            return ref

    for ref in lista_referencia:
        if f" {ref.lower()} " in f" {nome_proc} ":
            return ref

    return None

if st.button("🔄 Processar Correspondências"):

    if not arquivo_referencia or not arquivo_consulta:
        st.error("❌ É necessário enviar os dois arquivos antes de processar.")
        st.stop()

    try:
        df_referencia = pd.read_csv(arquivo_referencia, sep="\t", encoding='utf-8')
        df_consulta = pd.read_csv(arquivo_consulta, sep="\t", encoding='utf-8')
    except Exception as e:
        st.error(f"❌ Erro ao ler os arquivos: {e}")
        st.stop()

    if 'REFERENCIA' not in df_referencia.columns or 'CONSULTA' not in df_consulta.columns:
        st.error("❌ Os arquivos precisam conter as colunas 'REFERENCIA' e 'CONSULTA', respectivamente.")
        st.stop()

    lista_referencia = [str(n).strip() for n in df_referencia['REFERENCIA']]
    df_resultado = df_consulta.copy()
    df_resultado['correspondencia_encontrada'] = df_resultado['CONSULTA'].apply(
        lambda nome: encontrar_correspondencia(nome, lista_referencia)
    )

    df_resultado = df_resultado.rename(columns={'CONSULTA': 'entrada_consulta'})

    output = BytesIO()
    try:
        df_resultado.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        st.success("✅ Processamento finalizado!")

        st.download_button(
            label="📥 Baixar resultado (.xlsx)",
            data=output,
            file_name="resultado_correspondencias.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"❌ Erro ao salvar o arquivo Excel: {e}")
