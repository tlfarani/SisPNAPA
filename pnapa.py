import streamlit as st
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="PNAPA via Power Automate", layout="wide")

URL_LER = st.secrets["power_automate"]["URL_LER"]
URL_GRAVAR = st.secrets["power_automate"]["URL_GRAVAR"]

COLUNAS_PNAPA = [
    "Id", "Ano da Ação", "Número da Ação PNAPA", "Nome da Ação PNAPA", "Nível", 
    "Nome da Atividade", "Andamento", "Indicador", "Meta_Indicador", "Resultado_Indicador", 
    "Doc_Probatorio_Exec", "UF_Acao_PNAPA", "Importância da Atividade", "Tema da Atividade", 
    "Objetivo da Atividade", "Tipo de Atividade", "Periculosidade/Insalubridade", "Servidor", 
    "UF_Servidor", "Lotação", "Faz parte da Equipe de Emergências", "Número da PCDP", 
    "País", "UF Onde Ocorreu/Ocorrerá a Ação", "Estado_Local_Acao", "Municipio Onde Ocorreu/Ocorrerá a Ação", 
    "Data de Início", "Data de Término", "Dias_Gastos_Plan", "Dias_Gastos_Exec", "Origem do Recurso", 
    "Rec_Plan_Diarias", "Rec_Plan_Passagens", "Rec_Plan_Outras_Despesas", "Rec_Plan_Total", 
    "Rec_Exec_Diarias", "Rec_Exec_Passagens", "Rec_Exec_Outras_Despesas", "Rec_Exec_Total", 
    "Observações", "Justificativa_Acao_PNAPA"
]

# --- FUNÇÃO DE LEITURA VIA WEBHOOK ---
def carregar_dados_da_nuvem():
    try:
        resposta = requests.post(URL_LER, json={})
        if resposta.status_code == 200:
            dados_json = resposta.json()
            if dados_json:
                df = pd.DataFrame(dados_json)
                return df[COLUNAS_PNAPA]
        return pd.DataFrame(columns=COLUNAS_PNAPA)
    except Exception as e:
        st.error(f"Erro ao conectar ao Power Automate para leitura: {e}")
        return pd.DataFrame(columns=COLUNAS_PNAPA)

# Inicialização do estado da sessão
if "df" not in st.session_state:
    with st.spinner("Buscando dados no SharePoint via Power Automate..."):
        st.session_state.df = carregar_dados_da_nuvem()

df_atual = st.session_state.df

# --- INTERFACE LATERAL ---
st.sidebar.header("Painel de Controle")
modo = st.sidebar.radio("Operação:", ["Inserir Nova Linha", "Editar Linha Existente"])

registro_selecionado = None
id_atual = ""

if modo == "Editar Linha Existente":
    if df_atual.empty:
        st.sidebar.warning("Base de dados vazia.")
        modo = "Inserir Nova Linha"
    else:
        ids_disponiveis = df_atual["Id"].dropna().astype(str).unique().tolist()
        id_para_editar = st.sidebar.selectbox("Selecione o ID:", ids_disponiveis)
        registro_selecionado = df_atual[df_atual["Id"].astype(str) == str(id_para_editar)].iloc[0]
        id_atual = str(registro_selecionado["Id"])

