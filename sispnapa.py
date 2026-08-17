import streamlit as st
import pandas as pd
import requests
import time
from datetime import date

st.set_page_config(page_title="SisPNAPA - Emergências Ambientais e Climáticas", layout="wide")

# =================================================================
# 1. ENDPOINTS DO POWER AUTOMATE & CREDENCIAIS (SHAREPOINT)
# =================================================================
# URLs das tabelas auxiliares (Gerenciamento de Infraestrutura)
URL_FLOW_UNIDADES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/c2207ed01bf64853a477e7b6b165c3e8/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=GR6JhJzrEZTapCOAKwlY9VGzT_g-6xQGBG7YLraG6Z4"
URL_FLOW_EQUIPES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/3d124cc6783845e1b8618cfb3302eca0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ubTQ-LAIsToMOX0CGytlI2YM_WKmC_mRT64ybRLBRSY"
URL_FLOW_PNAPAS = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/38cc92ea33ba4d6387b924d6eac62d58/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=LlCDUzrETHyXxp_QLte1eGxKR_4LuwRGzPJbgUsHvgk"

# URL da Planilha Macro Principal (Movidas para o topo para evitar NameError)
URL_FLOW_PRINCIPAL = st.secrets["power_automate"]["URL_PRINCIPAL"]

# =================================================================
# LISTAS OFICIAIS DE VALIDAÇÃO E MAPEAMENTO GEOGRÁFICO
# =================================================================
LISTA_UFS_COMPLETA = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]

MAPEAMENTO_ESTADOS_COMPLETO = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul", "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia",
    "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins"
}

LISTA_TEMAS = ["Dutos", "Emergências Climáticas", "Fauna", "Ferrovias", "Nuclear", "Outros temas", "Planejamento", "Plataformas", "Portos", "Rodovias", "SCI"]
LISTA_OBJETIVOS = ["Atendimento a Acidentes", "Prevenção e Gestão de Riscos", "Preparação"]
LISTA_TIPOS_ATIVIDADE = ["Capacitação", "Coleta de Amostras", "Desenvolvimento de Ferramentas", "Documentos de Análise", "Elaboração de Normativas", "Fiscalização", "Operação", "Outros tipos", "Reunião", "Simulados", "Vistoria"]
LISTA_PERIGOS = ["Periculosidade", "Insalubridade", "Não se Aplica"]
LISTA_ORIGENS_RECURSO = LISTA_UFS_COMPLETA + ["Ceneac", "Não se aplica", "Outras fontes"]

LISTA_JUSTIFICATIVAS_ACAO = [
    "Indisponibilidade de meios orçamentários/financeiros para a execução da Ação",
    "Alteração nas condições para a realização da Ação",
    "Condições pré-existentes não atendidas",
    "Falta de estrutura rodoviária/transporte na região de execução da Ação",
    "Indisponibilidade de meios materiais e/ou humanos para execução da Ação",
    "Mobilização de servidores (paralisação)",
    "Período planejado inexequivel para a execução da Ação",
    "Programação não aprovada pela CEDUC/CGGP",
    "Programação não aprovada por proponente/autoridade superior/ordenador de despesas",
    "Riscos de doenças infecto/contagiosas na região de execução da Ação",
    "Outras justificativas"
]

# Função performática com cache para puxar municípios do IBGE em tempo real por UF
@st.cache_data(ttl=3600)
def obter_municipios_ibge(sigla_uf):
    if not sigla_uf or sigla_uf not in MAPEAMENTO_ESTADOS_COMPLETO:
        return []
    try:
        url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{sigla_uf}/municipios"
        resposta = requests.get(url, timeout=5)
        if resposta.status_code == 200:
            return sorted([m["nome"] for m in resposta.json()])
    except:
        pass
    return []

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
def executar_envio_sharepoint(lista_payloads):
    sucessos = 0
    with st.spinner(f"Processando e sincronizando {len(lista_payloads)} requisições com o IBAMA..."):
        for p in lista_payloads:
            try:
                # Dispara para a URL unificada
                resposta = requests.post(URL_FLOW_PRINCIPAL, json=p, timeout=20)
                if resposta.status_code in [200, 202]: 
                    sucessos += 1
            except: 
                pass
            
    if sucessos > 0:
        with st.spinner("Consolidando alterações no banco do SharePoint..."):
            time.sleep(2.5)
            st.cache_data.clear()
            if "df" in st.session_state: del st.session_state.df
        st.success(f"🎉 🎉 Sucesso! {sucessos} atividades cadastradas e indexadas no SharePoint!")
        time.sleep(1)
        st.rerun()
    else:
        st.error("❌ Falha crítica: O Power Automate rejeitou a carga em lote.")

def payload_gerador(
    val_ano, val_num_acao, val_nome_acao, val_indicador, nivel_selecionado, 
    nome_atividade, andamento, resultado_indicador, doc_probatorio, uf_acao, 
    importancia, tema, objective, tipo_atividade, periculosidade, servidor, 
    uf_servidor, lotacao, equipe_emergencia, num_pcdp, pais, uf_ocorrencia, 
    estado_local, municipio, dt_inicio, dt_termino, dias_plan, dias_exec, 
    origem_recurso, rec_p_diarias, rec_p_passagens, rec_p_outras, rec_e_diarias, 
    rec_e_passagens, rec_e_outras, obs, justificativa, id_atual, modo, df_atual
):
    # Calcula o próximo ID sequencial se for inserção, ou preserva o ID atual se for edição
    if modo == "➕ Inserir Nova Linha":
        id_final = str(int(pd.to_numeric(df_atual["Id"], errors='coerce').dropna().max() + 1)) if not df_atual.empty else "1"
        acao_switch = "Inserir"
    else:
        id_final = str(id_atual)
        acao_switch = "Editar"

    return {
        "Acao": acao_switch,  # <- Alinhado exatamente ao seu Switch do Power Automate
        "Id": id_final,
        "Ano da Ação": int(val_ano) if val_ano else 2026,
        "Número da Ação PNAPA": str(val_num_acao),
        "Nome da Ação PNAPA": str(val_nome_acao),
        "Nível": str(nivel_selecionado),
        "Nome da Atividade": str(nome_atividade),
        "Andamento": str(andamento),
        "Indicador": str(val_indicador),
        "Meta_Indicador": "",
        "Resultado_Indicador": str(resultado_indicador),
        "Doc_Probatorio_Exec": str(doc_probatorio),
        "UF_Acao_PNAPA": str(uf_acao),
        "Importância da Atividade": str(importancia),
        "Tema da Atividade": str(tema),
        "Objetivo da Atividade": str(objective),
        "Tipo de Atividade": str(tipo_atividade),
        "Periculosidade/Insalubridade": str(periculosidade),
        "Servidor": str(servidor),
        "UF_Servidor": str(uf_servidor),
        "Lotação": str(lotacao),
        "Faz parte da Equipe de Emergências": str(equipe_emergencia),
        "Número da PCDP": str(num_pcdp),
        "País": str(pais),
        "UF Onde Ocorreu/Ocorrerá a Ação": str(uf_ocorrencia),
        "Estado_Local_Acao": str(estado_local),
        "Municipio Onde Ocorreu/Ocorrerá a Ação": str(municipio),
        "Data de Início": str(dt_inicio),
        "Data de Término": str(dt_termino),
        "Dias_Gastos_Plan": float(dias_plan),
        "Dias_Gastos_Exec": float(dias_exec),
        "Origem do Recurso": str(origem_recurso),
        "Rec_Plan_Diarias": float(rec_p_diarias),
        "Rec_Plan_Passagens": float(rec_p_passagens),
        "Rec_Plan_Outras_Despesas": float(rec_p_outras),
        "Rec_Plan_Total": float(rec_p_diarias + rec_p_passagens + rec_p_outras),
        "Rec_Exec_Diarias": float(rec_e_diarias),
        "Rec_Exec_Passagens": float(rec_e_passagens),
        "Rec_Exec_Outras_Despesas": float(rec_e_outras),
        "Rec_Exec_Total": float(rec_e_diarias + rec_e_passagens + rec_e_outras),
        "Observações": str(obs),
        "Justificativa_Acao_PNAPA": str(justificativa)
    }

def verificar_string_limpa(txt):
    return str(txt).replace('\xa0', ' ').strip()

def executar_api_pnapas(dados_json):
    try:
        resposta = requests.post(URL_FLOW_PNAPAS, json=dados_json, timeout=15)
        if resposta.status_code == 200: return resposta.json()
        return []
    except: return []

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

# Função de Leitura Blindada contra Chaves Ausentes do Power Automate
def carregar_dados_da_nuvem():
    try:
        resposta = requests.post(URL_FLOW_PRINCIPAL, json={"Acao": "Ler"}, timeout=20)
        if resposta.status_code == 200:
            dados_json = resposta.json()
            if dados_json:
                df = pd.DataFrame(dados_json)
                df.columns = [str(col).replace('\xa0', ' ').strip() for col in df.columns]
                df = df.reindex(columns=COLUNAS_PNAPA, fill_value="")
                return df
        return pd.DataFrame(columns=COLUNAS_PNAPA)
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao Power Automate: {e}")
        return pd.DataFrame(columns=COLUNAS_PNAPA)

