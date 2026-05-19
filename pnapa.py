import streamlit as st
import pandas as pd
import requests
import time
from datetime import date

st.set_page_config(page_title="PNAPA via Power Automate", layout="wide")

# =================================================================
# 1. ENDPOINTS DO POWER AUTOMATE & CREDENCIAIS (SHAREPOINT)
# =================================================================
# URLs das tabelas auxiliares (Gerenciamento de Infraestrutura)
URL_FLOW_UNIDADES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/c2207ed01bf64853a477e7b6b165c3e8/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=GR6JhJzrEZTapCOAKwlY9VGzT_g-6xQGBG7YLraG6Z4" 
URL_FLOW_EQUIPES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/3d124cc6783845e1b8618cfb3302eca0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ubTQ-LAIsToMOX0CGytlI2YM_WKmC_mRT64ybRLBRSY"

# URLs da Planilha Macro Principal do PNAPA (Vindas do st.secrets)
URL_LER = st.secrets["power_automate"]["URL_LER"]
URL_GRAVAR = st.secrets["power_automate"]["URL_GRAVAR"]
URL_DELETAR = st.secrets["power_automate"]["URL_DELETAR"]

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

# =================================================================
# II. FUNÇÕES DE COMUNICAÇÃO HTTP COM O POWER AUTOMATE (APIs)
# =================================================================
def executar_api_unidades(dados_json):
    try:
        resposta = requests.post(URL_FLOW_UNIDADES, json=dados_json, timeout=15)
        if resposta.status_code == 200: return resposta.json()
        return []
    except: return []

def executar_api_equipes(dados_json):
    try:
        resposta = requests.post(URL_FLOW_EQUIPES, json=dados_json, timeout=15)
        if resposta.status_code == 200: return resposta.json()
        return []
    except: return []

# Função de Leitura da Base Macro Principal via Webhook
def carregar_dados_da_nuvem():
    try:
        resposta = requests.post(URL_LER, json={}, timeout=20)
        if resposta.status_code == 200:
            dados_json = resposta.json()
            if dados_json:
                df = pd.DataFrame(dados_json)
                return df[COLUNAS_PNAPA]
        return pd.DataFrame(columns=COLUNAS_PNAPA)
    except Exception as e:
        st.markdown(f"<div style='padding:10px; border-radius:5px; background-color:#2a1a1a; color:#f87171; border:1px solid #7f1d1d;'>❌ Erro ao conectar ao Power Automate para leitura da base macro: {e}</div>", unsafe_allow_html=True)
        return pd.DataFrame(columns=COLUNAS_PNAPA)

# Carregamento das tabelas de apoio (Unidades e Servidores)
@st.cache_data(ttl=60)
def carregar_bases_vias_power_automate():
    dados_uni = executar_api_unidades({"Acao": "Ler"})
    dados_srv = executar_api_equipes({"Acao": "Ler"})
    df_lot = pd.DataFrame(dados_uni) if dados_uni else pd.DataFrame(columns=["ID_UF", "UF", "Unidade"])
    df_serv = pd.DataFrame(dados_srv) if dados_srv else pd.DataFrame(columns=["ID_SERV", "Servidor", "UF_Servidor", "Lotacao", "Equipe_Emergencias", "Fiscal", "AEAC", "Funcao", "E_mail", "Perfil", "Token"])
    return df_lot, df_serv

df_lotacoes, df_servidores = carregar_bases_vias_power_automate()

# Inicialização e Cache da Planilha Macro Principal no session_state
if "df" not in st.session_state:
    with st.spinner("Buscando dados no SharePoint via Power Automate..."):
        st.session_state.df = carregar_dados_da_nuvem()

df_atual = st.session_state.df

