import streamlit as st
import pandas as pd
import requests
import time
from datetime import date

st.set_page_config(page_title="PNAPA via Power Automate", layout="wide")

# --- BLINDAGEM VISUAL CORPORATIVA (MÁXIMO CONTRASTE GERAL) ---
st.markdown("""
    <style>
        /* =================================================================
           1. BARRA LATERAL (SIDEBAR): TEXTOS GERAIS E LABELS EM BRANCO
           ================================================================= */
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
        section[data-testid="stSidebar"] label p,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] div[data-testid="stRadio"] label p {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        /* CAIXA DO SELECTBOX (ID) NA SIDEBAR */
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div,
        section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important; /* Mantém a caixinha do ID branca */
            border: 1px solid #cbd5e1 !important;
        }

        /* Garante que o número '1' de dentro do selectbox da lateral fique escoro e nítido */
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] *,
        section[data-testid="stSidebar"] div[data-baseweb="select"] * {
            color: #03170a !important;
            font-weight: bold !important;
        }
        
        section[data-testid="stSidebar"] div[data-testid="stSelectbox"] svg {
            fill: #03170a !important;
        }

        /* =================================================================
           2. ÁREA CENTRAL: BANIMENTO COMPLETO DE FUNDO ESCURO EM SELECTBOXES (COMBO)
           ================================================================= */
        /* Captura QUALQUE caixa de seleção ou combo na área central e força fundo branco */
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] > div,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] > div,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
        }

        /* Força os textos internos de todas as opções centrais ("Alta", "Nacional", etc.) a ficarem escuros */
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] * ,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] *,
        div[data-testid="stAppViewContainer"] [aria-selected="true"] {
            color: #03170a !important;
            background-color: transparent !important;
        }

        /* Garante a cor escura na setinha das caixas de seleção centrais */
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] svg,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] svg {
            fill: #03170a !important;
        }

        /* =================================================================
           3. DEMAIS COMPONENTES DA ÁREA CENTRAL (TEXTO, NÚMERO, DATAS, ABAS)
           ================================================================= */
        h2, h3, [data-testid="stHeader"] {
            color: #03170a !important;
            font-weight: 700 !important;
        }

        /* Inputs Numéricos (+ / -) e de Texto */
        div[data-testid="stNumberInput"] input { background-color: #ffffff !important; color: #03170a !important; }
        div[data-testid="stNumberInput"] > div { border: 1px solid #cbd5e1 !important; background-color: #ffffff !important; }
        div[data-testid="stNumberInput"] button { background-color: #f1f5f9 !important; color: #03170a !important; border: 1px solid #cbd5e1 !important; }
        
        /* Datas */
        div[data-testid="stDateInput"] > div, div[data-testid="stDateInput"] div[role="button"], div[data-testid="stDateInput"] input {
            background-color: #ffffff !important; color: #03170a !important; border: 1px solid #cbd5e1 !important;
        }
        div[data-testid="stDateInput"] svg { fill: #03170a !important; }

        /* Abas (Tabs) */
        button[data-baseweb="tab"] p { color: #4a5568 !important; font-weight: 500; }
        button[aria-selected="true"] p { color: #03170a !important; font-weight: 700 !important; }
        div[data-baseweb="tab-highlight"] { background-color: #4d6b53 !important; }

        /* Caixas de Texto */
        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
            border: 1px solid #cbd5e1 !important; background-color: #ffffff !important; color: #03170a !important;
        }
        div[data-testid="stAppViewContainer"] label[data-testid="stWidgetLabel"] p { color: #03170a !important; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# --- LEITURA DE CREDENCIAIS / SECRETS ---
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
        st.markdown(f"<div style='padding:10px; border-radius:5px; background-color:#2a1a1a; color:#f87171; border:1px solid #7f1d1d;'>❌ Erro ao conectar ao Power Automate para leitura: {e}</div>", unsafe_allow_html=True)
        return pd.DataFrame(columns=COLUNAS_PNAPA)

# Inicialização do estado da sessão (Cache Local)
if "df" not in st.session_state:
    with st.spinner("Buscando dados no SharePoint via Power Automate..."):
        st.session_state.df = carregar_dados_da_nuvem()

df_atual = st.session_state.df

# --- INTERFACE LATERAL (PAINEL DE CONTROLE) ---
st.sidebar.markdown("<h2 style='color: #f1f3f5; font-weight: 600;'>🕹️ Painel de Controle</h2>", unsafe_allow_html=True)
modo = st.sidebar.radio(
    "Operação:", 
    ["📊 Visualizar Base", "➕ Inserir Nova Linha", "📝 Editar Linha Existente", "🗑️ Deletar Linha (ID)"]
)

# Variáveis de controle de contexto
registro_selecionado = None
id_atual = ""

# Regras de transição e seletores na barra lateral
if modo == "📝 Editar Linha Existente":
    if df_atual.empty:
        st.sidebar.warning("Base de dados vazia para edição.")
        modo = "📊 Visualizar Base"
    else:
        ids_disponiveis = df_atual["Id"].dropna().astype(str).unique().tolist()
        
        # Corrigido: margem reajustada para dar espaço seguro ao texto
        st.sidebar.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 5px;'>Selecione o ID para Editar:</p>", unsafe_allow_html=True)
        id_para_editar = st.sidebar.selectbox("", ids_disponiveis, label_visibility="collapsed")
        
        registro_selecionado = df_atual[df_atual["Id"].astype(str) == str(id_para_editar)].iloc[0]
        id_atual = str(registro_selecionado["Id"])

elif modo == "🗑️ Deletar Linha (ID)":
    if df_atual.empty:
        st.sidebar.warning("Base de dados vazia para exclusão.")
        modo = "📊 Visualizar Base"
    else:
        ids_disponiveis = df_atual["Id"].dropna().astype(str).unique().tolist()
        
        # Corrigido: margem reajustada para dar espaço seguro ao texto
        st.sidebar.markdown("<p style='color: #ffffff; font-weight: 600; margin-bottom: 5px;'>Selecione o ID para Deletar:</p>", unsafe_allow_html=True)
        id_para_deletar = st.sidebar.selectbox("", ids_disponiveis, label_visibility="collapsed")
        
        id_atual = str(id_para_deletar)


# --- FLUXO DE TELAS CENTRAL ---

# --- TELA 1: VISUALIZAÇÃO COM CONVERSOR DE DATA SERIAL DO EXCEL ---
if modo == "📊 Visualizar Base":
    st.markdown("<h3 style='color: #03170a;'>📊 Visualização Atual dos Dados (Espelho SharePoint)</h3>", unsafe_allow_html=True)
    
    if df_atual.empty:
        st.info("A base de dados está vazia.")
    else:
        # --- 1. FUNÇÃO DE TRATAMENTO E CONVERSÃO DE DATAS MISTAS (EXCEL SERIAL VS ISO) ---
        def limpar_e_converter_data(valor):
            if pd.isna(valor):
                return pd.NaT
            
            # Limpa espaços e transforma em string
            val_str = str(valor).strip()
            if val_str == "" or val_str.lower() in ["none", "nat", "nan"]:
                return pd.NaT
            
            # Se for um número serial do Excel (ex: 45818 ou 45818.0)
            if val_str.replace('.', '', 1).isdigit():
                try:
                    num_serial = int(float(val_str))
                    # O Excel conta a partir de 30/12/1899 devido a um bug histórico com o ano de 1900
                    return pd.to_datetime(num_serial, unit='D', origin='1899-12-30')
                except:
                    pass
            
            # Se já for uma string de data (ex: 2026-05-19 ou 19/05/2026)
            return pd.to_datetime(val_str, errors='coerce', format='mixed')

        # Criamos uma cópia de trabalho e aplicamos a conversão robusta nas duas colunas de data
        df_trabalho = df_atual.copy()
        df_trabalho["Data_Inicio_Datetime"] = df_trabalho["Data de Início"].apply(limpar_e_converter_data)
        df_trabalho["Data_Termino_Datetime"] = df_trabalho["Data de Término"].apply(limpar_e_converter_data)
        
        # Define os limites ABSOLUTOS reais baseados no que existe nos dados para o Slider
        data_min_absoluta = df_trabalho["Data_Inicio_Datetime"].min()
        data_max_absoluta = df_trabalho["Data_Inicio_Datetime"].max()
        
        # Fallback de segurança se a coluna inteira estiver nula
        if pd.isna(data_min_absoluta) or pd.isna(data_max_absoluta):
            data_min_absoluta = pd.Timestamp("2025-01-01")
            data_max_absoluta = pd.Timestamp("2026-12-31")

        # --- 2. LÓGICA DOS FILTROS DE SELEÇÃO (CASCATA SEQUENCIAL) ---
        df_filtros = df_trabalho.copy()
        
        # LINHA 1 DE FILTROS
        col_ano, col_uf, col_nivel = st.columns(3)
        
        # Filtro 1: Ano da Ação
        anos_disponiveis = ["Todos"] + sorted(df_filtros["Ano da Ação"].dropna().astype(str).unique().tolist())
        with col_ano:
            ano_selecionado = st.selectbox("📅 Filtrar por Ano:", anos_disponiveis)
        if ano_selecionado != "Todos":
            df_filtros = df_filtros[df_filtros["Ano da Ação"].astype(str) == ano_selecionado]
        
        # Filtro 2: UF_Acao_PNAPA
        ufs_disponiveis = ["Todas"] + sorted(df_filtros["UF_Acao_PNAPA"].dropna().astype(str).unique().tolist())
        with col_uf:
            uf_selecionada = st.selectbox("📍 Filtrar por UF:", ufs_disponiveis)
        if uf_selecionada != "Todas":
            df_filtros = df_filtros[df_filtros["UF_Acao_PNAPA"].astype(str) == uf_selecionada]
            
        # Filtro 3: Nível
        niveis_disponiveis = ["Todos"] + sorted(df_filtros["Nível"].dropna().astype(str).unique().tolist())
        with col_nivel:
            nivel_selecionado = st.selectbox("🎚️ Filtrar por Nível:", niveis_disponiveis)
        if nivel_selecionado != "Todos":
            df_filtros = df_filtros[df_filtros["Nível"].astype(str) == nivel_selecionado]

        # LINHA 2 DE FILTROS
        col_servidor, col_data = st.columns([1, 2])
        
        # Filtro 4: Servidor
        servidores_disponiveis = ["Todos"] + sorted(df_filtros["Servidor"].dropna().astype(str).unique().tolist())
        with col_servidor:
            servidor_selecionado = st.selectbox("👤 Filtrar por Servidor:", servidores_disponiveis)

        # Filtro 5: Slider de Datas (Baseado nas datas tratadas)
        with col_data:
            intervalo_datas = st.slider(
                "⏳ Período (Data de Início):",
                min_value=data_min_absoluta.to_pydatetime().date(),
                max_value=data_max_absoluta.to_pydatetime().date(),
                value=(data_min_absoluta.to_pydatetime().date(), data_max_absoluta.to_pydatetime().date()),
                format="DD/MM/YYYY"
            )

        # --- 3. APLICAÇÃO VISUAL DOS FILTROS COMBINADOS ---
        df_exibicao = df_trabalho.copy()
        
        if ano_selecionado != "Todos":
            df_exibicao = df_exibicao[df_exibicao["Ano da Ação"].astype(str) == ano_selecionado]
        if uf_selecionada != "Todas":
            df_exibicao = df_exibicao[df_exibicao["UF_Acao_PNAPA"].astype(str) == uf_selecionada]
        if nivel_selecionado != "Todos":
            df_exibicao = df_exibicao[df_exibicao["Nível"].astype(str) == nivel_selecionado]
        if servidor_selecionado != "Todos":
            df_exibicao = df_exibicao[df_exibicao["Servidor"].astype(str) == servidor_selecionado]
            
        # Filtro do intervalo do Slider
        inicio_busca = pd.Timestamp(intervalo_datas[0])
        fim_busca = pd.Timestamp(intervalo_datas[1])
        
        if intervalo_datas[0] == data_min_absoluta.to_pydatetime().date() and intervalo_datas[1] == data_max_absoluta.to_pydatetime().date():
            pass
        else:
            df_exibicao = df_exibicao[
                (df_exibicao["Data_Inicio_Datetime"] >= inicio_busca) & 
                (df_exibicao["Data_Inicio_Datetime"] <= fim_busca)
            ]
        
        # --- REFORMATAR AS COLUNAS ORIGINAIS PARA TEXTO BR EM DATAFRAME PURO ---
        df_exibicao["Data de Início"] = df_exibicao["Data_Inicio_Datetime"].dt.strftime('%d/%m/%Y').fillna("")
        df_exibicao["Data de Término"] = df_exibicao["Data_Termino_Datetime"].dt.strftime('%d/%m/%Y').fillna("")
        
        # Remove as colunas auxiliares com segurança para manter o Grid limpo
        df_exibicao = df_exibicao.drop(columns=["Data_Inicio_Datetime", "Data_Termino_Datetime"])

        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- 4. EXIBIÇÃO DA PLANILHA INTERATIVA ZEBRADA DINÂMICA ---
        def estilar_linhas_zebradas(linha):
            # Agora que o índice foi resetado, a contagem par/ímpar será sempre contínua (0, 1, 2, 3...)
            cor_fundo = '#f0f5df' if linha.name % 2 == 0 else '#ffffff'
            return [f'background-color: {cor_fundo}; color: #03170a;' for _ in linha]

        # O TRUQUE: .reset_index(drop=True) reconstrói a numeração sequencial das linhas que sobraram
        df_para_visualizar = df_exibicao.reset_index(drop=True)
        
        # O estilo agora é aplicado sobre uma sequência limpa e recalcula o zebrado perfeitamente
        df_estilizado = df_para_visualizar.style.apply(estilar_linhas_zebradas, axis=1)
        
        st.dataframe(df_estilizado, use_container_width=True)

# --- TELA 2 E 3: FORMULÁRIO (INSERIR OU EDITAR) ---
elif modo in ["➕ Inserir Nova Linha", "📝 Editar Linha Existente"]:
    st.markdown(f"<h3 style='color: #f1f3f5;'>Formulário de Dados PNAPA — Modo: {modo}</h3>", unsafe_allow_html=True)
    
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
            
            st.markdown("<p style='font-weight: bold; margin-top:15px; color:#f1f3f5;'>Valores Orçamentários</p>", unsafe_allow_html=True)
            
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

    # --- PROCESSAMENTO DA GRAVAÇÃO (INSERIR/EDITAR) ---
    if submetido:
        total_plan = rec_p_diarias + rec_p_passagens + rec_p_outras
        total_exec = rec_e_diarias + rec_e_passagens + rec_e_outras
        
        if modo == "➕ Inserir Nova Linha":
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

        with st.spinner("Sincronizando com a nuvem do IBAMA..."):
            try:
                resposta = requests.post(URL_GRAVAR, json=payload)
                if resposta.status_code in [200, 202]:
                    st.markdown(f"<div style='padding:12px; border-radius:5px; background-color:#1c2d20; color:#a3e635; border:1px solid #3f6212; margin-bottom:15px;'>🎉 Sucesso! Registro {id_final} enviado ao SharePoint.</div>", unsafe_allow_html=True)
                    time.sleep(2)
                    st.cache_data.clear()
                    if "df" in st.session_state:
                        del st.session_state.df
                    st.rerun()
                else:
                    st.markdown(f"<div style='padding:12px; border-radius:5px; background-color:#2a1a1a; color:#f87171; border:1px solid #7f1d1d; margin-bottom:15px;'>❌ Erro no Power Automate: Status {resposta.status_code}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"<div style='padding:12px; border-radius:5px; background-color:#2a1a1a; color:#f87171; border:1px solid #7f1d1d; margin-bottom:15px;'>❌ Falha na comunicação com o fluxo: {e}</div>", unsafe_allow_html=True)

# --- TELA 4: EXCLUSÃO DE LINHA ---
elif modo == "🗑️ Deletar Linha (ID)":
    st.markdown("<h3 style='color: #f1f3f5;'>🗑️ Excluir Registro Existente</h3>", unsafe_allow_html=True)
    st.markdown("<div style='padding:12px; border-radius:5px; background-color:#2a1b15; color:#fdba74; border:1px solid #c2410c; margin-bottom:20px;'>⚠️ Atenção: A remoção de registros da base do PNAPA é uma operação definitiva dentro do SharePoint.</div>", unsafe_allow_html=True)
    
    # Campo informativo mostrando qual ID veio selecionado na Sidebar
    st.text_input("ID Marcado para Exclusão", value=id_atual, disabled=True)
    
    # Caixa Popover de segurança (Atua como modal de confirmação)
    with st.popover("🚨 Confirmar Exclusão Permanente", use_container_width=True):
        st.markdown(f"<p style='color:#f1f3f5;'>Tem certeza absoluta de que deseja destruir permanentemente o registro de <b>ID {id_atual}</b>?</p>", unsafe_allow_html=True)
        confirmou_exclusao = st.button("Sim, deletar agora!", type="primary", use_container_width=True)
        
        if confirmou_exclusao:
            payload_deletar = {"Id": str(id_atual)}
            
            with st.spinner("Removendo linha no SharePoint via Power Automate..."):
                try:
                    resposta_del = requests.post(URL_DELETAR, json=payload_deletar)
                    if resposta_del.status_code in [200, 202]:
                        st.markdown(f"<div style='padding:12px; border-radius:5px; background-color:#1c2d20; color:#a3e635; border:1px solid #3f6212; margin-bottom:15px;'>💥 Sucesso! O Registro {id_atual} foi excluído da base.</div>", unsafe_allow_html=True)
                        time.sleep(2)
                        st.cache_data.clear()
                        if "df" in st.session_state:
                            del st.session_state.df
                        st.rerun()
                    else:
                        st.markdown(f"<div style='padding:12px; border-radius:5px; background-color:#2a1a1a; color:#f87171; border:1px solid #7f1d1d;'>❌ Erro no Power Automate ao deletar: Status {resposta_del.status_code}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f"<div style='padding:12px; border-radius:5px; background-color:#2a1a1a; color:#f87171; border:1px solid #7f1d1d;'>❌ Falha na comunicação com o fluxo de exclusão: {e}</div>", unsafe_allow_html=True)