# Carregamento das tabelas de apoio (Unidades, Servidores e Ações PNAPA)
@st.cache_data(ttl=60)
def carregar_bases_vias_power_automate():
    dados_uni = executar_api_unidades({"Acao": "Ler"})
    dados_srv = executar_api_equipes({"Acao": "Ler"})
    dados_pna = executar_api_pnapas({"Acao": "Ler"})
    
    df_lot = pd.DataFrame(dados_uni) if dados_uni else pd.DataFrame(columns=["ID_UF", "UF", "Unidade"])
    df_serv = pd.DataFrame(dados_srv) if dados_srv else pd.DataFrame(columns=["ID_SERV", "Servidor", "UF_Servidor", "Lotacao", "Equipe_Emergencias", "Fiscal", "AEAC", "Funcao", "E_mail", "Perfil", "Token"])
    df_pna = pd.DataFrame(dados_pna) if dados_pna else pd.DataFrame(columns=["ID_PNAPA", "Ano", "Num_Acao_PNAPA", "Acao_Ano", "Nome_Acao_Completo", "Nome_Acao_Apelido", "Importância", "Indicador"])
    
    return df_lot, df_serv, df_pna

df_lotacoes, df_servidores, df_pnapas = carregar_bases_vias_power_automate()

# Inicialização e Cache da Planilha Macro Principal no session_state
if "df" not in st.session_state:
    with st.spinner("Buscando dados no SharePoint via Power Automate..."):
        st.session_state.df = carregar_dados_da_nuvem()

df_atual = st.session_state.df

# [O restante do seu arquivo de controle visual (CSS, SSO, Menus, Telas 1 a 7) continua exatamente igual]

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

# Menu de navegação lateral baseado em níveis de acesso (Enxugado)
opcoes_menu = ["📊 Visualizar Base"]
if acesso_liberado and perfil_usuario in ["Administrador", "Editor Regional"]:
    opcoes_menu.extend(["➕ Inserir Nova Linha", "🏢 Gerenciar Unidades", "👥 Gerenciar Equipes", "🗂️ Gerenciar Ações PNAPA"])

st.sidebar.markdown("## 🕹️ Painel de Controle")
modo = st.sidebar.radio("Operação:", opcoes_menu)