# --- FORMULÁRIO EM ABAS ---
with st.form(key="form_power_automate", clear_on_submit=True):
    st.text_input("ID do Registro", value=id_atual if id_atual else "Definido no envio", disabled=True)
    
    aba1, aba2, aba3, aba4, aba5 = st.tabs([
        "1. Identificação", "2. Detalhes", "3. Recursos Humanos & Local", "4. Cronograma & Custos", "5. Justificativas"
    ])
    
    with aba1:
        ano_acao = st.number_input("Ano da Ação", min_value=2000, max_value=2100, value=int(registro_selecionado["Ano da Ação"]) if registro_selecionado is not None and pd.notna(registro_selecionado["Ano da Ação"]) else 2026)
        num_acao = st.text_input("Número da Ação PNAPA", value=str(registro_selecionado["Número da Ação PNAPA"]) if registro_selecionado is not None else "")
        nome_acao = st.text_input("Nome da Ação PNAPA", value=str(registro_selecionado["Nome da Ação PNAPA"]) if registro_selecionado is not None else "")
        nivel = st.selectbox("Nível", ["Nacional", "Regional", "Local"], index=["Nacional", "Regional", "Local"].index(registro_selecionado["Nível"]) if registro_selecionado is not None and registro_selecionado["Nível"] in ["Nacional", "Regional", "Local"] else 0)
        nome_atividade = st.text_input("Nome da Atividade", value=str(registro_selecionado["Nome da Atividade"]) if registro_selecionado is not None else "")
        andamento = st.selectbox("Andamento", ["Não Iniciada", "Em Planejamento", "Em Execução", "Concluída", "Cancelada"], index=["Não Iniciada", "Em Planejamento", "Em Execução", "Concluída", "Cancelada"].index(registro_selecionado["Andamento"]) if registro_selecionado is not None and registro_selecionado["Andamento"] in ["Não Iniciada", "Em Planejamento", "Em Execução", "Concluída", "Cancelada"] else 0)

    with aba2:
        indicador = st.text_input("Indicador", value=str(registro_selecionado["Indicador"]) if registro_selecionado is not None else "")
        meta_indicador = st.text_input("Meta_Indicador", value=str(registro_selecionado["Meta_Indicador"]) if registro_selecionado is not None else "")
        resultado_indicador = st.text_input("Resultado_Indicador", value=str(registro_selecionado["Resultado_Indicador"]) if registro_selecionado is not None else "")
        doc_probatorio = st.text_input("Doc_Probatorio_Exec", value=str(registro_selecionado["Doc_Probatorio_Exec"]) if registro_selecionado is not None else "")
        importancia = st.selectbox("Importância da Atividade", ["Alta", "Média", "Baixa"], index=["Alta", "Média", "Baixa"].index(registro_selecionado["Importância da Atividade"]) if registro_selecionado is not None and registro_selecionado["Importância da Atividade"] in ["Alta", "Média", "Baixa"] else 0)
        tema = st.text_input("Tema da Atividade", value=str(registro_selecionado["Tema da Atividade"]) if registro_selecionado is not None else "")
        objetivo = st.text_area("Objetivo da Atividade", value=str(registro_selecionado["Objetivo da Atividade"]) if registro_selecionado is not None else "")
        tipo_atividade = st.text_input("Tipo de Atividade", value=str(registro_selecionado["Tipo de Atividade"]) if registro_selecionado is not None else "")
        periculosidade = st.selectbox("Periculosidade/Insalubridade", ["Não", "Insalubridade", "Periculosidade", "Ambos"], index=["Não", "Insalubridade", "Periculosidade", "Ambos"].index(registro_selecionado["Periculosidade/Insalubridade"]) if registro_selecionado is not None and registro_selecionado["Periculosidade/Insalubridade"] in ["Não", "Insalubridade", "Periculosidade", "Ambos"] else 0)

    with aba3:
        servidor = st.text_input("Servidor", value=str(registro_selecionado["Servidor"]) if registro_selecionado is not None else "")
        uf_servidor = st.text_input("UF_Servidor", value=str(registro_selecionado["UF_Servidor"]) if registro_selecionado is not None else "", max_chars=2)
        lotacao = st.text_input("Lotação", value=str(registro_selecionado["Lotação"]) if registro_selecionado is not None else "")
        equipe_emergencia = st.selectbox("Faz parte da Equipe de Emergências", ["Não", "Sim"], index=1 if registro_selecionado is not None and registro_selecionado["Faz parte da Equipe de Emergências"] == "Sim" else 0)
        num_pcdp = st.text_input("Número da PCDP", value=str(registro_selecionado["Número da PCDP"]) if registro_selecionado is not None else "")
        pais = st.text_input("País", value=str(registro_selecionado["País"]) if registro_selecionado is not None else "Brasil")
        uf_acao_pnapa = st.text_input("UF_Acao_PNAPA", value=str(registro_selecionado["UF_Acao_PNAPA"]) if registro_selecionado is not None else "", max_chars=2)
        uf_ocorrencia = st.text_input("UF Onde Ocorreu/Ocorrerá a Ação", value=str(registro_selecionado["UF Onde Ocorreu/Ocorrerá a Ação"]) if registro_selecionado is not None else "", max_chars=2)
        estado_local = st.text_input("Estado_Local_Acao", value=str(registro_selecionado["Estado_Local_Acao"]) if registro_selecionado is not None else "")
        municipio = st.text_input("Municipio Onde Ocorreu/Ocorrerá a Ação", value=str(registro_selecionado["Municipio Onde Ocorreu/Ocorrerá a Ação"]) if registro_selecionado is not None else "")

    with aba4:
        with aba4:
        # --- Tratamento Robusto de Datas ---
        dt_inicio_convertida = pd.to_datetime(registro_selecionado["Data de Início"], errors='coerce') if registro_selecionado is not None else pd.NaT
        val_dt_inicio = dt_inicio_convertida.date() if pd.notna(dt_inicio_convertida) else date.today()
        
        dt_termino_convertida = pd.to_datetime(registro_selecionado["Data de Término"], errors='coerce') if registro_selecionado is not None else pd.NaT
        val_dt_termino = dt_termino_convertida.date() if pd.notna(dt_termino_convertida) else date.today()

        dt_inicio = st.date_input("Data de Início", value=val_dt_inicio)
        dt_termino = st.date_input("Data de Término", value=val_dt_termino)
        
        # --- FUNÇÃO DE CONVERSÃO NUMÉRICA SEGURA ---
        # Converte o valor para número de forma segura. Se tiver texto ou erro, vira 0.0
        def obter_num_seguro(registro, coluna):
            if registro is not None and coluna in registro:
                val = pd.to_numeric(registro[coluna], errors='coerce')
                return float(val) if pd.notna(val) else 0.0
            return 0.0

        # --- Inputs de Dias (Tratadas) ---
        dias_plan = st.number_input("Dias_Gastos_Plan", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Plan"))
        dias_exec = st.number_input("Dias_Gastos_Exec", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Exec"))
        
        origem_recurso = st.text_input("Origem do Recurso", value=str(registro_selecionado["Origem do Recurso"]) if registro_selecionado is not None else "")
        
        st.markdown("**Valores Orçamentários**")
        
        # --- Inputs de Custos Planejados (Tratadas) ---
        rec_p_diarias = st.number_input("Rec_Plan_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Diarias"), format="%.2f")
        rec_p_passagens = st.number_input("Rec_Plan_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Passagens"), format="%.2f")
        rec_p_outras = st.number_input("Rec_Plan_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Outras_Despesas"), format="%.2f")
        
        # --- Inputs de Custos Executados (Tratadas) ---
        rec_e_diarias = st.number_input("Rec_Exec_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Diarias"), format="%.2f")
        rec_e_passagens = st.number_input("Rec_Exec_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Passagens"), format="%.2f")
        rec_e_outras = st.number_input("Rec_Exec_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Outras_Despesas"), format="%.2f")

    with aba5:
        obs = st.text_area("Observações", value=str(registro_selecionado["Observações"]) if registro_selecionado is not None else "")
        justificativa = st.text_area("Justificativa_Acao_PNAPA", value=str(registro_selecionado["Justificativa_Acao_PNAPA"]) if registro_selecionado is not None else "")

    submetido = st.form_submit_button(label="🚀 Disparar Atualização para o SharePoint")

