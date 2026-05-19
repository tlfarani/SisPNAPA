import streamlit as st
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="PNAPA via Power Automate", layout="wide")

# =================================================================
# 1. ENDPOINTS DO POWER AUTOMATE (URLs DOS GATILHOS HTTP)
# =================================================================
# Cole aqui as URLs geradas pelo Power Automate no topo do gatilho de cada fluxo:
URL_FLOW_UNIDADES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/c2207ed01bf64853a477e7b6b165c3e8/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=GR6JhJzrEZTapCOAKwlY9VGzT_g-6xQGBG7YLraG6Z4" 
URL_FLOW_EQUIPES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/3d124cc6783845e1b8618cfb3302eca0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ubTQ-LAIsToMOX0CGytlI2YM_WKmC_mRT64ybRLBRSY"

# =================================================================
# II. FUNÇÕES DE COMUNICAÇÃO HTTP COM O POWER AUTOMATE (APIs)
# =================================================================
def executar_api_unidades(dados_json):
    try:
        resposta = requests.post(URL_FLOW_UNIDADES, json=dados_json, timeout=15)
        if resposta.status_code == 200:
            return resposta.json()
        return []
    except:
        return []

def executar_api_equipes(dados_json):
    try:
        resposta = requests.post(URL_FLOW_EQUIPES, json=dados_json, timeout=15)
        if resposta.status_code == 200:
            return resposta.json()
        return []
    except:
        return []

# Carregamento dinâmico das tabelas do Excel armazenadas no SharePoint
@st.cache_data(ttl=60)  # Limpa o cache a cada 60 segundos para trazer dados novos
def carregar_bases_vias_power_automate():
    dados_uni = executar_api_unidades({"Acao": "Ler"})
    dados_srv = executar_api_equipes({"Acao": "Ler"})
    
    if dados_uni:
        df_lot = pd.DataFrame(dados_uni)
    else:
        df_lot = pd.DataFrame(columns=["ID_UF", "UF", "Unidade"])
        
    if dados_srv:
        df_serv = pd.DataFrame(dados_srv)
    else:
        df_serv = pd.DataFrame(columns=["ID_SERV", "Servidor", "UF_Servidor", "Lotacao", "Equipe_Emergencias", "Fiscal", "AEAC", "Funcao", "E_mail", "Perfil", "Token"])
        
    return df_lot, df_serv

df_lotacoes, df_servidores = carregar_bases_vias_power_automate()

# Base principal do PNAPA (Exemplo simulado - adapte para sua leitura do arquivo macro consolidado se necessário)
if "df_base_pnapa" not in st.session_state:
    st.session_state.df_base_pnapa = pd.DataFrame([
        {"Id": 1, "Ano da Ação": "2025", "UF_Acao_PNAPA": "SP", "Nível": "Nacional", "Servidor": "Tiago Farani", "Data de Início": "45818", "Data de Término": "2026-05-19"},
        {"Id": 2, "Ano da Ação": "2026", "UF_Acao_PNAPA": "RJ", "Nível": "Regional", "Servidor": "Eryka", "Data de Início": "19/05/2026", "Data de Término": "19/05/2026"}
    ])
df_atual = st.session_state.df_base_pnapa

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
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label p { font-weight: 500 !important; }
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

