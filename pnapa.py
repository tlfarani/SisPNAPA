import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="PNAPA via Power Automate", layout="wide")

# =================================================================
# 1. DESIGN & CSS: BLINDAGEM DE ALTA LEGIBILIDADE CORPORATIVA
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
# 2. CARREGAMENTO DAS BASES DE DADOS (SIMULAÇÃO / LEITURA LOCAL)
# =================================================================
# Nota: Substitua pelas suas chamadas de API do Power Automate ou st.secrets se aplicável
@st.cache_data
def carregar_dados_auxiliares():
    try:
        lotacoes = pd.read_csv("lotacoes.csv")
        servidores = pd.read_csv("servidores.csv")
    except:
        # Fallbacks de segurança para primeira execução caso arquivos não existam localmente
        lotacoes = pd.DataFrame([["SP", "São Paulo"], ["SP", "Santos"]], columns=["UF", "Unidade"])
        servidores = pd.DataFrame([["Tiago Farani", "SP", "São Paulo", "Sim", "Sim", "Sim", "Sim", "tiago.farani@ibama.gov.br"]], 
                                  columns=["Servidor", "UF_Servidor", "Lotacao", "Equipe_Emergencias", "Fiscal", "AEAC", "Responsavel", "E_mail"])
    return lotacoes, servidores

df_lotacoes, df_servidores = carregar_dados_auxiliares()

# Simulando o df_atual principal do PNAPA vindo do SharePoint
# (Substitua pela leitura real do arquivo PNAPA_2026_Consolidado.csv)
if "df_base_pnapa" not in st.session_state:
    st.session_state.df_base_pnapa = pd.DataFrame([
        {"Id": 1, "Ano da Ação": "2025", "UF_Acao_PNAPA": "SP", "Nível": "Nacional", "Servidor": "Tiago Farani", "Data de Início": "45818", "Data de Término": "2026-05-19"},
        {"Id": 2, "Ano da Ação": "2026", "UF_Acao_PNAPA": "RJ", "Nível": "Regional", "Servidor": "Eryka", "Data de Início": "19/05/2026", "Data de Término": "19/05/2026"}
    ])

df_atual = st.session_state.df_base_pnapa

# =================================================================
# 3. CONTROLE DE ACESSO AVANÇADO (RLS & CHAVE MESTRA)
# =================================================================
email_logado = st.experimental_user.email
EMAIL_ADMIN = "tiago.farani@ibama.gov.br"
eh_admin = (email_logado == EMAIL_ADMIN)

try:
    dados_usuario = df_servidores[df_servidores["E_mail"] == email_logado].iloc[0]
    uf_usuario = dados_usuario["UF_Servidor"]
    eh_responsavel = (dados_usuario["Responsavel"] == "Sim")
except:
    uf_usuario = "Acesso Restrito"
    eh_responsavel = False

# Ajuste automático do escopo administrativo
if eh_admin:
    uf_usuario = "SP" # Estado inicial padrão para a visão do Admin
    eh_responsavel = True

# =================================================================
# 4. CONFIGURAÇÃO DINÂMICA DO MENU LATERAL
# =================================================================
opcoes_menu = ["📊 Visualizar Base", "➕ Inserir Nova Linha", "📝 Editar Linha Existente", "🗑️ Deletar Linha (ID)"]

if eh_admin or eh_responsavel:
    opcoes_menu.append("🏢 Gerenciar Unidades")
    opcoes_menu.append("👥 Gerenciar Equipes")

st.sidebar.markdown("## 🕹️ Painel de Controle")
modo = st.sidebar.radio("Operação:", opcoes_menu)

# =================================================================
# 5. EXECUÇÃO DAS TELAS DO SISTEMA
# =================================================================

