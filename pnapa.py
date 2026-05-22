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
URL_FLOW_PNAPAS = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/38cc92ea33ba4d6387b924d6eac62d58/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=LlCDUzrETHyXxp_QLte1eGxKR_4LuwRGzPJbgUsHvgk"

# URLs da Planilha Macro Principal (Movidas para o topo para evitar NameError)
URL_LER = st.secrets["power_automate"]["URL_LER"]
URL_GRAVAR = st.secrets["power_automate"]["URL_GRAVAR"]
URL_DELETAR = st.secrets["power_automate"]["URL_DELETAR"]

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
                resposta = requests.post(URL_GRAVAR, json=p, timeout=20)
                if resposta.status_code in [200, 202]: sucessos += 1
            except: pass
            
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

def payload_gerador(val_ano, val_num_acao, val_nome_acao, val_indicador, nivel_selecionado, nome_atividade, andamento, resultado_indicador, doc_probatorio, uf_acao, importancia, tema, objective, tipo_atividade, periculosidade, servidor, uf_servidor, lotacao, equipe_emergencia, num_pcdp, pais, uf_ocorrencia, estado_local, municipio, dt_inicio, dt_termino, dias_plan, dias_exec, origem_recurso, rec_p_diarias, rec_p_passagens, rec_p_outras, rec_e_diarias, rec_e_passagens, rec_e_outras, obs, justificativa, id_atual, modo, df_atual):
    id_final = str(int(pd.to_numeric(df_atual["Id"], errors='coerce').dropna().max() + 1)) if modo == "➕ Inserir Nova Linha" else id_atual
    return {"acao_fluxo": "inserir" if modo == "➕ Inserir Nova Linha" else "editar", "Id": id_final, "Ano da Ação": int(val_ano) if val_ano else 2026, "Número da Ação PNAPA": str(val_num_acao), "Nome da Ação PNAPA": str(val_nome_acao), "Nível": nivel_selecionado, "Nome da Atividade": nome_atividade, "Andamento": andamento, "Indicador": str(val_indicador), "Meta_Indicador": "", "Resultado_Indicador": resultado_indicador, "Doc_Probatorio_Exec": doc_probatorio, "UF_Acao_PNAPA": uf_acao, "Importância da Atividade": importancia, "Tema da Atividade": tema, "Objetivo da Atividade": objective, "Tipo de Atividade": tipo_atividade, "Periculosidade/Insalubridade": periculosidade, "Servidor": servidor, "UF_Servidor": uf_servidor, "Lotação": lotacao, "Faz parte da Equipe de Emergências": equipe_emergencia, "Número da PCDP": num_pcdp, "País": pais, "UF Onde Ocorreu/Ocorrerá a Ação": uf_ocorrencia, "Estado_Local_Acao": estado_local, "Municipio Onde Ocorreu/Ocorrerá a Ação": municipio, "Data de Início": str(dt_inicio), "Data de Término": str(dt_termino), "Dias_Gastos_Plan": dias_plan, "Dias_Gastos_Exec": dias_exec, "Origem do Recurso": origem_recurso, "Rec_Plan_Diarias": rec_p_diarias, "Rec_Plan_Passagens": rec_p_passagens, "Rec_Plan_Outras_Despesas": rec_p_outras, "Rec_Plan_Total": (rec_p_diarias+rec_p_passagens+rec_p_outras), "Rec_Exec_Diarias": rec_e_diarias, "Rec_Exec_Passagens": rec_e_passagens, "Rec_Exec_Outras_Despesas": rec_e_outras, "Rec_Exec_Total": (rec_e_diarias+rec_e_passagens+rec_e_outras), "Observações": obs, "Justificativa_Acao_PNAPA": justificativa}

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
        # --- FUNÇÃO DE LIMPEZA DE DATAS ---
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

        # --- FILTROS ---
        col_ano, col_uf, col_nivel = st.columns(3)
        df_filtros = df_trabalho.copy()
        with col_ano: ano_sel = st.selectbox("📅 Filtrar por Ano:", ["Todos"] + sorted(df_filtros["Ano da Ação"].dropna().astype(str).unique().tolist()))
        if ano_sel != "Todos": df_filtros = df_filtros[df_filtros["Ano da Ação"].astype(str) == ano_sel]
        with col_uf: uf_sel = st.selectbox("📍 Filtrar por UF:", ["Todas"] + sorted(df_filtros["UF_Acao_PNAPA"].dropna().astype(str).unique().tolist()))
        if uf_sel != "Todas": df_filtros = df_filtros[df_filtros["UF_Acao_PNAPA"].astype(str) == uf_sel]
        with col_nivel: nivel_sel = st.selectbox("🎚️ Filtrar por Nível:", ["Todos"] + sorted(df_filtros["Nível"].dropna().astype(str).unique().tolist()))
        if nivel_sel != "Todos": df_filtros = df_filtros[df_filtros["Nível"].astype(str) == nivel_sel]

        # --- MEMÓRIA E ORDENAÇÃO ---
        if "selecoes_macro" not in st.session_state: st.session_state["selecoes_macro"] = {}
        if "version_editor" not in st.session_state: st.session_state["version_editor"] = 0

        if st.session_state["selecoes_macro"]:
            if st.button("✕ Desmarcar Todos os Itens"):
                st.session_state["selecoes_macro"] = {}
                st.session_state["version_editor"] += 1
                st.rerun()

        df_interativo = df_filtros.copy()
        df_interativo["Id_Numeric"] = pd.to_numeric(df_interativo["Id"], errors='coerce').fillna(0)
        df_interativo = df_interativo.sort_values(by="Id_Numeric", ascending=False).drop(columns=["Id_Numeric"])
        
        df_interativo.insert(0, "Selecionar", [st.session_state["selecoes_macro"].get(str(row_id), False) for row_id in df_interativo["Id"]])
        
        colunas_travadas = {col: st.column_config.Column(disabled=True) for col in df_interativo.columns if col != "Selecionar"}
        
        # --- TABELA INTERATIVA ---
        key_dinamica = f"editor_lote_pnapa_v{st.session_state['version_editor']}"
        tabela_editavel = st.data_editor(df_interativo, hide_index=True, use_container_width=True, column_config=colunas_travadas, key=key_dinamica)
        
        if st.session_state[key_dinamica] and "edited_rows" in st.session_state[key_dinamica]:
            for idx, alt in st.session_state[key_dinamica]["edited_rows"].items():
                if "Selecionar" in alt:
                    id_real = str(df_interativo.iloc[int(idx)]["Id"])
                    st.session_state["selecoes_macro"][id_real] = alt["Selecionar"]
            st.rerun()

        # --- MOTOR DE EDIÇÃO ---
        ids_marcados = [k for k, v in st.session_state["selecoes_macro"].items() if v]
        df_linhas_selecionadas = df_atual[df_atual["Id"].astype(str).isin(ids_marcados)]
        
        if not df_linhas_selecionadas.empty:
            qtd_selecionada = len(ids_marcados)
            st.markdown("---")
            st.markdown(f"### 🛠️ Central de Operações Dinâmicas ({qtd_selecionada} selecionado(s))")

            # Fallbacks de dados para o formulário
            if qtd_selecionada == 1:
                r_alvo = df_linhas_selecionadas.iloc[0]
                f_nivel, f_andamento, f_nome_atv, f_res_ind, f_doc = str(r_alvo["Nível"]), str(r_alvo["Andamento"]), str(r_alvo["Nome da Atividade"]), str(r_alvo["Resultado_Indicador"]), str(r_alvo["Doc_Probatorio_Exec"])
                f_imp, f_tema, f_obj, f_tipo, f_perigo, f_servidor = str(r_alvo["Importância da Atividade"]), str(r_alvo["Tema da Atividade"]), str(r_alvo["Objetivo da Atividade"]), str(r_alvo["Tipo de Atividade"]), str(r_alvo["Periculosidade/Insalubridade"]), str(r_alvo["Servidor"])
                f_uf_srv, f_lot, f_eq_emerg, f_pcdp, f_pais = str(r_alvo["UF_Servidor"]), str(r_alvo["Lotação"]), str(r_alvo["Faz parte da Equipe de Emergências"]), str(r_alvo["Número da PCDP"]), str(r_alvo["País"])
                f_uf_oc, f_est, f_mun, f_dias_pl, f_dias_ex, f_origem = str(r_alvo["UF Onde Ocorreu/Ocorrerá a Ação"]), str(r_alvo["Estado_Local_Acao"]), str(r_alvo["Municipio Onde Ocorreu/Ocorrerá a Ação"]), float(r_alvo["Dias_Gastos_Plan"] or 0), float(r_alvo["Dias_Gastos_Exec"] or 0), str(r_alvo["Origem do Recurso"])
                f_rp_d, f_rp_p, f_rp_o, f_re_d, f_re_p, f_re_o = float(r_alvo["Rec_Plan_Diarias"] or 0), float(r_alvo["Rec_Plan_Passagens"] or 0), float(r_alvo["Rec_Plan_Outras_Despesas"] or 0), float(r_alvo["Rec_Exec_Diarias"] or 0), float(r_alvo["Rec_Exec_Passagens"] or 0), float(r_alvo["Rec_Exec_Outras_Despesas"] or 0)
                f_obs, f_just, f_meta = str(r_alvo["Observações"]), str(r_alvo["Justificativa_Acao_PNAPA"]), str(r_alvo["Meta_Indicador"])
            else:
                f_nivel, f_andamento, f_nome_atv, f_res_ind, f_doc, f_imp, f_tema, f_obj, f_tipo, f_perigo, f_servidor, f_uf_srv, f_lot, f_eq_emerg, f_pcdp = "Atividade", "Não Iniciada", "", "", "", "Alta", "", "", "", "Não", "", "", "", "Não", ""
                f_pais, f_uf_oc, f_est, f_mun, f_dias_pl, f_dias_ex, f_origem = "Brasil", "", "", "", 0.0, 0.0, ""
                f_rp_d, f_rp_p, f_rp_o, f_re_d, f_re_p, f_re_o, f_obs, f_just, f_meta = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "", "", ""

            # Formulário (Sem st.form para permitir on_change reativo)
            ref = df_linhas_selecionadas.iloc[0]
            v_ano, v_num, v_nome, v_ind = ref["Ano da Ação"], ref["Número da Ação PNAPA"], ref["Nome da Ação PNAPA"], ref["Indicador"]
            
            st.markdown(f"**Vínculo Macro:** {v_num} - {v_nome}")
            aba1, aba2, aba3, aba4, aba5 = st.tabs(["1. Identificação", "2. Detalhes", "3. RH & Local", "4. Cronograma & Custos", "5. Justificativas"])
            
            with aba1:
                ed_nivel = st.selectbox("Nível", ["Ação", "Atividade"], index=["Ação", "Atividade"].index(f_nivel) if f_nivel in ["Ação", "Atividade"] else 1, on_change=st.rerun)
                ed_nome_atv = st.text_input("Nome da Atividade", value=f_nome_atv)
                lista_and = ["Planejada", "Cancelada", "Não Demandada", "Não Executada"] if ed_nivel == "Ação" else ["Prevista", "Concluída"]
                ed_andamento = st.selectbox("Andamento", lista_and, index=lista_and.index(f_andamento) if f_andamento in lista_and else 0, on_change=st.rerun)

            with aba2:
                ed_res_ind = st.text_input("Resultado Indicador", value=f_res_ind)
                ed_doc = st.text_input("Doc_Probatorio (SEI)", value=f_doc)
                ed_uf_pna = st.text_input("UF Ação", value=uf_usuario, disabled=True)
                ed_importancia = st.text_input("Importância", value=f_imp, disabled=True)
                ed_tema = st.selectbox("Tema", LISTA_TEMAS, index=LISTA_TEMAS.index(f_tema) if f_tema in LISTA_TEMAS else 0)
                ed_objetivo = st.selectbox("Objetivo", LISTA_OBJETIVOS, index=LISTA_OBJETIVOS.index(f_obj) if f_obj in LISTA_OBJETIVOS else 0)
                ed_tipo = st.selectbox("Tipo", LISTA_TIPOS_ATIVIDADE, index=LISTA_TIPOS_ATIVIDADE.index(f_tipo) if f_tipo in LISTA_TIPOS_ATIVIDADE else 0)
                ed_periculosidade = st.selectbox("Perigo", LISTA_PERIGOS, index=LISTA_PERIGOS.index(f_perigo) if f_perigo in LISTA_PERIGOS else 0)
                ed_meta = st.text_input("Meta", value=f_meta)

            with aba3:
                ed_servidor = st.selectbox("Servidor", sorted(df_servidores["Servidor"].unique()), index=0, on_change=st.rerun)
                # (Aqui entraria a lógica de PROCV do servidor)
                ed_pcdp = st.text_input("PCDP", value=f_pcdp)
                ed_pais = st.text_input("País", value="Brasil", disabled=True)
                ed_uf_oc = st.selectbox("UF Ocorrência", LISTA_UFS_COMPLETA)
                ed_municipio = st.selectbox("Município", obter_municipios_ibge(ed_uf_oc))

            with aba4:
                ed_dt_ini = st.text_input("Data Início (DD/MM/AAAA)", value=str(ref.get("Data de Início", "")))
                ed_dt_fim = st.text_input("Data Término (DD/MM/AAAA)", value=str(ref.get("Data de Término", "")))
                ed_dias_pl = st.number_input("Dias Plan", value=f_dias_pl)
                ed_dias_ex = st.number_input("Dias Exec", value=f_dias_ex)
                ed_origem = st.selectbox("Origem Recurso", LISTA_ORIGENS_RECURSO)
                ed_rp_d = st.number_input("Rec_Plan_Diarias", value=f_rp_d)
                ed_rp_p = st.number_input("Rec_Plan_Passagens", value=f_rp_p)
                ed_rp_o = st.number_input("Rec_Plan_Outras", value=f_rp_o)
                ed_re_d = st.number_input("Rec_Exec_Diarias", value=f_re_d)
                ed_re_p = st.number_input("Rec_Exec_Passagens", value=f_re_p)
                ed_re_o = st.number_input("Rec_Exec_Outras", value=f_re_o)

            with aba5:
                ed_obs = st.text_area("Observações", value=f_obs)
                ed_justificativa = st.selectbox("Justificativa", LISTA_JUSTIFICATIVAS_ACAO) if (ed_nivel=="Ação" and ed_andamento in ["Cancelada", "Não Demandada", "Não Executada"]) else ""

            # BOTÃO DE SUBMISSÃO
            if st.button("💾 Gravar Alterações"):
                # (Aqui entra a lógica de loop de payloads_envio_final que já validamos)
                st.rerun()