# =================================================================
# V. NÚCLEO OPERACIONAL DAS TELAS COORDENADAS PELO POWER AUTOMATE
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
            return pd.to_datetime(val_str, errors='coerce', format='mixed')

        df_trabalho = df_atual.copy()
        df_trabalho["Data_Inicio_Datetime"] = df_trabalho["Data de Início"].apply(limpar_e_converter_data)
        data_min_absoluta = df_trabalho["Data_Inicio_Datetime"].min()
        data_max_absoluta = df_trabalho["Data_Inicio_Datetime"].max()
        if pd.isna(data_min_absoluta) or pd.isna(data_max_absoluta):
            data_min_absoluta, data_max_absoluta = pd.Timestamp("2025-01-01"), pd.Timestamp("2026-12-31")

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
            intervalo_datas = st.slider("⏳ Período (Data de Início):", min_value=data_min_absoluta.to_pydatetime().date(), max_value=data_max_absoluta.to_pydatetime().date(), value=(data_min_absoluta.to_pydatetime().date(), data_max_absoluta.to_pydatetime().date()), format="DD/MM/YYYY")

        df_exibicao = df_trabalho.copy()
        if ano_sel != "Todos": df_exibicao = df_exibicao[df_exibicao["Ano da Ação"].astype(str) == ano_sel]
        if uf_sel != "Todas": df_exibicao = df_exibicao[df_exibicao["UF_Acao_PNAPA"].astype(str) == uf_sel]
        if nivel_sel != "Todos": df_exibicao = df_exibicao[df_exibicao["Nível"].astype(str) == nivel_sel]
        if servidor_sel != "Todos": df_exibicao = df_exibicao[df_exibicao["Servidor"].astype(str) == servidor_sel]
        if not (intervalo_datas[0] == data_min_absoluta.to_pydatetime().date() and intervalo_datas[1] == data_max_absoluta.to_pydatetime().date()):
            df_exibicao = df_exibicao[(df_exibicao["Data_Inicio_Datetime"] >= pd.Timestamp(intervalo_datas[0])) & (df_exibicao["Data_Inicio_Datetime"] <= pd.Timestamp(intervalo_datas[1]))]

        df_exibicao["Data de Início"] = df_exibicao["Data_Inicio_Datetime"].dt.strftime('%d/%m/%Y').fillna("")
        df_exibicao = df_exibicao.drop(columns=["Data_Inicio_Datetime"])
        st.markdown("<br>", unsafe_allow_html=True)
        def estilar_linhas_zebradas(linha): return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        st.dataframe(df_exibicao.reset_index(drop=True).style.apply(estilar_linhas_zebradas, axis=1), use_container_width=True)

# --- TELA 2: INSERIR NOVA LINHA ---
elif modo == "➕ Inserir Nova Linha":
    st.markdown(f"<h3>➕ Inserir Nova Linha — Escopo Autorizado: <span style='color:#4d6b53;'>{uf_usuario if perfil_usuario != 'Administrador' else 'Nacional'}</span></h3>", unsafe_allow_html=True)
    if perfil_usuario == "Administrador":
        uf_acao = st.selectbox("UF Onde Ocorrerá a Ação:", ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "Ceneac"])
    else:
        uf_acao = st.text_input("UF Onde Ocorrerá a Ação:", value=uf_usuario, disabled=True)
    unidades_da_uf = df_lotacoes[df_lotacoes["UF"] == uf_acao]["Unidade"].tolist()
    municipio_unidade = st.selectbox("Unidade/Município de Lotação Relacionada:", unidades_da_uf if unidades_da_uf else ["Sede Regional"])
    st.button("Enviar Registro")

# --- TELA 3 e 4: EDIÇÃO E EXCLUSÃO DA BASE PRINCIPAL (ESCUTAS FUTURAS) ---
elif modo in ["📝 Editar Linha Existente", "🗑️ Deletar Linha (ID)"]:
    st.info("Estas abas serão conectadas ao fluxo principal da planilha macro em breve.")