# --- TELA 1: VISUALIZAÇÃO COM FILTROS INTERDEPENDENTES ---
if modo == "📊 Visualizar Base":
    st.markdown("<h3 style='color: #03170a;'>📊 Visualização Atual dos Dados (Espelho SharePoint)</h3>", unsafe_allow_html=True)
    
    if df_atual.empty:
        st.info("A base de dados está vazia.")
    else:
        # Tratamento do conversor de serial do Excel
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

        # Layout Cascata de Filtros
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

        # Aplicação cruzada de filtros na exibição
        df_exibicao = df_trabalho.copy()
        if ano_sel != "Todos": df_exibicao = df_exibicao[df_exibicao["Ano da Ação"].astype(str) == ano_sel]
        if uf_sel != "Todas": df_exibicao = df_exibicao[df_exibicao["UF_Acao_PNAPA"].astype(str) == uf_sel]
        if nivel_sel != "Todos": df_exibicao = df_exibicao[df_exibicao["Nível"].astype(str) == nivel_sel]
        if servidor_sel != "Todos": df_exibicao = df_exibicao[df_exibicao["Servidor"].astype(str) == servidor_sel]
        
        if not (intervalo_datas[0] == data_min_absoluta.to_pydatetime().date() and intervalo_datas[1] == data_max_absoluta.to_pydatetime().date()):
            df_exibicao = df_exibicao[(df_exibicao["Data_Inicio_Datetime"] >= pd.Timestamp(intervalo_datas[0])) & (df_exibicao["Data_Inicio_Datetime"] <= pd.Timestamp(intervalo_datas[1]))]

        # Conversão estrutural de data para o Grid
        df_exibicao["Data de Início"] = df_exibicao["Data_Inicio_Datetime"].dt.strftime('%d/%m/%Y').fillna("")
        df_exibicao = df_exibicao.drop(columns=["Data_Inicio_Datetime"])

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Zebrado dinâmico recalculado via Reset de Índices
        def estilar_linhas_zebradas(linha):
            return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]

        st.dataframe(df_exibicao.reset_index(drop=True).style.apply(estilar_linhas_zebradas, axis=1), use_container_width=True)

# --- TELA 2: INSERIR NOVA LINHA ---
elif modo == "➕ Inserir Nova Linha":
    st.markdown(f"<h3>➕ Inserir Nova Linha — Escopo: <span style='color:#4d6b53;'>{uf_usuario if not eh_admin else 'Admin Geral'}</span></h3>", unsafe_allow_html=True)
    
    if not eh_admin and uf_usuario == "Acesso Restrito":
        st.error("🚫 Credenciais não autorizadas para inserção de dados.")
    else:
        if eh_admin:
            uf_acao = st.selectbox("UF Onde Ocorrerá a Ação:", sorted(df_lotacoes["UF"].unique().tolist()))
        else:
            uf_acao = st.text_input("UF Onde Ocorrerá a Ação:", value=uf_usuario, disabled=True)
            
        unidades_da_uf = df_lotacoes[df_lotacoes["UF"] == uf_acao]["Unidade"].tolist()
        municipio_unidade = st.selectbox("Unidade/Município de Lotação Relacionada:", unidades_da_uf if unidades_da_uf else ["Nenhuma lotação cadastrada"])
        
        # O resto do formulário do PNAPA entra aqui...
        st.button("Enviar Registro")

# --- TELA 3: EDITAR LINHA EXISTENTE ---
elif modo == "📝 Editar Linha Existente":
    st.markdown(f"<h3>📝 Editar Linha Existente</h3>", unsafe_allow_html=True)
    
    df_procurado = df_atual if eh_admin else df_atual[df_atual["UF_Acao_PNAPA"] == uf_usuario]
    
    if df_procurado.empty:
        st.warning(f"Nenhum registro encontrado sob os critérios da UF {uf_usuario}.")
    else:
        ids_disponiveis = df_procurado["Id"].dropna().astype(str).unique().tolist()
        st.sidebar.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 5px;'>Selecione o ID para Editar:</p>", unsafe_allow_html=True)
        id_para_editar = st.sidebar.selectbox("", ids_disponiveis, label_visibility="collapsed")
        st.info(f"Carregando formulário para o ID {id_para_editar}...")

# --- TELA 4: DELETAR LINHA ---
elif modo == "🗑️ Deletar Linha (ID)":
    st.markdown(f"<h3>🗑️ Excluir Registro Permanente</h3>", unsafe_allow_html=True)
    df_procurado = df_atual if eh_admin else df_atual[df_atual["UF_Acao_PNAPA"] == uf_usuario]
    
    if df_procurado.empty:
        st.warning("Sem registros válidos para exclusão.")
    else:
        ids_disponiveis = df_procurado["Id"].dropna().astype(str).unique().tolist()
        st.sidebar.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 5px;'>Selecione o ID para Deletar:</p>", unsafe_allow_html=True)
        id_para_deletar = st.sidebar.selectbox("", ids_disponiveis, label_visibility="collapsed")
        st.warning(f"ID selecionado para deleção: {id_para_deletar}")