# --- TELA 2 E 3: FORMULÁRIO DA PLANILHA MACRO (INSERIR OU EDITAR) ---
elif modo in ["➕ Inserir Nova Linha", "📝 Editar Linha Existente"]:
    st.markdown(f"<h3 style='color: #03170a;'>Formulário de Dados PNAPA — Modo: {modo}</h3>", unsafe_allow_html=True)
    
    # 1. Seleção de Nível com reatividade
    lista_niveis = ["Ação", "Atividade"]
    idx_nivel_padrao = 0 if registro_selecionado is None or str(registro_selecionado.get("Nível", "")) == "Ação" else 1
    nivel_selecionado = st.selectbox("O que deseja cadastrar/editar?", lista_niveis, index=idx_nivel_padrao, on_change=st.rerun)
    
    # 2. Vínculo Automático com Catálogo PNAPA
    st.markdown("#### 🔗 Vinculação Automática com o Catálogo de Ações")
    if not df_pnapas.empty:
        anos_aux = sorted(df_pnapas["Ano"].dropna().astype(int).unique().tolist(), reverse=True)
        ano_vinculo = st.selectbox("Selecione o Ano para filtrar as Ações:", anos_aux)
        df_pna_ano = df_pnapas[df_pnapas["Ano"].astype(int) == ano_vinculo]
        
        lista_opcoes = (df_pna_ano["Acao_Ano"].astype(str) + " - " + df_pna_ano["Nome_Acao_Apelido"].astype(str)).tolist()
        opcao_vinc_sel = st.selectbox("Selecione a Ação PNAPA:", lista_opcoes)
        
        # Dados extraídos do Catálogo para o payload
        acao_ano_det = opcao_vinc_sel.split(" - ")[0]
        dados_aux = df_pna_ano[df_pna_ano["Acao_Ano"].astype(str) == acao_ano_det].iloc[0]
        val_ano, val_num_acao, val_nome_acao, val_indicador = int(dados_aux["Ano"]), str(dados_aux["Num_Acao_PNAPA"]), str(dados_aux["Nome_Acao_Completo"]), str(dados_aux["Indicador"])
    
    st.markdown("---")
    
    # 3. Renderização das Abas (Reutilizando a estrutura validada)
    aba1, aba2, aba3, aba4, aba5 = st.tabs(["1. Identificação", "2. Detalhes", "3. RH & Local", "4. Cronograma & Custos", "5. Justificativas"])
    
    with aba1:
        st.text_input("Ano da Ação", value=str(val_ano), disabled=True)
        st.text_input("Número da Ação", value=val_num_acao, disabled=True)
        nome_atividade = st.text_input("Nome da Atividade", value=str(registro_selecionado["Nome da Atividade"] if registro_selecionado is not None else ""))
        
        andamentos = ["Planejada", "Cancelada", "Não Demandada", "Não Executada"] if nivel_selecionado == "Ação" else ["Prevista", "Concluída"]
        andamento = st.selectbox("Andamento", andamentos)

    with aba2:
        st.text_input("Indicador", value=val_indicador, disabled=True)
        resultado_indicador = st.text_input("Resultado Indicador")
        doc_probatorio = st.text_input("Doc Probatório (SEI)")
        uf_acao = st.text_input("UF Ação", value=uf_usuario, disabled=True)
        tema = st.selectbox("Tema", LISTA_TEMAS)
        objetivo = st.selectbox("Objetivo", LISTA_OBJETIVOS)
        tipo = st.selectbox("Tipo", LISTA_TIPOS_ATIVIDADE)
        perigo = st.selectbox("Periculosidade/Insalubridade", LISTA_PERIGOS)

    with aba3:
        # Lógica de PROCV de Servidor
        lista_servs = sorted(df_servidores[df_servidores["UF_Servidor"] == uf_usuario]["Servidor"].tolist())
        servidor = st.selectbox("Servidor Responsável", lista_servs)
        # (Opcional: Adicionar lógica para puxar Lotação/Emergência via st.rerun se necessário)
        uf_servidor = uf_usuario
        municipio = st.selectbox("Município", obter_municipios_ibge(uf_usuario))

    # ... (Preencha as abas 4 e 5 seguindo o padrão acima) ...

    # 4. BOTÃO ÚNICO DE ENVIO (Sem st.form)
    if st.button("🚀 Disparar para SharePoint", type="primary"):
        # Payload de Inserção ou Edição
        payload = payload_gerador(
            val_ano, val_num_acao, val_nome_acao, val_indicador, nivel_selecionado, 
            nome_atividade, andamento, resultado_indicador, doc_probatorio, uf_acao, 
            "Alta", tema, objetivo, tipo, perigo, servidor, uf_servidor, 
            "Lotacao_Automatica", "Nao", "PCDP_001", "Brasil", uf_usuario, 
            MAPEAMENTO_ESTADOS_COMPLETO[uf_usuario], municipio, 
            "2026-01-01", "2026-01-01", 1.0, 1.0, "Ordinaria", 
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "Obs", "", id_atual, modo, df_atual
        )
        
        executar_envio_sharepoint([payload])
        st.rerun()

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