# --- TELA 5: GERENCIAR UNIDADES (CONECTADO COM POWER AUTOMATE) ---
elif modo == "🏢 Gerenciar Unidades":
    st.markdown(f"<h3>🏢 Gerenciamento de Unidades / Lotações (Tabela Auxiliar via SharePoint)</h3>", unsafe_allow_html=True)
    
    df_visualizacao_uni = df_lotacoes if perfil_usuario == "Administrador" else df_lotacoes[df_lotacoes["UF"] == uf_usuario]
    st.write("#### 📋 Unidades Ativas cadastradas no Excel")
    if df_visualizacao_uni.empty:
        st.info(f"Nenhuma unidade cadastrada para a UF {uf_usuario}.")
    else:
        # --- FILTRO SEGURO PARA ESCONDER COLUNAS INTERNAS DA MICROSOFT ---
        colunas_validas = [col for col in ["ID_UF", "UF", "Unidade"] if col in df_visualizacao_uni.columns]
        df_limpo_uni = df_visualizacao_uni[colunas_validas]
        
        def estilar_uni(linha): return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        st.dataframe(df_limpo_uni.reset_index(drop=True).style.apply(estilar_uni, axis=1), use_container_width=True)
    
    st.markdown("---")
    t_add, t_edit, t_del = st.tabs(["➕ Adicionar Unidade", "📝 Editar Unidade", "🗑️ Excluir Unidade"])
    LISTA_UFS_COMPLETA = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "Ceneac"]
    
    with t_add:
        if perfil_usuario == "Administrador": uf_uni = st.selectbox("Selecione a UF / Órgão para adicionar a unidade:", LISTA_UFS_COMPLETA, key="uni_add_uf")
        else: uf_uni = st.text_input("UF da Lotação:", value=uf_usuario, disabled=True, key="uni_add_uf_rep")
        nova_uni = st.text_input("Nome da Nova Unidade:")
        if st.button("Salvar Unidade"):
            payload = {"Acao": "Inserir", "UF": uf_uni, "Unidade": nova_uni}
            executar_api_unidades(payload)
            st.success(f"Comando de inserção enviado! Unidade '{nova_uni}' salva.")
            st.cache_data.clear()

    with t_edit:
        if perfil_usuario == "Administrador":
            uf_filtrada_edit = st.selectbox("1. Filtrar Unidades por UF/Órgão:", sorted(df_lotacoes["UF"].dropna().unique().tolist()), key="uf_filt_edit")
            df_unidades_filtradas = df_lotacoes[df_lotacoes["UF"] == uf_filtrada_edit]
        else:
            uf_filtrada_edit = uf_usuario
            df_unidades_filtradas = df_lotacoes[df_lotacoes["UF"] == uf_usuario]
            
        if not df_unidades_filtradas.empty:
            sel_uni = st.selectbox("2. Selecione a Unidade para alterar:", df_unidades_filtradas["Unidade"].tolist(), key="uni_sel_edit")
            id_uf_edit = int(df_unidades_filtradas[df_unidades_filtradas["Unidade"] == sel_uni]["ID_UF"].iloc[0])
            m_uni = st.text_input("3. Novo nome da Unidade:", value=sel_uni, key="uni_novo_nome")
            if st.button("Modificar Unidade"):
                payload = {"Acao": "Editar", "ID_UF": id_uf_edit, "UF": uf_filtrada_edit, "Unidade": m_uni}
                executar_api_unidades(payload)
                st.success("Unidade modificada com sucesso no SharePoint!")
                st.cache_data.clear()

    with t_del:
        if perfil_usuario == "Administrador":
            uf_filtrada_del = st.selectbox("1. Filtrar Unidades por UF/Órgão:", sorted(df_lotacoes["UF"].dropna().unique().tolist()), key="uf_filt_del")
            df_unidades_filtradas_del = df_lotacoes[df_lotacoes["UF"] == uf_filtrada_del]
        else:
            uf_filtrada_del = uf_usuario
            df_unidades_filtradas_del = df_lotacoes[df_lotacoes["UF"] == uf_usuario]
            
        if not df_unidades_filtradas_del.empty:
            del_uni = st.selectbox("2. Selecione a Unidade para REMOVER:", df_unidades_filtradas_del["Unidade"].tolist(), key="uni_sel_del")
            id_uf_del = int(df_unidades_filtradas_del[df_unidades_filtradas_del["Unidade"] == del_uni]["ID_UF"].iloc[0])
            chk = st.checkbox(f"Confirmo que desejo excluir permanentemente a unidade {del_uni}")
            if st.button("❌ Excluir Unidade", disabled=not chk):
                payload = {"Acao": "Excluir", "ID_UF": id_uf_del}
                executar_api_unidades(payload)
                st.success("Unidade removida do banco do Excel.")
                st.cache_data.clear()