# --- PROCESSAMENTO DO ENVIO ---
if submetido:
    total_plan = rec_p_diarias + rec_p_passagens + rec_p_outras
    total_exec = rec_e_diarias + rec_e_passagens + rec_e_outras
    
    # 1. Identificação da Ação do Fluxo e Cálculo do ID
    if modo == "Inserir Nova Linha":
        acao_fluxo = "inserir"
        if not df_atual.empty:
            ids_numericos = pd.to_numeric(df_atual["Id"], errors='coerce').dropna()
            novo_id = int(ids_numericos.max() + 1) if not ids_numericos.empty else 1
        else:
            novo_id = 1
        id_final = str(novo_id)
    else:
        acao_fluxo = "editar"
        id_final = id_atual

    # 2. Montagem do Payload JSON
    payload = {
        "acao_fluxo": acao_fluxo, "Id": id_final, "Ano da Ação": ano_acao, "Número da Ação PNAPA": num_acao,
        "Nome da Ação PNAPA": nome_acao, "Nível": nivel, "Nome da Atividade": nome_atividade, "Andamento": andamento,
        "Indicador": indicador, "Meta_Indicador": meta_indicador, "Resultado_Indicador": resultado_indicador,
        "Doc_Probatorio_Exec": doc_probatorio, "UF_Acao_PNAPA": uf_acao_pnapa, "Importância da Atividade": importancia,
        "Tema da Atividade": tema, "Objetivo da Atividade": objetivo, "Tipo de Atividade": tipo_atividade,
        "Periculosidade/Insalubridade": periculosidade, "Servidor": servidor, "UF_Servidor": uf_servidor,
        "Lotação": lotacao, "Faz parte da Equipe de Emergências": equipe_emergencia, "Número da PCDP": num_pcdp,
        "País": pais, "UF Onde Ocorreu/Ocorrerá a Ação": uf_ocorrencia, "Estado_Local_Acao": estado_local,
        "Municipio Onde Ocorreu/Ocorrerá a Ação": municipio, "Data de Início": str(dt_inicio), "Data de Término": str(dt_termino),
        "Dias_Gastos_Plan": dias_plan, "Dias_Gastos_Exec": dias_exec, "Origem do Recurso": origem_recurso,
        "Rec_Plan_Diarias": rec_p_diarias, "Rec_Plan_Passagens": rec_p_passagens, "Rec_Plan_Outras_Despesas": rec_p_outras,
        "Rec_Plan_Total": total_plan, "Rec_Exec_Diarias": rec_e_diarias, "Rec_Exec_Passagens": rec_e_passagens,
        "Rec_Exec_Outras_Despesas": rec_e_outras, "Rec_Exec_Total": total_exec, "Observações": obs,
        "Justificativa_Acao_PNAPA": justificativa
    }

    # 3. Disparo para o Webhook de gravação do Power Automate
    with st.spinner("Sincronizando com a nuvem do IBAMA..."):
        try:
            resposta = requests.post(URL_GRAVAR, json=payload)
            if resposta.status_code == 200:
                st.success(f"🎉 Sucesso! Registro {id_final} processado no SharePoint.")
                # Força a limpeza do cache para recarregar a tabela atualizada do Excel na próxima rodada
                del st.session_state.df
                st.rerun()
            else:
                st.error(f"Erro no Power Automate: Status {resposta.status_code}")
        except Exception as e:
            st.error(f"Falha na comunicação com o fluxo: {e}")

# Visualização de monitoramento
st.write("---")
st.subheader("📊 Visualização Atual dos Dados (Espelho)")
st.dataframe(df_atual, use_container_width=True)