# --- INSERIR O BOTÃO DE REFRESH AQUI ---
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Atualizar Base (Refresh)"):
    # 1. Limpa o cache das tabelas auxiliares (Unidades, Servidores, PNAPA)
    st.cache_data.clear()
    
    # 2. Apaga o dataframe da sessão para forçar a busca nova no SharePoint
    if "df" in st.session_state:
        del st.session_state.df
        
    # 3. Recarrega a página mantendo o usuário na mesma aba
    st.rerun()
    
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
    st.caption(f"📊 Registros carregados do SharePoint: **{len(df_atual)}** linhas.")
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
        
        # Garante a existência das colunas mesmo se vierem vazias do SharePoint/Power Automate
        if "Data de Início" not in df_trabalho.columns:
            df_trabalho["Data de Início"] = ""
        if "Data de Término" not in df_trabalho.columns:
            df_trabalho["Data de Término"] = ""

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
        
        # --- FILTRAGEM SEGURA POR TIMESTAMP (Inclui registros com ou sem data) ---
        ts_inicio = pd.to_datetime(intervalo_datas[0])
        ts_fim = pd.to_datetime(intervalo_datas[1]) + pd.Timedelta(hours=23, minutes=59, seconds=59)

        # Filtra registros dentro do período OU que ainda não tenham data definida
        mascara_datas = (
            df_exibicao["Data_Inicio_Datetime"].isna() |
            (
                (df_exibicao["Data_Inicio_Datetime"] >= ts_inicio) &
                (df_exibicao["Data_Inicio_Datetime"] <= ts_fim)
            )
        )

        df_exibicao = df_exibicao[mascara_datas]

        df_exibicao["Data de Início"] = df_exibicao["Data_Inicio_Datetime"].dt.strftime('%d/%m/%Y').fillna("")
        df_exibicao["Data de Término"] = df_exibicao["Data_Termino_Datetime"].dt.strftime('%d/%m/%Y').fillna("")
        df_exibicao = df_exibicao.drop(columns=["Data_Inicio_Datetime", "Data_Termino_Datetime"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        def estilar_linhas_zebradas(linha): return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        
        # --- 🧠 MEMÓRIA DE SELEÇÃO E CONTROLE DE RESET ---
        if "selecoes_macro" not in st.session_state:
            st.session_state["selecoes_macro"] = {}
        if "version_editor" not in st.session_state:
            st.session_state["version_editor"] = 0

        # --- 🎛️ BOTÃO DINÂMICO PARA DESMARCAR TODOS ---
        ids_marcados_check = [k for k, v in st.session_state["selecoes_macro"].items() if v]
        if ids_marcados_check:
            if st.button("✕ Desmarcar Todos os Itens", type="secondary"):
                st.session_state["selecoes_macro"] = {}
                st.session_state["version_editor"] += 1  # Força o reset visual do data_editor
                st.rerun()

        # --- 📊 ORDENAÇÃO NUMÉRICA POR ID ---
        df_interativo = df_exibicao.copy()
        # Converte a própria coluna Id para número inteiro (evita a ordenação alfabética 1, 10, 100)
        df_interativo["Id"] = pd.to_numeric(df_interativo["Id"], errors='coerce').fillna(0).astype(int)
        df_interativo = df_interativo.sort_values(by="Id", ascending=False).reset_index(drop=True)
        
        # Injeta os estados booleanos gravados na coluna visível do editor único
        df_interativo.insert(
            0, 
            "Selecionar", 
            [st.session_state["selecoes_macro"].get(str(row_id), False) for row_id in df_interativo["Id"]]
        )
        
        colunas_travadas = {col: st.column_config.Column(disabled=True) for col in df_interativo.columns if col != "Selecionar"}
        # Configura a coluna Id como NumberColumn sem casas decimais
        colunas_travadas["Id"] = st.column_config.NumberColumn("Id", format="%d", disabled=True)
        
        # RENDERIZAÇÃO DA TABELA ÚNICA CORPORATIVA
        key_dinamica = f"editor_lote_pnapa_v{st.session_state['version_editor']}"
        tabela_editavel = st.data_editor(
            df_interativo,
            hide_index=True,
            use_container_width=True,
            column_config=colunas_travadas,
            key=key_dinamica
        )
        
        # --- 💾 CAPTURA AS ALTERAÇÕES SEM ENTRAR EM LOOP ---
        if st.session_state[key_dinamica] and "edited_rows" in st.session_state[key_dinamica]:
            linhas_editadas = st.session_state[key_dinamica]["edited_rows"]
            mudanca_detectada = False
            
            for idx_linha, alteracao in linhas_editadas.items():
                if "Selecionar" in alteracao:
                    id_real_linha = str(df_interativo.iloc[int(idx_linha)]["Id"])
                    if st.session_state["selecoes_macro"].get(id_real_linha, False) != alteracao["Selecionar"]:
                        st.session_state["selecoes_macro"][id_real_linha] = alteracao["Selecionar"]
                        mudanca_detectada = True
            
            if mudanca_detectada:
                st.rerun()

        # O FILTRO DEFINITIVO: Mapeia quais IDs estão marcados como True na memória persistente
        ids_marcados = [id_key for id_key, marcado in st.session_state["selecoes_macro"].items() if marcado]
        df_linhas_selecionadas = df_exibicao[df_exibicao["Id"].astype(str).isin(ids_marcados)]
        
        # Se houver linhas retidas na memória, faz saltar o painel operacional de lote
        # --- MOTOR DINÂMICO DE EDIÇÃO / EXCLUSÃO (INDIVIDUAL OU EM LOTE) ---
        if not df_linhas_selecionadas.empty:
            ids_selecionados = df_linhas_selecionadas["Id"].astype(str).tolist()
            qtd_selecionada = len(ids_selecionados)
            
            st.markdown("---")
            st.markdown(f"### 🛠️ Central de Operações Dinâmicas ({qtd_selecionada} item(ns) selecionado(s))")
            st.caption(f"IDs detectados: {', '.join(ids_selecionados)}")
            
            # Botão de Exclusão unificado no topo do painel operacional
            with st.popover("🗑️ Remover Registro(s) Selecionado(s)", use_container_width=True):
                st.markdown(f"<p style='color:#03170a;'>⚠️ <b>CRÍTICO:</b> Deseja apagar de forma definitiva o(s) registro(s) de ID: <b>{', '.join(ids_selecionados)}</b> no SharePoint?</p>", unsafe_allow_html=True)
                if st.button("Sim, confirmar destruição permanente!", type="primary", key="btn_del_lote_tabela_final"):
                    # Adicionada a chave 'Acao': 'Excluir' para acionar a ramificação correta no Power Automate
                    payloads_del = [{"Acao": "Excluir", "Id": str(id_del)} for id_del in ids_selecionados]
                    sucessos_del = 0
                    with st.spinner("Removendo dados..."):
                        for p_del in payloads_del:
                            try:
                                # Enviando para a URL unificada
                                r = requests.post(URL_FLOW_PRINCIPAL, json=p_del, timeout=20)
                                if r.status_code in [200, 202]: 
                                    sucessos_del += 1
                            except:
                                pass
                                
                    if sucessos_del > 0:
                        st.cache_data.clear()
                        if "df" in st.session_state: 
                            del st.session_state.df
                        st.success(f"💥 {sucessos_del} registro(s) removido(s) com sucesso!")
                        st.session_state["selecoes_macro"] = {}
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("❌ Falha ao excluir registros: o Power Automate rejeitou a requisição.")
                        
            st.markdown("#### 📝 Formulário Adaptativo de Atualização")
            
            # --- DEFINIÇÃO DE FALLBACKS (INDIVIDUAL VS LOTE) ---
            if qtd_selecionada == 1:
                # Carrega os dados originais exatos da única linha marcada
                registro_alvo = df_linhas_selecionadas.iloc[0]
                st.info(f"ℹ️ Modo de Edição Individual ativo para o ID **{ids_selecionados[0]}**.")
                
                f_nivel = str(registro_alvo.get("Nível", "Atividade"))
                f_andamento = str(registro_alvo.get("Andamento", "Não Iniciada"))
                f_nome_atv = str(registro_alvo.get("Nome da Atividade", ""))
                f_res_ind = str(registro_alvo.get("Resultado_Indicador", ""))
                f_doc = str(registro_alvo.get("Doc_Probatorio_Exec", ""))
                f_uf_pna = str(registro_alvo.get("UF_Acao_PNAPA", ""))
                f_imp = str(registro_alvo.get("Importância da Atividade", "Alta"))
                f_tema = str(registro_alvo.get("Tema da Atividade", ""))
                f_obj = str(registro_alvo.get("Objetivo da Atividade", ""))
                f_tipo = str(registro_alvo.get("Tipo de Atividade", ""))
                f_perigo = str(registro_alvo.get("Periculosidade/Insalubridade", "Não"))
                f_servidor = str(registro_alvo.get("Servidor", ""))
                f_uf_srv = str(registro_alvo.get("UF_Servidor", ""))
                f_lot = str(registro_alvo.get("Lotação", ""))
                f_eq_emerg = str(registro_alvo.get("Faz parte da Equipe de Emergências", "Não"))
                f_pcdp = str(registro_alvo.get("Número da PCDP", ""))
                f_pais = str(registro_alvo.get("País", "Brasil"))
                f_uf_oc = str(registro_alvo.get("UF Onde Ocorreu/Ocorrerá a Ação", ""))
                f_est = str(registro_alvo.get("Estado_Local_Acao", ""))
                f_mun = str(registro_alvo.get("Municipio Onde Ocorreu/Ocorrerá a Ação", ""))
                f_dias_pl = float(pd.to_numeric(registro_alvo.get("Dias_Gastos_Plan", 0), errors='coerce') or 0.0)
                f_dias_ex = float(pd.to_numeric(registro_alvo.get("Dias_Gastos_Exec", 0), errors='coerce') or 0.0)
                f_origem = str(registro_alvo.get("Origem do Recurso", ""))
                f_rp_d = float(pd.to_numeric(registro_alvo.get("Rec_Plan_Diarias", 0), errors='coerce') or 0.0)
                f_rp_p = float(pd.to_numeric(registro_alvo.get("Rec_Plan_Passagens", 0), errors='coerce') or 0.0)
                f_rp_o = float(pd.to_numeric(registro_alvo.get("Rec_Plan_Outras_Despesas", 0), errors='coerce') or 0.0)
                f_re_d = float(pd.to_numeric(registro_alvo.get("Rec_Exec_Diarias", 0), errors='coerce') or 0.0)
                f_re_p = float(pd.to_numeric(registro_alvo.get("Rec_Exec_Passagens", 0), errors='coerce') or 0.0)
                f_re_o = float(pd.to_numeric(registro_alvo.get("Rec_Exec_Outras_Despesas", 0), errors='coerce') or 0.0)
                f_obs = str(registro_alvo.get("Observações", ""))
                f_just = str(registro_alvo.get("Justificativa_Acao_PNAPA", ""))
                f_meta = str(registro_alvo.get("Meta_Indicador", ""))
            else:
                # Carga Multi-Item: Campos em branco ou com padrão neutro
                st.warning(f"ℹ️ Modo de Edição em Lote ativo para **{qtd_selecionada}** itens. Campos vazios não serão alterados.")
                f_nivel, f_andamento, f_nome_atv, f_res_ind, f_doc, f_uf_pna = "Atividade", "Não Iniciada", "", "", "", ""
                f_imp, f_tema, f_obj, f_tipo, f_perigo, f_servidor, f_uf_srv, f_lot, f_eq_emerg, f_pcdp = "Alta", "", "", "", "Não", "", "", "", "Não", ""
                f_pais, f_uf_oc, f_est, f_mun, f_dias_pl, f_dias_ex, f_origem = "Brasil", "", "", "", 0.0, 0.0, ""
                f_rp_d, f_rp_p, f_rp_o, f_re_d, f_re_p, f_re_o, f_obs, f_just, f_meta = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "", "", ""

            # --- RENDERING DO FORMULÁRIO COM AS ABAS TEMÁTICAS REATIVAS ---
            with st.form(key="form_edicao_lote_tabela", clear_on_submit=True):
                # Recupera metadados da linha (ou da primeira linha se for lote) para o PROCV dinâmico invisível
                ref_linha = df_linhas_selecionadas.iloc[0]
                v_ano = ref_linha.get("Ano da Ação")
                v_num = ref_linha.get("Número da Ação PNAPA")
                v_nome = ref_linha.get("Nome da Ação PNAPA")
                v_ind = ref_linha.get("Indicador")
                
                # Exibição estática dos dados vinculados superiores da ação macro
                st.markdown(f"**Vínculo Macro:** {v_num} - {v_nome}")
                
                aba1, aba2, aba3, aba4, aba5 = st.tabs(["1. Identificação", "2. Detalhes", "3. Recursos Humanos & Local", "4. Cronograma & Custos", "5. Justificativas"])
                
                with aba1:
                    lista_niveis = ["Ação", "Atividade"]
                    idx_n = lista_niveis.index(f_nivel) if f_nivel in lista_niveis else 1
                    ed_nivel = st.selectbox("Nível", lista_niveis, index=idx_n)
                    
                    ed_nome_atv = st.text_input("Nome da Atividade", value=f_nome_atv)
                    
                    # Validação de Andamento reativa baseada no nível escolhido no formulário
                    if ed_nivel == "Ação":
                        lista_andamentos_painel = ["Planejada", "Cancelada", "Não Demandada", "Não Executada"]
                    else:
                        lista_andamentos_painel = ["Prevista", "Concluída"]
                        
                    try: idx_a = lista_andamentos_painel.index(f_andamento)
                    except: idx_a = 0
                    ed_andamento = st.selectbox("Andamento", lista_andamentos_painel, index=idx_a)

                with aba2:
                    ed_res_ind = st.text_input("Resultado do Indicador", value=f_res_ind)
                    ed_doc = st.text_input("Doc_Probatorio_Exec (SEI)", value=f_doc)
                    
                    # A UF da ação herda automaticamente do Ibama logado
                    uf_trava_painel = uf_usuario if uf_usuario != "Acesso Restrito" else "SP"
                    ed_uf_pna = st.text_input("UF da Ação PNAPA", value=uf_trava_painel, disabled=True)
                    
                    # Importância puxada de forma fixa da ação selecionada
                    val_importancia_automatica = str(ref_linha.get("Importância da Atividade", "Baixa"))
                    ed_importancia = st.text_input("Importância da Atividade (Herdada)", value=val_importancia_automatica, disabled=True)
                    
                    ed_tema = st.selectbox("Tema da Atividade", LISTA_TEMAS, index=LISTA_TEMAS.index(f_tema) if f_tema in LISTA_TEMAS else 0)
                    ed_objetivo = st.selectbox("Objetivo da Atividade", LISTA_OBJETIVOS, index=LISTA_OBJETIVOS.index(f_obj) if f_obj in LISTA_OBJETIVOS else 0)
                    ed_tipo = st.selectbox("Tipo de Atividade", LISTA_TIPOS_ATIVIDADE, index=LISTA_TIPOS_ATIVIDADE.index(f_tipo) if f_tipo in LISTA_TIPOS_ATIVIDADE else 0)
                    ed_periculosidade = st.selectbox("Periculosidade/Insalubridade", LISTA_PERIGOS, index=LISTA_PERIGOS.index(f_perigo) if f_perigo in LISTA_PERIGOS else 0)
                    ed_meta = st.text_input("Meta do Indicador (Apenas para Nível Ação)", value=f_meta)

                with aba3:
                    # Dropdown de servidores filtrado dinamicamente pela UF logada
                    df_serv_painel = df_servidores[df_servidores["UF_Servidor"] == uf_trava_painel]
                    if not df_serv_painel.empty:
                        lista_srv_painel = sorted(df_serv_painel["Servidor"].dropna().unique().tolist())
                        ed_servidor = st.selectbox("Servidor", lista_srv_painel, index=lista_srv_painel.index(f_servidor) if f_servidor in lista_srv_painel else 0)
                                                                       
                        # Gatilhos automáticos do PROCV
                        dados_painel_srv = df_serv_painel[df_serv_painel["Servidor"] == ed_servidor].iloc[0]
                        ed_uf_srv = str(dados_painel_srv.get("UF_Servidor", uf_trava_painel))
                        ed_lotacao = str(dados_painel_srv.get("Lotacao", "Sede Superintendência"))
                        ed_eq_emergencia = str(dados_painel_srv.get("Equipe_Emergencias", "Não"))
                    else:
                        ed_servidor = st.text_input("Servidor", value=f_servidor)
                        ed_uf_srv = uf_trava_painel
                        ed_lotacao = "Sede Superintendência"
                        ed_eq_emergencia = "Não"

                    st.text_input("UF_Servidor (Automático)", value=ed_uf_srv, disabled=True)
                    st.text_input("Lotação (Automático)", value=ed_lotacao, disabled=True)
                    st.text_input("Faz parte da Equipe de Emergências (Automático)", value=ed_eq_emergencia, disabled=True)
                    ed_pcdp = st.text_input("Número da PCDP", value=f_pcdp)
                    
                    st.markdown("##### 📍 Geolocalização")
                    ed_pais = st.text_input("País", value="Brasil", disabled=True)
                    ed_uf_oc = st.selectbox("UF Onde Ocorreu/Ocorrerá a Ação", LISTA_UFS_COMPLETA, index=LISTA_UFS_COMPLETA.index(f_uf_oc) if f_uf_oc in LISTA_UFS_COMPLETA else 0)
                    
                    ed_estado_local = MAPEAMENTO_ESTADOS_COMPLETO[ed_uf_oc]
                    st.text_input("Estado_Local_Acao (Automático)", value=ed_estado_local, disabled=True)
                    
                    # API IBGE acoplada de forma fluida no painel
                    lista_mun_painel = obter_municipios_ibge(ed_uf_oc)
                    ed_municipio = st.selectbox("Municipio Onde Ocorreu/Ocorrerá a Ação", lista_mun_painel if lista_mun_painel else ["Superintendência Sede"])

                with aba4:
                    st.caption("Insira no formato DD/MM/AAAA se quiser sobrescrever")
                    ed_dt_ini = st.text_input("Data de Início", value=str(ref_linha.get("Data de Início", "")) if qtd_selecionada == 1 else "")
                    ed_dt_fim = st.text_input("Data de Término", value=str(ref_linha.get("Data de Término", "")) if qtd_selecionada == 1 else "")
                    
                    ed_dias_pl = st.number_input("Dias_Gastos_Plan", min_value=0.0, value=f_dias_pl)
                    ed_dias_ex = st.number_input("Dias_Gastos_Exec", min_value=0.0, value=f_dias_ex)
                    ed_origem = st.selectbox("Origem do Recurso", LISTA_ORIGENS_RECURSO, index=LISTA_ORIGENS_RECURSO.index(f_origem) if f_origem in LISTA_ORIGENS_RECURSO else 0)
                    
                    st.markdown("<p style='font-weight: bold; margin-top:10px; color:#03170a;'>Valores Orçamentários</p>", unsafe_allow_html=True)
                    c_p, c_e = st.columns(2)
                    with c_p:
                        st.caption("Planejado")
                        ed_rp_d = st.number_input("Rec_Plan_Diarias", min_value=0.0, value=f_rp_d, format="%.2f")
                        ed_rp_p = st.number_input("Rec_Plan_Passagens", min_value=0.0, value=f_rp_p, format="%.2f")
                        ed_rp_o = st.number_input("Rec_Plan_Outras_Despesas", min_value=0.0, value=f_rp_o, format="%.2f")
                    with c_e:
                        st.caption("Executado")
                        ed_re_d = st.number_input("Rec_Exec_Diarias", min_value=0.0, value=f_re_d, format="%.2f")
                        ed_re_p = st.number_input("Rec_Exec_Passagens", min_value=0.0, value=f_re_p, format="%.2f")
                        ed_re_o = st.number_input("Rec_Exec_Outras_Despesas", min_value=0.0, value=f_re_o, format="%.2f")

                with aba5:
                    ed_obs = st.text_area("Observações", value=f_obs)
                    
                    # Justificativa condicional reativa para o painel de grid
                    if ed_nivel == "Ação" and ed_andamento in ["Cancelada", "Não Demandada", "Não Executada"]:
                        ed_justificativa = st.selectbox("Justificativa_Acao_PNAPA", LISTA_JUSTIFICATIVAS_ACAO, index=LISTA_JUSTIFICATIVAS_ACAO.index(f_just) if f_just in LISTA_JUSTIFICATIVAS_ACAO else 0)
                    else:
                        ed_justificativa = ""
                        st.info("ℹ️ Campo Justificativa desabilitado para o nível e andamento atuais.")

                submeter_alteracao = st.form_submit_button(label="💾 Gravar Alterações no SharePoint")

            # --- PROCESSAMENTO LOGÍSTICO COMPILADO DO ENVIO (PRESERVAÇÃO E PARSER ISO) ---
            if submeter_alteracao:
                payloads_envio_final = []
                
                for _, row_orig in df_linhas_selecionadas.iterrows():
                    id_alvo_loop = str(row_orig["Id"])
                    
                    # CORE DE PRESERVAÇÃO: Monta o payload inicial a partir dos dados do Cache Puro (df_atual)
                    p_final = {col: row_orig[col] for col in df_atual.columns if col in row_orig}
                    
                    # ALTERAÇÃO AQUI: 'Acao' = 'Editar' para o Switch do Power Automate
                    p_final["Acao"] = "Editar"
                    if "acao_fluxo" in p_final:
                        del p_final["acao_fluxo"]
                        
                    p_final["Id"] = str(id_alvo_loop)
                    
                    if qtd_selecionada == 1 or ed_nivel != f_nivel: p_final["Nível"] = str(ed_nivel)
                    if qtd_selecionada == 1 or (ed_nome_atv.strip() != ""): p_final["Nome da Atividade"] = str(ed_nome_atv).strip()
                    if qtd_selecionada == 1 or ed_andamento != f_andamento: p_final["Andamento"] = str(ed_andamento)
                    if qtd_selecionada == 1 or (ed_res_ind.strip() != ""): p_final["Resultado_Indicador"] = str(ed_res_ind).strip()
                    if qtd_selecionada == 1 or (ed_doc.strip() != ""): p_final["Doc_Probatorio_Exec"] = str(ed_doc).strip()
                    if qtd_selecionada == 1 or (ed_uf_pna.strip() != ""): p_final["UF_Acao_PNAPA"] = str(ed_uf_pna).strip()
                    
                    # 🚀 ENCAIXE DAS NOVAS VALIDAÇÕES DE CAMPOS (Mapeamento Cirúrgico)
                    p_final["Importância da Atividade"] = str(ed_importancia) if ed_importancia else str(row_orig.get("Importância da Atividade", "Baixa"))
                    if qtd_selecionada == 1 or (ed_tema != ""): p_final["Tema da Atividade"] = str(ed_tema)
                    if qtd_selecionada == 1 or (ed_objetivo != ""): p_final["Objetivo da Atividade"] = str(ed_objetivo)
                    if qtd_selecionada == 1 or (ed_tipo != ""): p_final["Tipo de Atividade"] = str(ed_tipo)
                    if qtd_selecionada == 1 or ed_periculosidade != f_perigo: p_final["Periculosidade/Insalubridade"] = str(ed_periculosidade)
                    if qtd_selecionada == 1 or (ed_meta.strip() != ""): p_final["Meta_Indicador"] = str(ed_meta).strip()
                    
                    # Recursos Humanos e Localização (Herança Automática das Tabelas Auxiliares)
                    if qtd_selecionada == 1 or (ed_servidor != ""): p_final["Servidor"] = str(ed_servidor)
                    p_final["UF_Servidor"] = str(ed_uf_srv) if ed_uf_srv else str(row_orig.get("UF_Servidor", ""))
                    p_final["Lotação"] = str(ed_lotacao) if ed_lotacao else str(row_orig.get("Lotação", ""))
                    p_final["Faz parte da Equipe de Emergências"] = str(ed_eq_emergencia) if ed_eq_emergencia else str(row_orig.get("Faz parte da Equipe de Emergências", "Não"))
                    if qtd_selecionada == 1 or (ed_pcdp.strip() != ""): p_final["Número da PCDP"] = str(ed_pcdp).strip()
                    p_final["País"] = "Brasil"
                    if qtd_selecionada == 1 or (ed_uf_oc != ""): p_final["UF Onde Ocorreu/Ocorrerá a Ação"] = str(ed_uf_oc)
                    p_final["Estado_Local_Acao"] = str(ed_estado_local) if ed_estado_local else str(row_orig.get("Estado_Local_Acao", ""))
                    p_final["Municipio Onde Ocorreu/Ocorrerá a Ação"] = str(ed_municipio) if ed_municipio else str(row_orig.get("Municipio Onde Ocorreu/Ocorrerá a Ação", ""))
                    
                    # Cronograma e Custos
                    if qtd_selecionada == 1 or (ed_dt_ini.strip() != ""): p_final["Data de Início"] = str(ed_dt_ini).strip()
                    if qtd_selecionada == 1 or (ed_dt_fim.strip() != ""): p_final["Data de Término"] = str(ed_dt_fim).strip()
                    if qtd_selecionada == 1 or ed_dias_pl != 0.0: p_final["Dias_Gastos_Plan"] = float(ed_dias_pl)
                    if qtd_selecionada == 1 or ed_dias_ex != 0.0: p_final["Dias_Gastos_Exec"] = float(ed_dias_ex)
                    if qtd_selecionada == 1 or (ed_origem != ""): p_final["Origem do Recurso"] = str(ed_origem)
                    if qtd_selecionada == 1 or ed_rp_d != 0.0: p_final["Rec_Plan_Diarias"] = float(ed_rp_d)
                    if qtd_selecionada == 1 or ed_rp_p != 0.0: p_final["Rec_Plan_Passagens"] = float(ed_rp_p)
                    if qtd_selecionada == 1 or ed_rp_o != 0.0: p_final["Rec_Plan_Outras_Despesas"] = float(ed_rp_o)
                    if qtd_selecionada == 1 or ed_re_d != 0.0: p_final["Rec_Exec_Diarias"] = float(ed_re_d)
                    if qtd_selecionada == 1 or ed_re_p != 0.0: p_final["Rec_Exec_Passagens"] = float(ed_re_p)
                    if qtd_selecionada == 1 or ed_re_o != 0.0: p_final["Rec_Exec_Outras_Despesas"] = float(ed_re_o)
                    
                    # Parser de Datas Padrão ISO
                    raw_ini = ed_dt_ini.strip() if (qtd_selecionada == 1 or ed_dt_ini.strip() != "") else str(row_orig.get("Data de Início", ""))
                    raw_fim = ed_dt_fim.strip() if (qtd_selecionada == 1 or ed_dt_fim.strip() != "") else str(row_orig.get("Data de Término", ""))
                    
                    def normalizar_padrao_iso(data_str):
                        data_limpa = str(data_str).strip()
                        if "/" in data_limpa:
                            try:
                                d, m, a = data_limpa.split("/")
                                return f"{a}-{m}-{d}"
                            except: pass
                        return data_limpa
                    
                    p_final["Data de Início"] = normalizar_padrao_iso(raw_ini)
                    p_final["Data de Término"] = normalizar_padrao_iso(raw_fim)
                    
                    if qtd_selecionada == 1 or (ed_obs.strip() != ""): p_final["Observações"] = str(ed_obs).strip()
                    p_final["Justificativa_Acao_PNAPA"] = str(ed_justificativa) if ed_justificativa else str(row_orig.get("Justificativa_Acao_PNAPA", ""))

                    # Recalcula Totais
                    p_final["Rec_Plan_Total"] = float(p_final.get("Rec_Plan_Diarias", 0)) + float(p_final.get("Rec_Plan_Passagens", 0)) + float(p_final.get("Rec_Plan_Outras_Despesas", 0))
                    p_final["Rec_Exec_Total"] = float(p_final.get("Rec_Exec_Diarias", 0)) + float(p_final.get("Rec_Exec_Passagens", 0)) + float(p_final.get("Rec_Exec_Outras_Despesas", 0))
                    
                    # Sanitização final contra NaNs residuais do Pandas antes de anexar à lista de envios
                    payload_sanitizado = {}
                    for k, v in p_final.items():
                        payload_sanitizado[k] = 0.0 if pd.isna(v) and ("Rec_" in k or "Dias_" in k) else ("" if pd.isna(v) else v)
                    
                    payloads_envio_final.append(payload_sanitizado)
                
                # Despacha a rajada mapeada e higienizada
                executar_envio_sharepoint(payloads_envio_final)
                
                st.session_state["selecoes_macro"] = {}
                st.session_state["version_editor"] += 1
                st.rerun()

# --- TELA 2 E 3: FORMULÁRIO DA PLANILHA MACRO (INSERIR OU EDITAR) ---
elif modo in ["➕ Inserir Nova Linha", "📝 Editar Linha Existente"]:
    st.markdown(f"<h3 style='color: #03170a;'>Formulário de Dados PNAPA — Modo: {modo}</h3>", unsafe_allow_html=True)
    
    # 🌟 PASSO 1: CONTROLES FORA DO FORMULÁRIO PARA GARANTIR REATIVIDADE EM TEMPO REAL
    idx_nivel_padrao = 0 if registro_selecionado is None or str(registro_selecionado.get("Nível", "")) == "Ação" else 1
    nivel_selecionado = st.selectbox("O que deseja cadastrar/editar?", ["Ação", "Atividade"], index=idx_nivel_padrao, key="main_txt_nivel")
    
    st.markdown("#### 🔗 Vinculação Automática com o Catálogo de Ações PNAPA")
    if not df_pnapas.empty:
        anos_aux_disponiveis = sorted(df_pnapas["Ano"].dropna().astype(int).unique().tolist(), reverse=True)
        
        ano_padrao_form = int(registro_selecionado["Ano da Ação"]) if registro_selecionado is not None and pd.notna(registro_selecionado["Ano da Ação"]) else anos_aux_disponiveis[0]
        try: idx_ano_form = anos_aux_disponiveis.index(ano_padrao_form)
        except ValueError: idx_ano_form = 0
            
        ano_vinculo = st.selectbox("Selecione o Ano para filtrar as Ações:", anos_aux_disponiveis, index=idx_ano_form, key="form_pna_vinculo_ano")
        df_pnapas_ano = df_pnapas[df_pnapas["Ano"].astype(int) == ano_vinculo]
        
        if not df_pnapas_ano.empty:
            lista_opcoes_vinc = (df_pnapas_ano["Acao_Ano"].astype(str) + " - " + df_pnapas_ano["Nome_Acao_Apelido"].astype(str)).tolist()
            
            num_acao_gravada = str(registro_selecionado.get("Número da Ação PNAPA", "")) if registro_selecionado is not None else ""
            idx_pna_vinc = 0
            for i, opc in enumerate(lista_opcoes_vinc):
                if opc.startswith(num_acao_gravada + "-"):
                    idx_pna_vinc = i
                    break
            
            opcao_vinc_sel = st.selectbox("Selecione a Ação PNAPA correspondente:", lista_opcoes_vinc, index=idx_pna_vinc, key="form_pna_vinculo_sel")
            
            # PROCV automático do Catálogo Auxiliar
            acao_ano_detectado = opcao_vinc_sel.split(" - ")[0]
            dados_aux_linha = df_pnapas_ano[df_pnapas_ano["Acao_Ano"].astype(str) == acao_ano_detectado].iloc[0]
            
            val_ano = int(dados_aux_linha["Ano"])
            val_num_acao = str(dados_aux_linha["Num_Acao_PNAPA"])
            val_nome_acao = str(dados_aux_linha["Nome_Acao_Completo"])
            val_indicador = str(dados_aux_linha["Indicador"])
            
            st.success(f"✅ Dados Vinculados: Código {val_num_acao} | {val_nome_acao[:60]}...")
        else:
            st.warning("⚠️ Nenhuma ação cadastrada para este ano no catálogo auxiliar.")
            val_ano, val_num_acao, val_nome_acao, val_indicador = None, "", "", ""
    else:
        st.error("⚠️ O catálogo auxiliar de Ações PNAPA está vazio.")
        val_ano, val_num_acao, val_nome_acao, val_indicador = None, "", "", ""

    st.markdown("---")
    
    # Fallbacks de Configuração Geral de Dados
    dt_inicio_convertida = pd.to_datetime(registro_selecionado["Data de Início"], errors='coerce') if registro_selecionado is not None else pd.NaT
    val_dt_inicio = dt_inicio_convertida.date() if pd.notna(dt_inicio_convertida) else date.today()
    dt_termino_convertida = pd.to_datetime(registro_selecionado["Data de Término"], errors='coerce') if registro_selecionado is not None else pd.NaT
    val_dt_termino = dt_termino_convertida.date() if pd.notna(dt_termino_convertida) else date.today()

    def obter_num_seguro(registro, coluna):
        if registro is not None and coluna in registro:
            val = pd.to_numeric(registro[coluna], errors='coerce')
            return float(val) if pd.notna(val) else 0.0
        return 0.0

    # 🌟 PASSO 2: INÍCIO DO FORMULÁRIO ENVELOPANDO AS ABAS TEMÁTICAS DINÂMICAS
    with st.form(key="form_power_automate", clear_on_submit=True):
        st.text_input("ID do Registro", value=id_atual if id_atual else "Definido no envio", disabled=True)
        
        # =================================================================
        # CONDICIONAL VISUAL: SE FOR AÇÃO
        # =================================================================
        if nivel_selecionado == "Ação":
            # REFEITO CONFORME DIRETRIZ: Importância da Atividade herdada do Catálogo Auxiliar da Ação selecionada
            val_importancia_automatica = str(dados_aux_linha.get("Importância", "Ordinária"))
            if val_importancia_automatica == "Ordinária":
                importancia = "Baixa"
            elif val_importancia_automatica == "Estratégica":
                importancia = "Alta"
            else:
                importancia = "Média"

            aba1, aba2, aba4, aba5 = st.tabs(["1. Identificação", "2. Detalhes", "4. Cronograma & Custos", "5. Justificativas"])
            
            with aba1:
                st.text_input("Ano da Ação (Automático)", value=str(val_ano if val_ano else ""), disabled=True)
                st.text_input("Número da Ação PNAPA (Automático)", value=val_num_acao, disabled=True)
                st.text_input("Nome da Ação PNAPA (Automático)", value=val_nome_acao, disabled=True)
                
                # REFEITO CONFORME DIRETRIZ: Andamento restrito para Ação
                lista_andamentos_acao = ["Planejada", "Cancelada", "Não Demandada", "Não Executada"]
                try: idx_and = lista_andamentos_acao.index(registro_selecionado["Andamento"])
                except: idx_and = 0
                andamento = st.selectbox("Andamento da Ação", lista_andamentos_acao, index=idx_and)

                
            with aba2:
                st.text_input("Indicador (Automático)", value=val_indicador, disabled=True)
                meta_indicador = st.text_input("Meta do Indicador", value=str(registro_selecionado["Meta_Indicador"]) if registro_selecionado is not None else "")
                
                # Trava a UF da ação com base no usuário logado ou SP padrão administrativo Ibama
                uf_acao = st.text_input("UF da Ação PNAPA", value=str(uf_usuario if uf_usuario != "Acesso Restrito" else "SP"), disabled=True)
                st.text_input("Importância da Atividade (Herdada do Catálogo)", value=importancia, disabled=True)
                
                tema = st.selectbox("Tema da Atividade", LISTA_TEMAS)
                objetivo = st.selectbox("Objetivo da Atividade", LISTA_OBJETIVOS)
                tipo_atividade = st.selectbox("Tipo de Atividade", LISTA_TIPOS_ATIVIDADE)

            with aba4:
                dt_inicio = st.date_input("Data de Início", value=val_dt_inicio)
                dt_termino = st.date_input("Data de Término", value=val_dt_termino)
                dias_plan = st.number_input("Dias Gastos Plan", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Plan"))
                origem_recurso = st.selectbox("Origem do Recurso", LISTA_ORIGENS_RECURSO)
                
                st.markdown("<p style='font-weight: bold; margin-top:15px; color:#03170a;'>Valores Orçamentários Planejados</p>", unsafe_allow_html=True)
                rec_p_diarias = st.number_input("Rec_Plan_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Diarias"), format="%.2f")
                rec_p_passagens = st.number_input("Rec_Plan_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Passagens"), format="%.2f")
                rec_p_outras = st.number_input("Rec_Plan_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Outras_Despesas"), format="%.2f")

            with aba5:
                obs = st.text_area("Observações", value=str(registro_selecionado["Observações"]) if registro_selecionado is not None else "")
                
                # REFEITO CONFORME DIRETRIZ: Justificativa condicional reativa para andamentos restritivos de Ação
                if andamento in ["Cancelada", "Não Demandada", "Não Executada"]:
                    justificativa = st.selectbox("Justificativa_Acao_PNAPA", LISTA_JUSTIFICATIVAS_ACAO)
                else:
                    justificativa = ""
                    st.info("ℹ️ Justificativa habilitada apenas para ações com andamento Cancelada, Não Demandada ou Não Executada.")

            # Inicializa nulos regulamentares de Atividade para o construtor do payload
            nome_atividade, resultado_indicador, doc_probatorio, periculosidade = "", "", "", "Não se Aplica"
            servidor, uf_servidor, lotacao, equipe_emergencia, num_pcdp = "", "", "", "Não", ""
            pais, uf_ocorrencia, estado_local, municipio, dias_exec = "Brasil", "", "", "", 0.0
            rec_e_diarias, rec_e_passagens, rec_e_outras = 0.0, 0.0, 0.0

        # =================================================================
        # CONDICIONAL VISUAL: SE FOR ATIVIDADE
        # =================================================================
        elif nivel_selecionado == "Atividade":
            aba1, aba2, aba3, aba4, aba5 = st.tabs(["1. Identificação", "2. Detalhes", "3. Recursos Humanos & Local", "4. Cronograma & Custos", "5. Justificativas"])
            
            with aba1:
                st.text_input("Ano da Ação (Automático)", value=str(val_ano if val_ano else ""), disabled=True)
                st.text_input("Número da Ação PNAPA (Automático)", value=val_num_acao, disabled=True)
                st.text_input("Nome da Ação PNAPA (Automático)", value=val_nome_acao, disabled=True)
                
                nome_atividade = st.text_input("Nome da Atividade", value=str(registro_selecionado["Nome da Atividade"]) if registro_selecionado is not None else "")
                
                # REFEITO CONFORME DIRETRIZ: Andamento restrito para Atividade
                lista_andamentos_atividade = ["Prevista", "Concluída"]
                try: idx_and_atv = lista_andamentos_atividade.index(registro_selecionado["Andamento"])
                except: idx_and_atv = 0
                andamento = st.selectbox("Andamento da Atividade", lista_andamentos_atividade, index=idx_and_atv)

            with aba2:
                st.text_input("Indicador (Automático)", value=val_indicador, disabled=True)
                resultado_indicador = st.text_input("Resultado do Indicador", value=str(registro_selecionado["Resultado_Indicador"]) if registro_selecionado is not None else "")
                doc_probatorio = st.text_input("Doc_Probatorio_Exec (SEI)", value=str(registro_selecionado["Doc_Probatorio_Exec"]) if registro_selecionado is not None else "")
                uf_acao = st.text_input("UF da Ação PNAPA", value=str(uf_usuario if uf_usuario != "Acesso Restrito" else "SP"), disabled=True)
                
                # Importância herdada do catálogo macro
                val_importancia_automatica = str(dados_aux_linha.get("Importância", "Ordinária"))
                importancia = "Alta" if val_importancia_automatica == "Estratégica" else ("Baixa" if val_importancia_automatica == "Ordinária" else "Média")
                st.text_input("Importância da Atividade (Herdada)", value=importancia, disabled=True)
                
                tema = st.selectbox("Tema da Atividade", LISTA_TEMAS)
                objetivo = st.selectbox("Objetivo da Atividade", LISTA_OBJETIVOS)
                tipo_atividade = st.selectbox("Tipo de Atividade", LISTA_TIPOS_ATIVIDADE)
                periculosidade = st.selectbox("Periculosidade/Insalubridade", LISTA_PERIGOS)

            with aba3:
                # REFEITO CONFORME DIRETRIZ: Dropdown de servidores filtrado dinamicamente pela UF da Ação (uf_usuario do SSO)
                uf_filtro_servidor = uf_usuario if uf_usuario != "Acesso Restrito" else "SP"
                df_servidores_filtrados = df_servidores[df_servidores["UF_Servidor"] == uf_filtro_servidor]
                
                if not df_servidores_filtrados.empty:
                    lista_nomes_servidores = sorted(df_servidores_filtrados["Servidor"].dropna().unique().tolist())
                    servidor = st.selectbox("Servidor Responsável", lista_nomes_servidores)
                    
                    # PROCV AUTOMÁTICO DA EQUIPE AUXILIAR
                    dados_serv_linha = df_servidores_filtrados[df_servidores_filtrados["Servidor"] == servidor].iloc[0]
                    uf_servidor = str(dados_serv_linha.get("UF_Servidor", uf_filtro_servidor))
                    lotacao = str(dados_serv_linha.get("Lotacao", "Sede Superintendência"))
                    equipe_emergencia = str(dados_serv_linha.get("Equipe_Emergencias", "Não"))
                else:
                    st.warning(f"⚠️ Nenhum servidor localizado no catálogo auxiliar para a UF: {uf_filtro_servidor}")
                    servidor = st.text_input("Servidor (Entrada Manual Emergencial)", value="")
                    uf_servidor = uf_filtro_servidor
                    lotacao = "Sede Superintendência"
                    equipe_emergencia = "Não"

                st.text_input("UF do Servidor (Automático)", value=uf_servidor, disabled=True)
                st.text_input("Lotação (Automático)", value=lotacao, disabled=True)
                st.text_input("Faz parte da Equipe de Emergências? (Automático)", value=equipe_emergencia, disabled=True)
                num_pcdp = st.text_input("Número da PCDP", value=str(registro_selecionado["Número da PCDP"]) if registro_selecionado is not None else "")
                
                st.markdown("<p style='font-weight: bold; margin-top:10px; color:#03170a;'>📍 Geolocalização da Atividade</p>", unsafe_allow_html=True)
                pais = st.text_input("País", value="Brasil", disabled=True)
                
                # REFEITO CONFORME DIRETRIZ: Caixa de seleção de UFs e preenchimento automático do Estado por Extenso
                uf_ocorrencia = st.selectbox("UF Onde Ocorreu/Ocorrerá a Ação", LISTA_UFS_COMPLETA)
                estado_local = MAPEAMENTO_ESTADOS_COMPLETO[uf_ocorrencia]
                st.text_input("Estado_Local_Acao (Automático)", value=estado_local, disabled=True)
                
                # REFEITO CONFORME DIRETRIZ: Municípios reativos com busca e escrita via API do IBGE
                lista_municipios_uf = obter_municipios_ibge(uf_ocorrencia)
                municipio = st.selectbox("Municipio Onde Ocorreu/Ocorrerá a Ação", lista_municipios_uf if lista_municipios_uf else ["Superintendência Sede"])

            with aba4:
                dt_inicio = st.date_input("Data de Início", value=val_dt_inicio)
                dt_termino = st.date_input("Data de Término", value=val_dt_termino)
                dias_plan = st.number_input("Dias_Gastos_Plan", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Plan"))
                dias_exec = st.number_input("Dias_Gastos_Exec", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Exec"))
                origem_recurso = st.selectbox("Origem do Recurso", LISTA_ORIGENS_RECURSO)
                
                st.markdown("<p style='font-weight: bold; margin-top:15px; color:#03170a;'>Valores Orçamentários (Planejado vs Executado)</p>", unsafe_allow_html=True)
                c_pl, c_ex = st.columns(2)
                with c_pl:
                    rec_p_diarias = st.number_input("Rec_Plan_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Diarias"), format="%.2f")
                    rec_p_passagens = st.number_input("Rec_Plan_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Passagens"), format="%.2f")
                    rec_p_outras = st.number_input("Rec_Plan_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Outras_Despesas"), format="%.2f")
                with c_ex:
                    rec_e_diarias = st.number_input("Rec_Exec_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Diarias"), format="%.2f")
                    rec_e_passagens = st.number_input("Rec_Exec_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Passagens"), format="%.2f")
                    rec_e_outras = st.number_input("Rec_Exec_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Outras_Despesas"), format="%.2f")

            with aba5:
                obs = st.text_area("Observações", value=str(registro_selecionado["Observações"]) if registro_selecionado is not None else "")
                justificativa = "" # Atividade nunca possui justificativa PNAPA
                st.info("ℹ️ Campo Justificativa ocultado. Regra aplicada: Habilitado apenas para cadastro de Ações.")

            meta_indicador = ""

        # Botão principal de envio individual dentro do formulário
        btn_enviar_individual = st.form_submit_button(label="🚀 Gravar Registro no SharePoint", type="primary")

    # =================================================================
    # PROCESSAMENTO DO ENVIO: INDIVIDUAL OU EM LOTE
    # =================================================================
    
    # 1. DISPARO DO ENVIO INDIVIDUAL
    if btn_enviar_individual:
        payload_unico = payload_gerador(
            val_ano, val_num_acao, val_nome_acao, val_indicador, nivel_selecionado, 
            nome_atividade, andamento, resultado_indicador, doc_probatorio, uf_acao, 
            importancia, tema, objetivo, tipo_atividade, periculosidade, servidor, 
            uf_servidor, lotacao, equipe_emergencia, num_pcdp, pais, uf_ocorrencia, 
            estado_local, municipio, dt_inicio, dt_termino, dias_plan, dias_exec, 
            origem_recurso, rec_p_diarias, rec_p_passagens, rec_p_outras, rec_e_diarias, 
            rec_e_passagens, rec_e_outras, obs, justificativa, id_atual, modo, df_atual
        )
        executar_envio_sharepoint([payload_unico])

    # 2. OPÇÃO EM LOTE (Apenas para inserção de novas Atividades)
    if modo == "➕ Inserir Nova Linha" and nivel_selecionado == "Atividade":
        st.markdown("---")
        with st.popover("👥 Deseja cadastrar esta atividade para múltiplos servidores? (Carga em Lote)", use_container_width=True):
            st.markdown("### 👥 Cadastro Multi-Servidor / Lote")
            
            lista_servidores_lote = st.text_area(
                "Digite os nomes dos Servidores (um por linha):", 
                value=servidor,
                help="Cada linha gerará uma atividade idêntica no SharePoint."
            )
            
            servidores_finais = [s.strip() for s in lista_servidores_lote.split("\n") if s.strip()]
            st.info(f"📋 Serão gerados **{len(servidores_finais)}** registros simultâneos no SharePoint.")
            
            st.markdown("---")
            st.markdown("### 🎯 Espelhamento de Campos")
            st.caption("Desmarque os campos que deseja enviar EM BRANCO para edição posterior:")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if st.button("✓ Marcar Todos"): 
                    st.session_state["chk_lote_all"] = True
            with col_c2:
                if st.button("✕ Desmarcar Todos"): 
                    st.session_state["chk_lote_all"] = False
            
            status_padrao = st.session_state.get("chk_lote_all", True)
            
            espelhar_detalhes = st.checkbox("Espelhar Detalhes da Atividade e Documentos SEI", value=status_padrao)
            espelhar_local = st.checkbox("Espelhar Localidade (País, UF, Estado, Município)", value=status_padrao)
            espelhar_crono = st.checkbox("Espelhar Cronograma (Datas e Dias Gastos)", value=status_padrao)
            espelhar_custos = st.checkbox("Espelhar Custos (Valores Planejados e Executados)", value=status_padrao)
            espelhar_just = st.checkbox("Espelhar Justificativas e Observações", value=status_padrao)
            
            if st.button("🔥 Disparar Carga em Lote para o SharePoint", type="primary", use_container_width=True):
                payloads_lote = []
                id_base_calculado = int(pd.to_numeric(df_atual["Id"], errors='coerce').dropna().max() + 1) if not df_atual.empty else 1
                
                for idx, serv_lote in enumerate(servidores_finais):
                    id_loop = str(id_base_calculado + idx)
                    
                    p_nome_atv = nome_atividade if espelhar_detalhes else ""
                    p_andamento = andamento if espelhar_detalhes else "Não Iniciada"
                    p_res_ind = resultado_indicador if espelhar_detalhes else ""
                    p_doc = doc_probatorio if espelhar_detalhes else ""
                    
                    p_pais = pais if espelhar_local else "Brasil"
                    p_uf_oc = uf_ocorrencia if espelhar_local else ""
                    p_est = estado_local if espelhar_local else ""
                    p_mun = municipio if espelhar_local else ""
                    
                    p_ini = str(dt_inicio) if espelhar_crono else ""
                    p_fim = str(dt_termino) if espelhar_crono else ""
                    p_d_pl = dias_plan if espelhar_crono else 0.0
                    p_d_ex = dias_exec if espelhar_crono else 0.0
                    
                    p_origem = origem_recurso if espelhar_custos else ""
                    p_rp_d = rec_p_diarias if espelhar_custos else 0.0
                    p_rp_p = rec_p_passagens if espelhar_custos else 0.0
                    p_rp_o = rec_p_outras if espelhar_custos else 0.0
                    p_re_d = rec_e_diarias if espelhar_custos else 0.0
                    p_re_p = rec_e_passagens if espelhar_custos else 0.0
                    p_re_o = rec_e_outras if espelhar_custos else 0.0
                    
                    p_obs = obs if espelhar_just else ""
                    p_just = justificativa if espelhar_just else ""
                    
                    payload_linha = {
                        "Acao": "Inserir", 
                        "Id": id_loop, 
                        "Ano da Ação": int(val_ano) if val_ano else 2026,
                        "Número da Ação PNAPA": str(val_num_acao), 
                        "Nome da Ação PNAPA": str(val_nome_acao),
                        "Nível": nivel_selecionado, 
                        "Nome da Atividade": p_nome_atv, 
                        "Andamento": p_andamento,
                        "Indicador": str(val_indicador), 
                        "Meta_Indicador": "", 
                        "Resultado_Indicador": p_res_ind,
                        "Doc_Probatorio_Exec": p_doc, 
                        "UF_Acao_PNAPA": uf_acao, 
                        "Importância da Atividade": importancia,
                        "Tema da Atividade": tema, 
                        "Objetivo da Atividade": objetivo, 
                        "Tipo de Atividade": tipo_atividade,
                        "Periculosidade/Insalubridade": periculosidade, 
                        "Servidor": serv_lote, 
                        "UF_Servidor": uf_servidor,
                        "Lotação": lotacao, 
                        "Faz parte da Equipe de Emergências": equipe_emergencia, 
                        "Número da PCDP": num_pcdp,
                        "País": p_pais, 
                        "UF Onde Ocorreu/Ocorrerá a Ação": p_uf_oc, 
                        "Estado_Local_Acao": p_est,
                        "Municipio Onde Ocorreu/Ocorrerá a Ação": p_mun, 
                        "Data de Início": p_ini, 
                        "Data de Término": p_fim,
                        "Dias_Gastos_Plan": p_d_pl, 
                        "Dias_Gastos_Exec": p_d_ex, 
                        "Origem do Recurso": p_origem,
                        "Rec_Plan_Diarias": p_rp_d, 
                        "Rec_Plan_Passagens": p_rp_p, 
                        "Rec_Plan_Outras_Despesas": p_rp_o,
                        "Rec_Plan_Total": (p_rp_d + p_rp_p + p_rp_o), 
                        "Rec_Exec_Diarias": p_re_d, 
                        "Rec_Exec_Passagens": p_re_p,
                        "Rec_Exec_Outras_Despesas": p_re_o, 
                        "Rec_Exec_Total": (p_re_d + p_re_p + p_re_o),
                        "Observações": p_obs, 
                        "Justificativa_Acao_PNAPA": p_just
                    }
                    payloads_lote.append(payload_linha)
                
                executar_envio_sharepoint(payloads_lote)

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
                    resposta_del = requests.post(URL_FLOW_PRINCIPAL, json={"Acao": "Excluir", "Id": str(id_atual)}, timeout=20)
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

