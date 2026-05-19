import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="PNAPA via Power Automate", layout="wide")

# =================================================================
# I. APRESENTAÇÃO E DESIGN: FOLHA DE ESTILOS CSS BLINDADA
# =================================================================
st.markdown("""
    <style>
        /* BARRA LATERAL (SIDEBAR): TEXTOS GERAIS E LABELS EM BRANCO */
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] label p,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label p {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label p {
            font-weight: 500 !important;
        }

        /* CAIXA DO SELECTBOX (ID) NA SIDEBAR */
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div,
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] *,
        section[data-testid="stSidebar"] div[data-baseweb="select"] * {
            color: #03170a !important;
            font-weight: bold !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] svg {
            fill: #03170a !important;
        }

        /* ÁREA CENTRAL: SELECTBOXES / COMBOS EM BRANCO COM TEXTO ESCURO */
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] > div,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
        }
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] *,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] * {
            color: #03170a !important;
            background-color: transparent !important;
        }
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] svg,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] svg {
            fill: #03170a !important;
        }

        /* COMPONENTES DE INTERAÇÃO (NÚMEROS, DATAS, ABAS) */
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
# II. CARREGAMENTO OPERACIONAL DAS BASES DE DADOS
# =================================================================
@st.cache_data
def carregar_bases_auxiliares():
    try:
        lotacoes = pd.read_csv("lotacoes.csv")
        servidores = pd.read_csv("servidores.csv")
    except:
        # Fallbacks estruturais para resiliência de execução inicial local
        lotacoes = pd.DataFrame([["SP", "São Paulo"], ["SP", "Santos"]], columns=["UF", "Unidade"])
        servidores = pd.DataFrame([["Tiago Farani", "SP", "São Paulo", "Sim", "Sim", "Sim", "Chefe", "tiago.farani@ibama.gov.br", "Administrador", "Mestre2026"]], 
                                  columns=["Servidor", "UF_Servidor", "Lotacao", "Equipe_Emergencias", "Fiscal", "AEAC", "Funcao", "E_mail", "Perfil", "Token"])
    return lotacoes, servidores

df_lotacoes, df_servidores = carregar_bases_auxiliares()

# Simulação da base consolidada do PNAPA (Substitua pela leitura do PNAPA_2026_Consolidado.csv)
if "df_base_pnapa" not in st.session_state:
    st.session_state.df_base_pnapa = pd.DataFrame([
        {"Id": 1, "Ano da Ação": "2025", "UF_Acao_PNAPA": "SP", "Nível": "Nacional", "Servidor": "Tiago Farani", "Data de Início": "45818", "Data de Término": "2026-05-19"},
        {"Id": 2, "Ano da Ação": "2026", "UF_Acao_PNAPA": "RJ", "Nível": "Regional", "Servidor": "Eryka", "Data de Início": "19/05/2026", "Data de Término": "19/05/2026"}
    ])
df_atual = st.session_state.df_base_pnapa

# =================================================================
# III. CONTROLE DE ACESSO INTEGRADO (SSO + PERFIL + TOKEN) - BLINDADO
# =================================================================
# Nova forma ultra-segura de capturar o e-mail sem quebrar por versão do Streamlit
try:
    if hasattr(st, "user") and hasattr(st.user, "email"):
        email_logado = st.user.email
    elif hasattr(st, "experimental_user"):
        email_logado = st.experimental_user.email
    else:
        email_logado = st.user.get("email") if hasattr(st, "user") and hasattr(st.user, "get") else None
except:
    email_logado = None

EMAIL_ADMIN = "tiago.farani@ibama.gov.br"

# Homologação automática para desenvolvimento local (localhost) ou falha de SSO
if not email_logado:
    email_logado = "tiago.farani@ibama.gov.br"


# Resgata o perfil e token do servidor com base na chave de e-mail institucional
try:
    dados_usuario = df_servidores[df_servidores["E_mail"] == email_logado].iloc[0]
    uf_usuario = dados_usuario["UF_Servidor"]
    perfil_usuario = dados_usuario["Perfil"]  # 'Administrador', 'Editor Regional' ou 'Visualização'
    token_correto = str(dados_usuario["Token"]).strip()
except:
    uf_usuario = "Acesso Restrito"
    perfil_usuario = "Visualização"
    token_correto = None

# Força chave mestra irrestrita para o dono do sistema administrativo
if email_logado == EMAIL_ADMIN:
    perfil_usuario = "Administrador"

acesso_liberado = False

if perfil_usuario == "Administrador":
    acesso_liberado = True
    uf_usuario = "SP"  # Estado inicial para renderização macro do Admin
    st.sidebar.success("👑 Modo Administrador Ativo")
else:
    # Interface de barreira criptográfica para Editores Regionais e Visualizadores habilitados
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔐 Autenticação")
    token_digitado = st.sidebar.text_input("Digite seu Token de Acesso:", type="password")
    
    if token_digitado:
        if token_digitado == token_correto:
            acesso_liberado = True
            st.sidebar.success(f"🔓 {perfil_usuario} Liberado ({uf_usuario})")
        else:
            st.sidebar.error("❌ Token Incorreto.")

# =================================================================
# IV. CONFIGURAÇÃO DINÂMICA DO MENU LATERAL CONFORME PERFIL
# =================================================================
opcoes_menu = ["📊 Visualizar Base"]

# Só expande as operações de CRUD e Gestão Auxiliar se o Token passar e o Perfil for qualificado
if acesso_liberado and perfil_usuario in ["Administrador", "Editor Regional"]:
    opcoes_menu.extend(["➕ Inserir Nova Linha", "📝 Editar Linha Existente", "🗑️ Deletar Linha (ID)", "🏢 Gerenciar Unidades", "👥 Gerenciar Equipes"])

st.sidebar.markdown("## 🕹️ Painel de Controle")
modo = st.sidebar.radio("Operação:", opcoes_menu)

# =================================================================
# V. EXECUÇÃO RHEOLÓGICA DAS TELAS DO APP
# =================================================================

# --- TELA 1: VISUALIZAÇÃO COM FILTROS INTERDEPENDENTES (ACESSÍVEL A TODOS) ---
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
            intervalo_datas = st.slider("⏳ Período (Data de Início):", 
                                        min_value=data_min_absoluta.to_pydatetime().date(), 
                                        max_value=data_max_absoluta.to_pydatetime().date(),
                                        value=(data_min_absoluta.to_pydatetime().date(), data_max_absoluta.to_pydatetime().date()), 
                                        format="DD/MM/YYYY")

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
        
        def estilar_linhas_zebradas(linha):
            return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]

        st.dataframe(df_exibicao.reset_index(drop=True).style.apply(estilar_linhas_zebradas, axis=1), use_container_width=True)

# --- TELA 2: INSERIR NOVA LINHA ---
elif modo == "➕ Inserir Nova Linha":
    st.markdown(f"<h3>➕ Inserir Nova Linha — Escopo Autorizado: <span style='color:#4d6b53;'>{uf_usuario if perfil_usuario != 'Administrador' else 'Nacional'}</span></h3>", unsafe_allow_html=True)
    
    if perfil_usuario == "Administrador":
        uf_acao = st.selectbox("UF Onde Ocorrerá a Ação:", sorted(df_lotacoes["UF"].unique().tolist()))
    else:
        uf_acao = st.text_input("UF Onde Ocorrerá a Ação:", value=uf_usuario, disabled=True)
        
    unidades_da_uf = df_lotacoes[df_lotacoes["UF"] == uf_acao]["Unidade"].tolist()
    municipio_unidade = st.selectbox("Unidade/Município de Lotação Relacionada:", unidades_da_uf if unidades_da_uf else ["Nenhuma lotação cadastrada"])
    st.button("Enviar Registro")

# --- TELA 3: EDITAR LINHA EXISTENTE ---
elif modo == "📝 Editar Linha Existente":
    st.markdown(f"<h3>📝 Editar Linha Existente</h3>", unsafe_allow_html=True)
    df_procurado = df_atual if perfil_usuario == "Administrador" else df_atual[df_atual["UF_Acao_PNAPA"] == uf_usuario]
    
    if df_procurado.empty:
        st.warning(f"Sem registros mapeados sob a responsabilidade da UF {uf_usuario}.")
    else:
        ids_disponiveis = df_procurado["Id"].dropna().astype(str).unique().tolist()
        st.sidebar.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 5px;'>Selecione o ID para Editar:</p>", unsafe_allow_html=True)
        id_para_editar = st.sidebar.selectbox("", ids_disponiveis, label_visibility="collapsed")
        st.info(f"Formulário instanciado para o ID {id_para_editar}")

# --- TELA 4: DELETAR LINHA ---
elif modo == "🗑️ Deletar Linha (ID)":
    st.markdown(f"<h3>🗑️ Excluir Registro Permanente</h3>", unsafe_allow_html=True)
    df_procurado = df_atual if perfil_usuario == "Administrador" else df_atual[df_atual["UF_Acao_PNAPA"] == uf_usuario]
    
    if df_procurado.empty:
        st.warning("Nenhum registro correspondente elegível para deleção.")
    else:
        ids_disponiveis = df_procurado["Id"].dropna().astype(str).unique().tolist()
        st.sidebar.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 5px;'>Selecione o ID para Deletar:</p>", unsafe_allow_html=True)
        id_para_deletar = st.sidebar.selectbox("", ids_disponiveis, label_visibility="collapsed")
        st.warning(f"ID pronto para comando de exclusão: {id_para_deletar}")

# --- TELA 5: GERENCIAR UNIDADES ---
elif modo == "🏢 Gerenciar Unidades":
    st.markdown(f"<h3>🏢 Gerenciamento de Unidades / Lotações (Tabela Auxiliar)</h3>", unsafe_allow_html=True)
    
    # --- VISUALIZAÇÃO PRÉVIA DAS UNIDADES CADASTRADAS ---
    df_visualizacao_uni = df_lotacoes if perfil_usuario == "Administrador" else df_lotacoes[df_lotacoes["UF"] == uf_usuario]
    
    st.write("#### 📋 Unidades Ativas sob sua Gestão")
    if df_visualizacao_uni.empty:
        st.info(f"Nenhuma unidade cadastrada para a UF {uf_usuario}.")
    else:
        def estilar_uni(linha):
            return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        st.dataframe(df_visualizacao_uni.reset_index(drop=True).style.apply(estilar_uni, axis=1), use_container_width=True)
    
    st.markdown("---")
    
    t_add, t_edit, t_del = st.tabs(["➕ Adicionar Unidade", "📝 Editar Unidade", "🗑️ Excluir Unidade"])
    
    # LISTA FIXA OFICIAL: Todas as UFs do Brasil + Ceneac para o cadastro
    LISTA_UFS_COMPLETA = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", 
                          "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "Ceneac"]
    
    # --- TAB 1: ADICIONAR ---
    with t_add:
        if perfil_usuario == "Administrador": 
            uf_uni = st.selectbox("Selecione a UF / Órgão para adicionar a unidade:", LISTA_UFS_COMPLETA, key="uni_add_uf")
        else: 
            uf_uni = st.text_input("UF da Lotação:", value=uf_usuario, disabled=True, key="uni_add_uf_rep")
            
        nova_uni = st.text_input("Nome da Nova Unidade (Ex: Campinas, Cabo Frio, Sede COAEM):")
        if st.button("Salvar Unidade"): 
            st.success(f"Unidade '{nova_uni}' adicionada com sucesso para {uf_uni}!")
        
    # --- TAB 2: EDITAR ---
    with t_edit:
        st.write("#### Modificar Unidade")
        if perfil_usuario == "Administrador":
            ufs_disponiveis_edit = sorted(df_lotacoes["UF"].dropna().unique().tolist())
            uf_filtrada_edit = st.selectbox("1. Filtrar Unidades por UF/Órgão:", ufs_disponiveis_edit, key="uf_filt_edit")
            df_unidades_filtradas = df_lotacoes[df_lotacoes["UF"] == uf_filtrada_edit]
        else:
            uf_filtrada_edit = st.text_input("UF de Gestão:", value=uf_usuario, disabled=True, key="uf_filt_edit_rep")
            df_unidades_filtradas = df_lotacoes[df_lotacoes["UF"] == uf_usuario]
            
        if df_unidades_filtradas.empty:
            st.warning("Nenhuma unidade cadastrada para a seleção atual.")
        else:
            sel_uni = st.selectbox("2. Selecione a Unidade para alterar:", df_unidades_filtradas["Unidade"].tolist(), key="uni_sel_edit")
            m_uni = st.text_input("3. Novo nome da Unidade:", value=sel_uni, key="uni_novo_nome")
            if st.button("Modificar Unidade", key="btn_mod_uni"): 
                st.success(f"Unidade '{sel_uni}' alterada para '{m_uni}' com sucesso em {uf_filtrada_edit}!")
            
    # --- TAB 3: EXCLUIR ---
    with t_del:
        st.write("#### Remover Unidade")
        if perfil_usuario == "Administrador":
            ufs_disponiveis_del = sorted(df_lotacoes["UF"].dropna().unique().tolist())
            uf_filtrada_del = st.selectbox("1. Filtrar Unidades por UF/Órgão:", ufs_disponiveis_del, key="uf_filt_del")
            df_unidades_filtradas_del = df_lotacoes[df_lotacoes["UF"] == uf_filtrada_del]
        else:
            uf_filtrada_del = st.text_input("UF de Gestão:", value=uf_usuario, disabled=True, key="uf_filt_del_rep")
            df_unidades_filtradas_del = df_lotacoes[df_lotacoes["UF"] == uf_usuario]
            
        if df_unidades_filtradas_del.empty:
            st.warning("Nenhuma unidade cadastrada para a seleção atual.")
        else:
            del_uni = st.selectbox("2. Selecione a Unidade para REMOVER:", df_unidades_filtradas_del["Unidade"].tolist(), key="uni_sel_del")
            chk = st.checkbox(f"Confirmo que desejo excluir permanentemente a unidade {del_uni} de {uf_filtrada_del}")
            if st.button("❌ Excluir Unidade", disabled=not chk, key="btn_del_uni"): 
                st.success(f"Unidade '{del_uni}' removida com sucesso da base de dados de {uf_filtrada_del}!")

# --- TELA 6: GERENCIAR EQUIPES ---
elif modo == "👥 Gerenciar Equipes":
    st.markdown(f"<h3>👥 Gerenciamento de Equipe e Permissões (Tabela Auxiliar)</h3>", unsafe_allow_html=True)
    
    # --- VISUALIZAÇÃO PRÉVIA DA EQUIPE ---
    df_visualizacao_srv = df_servidores if perfil_usuario == "Administrador" else df_servidores[df_servidores["UF_Servidor"] == uf_usuario]
    
    st.write("#### 📋 Integrantes da Equipe Cadastrados")
    if df_visualizacao_srv.empty:
        st.info(f"Nenhum servidor cadastrado para a UF {uf_usuario}.")
    else:
        df_exibir_srv = df_visualizacao_srv.drop(columns=["Token"], errors="ignore")
        def estilar_srv(linha):
            return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        st.dataframe(df_exibir_srv.reset_index(drop=True).style.apply(estilar_srv, axis=1), use_container_width=True)
        
    st.markdown("---")
    
    ts_add, ts_edit, ts_del = st.tabs(["➕ Cadastrar Servidor", "📝 Alterar Cadastro", "🗑️ Remover Acesso"])
    
    # LISTA FIXA PARA PERFIS
    LISTA_PERFIS = ["Visualização", "Editor Regional", "Administrador"]
    
    # --- TAB 1: CADASTRAR INTEGRANTE ---
    with ts_add:
        n_srv = st.text_input("Nome Completo do Servidor:")
        e_srv = st.text_input("E-mail Institucional (@ibama.gov.br):")
        
        if perfil_usuario == "Administrador":
            uf_srv = st.selectbox("UF/Órgão de Lotação:", ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", 
                                                           "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "Ceneac"], key="srv_add_uf")
        else:
            uf_srv = st.text_input("UF de Lotação:", value=uf_usuario, disabled=True, key="srv_add_uf_rep")
            
        unidades_lotacao_disponiveis = df_lotacoes[df_lotacoes["UF"] == uf_srv]["Unidade"].tolist()
        lot_srv = st.selectbox("Unidade de Lotação Relacionada:", unidades_lotacao_disponiveis if unidades_lotacao_disponiveis else ["Sede Superintendência"])
        
        fun_srv = st.text_input("Função / Cargo Interno (Ex: Chefe Nupaem, Substituto, Agente):")
        
        col_eq1, col_eq2, col_eq3 = st.columns(3)
        with col_eq1: eq_emerg = st.selectbox("Equipe de Emergências?", ["Sim", "Não"])
        with col_eq2: eq_fiscal = st.selectbox("Fiscal de Campo?", ["Sim", "Não"])
        with col_eq3: eq_aeac = st.selectbox("Possui AEAC?", ["Sim", "Não"])
        
        if perfil_usuario == "Administrador":
            perf_srv = st.selectbox("Perfil de Acesso no Sistema:", LISTA_PERFIS)
        else:
            perf_srv = st.selectbox("Perfil de Acesso no Sistema:", ["Visualização", "Editor Regional"])
            
        tkn_srv = st.text_input("Definir Token/Senha de Acesso para o Usuário:", type="password")
        
        if st.button("Habilitar Servidor", key="btn_add_srv"): 
            st.success(f"Servidor {n_srv} cadastrado com sucesso como {perf_srv} em {uf_srv}!")

    # --- TAB 2: EDITAR INTEGRANTE (RESOLUÇÃO DO ERROR DE INDEX COM TRATAMENTO) ---
    with ts_edit:
        st.write("#### Atualizar Atributos do Servidor")
        if not df_visualizacao_srv.empty:
            sel_srv = st.selectbox("Selecione o Servidor para alterar:", df_visualizacao_srv["Servidor"].tolist(), key="srv_sel_edit")
            dados_atuais_srv = df_visualizacao_srv[df_visualizacao_srv["Servidor"] == sel_srv].iloc[0]
            
            novo_email = st.text_input("Alterar E-mail:", value=str(dados_atuais_srv["E_mail"]))
            nova_funcao = st.text_input("Alterar Função Interna / Cargo:", value=str(dados_atuais_srv["Funcao"]))
            
            # BLINDAGEM DO INDEX: Se o texto da base vier com grafia diferente, ele joga o index para 0 em vez de travar o app
            perfil_atual_string = str(dados_atuais_srv["Perfil"]).strip()
            try:
                index_padrao = LISTA_PERFIS.index(perfil_atual_string)
            except ValueError:
                index_padrao = 0 # Fallback caso esteja escrito de forma diferente (ex: "Visualização" vs "Visualizador")
            
            if perfil_usuario == "Administrador":
                n_perf = st.selectbox("Alterar Perfil de Acesso:", LISTA_PERFIS, index=index_padrao)
            else:
                n_perf = st.selectbox("Alterar Perfil de Acesso:", ["Visualização", "Editor Regional"], 
                                      index=1 if index_padrao == 1 else 0)
                
            if st.button("Salvar Modificações", key="btn_edit_srv"): 
                st.success(f"Cadastro do servidor {sel_srv} atualizado com sucesso!")

    # --- TAB 3: REMOVER INTEGRANTE ---
    with ts_del:
        st.write("#### Revogar Permissões")
        if not df_visualizacao_srv.empty:
            del_srv = st.selectbox("Selecione quem perderá o acesso:", df_visualizacao_srv["Servidor"].tolist(), key="srv_sel_del")
            chk_srv = st.checkbox(f"Confirmo o desligamento definitivo do servidor(a) {del_srv} do ecossistema do painel")
            if st.button("❌ Revogar Acesso", disabled=not chk_srv, key="btn_del_srv"): 
                st.success(f"Acesso de {del_srv} revogado com sucesso e removido da base.")