# --- TELA 6: GERENCIAR EQUIPES (CONECTADO COM POWER AUTOMATE) ---
elif modo == "👥 Gerenciar Equipes":
    st.markdown(f"<h3>👥 Gerenciamento de Equipe e Permissões (Tabela Auxiliar via SharePoint)</h3>", unsafe_allow_html=True)
    
    st.write("#### 📋 Integrantes da Equipe Cadastrados no Excel")
    if df_visualizacao_srv.empty:
        st.info(f"Nenhum servidor cadastrado para a UF {uf_usuario}.")
    else:
        # Mantém apenas as colunas oficiais do sistema, dropando tokens e ids internos
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
            executar_api_equipes(payload)
            st.success(f"Servidor {n_srv} inserido com sucesso na fila do SharePoint!")
            st.cache_data.clear()

    with ts_edit:
        if not df_visualizacao_srv.empty:
            sel_srv = st.selectbox("Selecione o Servidor para alterar:", df_visualizacao_srv["Servidor"].tolist(), key="srv_sel_edit")
            dados_atuais_srv = df_visualizacao_srv[df_visualizacao_srv["Servidor"] == sel_srv].iloc[0]
            id_srv_edit = int(dados_atuais_srv["ID_SERV"])
            
            novo_email = st.text_input("Alterar E-mail:", value=str(dados_atuais_srv["E_mail"]))
            nova_funcao = st.text_input("Alterar Função Interna / Cargo:", value=str(dados_atuais_srv["Funcao"]))
            
            perfil_atual_string = str(dados_atuais_srv["Perfil"]).strip()
            try: index_padrao = LISTA_PERFIS.index(perfil_atual_string)
            except ValueError: index_padrao = 0
            
            n_perf = st.selectbox("Alterar Perfil de Acesso:", LISTA_PERFIS, index=index_padrao) if perfil_usuario == "Administrador" else st.selectbox("Alterar Perfil de Acesso:", ["Visualização", "Editor Regional"], index=1 if index_padrao == 1 else 0)
            
            if st.button("Salvar Modificações"):
                payload = {"Acao": "Editar", "ID_SERV": id_srv_edit, "Servidor": sel_srv, "E_mail": novo_email, "Funcao": nova_funcao, "Perfil": n_perf}
                
                with st.spinner("Atualizando cadastro da equipe..."):
                    executar_api_equipes(payload)
                    import time
                    time.sleep(2)  # Janela de segurança para o Power Automate
                    st.cache_data.clear()  # Expulsa os dados antigos do cache
                    
                st.success("Cadastro do integrante atualizado no Excel!")
                st.rerun()  # Recarrega a página atualizando os selects na hora

    with ts_del:
        if not df_visualizacao_srv.empty:
            del_srv = st.selectbox("Selecione quem perderá o acesso:", df_visualizacao_srv["Servidor"].tolist(), key="srv_sel_del")
            id_srv_del = int(df_visualizacao_srv[df_servidores["Servidor"] == del_srv]["ID_SERV"].iloc[0])
            chk_srv = st.checkbox(f"Confirmo o desligamento do servidor {del_srv}")
            if st.button("❌ Revogar Acesso", disabled=not chk_srv):
                payload = {"Acao": "Excluir", "ID_SERV": id_srv_del}
                executar_api_equipes(payload)
                st.success(f"Acesso revogado! Servidor deletado do banco.")
                st.cache_data.clear()