# --- TELA 5: GERENCIAR UNIDADES ---
elif modo == "🏢 Gerenciar Unidades":
    st.markdown(f"<h3>🏢 Gerenciamento de Unidades / Lotações (Tabela Auxiliar)</h3>", unsafe_allow_html=True)
    t_add, t_edit, t_del = st.tabs(["➕ Adicionar Unidade", "📝 Editar Unidade", "🗑️ Excluir Unidade"])
    
    with t_add:
        if eh_admin: uf_uni = st.selectbox("Selecione a UF:", sorted(df_lotacoes["UF"].unique().tolist()), key="uni_add_uf")
        else: uf_uni = st.text_input("UF da Lotação:", value=uf_usuario, disabled=True, key="uni_add_uf_rep")
        nova_uni = st.text_input("Nome da Nova Unidade:")
        if st.button("Salvar Unidade"): st.success(f"Unidade '{nova_uni}' adicionada para {uf_uni}!")
        
    with t_edit:
        df_f = df_lotacoes if eh_admin else df_lotacoes[df_lotacoes["UF"] == uf_usuario]
        if not df_f.empty:
            sel_uni = st.selectbox("Selecione a Unidade para alterar:", df_f["Unidade"].tolist())
            m_uni = st.text_input("Novo nome da Unidade:", value=sel_uni)
            if st.button("Modificar Unidade"): st.success("Lotação atualizada!")
            
    with t_del:
        df_f = df_lotacoes if eh_admin else df_lotacoes[df_lotacoes["UF"] == uf_usuario]
        if not df_f.empty:
            del_uni = st.selectbox("Selecione a Unidade para REMOVER:", df_f["Unidade"].tolist())
            chk = st.checkbox(f"Confirmo a exclusão da unidade {del_uni}")
            if st.button("❌ Excluir", disabled=not chk): st.success("Unidade removida.")

# --- TELA 6: GERENCIAR EQUIPES ---
elif modo == "👥 Gerenciar Equipes":
    st.markdown(f"<h3>👥 Gerenciamento de Equipe e Permissões (Tabela Auxiliar)</h3>", unsafe_allow_html=True)
    ts_add, ts_edit, ts_del = st.tabs(["➕ Cadastrar Servidor", "📝 Alterar Cadastro", "🗑️ Remover Acesso"])
    
    with ts_add:
        n_srv = st.text_input("Nome Completo:")
        e_srv = st.text_input("E-mail Institucional (@ibama.gov.br):")
        if eh_admin:
            uf_srv = st.selectbox("UF de Lotação:", sorted(df_lotacoes["UF"].unique().tolist()), key="srv_add_uf")
            perf_srv = st.selectbox("Perfil do Servidor:", ["Visualizador", "Representante", "Administrador"])
        else:
            uf_srv = st.text_input("UF de Lotação:", value=uf_usuario, disabled=True, key="srv_add_uf_rep")
            perf_srv = st.selectbox("Perfil do Servidor:", ["Visualizador", "Representante"])
        if st.button("Habilitar Servidor"): st.success(f"{n_srv} cadastrado!")

    with ts_edit:
        df_f = df_servidores if eh_admin else df_servidores[df_servidores["UF_Servidor"] == uf_usuario]
        if not df_f.empty:
            sel_srv = st.selectbox("Selecione o Servidor para alterar:", df_f["Servidor"].tolist())
            st.text_input("E-mail:", value=df_f[df_f["Servidor"] == sel_srv]["E_mail"].iloc[0])
            if st.button("Salvar Modificações"): st.success("Cadastro atualizado!")

    with ts_del:
        df_f = df_servidores if eh_admin else df_servidores[df_servidores["UF_Servidor"] == uf_usuario]
        if not df_f.empty:
            del_srv = st.selectbox("Selecione quem perderá o acesso:", df_f["Servidor"].tolist())
            chk_srv = st.checkbox(f"Confirmo o desligamento do servidor {del_srv}")
            if st.button("❌ Revogar Acesso", disabled=not chk_srv): st.success("Acesso revogado.")