# --- TELA 7: GERENCIAR AÇÕES PNAPA (TABELA AUXILIAR) ---
elif modo == "🗂️ Gerenciar Ações PNAPA":
    st.markdown("<h3>🗂️ Gerenciamento de Ações Cadastradas (Tabela Auxiliar via SharePoint)</h3>", unsafe_allow_html=True)
    
    st.write("#### 📋 Ações Ativas no Catálogo")
    if df_pnapas.empty:
        st.info("Nenhuma ação do PNAPA cadastrada na base de dados.")
    else:
        # Oculta colunas de metadados da Microsoft se houverem
        colunas_validas_pna = [col for col in ["ID_PNAPA", "Ano", "Num_Acao_PNAPA", "Acao_Ano", "Nome_Acao_Completo", "Nome_Acao_Apelido", "Importância", "Indicador"] if col in df_pnapas.columns]
        df_limpo_pna = df_pnapas[colunas_validas_pna].sort_values(by=["Ano", "Num_Acao_PNAPA"], ascending=[False, True])
        
        def estilar_pna(linha): return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        st.dataframe(df_limpo_pna.reset_index(drop=True).style.apply(estilar_pna, axis=1), use_container_width=True)
        
    st.markdown("---")
    tp_add, tp_edit, tp_del = st.tabs(["➕ Cadastrar Nova Ação", "📝 Alterar Cadastro", "🗑️ Remover Ação"])
    
    with tp_add:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_ano = st.number_input("Ano da Ação PNAPA:", min_value=2020, max_value=2100, value=2026, step=1, key="pna_ins_ano")
            # --- MODIFICADO PARA TEXTO LIVRE ---
            p_num = st.text_input("Número da Ação PNAPA:", placeholder="Ex: CEN001", key="pna_ins_num").strip()
            p_importancia = st.selectbox("Importância da Ação:", ["Ordinária", "Estratégica"], key="pna_ins_imp")
        with col_p2:
            p_nome_completo = st.text_input("Nome da Ação Completo:", placeholder="Ex: Reuniões do Plano de Área do Porto de Santos", key="pna_ins_comp")
            p_nome_apelido = st.text_input("Nome da Ação Apelido (Amigável):", placeholder="Ex: Reuniões Plano de Área Santos", key="pna_ins_apel")
            p_indicador = st.text_input("Indicador Associado:", placeholder="Ex: Reuniões Atendidas", key="pna_ins_ind")
            
        # Concatenação flexível (ex: CEN001-2026)
        p_acao_ano = f"{p_num}-{int(p_ano)}" if p_num else f"-[{int(p_ano)}]"
        st.info(f"**Código Identificador Gerado Automaticamente (Acao_Ano):** {p_acao_ano}")
        
        if st.button("Gravar Nova Ação"):
            if not p_num or not p_nome_completo or not p_nome_apelido:
                st.error("❌ Os campos de Número da Ação, Nome Completo e Nome Apelido são obrigatórios.")
            else:
                next_id_pnapa = int(pd.to_numeric(df_pnapas["ID_PNAPA"], errors='coerce').dropna().max() + 1) if not df_pnapas.empty else 1
                payload_novo_pna = {
                    "Acao": "Inserir",
                    "ID_PNAPA": next_id_pnapa,
                    "Ano": int(p_ano),
                    "Num_Acao_PNAPA": str(p_num), # <- Enviado como String
                    "Acao_Ano": p_acao_ano,
                    "Nome_Acao_Completo": p_nome_completo,
                    "Nome_Acao_Apelido": p_nome_apelido,
                    "Importância": p_importancia,
                    "Indicador": p_indicador
                }
                with st.spinner("Sincronizando com o SharePoint..."):
                    executar_api_pnapas(payload_novo_pna)
                    time.sleep(2)
                    st.cache_data.clear()
                st.success(f"🎉 Ação {p_acao_ano} inserida com sucesso!")
                st.rerun()

    with tp_edit:
        if not df_pnapas.empty:
            st.markdown("### 📝 Filtrar e Editar Ação")
            
            # --- NOVO FILTRO DE ANO PARA EDIÇÃO ---
            anos_disponiveis_edit = sorted(df_pnapas["Ano"].dropna().astype(int).unique().tolist(), reverse=True)
            ano_selecionado_edit = st.selectbox("1. Filtrar Ações pelo Ano:", anos_disponiveis_edit, key="pna_ed_filtro_ano")
            
            # Filtra o DataFrame de PNAPAs pelo ano escolhido antes de montar o dropdown de seleção
            df_pnapas_filtrado_edit = df_pnapas[df_pnapas["Ano"].astype(int) == ano_selecionado_edit]
            
            if not df_pnapas_filtrado_edit.empty:
                lista_selecao_pna = (df_pnapas_filtrado_edit["Acao_Ano"].astype(str) + " - " + df_pnapas_filtrado_edit["Nome_Acao_Apelido"].astype(str)).tolist()
                sel_pnapa_str = st.selectbox("2. Selecione a Ação que deseja editar:", lista_selecao_pna, key="pna_edit_sel")
                
                acao_ano_sel = sel_pnapa_str.split(" - ")[0]
                dados_atuais_p = df_pnapas_filtrado_edit[df_pnapas_filtrado_edit["Acao_Ano"].astype(str) == acao_ano_sel].iloc[0]
                id_pnapa_edit = int(float(dados_atuais_p["ID_PNAPA"]))
                
                col_pe1, col_pe2 = st.columns(2)
                with col_pe1:
                    ed_nome_completo = st.text_input("Alterar Nome Completo:", value=str(dados_atuais_p.get("Nome_Acao_Completo", "")), key="pna_ed_comp")
                    ed_nome_apelido = st.text_input("Alterar Nome Apelido:", value=str(dados_atuais_p.get("Nome_Acao_Apelido", "")), key="pna_ed_apel")
                with col_pe2:
                    idx_imp = 0 if str(dados_atuais_p.get("Importância", "")) == "Ordinária" else 1
                    ed_importancia = st.selectbox("Alterar Importância:", ["Ordinária", "Estratégica"], index=idx_imp, key="pna_ed_imp")
                    ed_indicador = st.text_input("Alterar Indicador:", value=str(dados_atuais_p.get("Indicador", "")), key="pna_ed_ind")
                    
                if st.button("Salvar Modificações da Ação"):
                    payload_editar_pna = {
                        "Acao": "Editar",
                        "ID_PNAPA": id_pnapa_edit,
                        "Ano": int(dados_atuais_p["Ano"]),
                        "Num_Acao_PNAPA": str(dados_atuais_p["Num_Acao_PNAPA"]),
                        "Acao_Ano": acao_ano_sel,
                        "Nome_Acao_Completo": ed_nome_completo,
                        "Nome_Acao_Apelido": ed_nome_apelido,
                        "Importância": ed_importancia,
                        "Indicador": ed_indicador
                    }
                    with st.spinner("Atualizando dados no SharePoint..."):
                        executar_api_pnapas(payload_editar_pna)
                        time.sleep(2)
                        st.cache_data.clear()
                    st.success(f"🚀 Ação {acao_ano_sel} atualizada com sucesso!")
                    st.rerun()
            else:
                st.warning(f"Nenhuma ação cadastrada para o ano de {ano_selecionado_edit}.")
        else:
            st.info("Nenhuma ação disponível para edição.")

    with tp_del:
        if not df_pnapas.empty:
            st.markdown("### 🗑️ Filtrar e Remover Ação")
            
            # --- NOVO FILTRO DE ANO PARA EXCLUSÃO ---
            anos_disponiveis_del = sorted(df_pnapas["Ano"].dropna().astype(int).unique().tolist(), reverse=True)
            ano_selecionado_del = st.selectbox("1. Filtrar Ações pelo Ano:", anos_disponiveis_del, key="pna_del_filtro_ano")
            
            # Filtra o DataFrame de PNAPAs pelo ano escolhido antes de montar o dropdown de remoção
            df_pnapas_filtrado_del = df_pnapas[df_pnapas["Ano"].astype(int) == ano_selecionado_del]
            
            if not df_pnapas_filtrado_del.empty:
                lista_del_pna = (df_pnapas_filtrado_del["Acao_Ano"].astype(str) + " - " + df_pnapas_filtrado_del["Nome_Acao_Apelido"].astype(str)).tolist()
                del_pnapa_str = st.selectbox("2. Selecione a Ação para REMOVER:", lista_del_pna, key="pna_del_sel")
                
                acao_ano_del = del_pnapa_str.split(" - ")[0]
                id_pnapa_del = int(float(df_pnapas_filtrado_del[df_pnapas_filtrado_del["Acao_Ano"].astype(str) == acao_ano_del]["ID_PNAPA"].iloc[0]))
                
                if st.button("❌ Eliminar Ação", disabled=not st.checkbox(f"Confirmo que desejo excluir permanentemente a ação {acao_ano_del}", key="chk_pna_del")):
                    with st.spinner("Removendo do SharePoint..."):
                        executar_api_pnapas({"Acao": "Excluir", "ID_PNAPA": id_pnapa_del})
                        time.sleep(2)
                        st.cache_data.clear()
                    st.success(f"Ação {acao_ano_del} removida com sucesso!")
                    st.rerun()
            else:
                st.warning(f"Nenhuma ação cadastrada para o ano de {ano_selecionado_del}.")
        else:
            st.info("Nenhuma ação disponível para exclusão.")