# =================================================================
# III. DESIGN & CSS: BLINDAGEM DE INTERFACE CORPORATIVA
# =================================================================
st.markdown("""
    <style>
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] label p,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label p {
            color: #ffffff !important; font-weight: 700 !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div,
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important; border: 1px solid #cbd5e1 !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] *,
        section[data-testid="stSidebar"] div[data-baseweb="select"] * {
            color: #03170a !important; font-weight: bold !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] svg { fill: #03170a !important; }
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] > div,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important; border: 1px solid #cbd5e1 !important;
        }
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] *,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] * {
            color: #03170a !important; background-color: transparent !important;
        }
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] svg,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] svg { fill: #03170a !important; }
        div[data-testid="stNumberInput"] input { background-color: #ffffff !important; color: #03170a !important; }
        div[data-testid="stNumberInput"] > div { border: 1px solid #cbd5e1 !important; background-color: #ffffff !important; }
        div[data-testid="stNumberInput"] button { background-color: #f1f5f9 !important; color: #03170a !important; border: 1px solid #cbd5e1 !important; }
        div[data-testid="stDateInput"] > div, div[data-testid="stDateInput"] div[role="button"], div[data-testid="stDateInput"] input {
            background-color: #ffffff !important; color: #03170a !important; border: 1px solid #cbd5e1 !important;
        }
        div[data-testid="stDateInput"] svg { fill: #03170a !important; }
        button[data-baseweb="tab"] p { color: #4a5568 !important; font-weight: 500; }
        button[aria-selected="true"] p { color: #03170a !important; font-weight: 700 !important; }
        div[data-baseweb="tab-highlight"] { background-color: #4d6b53 !important; }
        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
            border: 1px solid #cbd5e1 !important; background-color: #ffffff !important; color: #03170a !important;
        }
        div[data-testid="stAppViewContainer"] label[data-testid="stWidgetLabel"] p { color: #03170a !important; font-weight: 500; }
        h2, h3, [data-testid="stHeader"] { color: #03170a !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# IV. GESTÃO DE AUTENTICAÇÃO E PERFIS DE ACESSO (SSO CONTEXT)
# =================================================================
try:
    if hasattr(st, "user") and hasattr(st.user, "email"): email_logado = st.user.email
    elif hasattr(st, "experimental_user"): email_logado = st.experimental_user.email
    else: email_logado = st.user.get("email") if hasattr(st, "user") and hasattr(st.user, "get") else None
except:
    email_logado = None

EMAIL_ADMIN = "tiago.farani@ibama.gov.br"
if not email_logado:
    email_logado = "tiago.farani@ibama.gov.br"

try:
    dados_usuario = df_servidores[df_servidores["E_mail"] == email_logado].iloc[0]
    uf_usuario = dados_usuario["UF_Servidor"]
    perfil_usuario = dados_usuario["Perfil"]
    token_correto = str(dados_usuario["Token"]).strip()
except:
    uf_usuario = "Acesso Restrito"
    perfil_usuario = "Visualização"
    token_correto = None

if email_logado == EMAIL_ADMIN:
    perfil_usuario = "Administrador"

acesso_liberado = False

if perfil_usuario == "Administrador":
    acesso_liberado = True
    uf_usuario = "SP"
    st.sidebar.success("👑 Modo Administrador Ativo")
else:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔐 Autenticação")
    token_digitado = st.sidebar.text_input("Digite seu Token de Acesso:", type="password")
    if token_digitado and token_digitado == token_correto:
        acesso_liberado = True
        st.sidebar.success(f"🔓 {perfil_usuario} Liberado ({uf_usuario})")
    elif token_digitado:
        st.sidebar.error("❌ Token Incorreto.")

# Menu de navegação lateral baseado em níveis de acesso
opcoes_menu = ["📊 Visualizar Base"]
if acesso_liberado and perfil_usuario in ["Administrador", "Editor Regional"]:
    opcoes_menu.extend(["➕ Inserir Nova Linha", "📝 Editar Linha Existente", "🗑️ Deletar Linha (ID)", "🏢 Gerenciar Unidades", "👥 Gerenciar Equipes"])

st.sidebar.markdown("## 🕹️ Painel de Controle")
modo = st.sidebar.radio("Operação:", opcoes_menu)

# Variáveis de controle de contexto para a Planilha Macro
registro_selecionado = None
id_atual = ""

if modo == "📝 Editar Linha Existente" and not df_atual.empty:
    ids_disponiveis = df_atual["Id"].dropna().astype(str).unique().tolist()
    st.sidebar.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 5px;'>Selecione o ID para Editar:</p>", unsafe_allow_html=True)
    id_para_editar = st.sidebar.selectbox("", ids_disponiveis, label_visibility="collapsed")
    registro_selecionado = df_atual[df_atual["Id"].astype(str) == str(id_para_editar)].iloc[0]
    id_atual = str(registro_selecionado["Id"])

elif modo == "🗑️ Deletar Linha (ID)" and not df_atual.empty:
    ids_disponiveis = df_atual["Id"].dropna().astype(str).unique().tolist()
    st.sidebar.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 5px;'>Selecione o ID para Deletar:</p>", unsafe_allow_html=True)
    id_para_deletar = st.sidebar.selectbox("", ids_disponiveis, label_visibility="collapsed")
    id_atual = str(id_para_deletar)

# =================================================================
# V. NÚCLEO OPERACIONAL DAS TELAS
# =================================================================

# --- TELA 1: VISUALIZAÇÃO COM FILTROS INTERDEPENDENTES ---
if modo == "📊 Visualizar Base":
    st.markdown("<h3 style='color: #03170a;'>📊 Visualização Atual dos Dados (Espelho SharePoint)</h3>", unsafe_allow_html=True)
    if df_atual.empty:
        st.info("A base de dados está vazia.")
    else:
        def limpar_e_converter_data(valor):
            if pd.isna(valor): return pd.NaT
            val_str = str(valor).strip()
            if val_str == "" or val_str.lower() in ["none", "nat", "nan"]: return pd.NaT
            if val_str.replace('.', '', 1).isdigit():
                try: return pd.to_datetime(int(float(val_str)), unit='D', origin='1899-12-30')
                except: pass
            return pd.to_datetime(val_str, errors='coerce', dayfirst=True)

        df_trabalho = df_atual.copy()
        df_trabalho["Data_Inicio_Datetime"] = df_trabalho["Data de Início"].apply(limpar_e_converter_data)
        df_trabalho["Data_Termino_Datetime"] = df_trabalho["Data de Término"].apply(limpar_e_converter_data)

        data_min_absoluta = df_trabalho["Data_Inicio_Datetime"].min()
        data_max_absoluta = df_trabalho["Data_Inicio_Datetime"].max()
        
        if pd.isna(data_min_absoluta) or pd.isna(data_max_absoluta):
            data_min_slider, data_max_slider = date(2025, 1, 1), date(2026, 12, 31)
        else:
            data_min_slider = (data_min_absoluta - pd.Timedelta(days=30)).to_pydatetime().date()
            data_max_slider = (data_max_absoluta + pd.Timedelta(days=30)).to_pydatetime().date()

        col_ano, col_uf, col_nivel = st.columns(3)
        df_filtros = df_trabalho.copy()
        with col_ano: ano_sel = st.selectbox("📅 Filtrar por Ano:", ["Todos"] + sorted(df_filtros["Ano da Ação"].dropna().astype(str).unique().tolist()))
        if ano_sel != "Todos": df_filtros = df_filtros[df_filtros["Ano da Ação"].astype(str) == ano_sel]
        with col_uf: uf_sel = st.selectbox("📍 Filtrar por UF:", ["Todas"] + sorted(df_filtros["UF_Acao_PNAPA"].dropna().astype(str).unique().tolist()))
        if uf_sel != "Todas": df_filtros = df_filtros[df_filtros["UF_Acao_PNAPA"].astype(str) == uf_sel]
        with col_nivel: nivel_sel = st.selectbox("🎚️ Filtrar por Nível:", ["Todos"] + sorted(df_filtros["Nível"].dropna().astype(str).unique().tolist()))
        if nivel_sel != "Todos": df_filtros = df_filtros[df_filtros["Nível"].astype(str) == nivel_sel]

        col_servidor, col_data = st.columns([1, 2])
        with col_servidor: servidor_sel = st.selectbox("👤 Filtrar por Servidor:", ["Todos"] + sorted(df_filtros["Servidor"].dropna().astype(str).unique().tolist()))
        with col_data:
            intervalo_datas = st.slider("⏳ Período (Data de Início):", min_value=data_min_slider, max_value=data_max_slider, value=(data_min_slider, data_max_slider), format="DD/MM/YYYY")

        df_exibicao = df_trabalho.copy()
        if ano_sel != "Todos": df_exibicao = df_exibicao[df_exibicao["Ano da Ação"].astype(str) == ano_sel]
        if uf_sel != "Todas": df_exibicao = df_exibicao[df_exibicao["UF_Acao_PNAPA"].astype(str) == uf_sel]
        if nivel_sel != "Todos": df_exibicao = df_exibicao[df_exibicao["Nível"].astype(str) == nivel_sel]
        if servidor_sel != "Todos": df_exibicao = df_exibicao[df_exibicao["Servidor"].astype(str) == servidor_sel]
        
        df_exibicao = df_exibicao[(df_exibicao["Data_Inicio_Datetime"].dt.date >= intervalo_datas[0]) & (df_exibicao["Data_Inicio_Datetime"].dt.date <= intervalo_datas[1])]

        df_exibicao["Data de Início"] = df_exibicao["Data_Inicio_Datetime"].dt.strftime('%d/%m/%Y').fillna("")
        df_exibicao["Data de Término"] = df_exibicao["Data_Termino_Datetime"].dt.strftime('%d/%m/%Y').fillna("")
        df_exibicao = df_exibicao.drop(columns=["Data_Inicio_Datetime", "Data_Termino_Datetime"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        def estilar_linhas_zebradas(linha): return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        st.dataframe(df_exibicao.reset_index(drop=True).style.apply(estilar_linhas_zebradas, axis=1), use_container_width=True)

# --- TELA 2 E 3: FORMULÁRIO DA PLANILHA MACRO (INSERIR OU EDITAR) ---
elif modo in ["➕ Inserir Nova Linha", "📝 Editar Linha Existente"]:
    st.markdown(f"<h3 style='color: #03170a;'>Formulário de Dados PNAPA — Modo: {modo}</h3>", unsafe_allow_html=True)
    
    with st.form(key="form_power_automate", clear_on_submit=True):
        st.text_input("ID do Registro", value=id_atual if id_atual else "Definido no envio", disabled=True)
        aba1, aba2, aba3, aba4, aba5 = st.tabs(["1. Identificação", "2. Detalhes", "3. Recursos Humanos & Local", "4. Cronograma & Custos", "5. Justificativas"])
        
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
            uf_acao = st.text_input("UF_Acao_PNAPA", value=str(registro_selecionado["UF_Acao_PNAPA"]) if registro_selecionado is not None else "", max_chars=2)
            uf_ocorrencia = st.text_input("UF Onde Ocorreu/Ocorrerá a Ação", value=str(registro_selecionado["UF Onde Ocorreu/Ocorrerá a Ação"]) if registro_selecionado is not None else "", max_chars=2)
            estado_local = st.text_input("Estado_Local_Acao", value=str(registro_selecionado["Estado_Local_Acao"]) if registro_selecionado is not None else "")
            municipio = st.text_input("Municipio Onde Ocorreu/Ocorrerá a Ação", value=str(registro_selecionado["Municipio Onde Ocorreu/Ocorrerá a Ação"]) if registro_selecionado is not None else "")

        with aba4:
            dt_inicio_convertida = pd.to_datetime(registro_selecionado["Data de Início"], errors='coerce') if registro_selecionado is not None else pd.NaT
            val_dt_inicio = dt_inicio_convertida.date() if pd.notna(dt_inicio_convertida) else date.today()
            dt_termino_convertida = pd.to_datetime(registro_selecionado["Data de Término"], errors='coerce') if registro_selecionado is not None else pd.NaT
            val_dt_termino = dt_termino_convertida.date() if pd.notna(dt_termino_convertida) else date.today()

            dt_inicio = st.date_input("Data de Início", value=val_dt_inicio)
            dt_termino = st.date_input("Data de Término", value=val_dt_termino)
            
            def obter_num_seguro(registro, coluna):
                if registro is not None and coluna in registro:
                    val = pd.to_numeric(registro[coluna], errors='coerce')
                    return float(val) if pd.notna(val) else 0.0
                return 0.0

            dias_plan = st.number_input("Dias_Gastos_Plan", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Plan"))
            dias_exec = st.number_input("Dias_Gastos_Exec", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Exec"))
            origem_recurso = st.text_input("Origem do Recurso", value=str(registro_selecionado["Origem do Recurso"]) if registro_selecionado is not None else "")
            
            st.markdown("<p style='font-weight: bold; margin-top:15px; color:#03170a;'>Valores Orçamentários</p>", unsafe_allow_html=True)
            rec_p_diarias = st.number_input("Rec_Plan_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Diarias"), format="%.2f")
            rec_p_passagens = st.number_input("Rec_Plan_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Passagens"), format="%.2f")
            rec_p_outras = st.number_input("Rec_Plan_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Outras_Despesas"), format="%.2f")
            rec_e_diarias = st.number_input("Rec_Exec_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Diarias"), format="%.2f")
            rec_e_passagens = st.number_input("Rec_Exec_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Passagens"), format="%.2f")
            rec_e_outras = st.number_input("Rec_Exec_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Outras_Despesas"), format="%.2f")

        with aba5:
            obs = st.text_area("Observações", value=str(registro_selecionado["Observações"]) if registro_selecionado is not None else "")
            justificativa = st.text_area("Justificativa_Acao_PNAPA", value=str(registro_selecionado["Justificativa_Acao_PNAPA"]) if registro_selecionado is not None else "")
        
        submetido = st.form_submit_button(label="🚀 Disparar Atualização para o SharePoint")

    if submetido:
        total_plan = rec_p_diarias + rec_p_passagens + rec_p_outras
        total_exec = rec_e_diarias + rec_e_passagens + rec_e_outras
        
        if modo == "➕ Inserir Nova Linha":
            acao_fluxo = "inserir"
            id_final = str(int(pd.to_numeric(df_atual["Id"], errors='coerce').dropna().max() + 1)) if not df_atual.empty else "1"
        else:
            acao_fluxo = "editar"
            id_final = id_atual

        payload = {
            "acao_fluxo": acao_fluxo, "Id": id_final, "Ano da Ação": ano_acao, "Número da Ação PNAPA": num_acao,
            "Nome da Ação PNAPA": nome_acao, "Nível": nivel, "Nome da Atividade": nome_atividade, "Andamento": andamento,
            "Indicador": indicador, "Meta_Indicador": meta_indicador, "Resultado_Indicador": resultado_indicador,
            "Doc_Probatorio_Exec": doc_probatorio, "UF_Acao_PNAPA": uf_acao, # <- Ajustado de uf_acao_pnapa para uf_acao
            "Importância da Atividade": importancia,
            "Tema da Atividade": tema, "Objetivo da Atividade": objetivo, "Tipo de Atividade": tipo_atividade,
            "Periculosidade/Insalubridade": periculosidade, "Servidor": servidor, "UF_Servidor": uf_servidor,
            "Lotação": lotacao, "Faz parte da Equipe de Emergências": equipe_emergencia, # <- Ajustado de equipe_emergency para equipe_emergencia
            "Número da PCDP": num_pcdp,
            "País": pais, "UF Onde Ocorreu/Ocorrerá a Ação": uf_ocorrencia, "Estado_Local_Acao": estado_local,
            "Municipio Onde Ocorreu/Ocorrerá a Ação": municipio, "Data de Início": str(dt_inicio), "Data de Término": str(dt_termino),
            "Dias_Gastos_Plan": dias_plan, "Dias_Gastos_Exec": dias_exec, "Origem do Recurso": origem_recurso,
            "Rec_Plan_Diarias": rec_p_diarias, "Rec_Plan_Passagens": rec_p_passagens, "Rec_Plan_Outras_Despesas": rec_p_outras,
            "Rec_Plan_Total": total_plan, "Rec_Exec_Diarias": rec_e_diarias, "Rec_Exec_Passagens": rec_e_passagens,
            "Rec_Exec_Outras_Despesas": rec_e_outras, "Rec_Exec_Total": total_exec, "Observações": obs, "Justificativa_Acao_PNAPA": justificativa
        }

        with st.spinner("Sincronizando com a nuvem do IBAMA..."):
            try:
                resposta = requests.post(URL_GRAVAR, json=payload, timeout=20)
                if resposta.status_code in [200, 202]:
                    st.success(f"🎉 Registro {id_final} enviado ao SharePoint!")
                    time.sleep(2)
                    st.cache_data.clear()
                    if "df" in st.session_state: del st.session_state.df
                    st.rerun()
                else:
                    st.error(f"❌ Erro no Power Automate: Status {resposta.status_code}")
            except Exception as e:
                st.error(f"❌ Falha de comunicação: {e}")

# --- TELA 4: EXCLUSÃO DE LINHA DA PLANILHA MACRO ---
elif modo == "🗑️ Deletar Linha (ID)":
    st.markdown("<h3 style='color: #03170a;'>🗑️ Excluir Registro Existente</h3>", unsafe_allow_html=True)
    st.markdown("<div style='padding:12px; border-radius:5px; background-color:#2a1b15; color:#fdba74; border:1px solid #c2410c; margin-bottom:20px;'>⚠️ Atenção: A remoção de registros da base do PNAPA é uma operação definitiva dentro do SharePoint.</div>", unsafe_allow_html=True)
    st.text_input("ID Marcado para Exclusão", value=id_atual, disabled=True)
    
    with st.popover("🚨 Confirmar Exclusão Permanente", use_container_width=True):
        st.markdown(f"<p>Tem certeza absoluta de que deseja destruir permanentemente o registro de <b>ID {id_atual}</b>?</p>", unsafe_allow_html=True)
        if st.button("Sim, deletar agora!", type="primary", use_container_width=True):
            with st.spinner("Removendo linha no SharePoint..."):
                try:
                    resposta_del = requests.post(URL_DELETAR, json={"Id": str(id_atual)}, timeout=20)
                    if resposta_del.status_code in [200, 202]:
                        st.success(f"💥 Registro {id_atual} excluído da base macro!")
                        time.sleep(2)
                        st.cache_data.clear()
                        if "df" in st.session_state: del st.session_state.df
                        st.rerun()
                    else:
                        st.error(f"❌ Erro no Power Automate: Status {resposta_del.status_code}")
                except Exception as e:
                    st.error(f"❌ Falha de comunicação: {e}")

# --- TELA 5: GERENCIAR UNIDADES ---
elif modo == "🏢 Gerenciar Unidades":
    st.markdown(f"<h3>🏢 Gerenciamento de Unidades / Lotações (Tabela Auxiliar via SharePoint)</h3>", unsafe_allow_html=True)
    df_visualizacao_uni = df_lotacoes if perfil_usuario == "Administrador" else df_lotacoes[df_lotacoes["UF"] == uf_usuario]
    
    st.write("#### 📋 Unidades Ativas cadastradas no Excel")
    if df_visualizacao_uni.empty:
        st.info(f"Nenhuma unidade cadastrada para a UF {uf_usuario}.")
    else:
        colunas_validas = [col for col in ["ID_UF", "UF", "Unidade"] if col in df_visualizacao_uni.columns]
        df_limpo_uni = df_visualizacao_uni[colunas_validas]
        def estilar_uni(linha): return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        st.dataframe(df_limpo_uni.reset_index(drop=True).style.apply(estilar_uni, axis=1), use_container_width=True)
    
    st.markdown("---")
    t_add, t_edit, t_del = st.tabs(["➕ Adicionar Unidade", "📝 Editar Unidade", "🗑️ Excluir Unidade"])
    LISTA_UFS_COMPLETA = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "Ceneac"]
    
    with t_add:
        uf_uni = st.selectbox("Selecione a UF / Órgão para adicionar a unidade:", LISTA_UFS_COMPLETA, key="uni_add_uf") if perfil_usuario == "Administrador" else st.text_input("UF da Lotação:", value=uf_usuario, disabled=True, key="uni_add_uf_rep")
        nova_uni = st.text_input("Nome da Nova Unidade:")
        if st.button("Salvar Unidade"):
            with st.spinner("Sincronizando nova unidade com o SharePoint..."):
                executar_api_unidades({"Acao": "Inserir", "UF": uf_uni, "Unidade": nova_uni})
                time.sleep(2)
                st.cache_data.clear()
            st.success(f"Unidade '{nova_uni}' salva com sucesso!")
            st.rerun()

    with t_edit:
        uf_filtrada_edit = st.selectbox("1. Filtrar Unidades por UF/Órgão:", sorted(df_lotacoes["UF"].dropna().unique().tolist()), key="uf_filt_edit") if perfil_usuario == "Administrador" else uf_usuario
        df_unidades_filtradas = df_lotacoes[df_lotacoes["UF"] == uf_filtrada_edit]
            
        if not df_unidades_filtradas.empty:
            sel_uni = st.selectbox("2. Selecione a Unidade para alterar:", df_unidades_filtradas["Unidade"].tolist(), key="uni_sel_edit")
            linha_filtrada = df_unidades_filtradas[df_unidades_filtradas["Unidade"].astype(str).str.strip() == str(sel_uni).strip()]
            
            if not linha_filtrada.empty:
                id_uf_edit = int(float(linha_filtrada["ID_UF"].iloc[0]))
                m_uni = st.text_input("3. Novo nome da Unidade:", value=sel_uni, key="uni_novo_nome")
                if st.button("Modificar Unidade"):
                    with st.spinner("Sincronizando alterações..."):
                        executar_api_unidades({"Acao": "Editar", "ID_UF": id_uf_edit, "UF": uf_filtrada_edit, "Unidade": m_uni})
                        time.sleep(2)
                        st.cache_data.clear()
                    st.success("Unidade modificada com sucesso!")
                    st.rerun()

    with t_del:
        uf_filtrada_del = st.selectbox("1. Filtrar Unidades por UF/Órgão:", sorted(df_lotacoes["UF"].dropna().unique().tolist()), key="uf_filt_del") if perfil_usuario == "Administrador" else uf_usuario
        df_unidades_filtradas_del = df_lotacoes[df_lotacoes["UF"] == uf_filtrada_del]
            
        if not df_unidades_filtradas_del.empty:
            del_uni = st.selectbox("2. Selecione a Unidade para REMOVER:", df_unidades_filtradas_del["Unidade"].tolist(), key="uni_sel_del")
            linha_filtrada_del = df_unidades_filtradas_del[df_unidades_filtradas_del["Unidade"].astype(str).str.strip() == str(del_uni).strip()]
            
            if not linha_filtrada_del.empty:
                id_uf_del = int(float(linha_filtrada_del["ID_UF"].iloc[0]))
                if st.button("❌ Excluir Unidade", disabled=not st.checkbox(f"Confirmo que desejo excluir permanentemente a unidade {del_uni}")):
                    with st.spinner("Removendo registro..."):
                        executar_api_unidades({"Acao": "Excluir", "ID_UF": id_uf_del})
                        time.sleep(2)
                        st.cache_data.clear()
                    st.success("Unidade removida com sucesso!")
                    st.rerun()

# --- TELA 6: GERENCIAR EQUIPES ---
elif modo == "👥 Gerenciar Equipes":
    st.markdown(f"<h3>👥 Gerenciamento de Equipe e Permissões (Tabela Auxiliar via SharePoint)</h3>", unsafe_allow_html=True)
    df_visualizacao_srv = df_servidores if perfil_usuario == "Administrador" else df_servidores[df_servidores["UF_Servidor"] == uf_usuario]
    
    st.write("#### 📋 Integrantes da Equipe Cadastrados no Excel")
    if df_visualizacao_srv.empty:
        st.info(f"Nenhum servidor cadastrado para a UF {uf_usuario}.")
    else:
        colunas_oficiais_srv = ["ID_SERV", "Servidor", "UF_Servidor", "Lotacao", "Equipe_Emergencias", "Fiscal", "AEAC", "Funcao", "E_mail", "Perfil"]
        colunas_validas_srv = [col for col in colunas_oficiais_srv if col in df_visualizacao_srv.columns]
        df_exibir_srv = df_visualizacao_srv[colunas_validas_srv]
        def estilar_srv(linha): return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        st.dataframe(df_exibir_srv.reset_index(drop=True).style.apply(estilar_srv, axis=1), use_container_width=True)
        
    st.markdown("---")
    ts_add, ts_edit, ts_del = st.tabs(["➕ Cadastrar Servidor", "📝 Alterar Cadastro", "🗑️ Remover Acesso"])
    LISTA_PERFIS = ["Visualização", "Editor Regional", "Administrador"]
    LISTA_UFS_COMPLETA = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "Ceneac"]
    
    with ts_add:
        n_srv = st.text_input("Nome Completo do Servidor:")
        e_srv = st.text_input("E-mail Institucional (@ibama.gov.br):")
        uf_srv = st.selectbox("UF/Órgão de Lotação:", LISTA_UFS_COMPLETA, key="srv_add_uf") if perfil_usuario == "Administrador" else st.text_input("UF de Lotação:", value=uf_usuario, disabled=True, key="srv_add_uf_rep")
        unidades_lotacao_disponiveis = df_lotacoes[df_lotacoes["UF"] == uf_srv]["Unidade"].tolist()
        lot_srv = st.selectbox("Unidade de Lotação Relacionada:", unidades_lotacao_disponiveis if unidades_lotacao_disponiveis else ["Sede Superintendência"])
        fun_srv = st.text_input("Função / Cargo Interno:")
        col_eq1, col_eq2, col_eq3 = st.columns(3)
        with col_eq1: eq_emerg = st.selectbox("Equipe de Emergências?", ["Sim", "Não"])
        with col_eq2: eq_fiscal = st.selectbox("Fiscal de Campo?", ["Sim", "Não"])
        with col_eq3: eq_aeac = st.selectbox("Possui AEAC?", ["Sim", "Não"])
        perf_srv = st.selectbox("Perfil de Acesso no Sistema:", LISTA_PERFIS) if perfil_usuario == "Administrador" else st.selectbox("Perfil de Acesso no Sistema:", ["Visualização", "Editor Regional"])
        tkn_srv = st.text_input("Definir Token/Senha de Acesso para o Usuário:", type="password")
        
        if st.button("Habilitar Servidor"):
            payload = {"Acao": "Inserir", "Servidor": n_srv, "UF_Servidor": uf_srv, "Lotacao": lot_srv, "Equipe_Emergencias": eq_emerg, "Fiscal": eq_fiscal, "AEAC": eq_aeac, "Funcao": fun_srv, "E_mail": e_srv, "Perfil": perf_srv, "Token": tkn_srv}
            with st.spinner("Adicionando integrante da equipe..."):
                executar_api_equipes(payload)
                time.sleep(2)
                st.cache_data.clear()
            st.success(f"Servidor {n_srv} inserido com sucesso!")
            st.rerun()

    with ts_edit:
        if not df_visualizacao_srv.empty:
            sel_srv = st.selectbox("Selecione o Servidor para alterar:", df_visualizacao_srv["Servidor"].tolist(), key="srv_sel_edit")
            dados_atuais_srv = df_visualizacao_srv[df_visualizacao_srv["Servidor"] == sel_srv].iloc[0]
            id_srv_edit = int(float(dados_atuais_srv["ID_SERV"]))
            
            # --- EXPANSÃO DOS CAMPOS DE EDIÇÃO ---
            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                novo_email = st.text_input("Alterar E-mail:", value=str(dados_atuais_srv.get("E_mail", "")))
                nova_funcao = st.text_input("Alterar Função Interna / Cargo:", value=str(dados_atuais_srv.get("Funcao", "")))
            
            with col_ed2:
                # Descobre a UF do servidor selecionado para filtrar as lotações disponíveis
                uf_atual_srv = dados_atuais_srv.get("UF_Servidor", uf_usuario)
                unidades_disponiveis_edit = df_lotacoes[df_lotacoes["UF"] == uf_atual_srv]["Unidade"].tolist()
                if not unidades_disponiveis_edit:
                    unidades_disponiveis_edit = ["Sede Superintendência"]
                
                # Define o índice padrão da lotação atual
                lotacao_atual_str = str(dados_atuais_srv.get("Lotacao", "")).strip()
                try: idx_lot = unidades_disponiveis_edit.index(lotacao_atual_str)
                except ValueError: idx_lot = 0
                
                nova_lot_srv = st.selectbox("Alterar Unidade de Lotação Relacionada:", unidades_disponiveis_edit, index=idx_lot)
                novo_token = st.text_input("Alterar Token/Senha de Acesso:", value=str(dados_atuais_srv.get("Token", "")), type="password")

            # Colunas para os Checkboxes/Dropdowns de Atributos Técnicos
            col_eq_ed1, col_eq_ed2, col_eq_ed3 = st.columns(3)
            
            def obter_index_sim_nao(valores_df, chave):
                val = str(valores_df.get(chave, "Não")).strip().capitalize()
                return 0 if val == "Sim" else 1

            with col_eq_ed1:
                n_eq_emerg = st.selectbox("Equipe de Emergências?", ["Sim", "Não"], index=obter_index_sim_nao(dados_atuais_srv, "Equipe_Emergencias"), key="srv_edit_emerg")
            with col_eq_ed2:
                n_eq_fiscal = st.selectbox("Fiscal de Campo?", ["Sim", "Não"], index=obter_index_sim_nao(dados_atuais_srv, "Fiscal"), key="srv_edit_fiscal")
            with col_eq_ed3:
                n_eq_aeac = st.selectbox("Possui AEAC?", ["Sim", "Não"], index=obter_index_sim_nao(dados_atuais_srv, "AEAC"), key="srv_edit_aeac")
            
            # Ajuste de Perfil de Acesso baseado nas regras de privilégio
            perfil_atual_string = str(dados_atuais_srv.get("Perfil", "Visualização")).strip()
            try: index_padrao = LISTA_PERFIS.index(perfil_atual_string)
            except ValueError: index_padrao = 0
            
            n_perf = st.selectbox("Alterar Perfil de Acesso:", LISTA_PERFIS, index=index_padrao) if perfil_usuario == "Administrador" else st.selectbox("Alterar Perfil de Acesso:", ["Visualização", "Editor Regional"], index=1 if index_padrao == 1 else 0)
            
            # --- DISPARO DE ATUALIZAÇÃO ---
            if st.button("Salvar Modificações"):
                # O payload agora reconstrói a linha completa para o Power Automate atualizar todas as células correspondentes
                payload_editar_srv = {
                    "Acao": "Editar", 
                    "ID_SERV": id_srv_edit, 
                    "Servidor": sel_srv, 
                    "UF_Servidor": uf_atual_srv,
                    "Lotacao": nova_lot_srv,
                    "Equipe_Emergencias": n_eq_emerg,
                    "Fiscal": n_eq_fiscal,
                    "AEAC": n_eq_aeac,
                    "E_mail": novo_email, 
                    "Funcao": nova_funcao, 
                    "Perfil": n_perf,
                    "Token": novo_token
                }
                
                with st.spinner("Atualizando cadastro completo da equipe no SharePoint..."):
                    executar_api_equipes(payload_editar_srv)
                    time.sleep(2)
                    st.cache_data.clear()
                st.success("Cadastro completo atualizado com sucesso no Excel!")
                st.rerun()

    with ts_del:
        if not df_visualizacao_srv.empty:
            del_srv = st.selectbox("Selecione quem perderá o acesso:", df_visualizacao_srv["Servidor"].tolist(), key="srv_sel_del")
            id_srv_del = int(float(df_visualizacao_srv[df_servidores["Servidor"] == del_srv]["ID_SERV"].iloc[0]))
            if st.button("❌ Revogar Acesso", disabled=not st.checkbox(f"Confirmo o desligamento do servidor {del_srv}")):
                with st.spinner("Revogando credenciais..."):
                    executar_api_equipes({"Acao": "Excluir", "ID_SERV": id_srv_del})
                    time.sleep(2)
                    st.cache_data.clear()
                st.success(f"Acesso revogado com sucesso!")
                st.rerun()
