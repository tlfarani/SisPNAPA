import streamlit as st
import pandas as pd
import requests
import time
from datetime import date, datetime
import plotly.express as px

st.set_page_config(page_title="SisPNAPA - Emergências Ambientais e Climáticas", layout="wide")

# =================================================================
# 1. ENDPOINTS DO POWER AUTOMATE & CREDENCIAIS (SHAREPOINT)
# =================================================================
# URLs das tabelas auxiliares (Gerenciamento de Infraestrutura)
URL_FLOW_UNIDADES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/c2207ed01bf64853a477e7b6b165c3e8/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=GR6JhJzrEZTapCOAKwlY9VGzT_g-6xQGBG7YLraG6Z4"
URL_FLOW_EQUIPES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/3d124cc6783845e1b8618cfb3302eca0/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ubTQ-LAIsToMOX0CGytlI2YM_WKmC_mRT64ybRLBRSY"
URL_FLOW_PNAPAS = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/38cc92ea33ba4d6387b924d6eac62d58/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=LlCDUzrETHyXxp_QLte1eGxKR_4LuwRGzPJbgUsHvgk"
URL_FLOW_SUGESTOES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/12/workflows/879c1fc3770545039e738cc24d0a4a23/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=_4vVSJhFVRuYWXneiKhnPkx3A66J9DFzLWM0OmISV-U"

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
LISTA_PERIGOS = ["Não se Aplica", "Periculosidade", "Insalubridade"]
LISTA_ORIGENS_RECURSO = LISTA_UFS_COMPLETA + ["Ceneac", "Não se aplica", "Outras fontes"]
LISTA_IMPORTANCIA = ["Ordinária", "Prioritária", "Estratégica"]
LISTA_PAPEIS_INSTITUCIONAIS = ["Coordenação", "Apoio"]
LISTA_FUNCOES_CAMPO = ["Coordenador de Campo", "Apoio de Campo"]

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
    "Codigo_Atividade", "Papel_Institucional", "Coordenador_Operacao",
    "Nome da Atividade", "Andamento", "Indicador", "Meta_Indicador", "Resultado_Indicador", 
    "Doc_Probatorio_Exec", "UF_Acao_PNAPA", "Importância da Atividade", "Tema da Atividade", 
    "Objetivo da Atividade", "Tipo de Atividade", "Periculosidade/Insalubridade", "Servidor", 
    "UF_Servidor", "Lotação", "Faz parte da Equipe de Emergências", "Número da PCDP", 
    "País", "UF Onde Ocorreu/Ocorrerá a Ação", "Estado_Local_Acao", "Municipio Onde Ocorreu/Ocorrerá a Ação", 
    "Data de Início", "Data de Término", "Dias_Gastos_Plan", "Dias_Gastos_Exec", "Origem do Recurso", 
    "Rec_Plan_Diarias", "Rec_Plan_Passagens", "Rec_Plan_Outras_Despesas", "Rec_Plan_Total", 
    "Rec_Exec_Diarias", "Rec_Exec_Passagens", "Rec_Exec_Outras_Despesas", "Rec_Exec_Total", 
    "Observações", "Justificativa_Acao_PNAPA", "Avaliacao_Qualidade", "Avaliacao_Feedback",
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

def obter_float_limpo(val):
    """Converte qualquer formato (string vazia, None, NaN, formato BR com vírgula) para float de forma segura."""
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip().replace("R$", "").replace(" ", "")
    if val_str == "" or val_str.lower() in ["none", "nan", "nat"]:
        return 0.0
    if "," in val_str and "." in val_str:
        val_str = val_str.replace(".", "").replace(",", ".")
    elif "," in val_str:
        val_str = val_str.replace(",", ".")
    num = pd.to_numeric(val_str, errors='coerce')
    return 0.0 if pd.isna(num) else float(num)

def payload_gerador(
    val_ano, val_num_acao, val_nome_acao, val_indicador, nivel_selecionado, 
    nome_atividade, andamento, resultado_indicador, doc_probatorio, uf_acao, 
    importancia, tema, objetivo, tipo_atividade, periculosidade, servidor, 
    uf_servidor, lotacao, equipe_emergencia, num_pcdp, pais, uf_ocorrencia, 
    estado_local, municipio, dt_inicio, dt_termino, dias_plan, dias_exec, 
    origem_recurso, rec_p_diarias, rec_p_passagens, rec_p_outras, rec_e_diarias, 
    rec_e_passagens, rec_e_outras, obs, justificativa, id_atual, modo, df_atual,
    papel_institucional="", coordenador_operacao="", meta_indicador="", codigo_atividade="",
    aval_qualidade="", aval_feedback=""
):
    if modo == "➕ Inserir Nova Linha":
        id_final = str(int(pd.to_numeric(df_atual["Id"], errors='coerce').dropna().max() + 1)) if not df_atual.empty else "1"
        acao_switch = "Inserir"
    else:
        id_final = str(id_atual)
        acao_switch = "Editar"

    # 🛡️ Sanitização blindada de todos os valores numéricos
    d_plan = obter_float_limpo(dias_plan)
    d_exec = obter_float_limpo(dias_exec)
    rp_d = obter_float_limpo(rec_p_diarias)
    rp_p = obter_float_limpo(rec_p_passagens)
    rp_o = obter_float_limpo(rec_p_outras)
    re_d = obter_float_limpo(rec_e_diarias)
    re_p = obter_float_limpo(rec_e_passagens)
    re_o = obter_float_limpo(rec_e_outras)
    meta_ind = obter_float_limpo(meta_indicador) if str(meta_indicador).strip() != "" else ""

    return {
        "Acao": acao_switch,
        "Id": id_final,
        "Ano da Ação": int(val_ano) if val_ano else 2026,
        "Número da Ação PNAPA": str(val_num_acao),
        "Nome da Ação PNAPA": str(val_nome_acao),
        "Nível": str(nivel_selecionado),
        "Codigo_Atividade": str(codigo_atividade),
        "Papel_Institucional": str(papel_institucional),
        "Coordenador_Operacao": str(coordenador_operacao),
        "Nome da Atividade": str(nome_atividade),
        "Andamento": str(andamento),
        "Indicador": str(val_indicador),
        "Meta_Indicador": str(meta_ind),
        "Resultado_Indicador": str(resultado_indicador),
        "Doc_Probatorio_Exec": str(doc_probatorio),
        "UF_Acao_PNAPA": str(uf_acao),
        "Importância da Atividade": str(importancia),
        "Tema da Atividade": str(tema),
        "Objetivo da Atividade": str(objetivo),
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
        "Dias_Gastos_Plan": d_plan,
        "Dias_Gastos_Exec": d_exec,
        "Origem do Recurso": str(origem_recurso),
        "Rec_Plan_Diarias": rp_d,
        "Rec_Plan_Passagens": rp_p,
        "Rec_Plan_Outras_Despesas": rp_o,
        "Rec_Plan_Total": float(rp_d + rp_p + rp_o),
        "Rec_Exec_Diarias": re_d,
        "Rec_Exec_Passagens": re_p,
        "Rec_Exec_Outras_Despesas": re_o,
        "Rec_Exec_Total": float(re_d + re_p + re_o),
        "Observações": str(obs),
        "Justificativa_Acao_PNAPA": str(justificativa),
        "Avaliacao_Qualidade": str(aval_qualidade),
        "Avaliacao_Feedback": str(aval_feedback)
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

@st.cache_data(ttl=15, show_spinner=False)
def carregar_sugestoes():
    """Lê os registros da planilha Sugestoes.xlsx via Power Automate com sanitização."""
    cols_padrao = ["Id", "Data_Registro", "Autor", "UF_Autor", "Modulo", "Titulo", "Descricao", "Prioridade", "Status", "Resposta_Admin"]
    try:
        r = requests.post(URL_FLOW_SUGESTOES, json={"Acao": "Ler", "Id": ""}, timeout=15)
        if r.status_code == 200:
            dados = r.json()
            lista_itens = dados.get("value", dados) if isinstance(dados, dict) else dados
            
            if isinstance(lista_itens, list) and len(lista_itens) > 0:
                df = pd.DataFrame(lista_itens)
                
                # 1. Limpeza de cabeçalhos
                df.columns = [str(c).replace('\xa0', ' ').strip() for c in df.columns]
                
                # 2. Garante as colunas necessárias
                for c in cols_padrao:
                    if c not in df.columns:
                        df[c] = ""
                
                # 3. Descarta linhas em branco/nulas do Excel
                df = df[df["Id"].notna()]
                df["Id_Str"] = df["Id"].astype(str).str.strip()
                df = df[~df["Id_Str"].isin(["", "nan", "None"])]
                df = df.drop(columns=["Id_Str"])
                
                # 4. Converte Id para número e ordena pelo mais recente
                df["Id_Num"] = pd.to_numeric(df["Id"], errors='coerce').fillna(0)
                df = df.sort_values(by="Id_Num", ascending=False).drop(columns=["Id_Num"]).reset_index(drop=True)
                
                return df
        else:
            st.error(f"⚠️ O Power Automate recusou a leitura de sugestões (Status {r.status_code}): {r.text}")
    except Exception as e:
        st.error(f"⚠️ Erro de conexão ao carregar sugestões: {e}")
    
    return pd.DataFrame(columns=cols_padrao)

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

def converter_para_data_segura(valor):
    """Converte com segurança qualquer formato (serial Excel, ISO, string BR) para date."""
    if pd.isna(valor) or valor is None:
        return date.today()
    if isinstance(valor, (datetime, pd.Timestamp)):
        return valor.date()
    if isinstance(valor, date):
        return valor
    val_str = str(valor).strip()
    if val_str == "" or val_str.lower() in ["none", "nat", "nan"]:
        return date.today()
    # Serial do Excel (ex: 45678)
    if val_str.replace('.', '', 1).isdigit():
        try:
            return pd.to_datetime(int(float(val_str)), unit='D', origin='1899-12-30').date()
        except:
            pass
    # Força o parsing com dia primeiro (Padrão Brasil)
    dt = pd.to_datetime(val_str, errors='coerce', dayfirst=True)
    return dt.date() if pd.notna(dt) else date.today()

def classificar_nivel_acao(dias):
    try:
        dias = float(dias)
    except:
        return "Indefinido"
    
    if dias <= 5:
        return "Nível 1 (Leve)"
    elif dias < 20:
        return "Nível 2 (Médio)"
    else:
        return "Nível 3 (Intensivo)"

# Carregamento das tabelas de apoio (Unidades, Servidores e Ações PNAPA)
@st.cache_data(ttl=60)
def carregar_bases_vias_power_automate():
    dados_uni = executar_api_unidades({"Acao": "Ler"})
    dados_srv = executar_api_equipes({"Acao": "Ler"})
    dados_pna = executar_api_pnapas({"Acao": "Ler"})
    
    df_lot = pd.DataFrame(dados_uni) if dados_uni else pd.DataFrame(columns=["ID_UF", "UF", "Unidade"])
    df_serv = pd.DataFrame(dados_srv) if dados_srv else pd.DataFrame(columns=["ID_SERV", "Servidor", "UF_Servidor", "Lotacao", "Equipe_Emergencias", "Fiscal", "AEAC", "Funcao", "E_mail", "Perfil", "Token"])
    
    # 🚀 Inclui as colunas de Governança Nacional
    cols_pna_padrao = ["ID_PNAPA", "Ano", "Num_Acao_PNAPA", "Acao_Ano", "Nome_Acao_Completo", "Nome_Acao_Apelido", "Importância", "Indicador", "UF_Dono", "Dono_Acao", "Meta_Nacional"]
    df_pna = pd.DataFrame(dados_pna) if dados_pna else pd.DataFrame(columns=cols_pna_padrao)
    for c in cols_pna_padrao:
        if c not in df_pna.columns:
            df_pna[c] = ""
    
    return df_lot, df_serv, df_pna

def obter_ponto_focal_acao(df, cod_acao, uf_alvo):
    """Localiza de forma flexível o Ponto Focal e o Papel do Estado na Ação Pai."""
    if df.empty or not cod_acao:
        return "", "Não Cadastrado"
    
    cod_puro = str(cod_acao).split("-")[0].strip().upper()
    cod_comp = str(cod_acao).strip().upper()
    uf_limpa = str(uf_alvo).strip().upper()
    
    linhas = df[
        (df["Nível"].astype(str).str.strip() == "Ação") &
        (df["UF_Acao_PNAPA"].astype(str).str.strip().str.upper() == uf_limpa) &
        (
            (df["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == cod_comp) |
            (df["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == cod_puro) |
            (df["Número da Ação PNAPA"].astype(str).str.strip().str.upper().str.startswith(cod_puro))
        )
    ]
    
    if not linhas.empty:
        focal = str(linhas["Servidor"].iloc[0]).strip()
        papel = str(linhas["Papel_Institucional"].iloc[0]).strip() if "Papel_Institucional" in linhas.columns else "Coordenação"
        return focal, papel
    return "", "Não Cadastrado"

df_lotacoes, df_servidores, df_pnapas = carregar_bases_vias_power_automate()

df_sugestoes = carregar_sugestoes()

# Inicialização e Cache da Planilha Macro Principal no session_state
if "df" not in st.session_state:
    with st.spinner("Buscando dados no SharePoint via Power Automate..."):
        st.session_state.df = carregar_dados_da_nuvem()

df_atual = st.session_state.df

# 🛡️ BLINDAGEM CONTRA KEYERROR: Garante que todas as colunas oficiais existam no DataFrame
for col_oficial in COLUNAS_PNAPA:
    if col_oficial not in df_atual.columns:
        df_atual[col_oficial] = ""

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
# IV. GESTÃO DE AUTENTICAÇÃO E PERFIS DE ACESSO (SSO & PERFIS)
# =================================================================
try:
    nome_usuario_logado = df_servidores[df_servidores["E_mail"] == email_logado]["Servidor"].iloc[0]
except:
    nome_usuario_logado = "Desconhecido"

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
    uf_usuario = str(dados_usuario["UF_Servidor"]).strip()
    perfil_usuario = str(dados_usuario["Perfil"]).strip()
    token_correto = str(dados_usuario["Token"]).strip()
except:
    uf_usuario = "SP"
    perfil_usuario = "Visualização"
    token_correto = None

if email_logado == EMAIL_ADMIN:
    perfil_usuario = "Administrador"

acesso_liberado = False

# Simulador de Perfis para Testes (Exclusivo para o Desenvolvedor / Admin)
if email_logado == EMAIL_ADMIN:
    st.sidebar.markdown("### 🧪 Simulador de Nível de Acesso")
    perfil_teste = st.sidebar.selectbox("Testar Perfil como:", ["Administrador", "Editor Regional", "Visualização"], index=0)
    perfil_usuario = perfil_teste
    if perfil_usuario == "Editor Regional":
        uf_usuario = st.sidebar.selectbox("Simular UF do Editor:", LISTA_UFS_COMPLETA, index=LISTA_UFS_COMPLETA.index("SP"))
    acesso_liberado = True if perfil_usuario != "Visualização" else False
else:
    if perfil_usuario == "Administrador":
        acesso_liberado = True
        st.sidebar.success("👑 Administrador Conectado")
    elif perfil_usuario == "Editor Regional":
        token_digitado = st.sidebar.text_input("Token de Editor Regional:", type="password")
        if token_digitado and token_digitado == token_correto:
            acesso_liberado = True
            st.sidebar.success(f"🔓 Editor Regional ({uf_usuario})")
        elif token_digitado:
            st.sidebar.error("❌ Token incorreto.")
    else:
        st.sidebar.info("👁️ Perfil: Somente Visualização")

# Montagem Dinâmica do Menu Lateral (Garantindo Sugestões como a ÚLTIMA opção)
opcoes_menu = [
    "📈 Dashboards Executivos", 
    "📊 Visualizar Base"
]

# Páginas com restrição operacional (Admin e Editor Regional)
if acesso_liberado and perfil_usuario in ["Administrador", "Editor Regional"]:
    opcoes_menu.extend([
        "➕ Inserir Nova Linha", 
        "🏢 Gerenciar Unidades", 
        "👥 Gerenciar Equipes", 
        "🗂️ Gerenciar Ações PNAPA"
    ])

# 🚀 Sugestões sempre como o último item para todos os perfis:
opcoes_menu.append("💡 Sugestões & Melhorias")

st.sidebar.markdown("## 🕹️ Painel de Controle")
modo = st.sidebar.radio("Navegação:", opcoes_menu)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Atualizar Base (Refresh)", use_container_width=True):
    st.cache_data.clear()
    if "df" in st.session_state: 
        del st.session_state.df
    st.rerun()
    
# Variáveis de controle de contexto para a Planilha Macro
registro_selecionado = None
id_atual = ""

# =================================================================
# V. NÚCLEO OPERACIONAL DAS TELAS
# =================================================================

# --- PÁGINA: DASHBOARDS EXECUTIVOS ---
if modo == "📈 Dashboards Executivos":
    st.markdown("<h2 style='color: #03170a;'>📈 Painel Executivo & Indicadores Estratégicos</h2>", unsafe_allow_html=True)
    st.caption("Visão consolidada das operações do Plano Nacional de Ação de Emergências Ambientais (PNAPA).")
    
    if df_atual.empty:
        st.info("Aguardando carregamento da base de dados do SharePoint.")
    else:
        import plotly.graph_objects as go
        import plotly.express as px
        from datetime import date
        import pandas as pd

        # =====================================================================
        # 1. PREPARAÇÃO DE DADOS E LÓGICA DE FILTRAGEM RESPONSIVA
        # =====================================================================
        df_dash_atv = df_atual[df_atual["Nível"].astype(str).str.strip() == "Atividade"].copy()
        
        # Conversão de Datas e Numéricos para Atividades
        df_dash_atv["Data_Inicio_DT"] = pd.to_datetime(df_dash_atv["Data de Início"], format='%d/%m/%Y', errors='coerce')
        df_dash_atv["Data_Fim_DT"] = pd.to_datetime(df_dash_atv["Data de Término"], format='%d/%m/%Y', errors='coerce')
        df_dash_atv["Mes_Inicio"] = df_dash_atv["Data_Inicio_DT"].dt.month
        df_dash_atv["Dias_Gastos_Plan"] = pd.to_numeric(df_dash_atv["Dias_Gastos_Plan"], errors='coerce').fillna(0)
        df_dash_atv["Dias_Gastos_Exec"] = pd.to_numeric(df_dash_atv["Dias_Gastos_Exec"], errors='coerce').fillna(0)
        
        meses_pt = {1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril', 5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto', 9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'}
        df_dash_atv["Mes_Nome"] = df_dash_atv["Mes_Inicio"].map(meses_pt)

        # Função de Cascata: Filtra os dados com base nos outros campos
        def aplicar_filtros_dash(df_orig, dict_filtros, chave_ignorar=None):
            df_res = df_orig.copy()
            for k, (col_nome, val) in dict_filtros.items():
                if k == chave_ignorar or val in ["Todos", "Todas", None, ""]:
                    continue
                if col_nome == "Ano da Ação":
                    df_res = df_res[df_res["Ano da Ação"].astype(str).str.split('.').str[0] == str(val)]
                elif col_nome == "Data_Inicio_DT":
                    if isinstance(val, (tuple, list)) and len(val) == 2:
                        ts_ini = pd.to_datetime(val[0])
                        ts_fim = pd.to_datetime(val[1]) + pd.Timedelta(hours=23, minutes=59, seconds=59)
                        df_res = df_res[df_res["Data_Inicio_DT"].isna() | ((df_res["Data_Inicio_DT"] >= ts_ini) & (df_res["Data_Inicio_DT"] <= ts_fim))]
                else:
                    if col_nome in df_res.columns:
                        df_res = df_res[df_res[col_nome].astype(str) == str(val)]
            return df_res

        # Função segura (Callback) para limpar os filtros antes do recarregamento da tela
        def limpar_filtros_dashboard():
            for k in ["fd_ano", "fd_uf", "fd_lot", "fd_srv", "fd_pna", "fd_tema", "fd_and"]:
                st.session_state[k] = "Todos"
            if "fd_dt_range" in st.session_state: del st.session_state["fd_dt_range"]
            if "clique_mes" in st.session_state: del st.session_state["clique_mes"]
            if "clique_atv" in st.session_state: del st.session_state["clique_atv"]

        # =====================================================================
        # 2. BARRA SUPERIOR DE FILTROS (TOP BAR - CROSS-FILTERING)
        # =====================================================================
        st.markdown("##### 🔍 Contexto e Filtros Globais")
        
        # Inicializa estado seguro dos filtros
        for k in ["fd_ano", "fd_uf", "fd_lot", "fd_srv", "fd_pna", "fd_tema", "fd_and"]:
            if k not in st.session_state: st.session_state[k] = "Todos"
            
        filtros_d = {
            "ano": ("Ano da Ação", st.session_state["fd_ano"]),
            "uf": ("UF_Acao_PNAPA", st.session_state["fd_uf"]),
            "lot": ("Lotação", st.session_state["fd_lot"]),
            "srv": ("Servidor", st.session_state["fd_srv"]),
            "pna": ("Número da Ação PNAPA", st.session_state["fd_pna"]),
            "tema": ("Tema da Atividade", st.session_state["fd_tema"]),
            "and": ("Andamento", st.session_state["fd_and"]),
            "data": ("Data_Inicio_DT", st.session_state.get("fd_dt_range", None))
        }

        c_filt1, c_filt2, c_filt3, c_filt4 = st.columns([1, 1, 1, 0.5])
        
        with c_filt1:
            with st.popover("📅 Período Considerado", use_container_width=True):
                # 1. Ano Responsivo
                df_p_ano = aplicar_filtros_dash(df_dash_atv, filtros_d, "ano")
                anos_disp = ["Todos"] + sorted([str(int(a)) for a in df_p_ano["Ano da Ação"].dropna().unique() if str(a).strip().isdigit()], reverse=True)
                idx_ano = anos_disp.index(filtros_d["ano"][1]) if filtros_d["ano"][1] in anos_disp else 0
                f_ano = st.selectbox("Ano da Ação:", anos_disp, index=idx_ano, key="fd_ano")
                filtros_d["ano"] = ("Ano da Ação", f_ano)

                # 2. Slider Responsivo Seguro
                df_p_data = aplicar_filtros_dash(df_dash_atv, filtros_d, "data")
                dts_validas = df_p_data["Data_Inicio_DT"].dropna()
                
                min_dt_val = dts_validas.min().date() if not dts_validas.empty else date(2025, 1, 1)
                max_dt_val = dts_validas.max().date() if not dts_validas.empty else date(2026, 12, 31)
                if min_dt_val >= max_dt_val: max_dt_val = min_dt_val + pd.Timedelta(days=1)
                
                # Ajusta os limites para não gerar erro na UI
                if "fd_dt_range" not in st.session_state:
                    st.session_state["fd_dt_range"] = (min_dt_val, max_dt_val)
                else:
                    c_start, c_end = st.session_state["fd_dt_range"]
                    n_start = max(min_dt_val, min(c_start, max_dt_val))
                    n_end = max(min_dt_val, min(c_end, max_dt_val))
                    if n_start > n_end: n_start = min_dt_val
                    st.session_state["fd_dt_range"] = (n_start, n_end)

                f_dt = st.slider("Data de Início:", min_value=min_dt_val, max_value=max_dt_val, format="DD/MM/YYYY", key="fd_dt_range")
                filtros_d["data"] = ("Data_Inicio_DT", f_dt)

        with c_filt2:
            with st.popover("🗺️ UF / Lotação / Servidor", use_container_width=True):
                df_p_uf = aplicar_filtros_dash(df_dash_atv, filtros_d, "uf")
                ufs_disp = ["Todos"] + sorted(df_p_uf["UF_Acao_PNAPA"].dropna().astype(str).unique().tolist())
                idx_uf = ufs_disp.index(filtros_d["uf"][1]) if filtros_d["uf"][1] in ufs_disp else 0
                f_uf = st.selectbox("UF da Ação:", ufs_disp, index=idx_uf, key="fd_uf")
                filtros_d["uf"] = ("UF_Acao_PNAPA", f_uf)

                df_p_lot = aplicar_filtros_dash(df_dash_atv, filtros_d, "lot")
                lot_disp = ["Todos"] + sorted(df_p_lot["Lotação"].dropna().astype(str).unique().tolist())
                idx_lot = lot_disp.index(filtros_d["lot"][1]) if filtros_d["lot"][1] in lot_disp else 0
                f_lot = st.selectbox("Lotação:", lot_disp, index=idx_lot, key="fd_lot")
                filtros_d["lot"] = ("Lotação", f_lot)

                df_p_srv = aplicar_filtros_dash(df_dash_atv, filtros_d, "srv")
                srvs_disp = ["Todos"] + sorted(df_p_srv["Servidor"].dropna().astype(str).unique().tolist())
                idx_srv = srvs_disp.index(filtros_d["srv"][1]) if filtros_d["srv"][1] in srvs_disp else 0
                f_srv = st.selectbox("Servidor:", srvs_disp, index=idx_srv, key="fd_srv")
                filtros_d["srv"] = ("Servidor", f_srv)

        with c_filt3:
            with st.popover("🏷️ Classificação Temática", use_container_width=True):
                df_p_pna = aplicar_filtros_dash(df_dash_atv, filtros_d, "pna")
                pnas_disp = ["Todos"] + sorted(df_p_pna["Número da Ação PNAPA"].dropna().astype(str).unique().tolist())
                idx_pna = pnas_disp.index(filtros_d["pna"][1]) if filtros_d["pna"][1] in pnas_disp else 0
                f_pna = st.selectbox("Ação PNAPA:", pnas_disp, index=idx_pna, key="fd_pna")
                filtros_d["pna"] = ("Número da Ação PNAPA", f_pna)

                df_p_tema = aplicar_filtros_dash(df_dash_atv, filtros_d, "tema")
                temas_disp = ["Todos"] + sorted(df_p_tema["Tema da Atividade"].dropna().astype(str).unique().tolist())
                idx_tema = temas_disp.index(filtros_d["tema"][1]) if filtros_d["tema"][1] in temas_disp else 0
                f_tema = st.selectbox("Tema:", temas_disp, index=idx_tema, key="fd_tema")
                filtros_d["tema"] = ("Tema da Atividade", f_tema)

                df_p_and = aplicar_filtros_dash(df_dash_atv, filtros_d, "and")
                ands_disp = ["Todos"] + sorted(df_p_and["Andamento"].dropna().astype(str).unique().tolist())
                idx_and = ands_disp.index(filtros_d["and"][1]) if filtros_d["and"][1] in ands_disp else 0
                f_and = st.selectbox("Status:", ands_disp, index=idx_and, key="fd_and")
                filtros_d["and"] = ("Andamento", f_and)

        with c_filt4:
            st.button("🧹 Limpar", use_container_width=True, on_click=limpar_filtros_dashboard)

        # --- APLICAÇÃO GERAL DOS FILTROS ---
        df_filt_atv = aplicar_filtros_dash(df_dash_atv, filtros_d, None)

        # Filtros Cruzados (Cliques de Gráficos)
        if "clique_mes" in st.session_state and st.session_state["clique_mes"]:
            df_filt_atv = df_filt_atv[df_filt_atv["Mes_Nome"] == st.session_state["clique_mes"]]
            st.warning(f"👆 Filtro cruzado ativo: **Mês de {st.session_state['clique_mes'].capitalize()}**. Use o botão 'Limpar' para remover.")
            
        if "clique_atv" in st.session_state and st.session_state["clique_atv"]:
            df_filt_atv = df_filt_atv[df_filt_atv["Nome da Atividade"] == st.session_state["clique_atv"]]
            st.warning(f"👆 Filtro cruzado ativo: **Atividade: {st.session_state['clique_atv']}**. Use o botão 'Limpar' para remover.")

        st.markdown("---")
              

        # =====================================================================
        # 3. NAVEGAÇÃO POR ABAS TEMÁTICAS
        # =====================================================================
        tab_exec, tab_oper, tab_gov, tab_desemp = st.tabs([
            "📊 Visão Executiva", 
            "🗓️ Operações & Calendário", 
            "⚖️ Governança & Carga", 
            "⭐ Desempenho de Equipes"
        ])

        # ---------------------------------------------------------------------
        # ABA 1: VISÃO EXECUTIVA
        # ---------------------------------------------------------------------
        with tab_exec:
            st.markdown("### Visão Geral do Portfólio")
            total_atividades_filt = len(df_filt_atv)
            total_acoes_global = len(df_atual[df_atual["Nível"] == "Ação"])
            rec_plan_total = pd.to_numeric(df_filt_atv["Rec_Plan_Total"], errors='coerce').fillna(0).sum()
            rec_exec_total = pd.to_numeric(df_filt_atv["Rec_Exec_Total"], errors='coerce').fillna(0).sum()
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("📌 Atividades Filtradas", f"{total_atividades_filt}")
            col_m2.metric("🎯 Total de Ações Globais", f"{total_acoes_global}")
            col_m3.metric("💰 Orçamento Planejado", f"R$ {rec_plan_total:,.2f}")
            col_m4.metric("💳 Orçamento Executado", f"R$ {rec_exec_total:,.2f}")
            
            col_g1, col_g2, col_g3 = st.columns([1, 1, 1])
            with col_g1:
                st.markdown("##### 🔄 Status das Atividades")
                df_and_chart = df_filt_atv["Andamento"].value_counts().reset_index()
                df_and_chart.columns = ["Andamento", "Quantidade"]
                st.bar_chart(df_and_chart.set_index("Andamento"), height=250)
                
            with col_g2:
                st.markdown("##### 📍 Concentração por UF")
                df_uf_cont = df_filt_atv[df_filt_atv["UF_Acao_PNAPA"] != ""]["UF_Acao_PNAPA"].value_counts().reset_index()
                df_uf_cont.columns = ["UF", "Quantidade"]
                st.bar_chart(df_uf_cont.set_index("UF"), height=250)
                
            with col_g3:
                st.markdown("##### 🍩 Dias Acumulados (Plan x Exec)")
                tot_plan = df_filt_atv["Dias_Gastos_Plan"].sum()
                tot_exec = df_filt_atv["Dias_Gastos_Exec"].sum()
                falta_executar = tot_plan - tot_exec if tot_plan > tot_exec else 0
                
                fig_donut = go.Figure(data=[go.Pie(
                    values=[tot_exec, falta_executar, max(tot_plan, tot_exec)], 
                    marker_colors=['#4f7942', '#e2e8f0', 'rgba(0,0,0,0)'], 
                    hole=0.7, direction='clockwise', sort=False, rotation=90, textinfo='none', hoverinfo='none'
                )])
                fig_donut.add_annotation(text=f"<b>{int(tot_exec)}</b>", x=0.5, y=0.4, font_size=40, showarrow=False)
                fig_donut.add_annotation(text=f"0", x=0.1, y=0.5, font_size=14, showarrow=False)
                fig_donut.add_annotation(text=f"{int(tot_plan)}", x=0.9, y=0.5, font_size=14, showarrow=False)
                fig_donut.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, showlegend=False, plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_donut, use_container_width=True)

        # ---------------------------------------------------------------------
        # ABA 2: OPERAÇÕES & CALENDÁRIO
        # ---------------------------------------------------------------------
        with tab_oper:
            st.markdown("### Acompanhamento Operacional Interativo")
            col_o1, col_o2 = st.columns([1, 1.5])
            
            with col_o1:
                st.markdown("##### 📅 Esforço Mensal (Dias)")
                df_mensal = df_filt_atv.groupby("Mes_Inicio")[["Dias_Gastos_Plan", "Dias_Gastos_Exec"]].sum().reset_index()
                df_mensal["Mes_Nome"] = df_mensal["Mes_Inicio"].map(meses_pt)
                df_mensal = df_mensal.sort_values("Mes_Inicio")
                
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(x=df_mensal["Mes_Nome"], y=df_mensal["Dias_Gastos_Plan"], name='Previstos', marker_color='#a3c1ad', text=df_mensal["Dias_Gastos_Plan"], textposition='outside'))
                fig_bar.add_trace(go.Bar(x=df_mensal["Mes_Nome"], y=df_mensal["Dias_Gastos_Exec"], name='Executados', marker_color='#4f7942', text=df_mensal["Dias_Gastos_Exec"], textposition='outside'))
                fig_bar.update_layout(barmode='group', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), margin=dict(t=10, b=0, l=0, r=0), height=300)
                
                try:
                    evento_bar = st.plotly_chart(fig_bar, use_container_width=True, on_select="rerun")
                    if evento_bar and evento_bar.selection and evento_bar.selection.points:
                        mes_selecionado = evento_bar.selection.points[0]["x"]
                        if st.session_state.get("clique_mes") != mes_selecionado:
                            st.session_state["clique_mes"] = mes_selecionado
                            st.session_state.pop("clique_atv", None)
                            st.rerun()
                except:
                    st.plotly_chart(fig_bar, use_container_width=True)

            with col_o2:
                st.markdown("##### 🗓️ Calendário de Ocorrências (Gantt)")
                df_gantt = df_filt_atv.dropna(subset=["Data_Inicio_DT", "Data_Fim_DT"]).copy()
                if not df_gantt.empty:
                    cor_mapa_gantt = {"Concluída": "#4f7942", "Prevista": "#60a5fa", "Não Iniciada": "#facc15", "Atrasada": "#ef4444"}
                    fig_gantt = px.timeline(df_gantt, x_start="Data_Inicio_DT", x_end="Data_Fim_DT", y="Nome da Atividade", color="Andamento", color_discrete_map=cor_mapa_gantt, hover_name="Servidor")
                    fig_gantt.update_yaxes(autorange="reversed", title_text="", showticklabels=True)
                    fig_gantt.update_xaxes(title_text="")
                    fig_gantt.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), margin=dict(t=10, b=0, l=0, r=0), height=300)
                    try:
                        evento_gantt = st.plotly_chart(fig_gantt, use_container_width=True, on_select="rerun")
                        if evento_gantt and evento_gantt.selection and evento_gantt.selection.points:
                            idx_gantt = evento_gantt.selection.points[0]["pointIndex"]
                            nome_atv_sel = df_gantt.iloc[idx_gantt]["Nome da Atividade"]
                            if st.session_state.get("clique_atv") != nome_atv_sel:
                                st.session_state["clique_atv"] = nome_atv_sel
                                st.session_state.pop("clique_mes", None)
                                st.rerun()
                    except:
                        st.plotly_chart(fig_gantt, use_container_width=True)
                else:
                    st.info("Não há atividades com datas válidas para o período.")

            st.markdown("##### 📋 Tabela Detalhada (Atividades Filtradas)")
            cols_tabela = ["Id", "Data de Início", "Data de Término", "Servidor", "Número da PCDP", "Número da Ação PNAPA", "Nome da Atividade"]
            df_tabela = df_filt_atv[[c for c in cols_tabela if c in df_filt_atv.columns]].copy()
            df_tabela = df_tabela.sort_values("Data de Início").reset_index(drop=True)
            st.dataframe(df_tabela, use_container_width=True, hide_index=True)

        # ---------------------------------------------------------------------
        # ABA 3: GOVERNANÇA E CARGA
        # ---------------------------------------------------------------------
        with tab_gov:
            st.markdown("### Governança Institucional (Nível Ação)")
            df_dashboard_acao = df_atual[df_atual["Nível"] == "Ação"].copy()
            df_dashboard_acao["Dias_Gastos_Plan"] = pd.to_numeric(df_dashboard_acao["Dias_Gastos_Plan"], errors='coerce').fillna(0)
            df_dashboard_acao["Nivel_Carga"] = df_dashboard_acao["Dias_Gastos_Plan"].apply(classificar_nivel_acao)
            ordem_carga = ["Nível 1 (Leve)", "Nível 2 (Médio)", "Nível 3 (Intensivo)", "Indefinido"]
            df_dashboard_acao["Nivel_Carga"] = pd.Categorical(df_dashboard_acao["Nivel_Carga"], categories=ordem_carga, ordered=True)
            
            col_gov1, col_gov2 = st.columns([1, 1.2])
            with col_gov1:
                st.markdown("#### ⚖️ Matriz de Sobrecarga (Ações)")
                df_carga = df_dashboard_acao.groupby(["Servidor", "Nivel_Carga"], observed=False).size().unstack(fill_value=0)
                st.dataframe(df_carga, use_container_width=True)
                st.caption("Recomendação: Evitar acúmulo de >2 ações de Nível 3 por Coordenador.")
            
            with col_gov2:
                st.markdown("#### 🎯 Matriz de Priorização")
                ordem_importancia = ["Ordinária", "Prioritária", "Estratégica"]
                fig_matriz = px.scatter(
                    df_dashboard_acao, x="Dias_Gastos_Plan", y="Importância da Atividade", color="Papel_Institucional",
                    hover_name="Nome da Ação PNAPA", size_max=15,
                    category_orders={"Importância da Atividade": ordem_importancia, "Nivel_Carga": ordem_carga},
                )
                fig_matriz.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
                fig_matriz.add_vline(x=5, line_dash="dash", line_color="green", annotation_text="Lim Nível 1")
                fig_matriz.add_vline(x=20, line_dash="dash", line_color="red", annotation_text="Lim Nível 3")
                fig_matriz.update_layout(xaxis_title="Dias Planejados", yaxis_title="", plot_bgcolor="white", margin=dict(t=10, b=0, l=0, r=0), height=350)
                st.plotly_chart(fig_matriz, use_container_width=True)

        # ---------------------------------------------------------------------
        # ABA 4: DESEMPENHO DAS EQUIPES (NOVO)
        # ---------------------------------------------------------------------
        with tab_desemp:
            st.markdown("### ⭐ Avaliação de Qualidade e Entregas")
            if "Avaliacao_Qualidade" in df_filt_atv.columns:
                df_avaliados = df_filt_atv[df_filt_atv["Avaliacao_Qualidade"].isin(["0 - Insatisfatória", "1 - Satisfatória"])]
                
                if df_avaliados.empty:
                    st.info("Nenhuma atividade avaliada pela liderança nos filtros selecionados.")
                else:
                    total_aval = len(df_avaliados)
                    sat_count = len(df_avaliados[df_avaliados["Avaliacao_Qualidade"] == "1 - Satisfatória"])
                    taxa_sucesso = (sat_count / total_aval) * 100 if total_aval > 0 else 0
                    
                    c_ds1, c_ds2 = st.columns([1, 2])
                    with c_ds1:
                        st.metric("Taxa de Entregas Satisfatórias", f"{taxa_sucesso:.1f}%")
                        st.caption(f"Baseado em {total_aval} avaliações concluídas.")
                        
                    with c_ds2:
                        st.markdown("##### Desempenho por Servidor")
                        df_perf = df_avaliados.groupby("Servidor")["Avaliacao_Qualidade"].value_counts().unstack(fill_value=0).reset_index()
                        if "1 - Satisfatória" not in df_perf.columns: df_perf["1 - Satisfatória"] = 0
                        if "0 - Insatisfatória" not in df_perf.columns: df_perf["0 - Insatisfatória"] = 0
                        
                        df_perf["Total"] = df_perf["1 - Satisfatória"] + df_perf["0 - Insatisfatória"]
                        df_perf["Taxa Sucesso (%)"] = (df_perf["1 - Satisfatória"] / df_perf["Total"] * 100).round(1)
                        st.dataframe(df_perf.sort_values("Taxa Sucesso (%)", ascending=False), use_container_width=True, hide_index=True)
            else:
                st.info("A coluna de avaliação de qualidade ainda não foi sincronizada ou gerada na base.")

# --- TELA 1: VISUALIZAÇÃO E EDIÇÃO EM DUAS SUBPÁGINAS (AÇÕES vs ATIVIDADES) ---
elif modo == "📊 Visualizar Base":
    st.markdown("<h3 style='color: #03170a;'>📊 Central de Visualização & Gestão de Registros</h3>", unsafe_allow_html=True)
    
    if df_atual.empty:
        st.info("A base de dados do SharePoint está vazia.")
    else:
        def limpar_e_converter_data(valor):
            if pd.isna(valor): return pd.NaT
            val_str = str(valor).strip()
            if val_str == "" or val_str.lower() in ["none", "nat", "nan"]: return pd.NaT
            if val_str.replace('.', '', 1).isdigit():
                try: return pd.to_datetime(int(float(val_str)), unit='D', origin='1899-12-30')
                except: pass
            return pd.to_datetime(val_str, errors='coerce', dayfirst=True)

        def obter_float_limpo(val):
            num = pd.to_numeric(val, errors='coerce')
            return 0.0 if pd.isna(num) else float(num)

        # Função universal de filtragem cruzada (responsiva)
        def aplicar_filtros_responsivos(df_orig, dict_filtros, chave_ignorar=None):
            df_res = df_orig.copy()
            for k, (col_nome, val) in dict_filtros.items():
                if k == chave_ignorar or val in ["Todos", "Todas", None, ""]:
                    continue
                if col_nome == "Ano da Ação":
                    df_res = df_res[df_res["Ano da Ação"].astype(str).str.split('.').str[0] == str(val)]
                elif col_nome == "Número da Ação PNAPA":
                    cod_alvo = str(val).split(" - ")[0].strip()
                    cod_puro = cod_alvo.split("-")[0].strip()
                    df_res = df_res[
                        (df_res["Número da Ação PNAPA"].astype(str).str.strip() == cod_alvo) |
                        (df_res["Número da Ação PNAPA"].astype(str).str.strip() == cod_puro)
                    ]
                elif col_nome == "Data_Inicio_Datetime":
                    if isinstance(val, (tuple, list)) and len(val) == 2:
                        ts_ini = pd.to_datetime(val[0])
                        ts_fim = pd.to_datetime(val[1]) + pd.Timedelta(hours=23, minutes=59, seconds=59)
                        df_res = df_res[
                            df_res["Data_Inicio_Datetime"].isna() |
                            ((df_res["Data_Inicio_Datetime"] >= ts_ini) & (df_res["Data_Inicio_Datetime"] <= ts_fim))
                        ]
                else:
                    if col_nome in df_res.columns:
                        df_res = df_res[df_res[col_nome].astype(str).str.strip() == str(val).strip()]
            return df_res

        df_trabalho = df_atual.copy()
        
        # Garante a existência de todas as colunas
        for col_nec in COLUNAS_PNAPA:
            if col_nec not in df_trabalho.columns: df_trabalho[col_nec] = ""

        df_trabalho["Data_Inicio_Datetime"] = df_trabalho["Data de Início"].apply(limpar_e_converter_data)
        df_trabalho["Data_Termino_Datetime"] = df_trabalho["Data de Término"].apply(limpar_e_converter_data)

        # 🚀 DIVISÃO EM DUAS SUBPÁGINAS DEDICADAS
        tab_sub_acoes, tab_sub_atividades = st.tabs([
            "🎯 Ações Estaduais (Planejamento & Metas)", 
            "📌 Atividades de Campo (Operações & Execução)"
        ])

        pode_editar = (perfil_usuario in ["Administrador", "Editor Regional"]) and acesso_liberado

        # =====================================================================
        # SUBPÁGINA 1: AÇÕES ESTADUAIS
        # =====================================================================
        with tab_sub_acoes:
            df_base_acoes = df_trabalho[df_trabalho["Nível"].astype(str).str.strip() == "Ação"].copy()
            st.caption(f"🎯 Total de Ações Estaduais cadastradas: **{len(df_base_acoes)}** registros.")
            
            if df_base_acoes.empty:
                st.info("Nenhuma Ação Estadual cadastrada na base.")
            else:
                # --- DICIONÁRIO DE ESTADO ATUAL DOS FILTROS DE AÇÕES ---
                filtros_ac = {
                    "ano": ("Ano da Ação", st.session_state.get("f_ano_ac", "Todos")),
                    "pna": ("Número da Ação PNAPA", st.session_state.get("f_pna_ac", "Todas")),
                    "uf": ("UF_Acao_PNAPA", st.session_state.get("f_uf_ac", "Todas")),
                    "papel": ("Papel_Institucional", st.session_state.get("f_papel_ac", "Todos")),
                    "focal": ("Servidor", st.session_state.get("f_focal_ac", "Todos")),
                    "and": ("Andamento", st.session_state.get("f_and_ac", "Todos")),
                    "tema": ("Tema da Atividade", st.session_state.get("f_tema_ac", "Todos")),
                    "data": ("Data_Inicio_Datetime", st.session_state.get("f_slider_dts_ac", None))
                }

                # --- LINHA 1 DE FILTROS RESPONSIVOS ---
                col_ac1, col_ac2, col_ac3, col_ac4 = st.columns(4)
                with col_ac1:
                    df_p_ano = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "ano")
                    anos_ac = sorted([str(a).split('.')[0] for a in df_p_ano["Ano da Ação"].dropna().unique() if str(a).strip() != ""], reverse=True)
                    opcs_ano_ac = ["Todos"] + anos_ac
                    idx_ano_ac = opcs_ano_ac.index(filtros_ac["ano"][1]) if filtros_ac["ano"][1] in opcs_ano_ac else 0
                    f_ano_ac = st.selectbox("📅 Ano:", opcs_ano_ac, index=idx_ano_ac, key="f_ano_ac")
                    filtros_ac["ano"] = ("Ano da Ação", f_ano_ac)

                with col_ac2:
                    df_p_pna = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "pna")
                    acoes_ac = sorted(df_p_pna["Número da Ação PNAPA"].dropna().astype(str).unique().tolist())
                    opcs_pna_ac = ["Todas"] + acoes_ac
                    idx_pna_ac = opcs_pna_ac.index(filtros_ac["pna"][1]) if filtros_ac["pna"][1] in opcs_pna_ac else 0
                    f_pna_ac = st.selectbox("🗂️ Ação PNAPA:", opcs_pna_ac, index=idx_pna_ac, key="f_pna_ac")
                    filtros_ac["pna"] = ("Número da Ação PNAPA", f_pna_ac)

                with col_ac3:
                    df_p_uf = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "uf")
                    ufs_ac = sorted([str(u).strip() for u in df_p_uf["UF_Acao_PNAPA"].dropna().unique() if str(u).strip() != ""])
                    opcs_uf_ac = ["Todas"] + ufs_ac
                    idx_uf_ac = opcs_uf_ac.index(filtros_ac["uf"][1]) if filtros_ac["uf"][1] in opcs_uf_ac else 0
                    f_uf_ac = st.selectbox("📍 UF da Ação:", opcs_uf_ac, index=idx_uf_ac, key="f_uf_ac")
                    filtros_ac["uf"] = ("UF_Acao_PNAPA", f_uf_ac)

                with col_ac4:
                    df_p_papel = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "papel")
                    papeis_disp = [p for p in ["Coordenação", "Apoio"] if p in df_p_papel["Papel_Institucional"].astype(str).str.strip().unique()]
                    opcs_papel_ac = ["Todos"] + (papeis_disp if papeis_disp else ["Coordenação", "Apoio"])
                    idx_papel_ac = opcs_papel_ac.index(filtros_ac["papel"][1]) if filtros_ac["papel"][1] in opcs_papel_ac else 0
                    f_papel_ac = st.selectbox("🏛️ Papel da UF:", opcs_papel_ac, index=idx_papel_ac, key="f_papel_ac")
                    filtros_ac["papel"] = ("Papel_Institucional", f_papel_ac)

                # --- LINHA 2 DE FILTROS RESPONSIVOS + SLIDER ---
                col_ac5, col_ac6, col_ac7, col_ac8 = st.columns([1, 1, 1, 2])
                with col_ac5:
                    df_p_focal = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "focal")
                    focais_ac = sorted([str(s).strip() for s in df_p_focal["Servidor"].dropna().unique() if str(s).strip() != ""])
                    opcs_focal_ac = ["Todos"] + focais_ac
                    idx_focal_ac = opcs_focal_ac.index(filtros_ac["focal"][1]) if filtros_ac["focal"][1] in opcs_focal_ac else 0
                    f_focal_ac = st.selectbox("👑 Ponto Focal:", opcs_focal_ac, index=idx_focal_ac, key="f_focal_ac")
                    filtros_ac["focal"] = ("Servidor", f_focal_ac)

                with col_ac6:
                    df_p_and = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "and")
                    ands_ac = sorted([str(a).strip() for a in df_p_and["Andamento"].dropna().unique() if str(a).strip() != ""])
                    opcs_and_ac = ["Todos"] + ands_ac
                    idx_and_ac = opcs_and_ac.index(filtros_ac["and"][1]) if filtros_ac["and"][1] in opcs_and_ac else 0
                    f_and_ac = st.selectbox("🔄 Andamento:", opcs_and_ac, index=idx_and_ac, key="f_and_ac")
                    filtros_ac["and"] = ("Andamento", f_and_ac)

                with col_ac7:
                    df_p_tema = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "tema")
                    temas_ac = sorted([str(t).strip() for t in df_p_tema["Tema da Atividade"].dropna().unique() if str(t).strip() != ""])
                    opcs_tema_ac = ["Todos"] + temas_ac
                    idx_tema_ac = opcs_tema_ac.index(filtros_ac["tema"][1]) if filtros_ac["tema"][1] in opcs_tema_ac else 0
                    f_tema_ac = st.selectbox("🏷️ Tema:", opcs_tema_ac, index=idx_tema_ac, key="f_tema_ac")
                    filtros_ac["tema"] = ("Tema da Atividade", f_tema_ac)

                with col_ac8:
                    # Cálculo dos limites do slider de datas para Ações
                    dts_validas_ac = df_base_acoes["Data_Inicio_Datetime"].dropna()
                    if not dts_validas_ac.empty:
                        min_dt_ac = dts_validas_ac.min().date()
                        max_dt_ac = dts_validas_ac.max().date()
                    else:
                        min_dt_ac, max_dt_ac = date(2025, 1, 1), date(2026, 12, 31)
                    if min_dt_ac >= max_dt_ac:
                        max_dt_ac = min_dt_ac + pd.Timedelta(days=1)

                    f_slider_dts_ac = st.slider(
                        "⏳ Período (Data de Início):",
                        min_value=min_dt_ac,
                        max_value=max_dt_ac,
                        value=(min_dt_ac, max_dt_ac),
                        format="DD/MM/YYYY",
                        key="f_slider_dts_ac"
                    )
                    filtros_ac["data"] = ("Data_Inicio_Datetime", f_slider_dts_ac)

                # Aplicação final de todos os filtros
                df_exib_ac = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, None)

                df_exib_ac["Data de Início"] = df_exib_ac["Data_Inicio_Datetime"].dt.date
                df_exib_ac["Data de Término"] = df_exib_ac["Data_Termino_Datetime"].dt.date

                # 📋 COLUNAS RELEVANTES PARA AÇÕES
                COLS_TABELA_ACOES = [
                    "Id", "Ano da Ação", "Número da Ação PNAPA", "Nome da Ação PNAPA", 
                    "Papel_Institucional", "Servidor", "UF_Acao_PNAPA", "Meta_Indicador", 
                    "Indicador", "Importância da Atividade", "Tema da Atividade", 
                    "Objetivo da Atividade", "Tipo de Atividade", "Andamento", 
                    "Data de Início", "Data de Término", "Dias_Gastos_Plan", 
                    "Origem do Recurso", "Rec_Plan_Total", "Observações", "Justificativa_Acao_PNAPA"
                ]

                cols_ac_validas = [c for c in COLS_TABELA_ACOES if c in df_exib_ac.columns]
                df_tab_ac = df_exib_ac[cols_ac_validas].copy()
                
                cols_numericas_ac = ["Id", "Meta_Indicador", "Dias_Gastos_Plan", "Rec_Plan_Total"]
                for c_num in cols_numericas_ac:
                    if c_num in df_tab_ac.columns:
                        df_tab_ac[c_num] = pd.to_numeric(df_tab_ac[c_num], errors='coerce')
                
                # 🚀 ORDENAÇÃO PADRÃO: DATA DE INÍCIO CRESCENTE (Cronológica Real)
                df_tab_ac = df_tab_ac.sort_values(by=["Data de Início", "Id"], ascending=[True, True], na_position='last').reset_index(drop=True)

                if "selecoes_acoes" not in st.session_state: st.session_state["selecoes_acoes"] = {}
                if "version_ed_ac" not in st.session_state: st.session_state["version_ed_ac"] = 0

                # Desmarcar todos de Ações
                if [k for k, v in st.session_state["selecoes_acoes"].items() if v]:
                    if st.button("✕ Desmarcar Todas as Ações", type="secondary", key="btn_desm_ac"):
                        st.session_state["selecoes_acoes"] = {}
                        st.session_state["version_ed_ac"] += 1
                        st.rerun()

                if pode_editar:
                    df_tab_ac.insert(0, "Selecionar", [st.session_state["selecoes_acoes"].get(str(int(row_id)), False) if pd.notna(row_id) else False for row_id in df_tab_ac["Id"]])
                    colunas_travadas_ac = {col: st.column_config.Column(disabled=True) for col in df_tab_ac.columns if col != "Selecionar"}
                else:
                    colunas_travadas_ac = {col: st.column_config.Column(disabled=True) for col in df_tab_ac.columns}

                colunas_travadas_ac["Id"] = st.column_config.NumberColumn("Id", format="%d", disabled=True)
                colunas_travadas_ac["Meta_Indicador"] = st.column_config.NumberColumn("Meta da UF", format="%.1f", disabled=True)
                colunas_travadas_ac["Dias_Gastos_Plan"] = st.column_config.NumberColumn("Dias Plan.", format="%.1f", disabled=True)
                colunas_travadas_ac["Rec_Plan_Total"] = st.column_config.NumberColumn("Rec. Plan. Total", format="R$ %.2f", disabled=True)
                colunas_travadas_ac["Data de Início"] = st.column_config.DateColumn("Data de Início", format="DD/MM/YYYY", disabled=True)
                colunas_travadas_ac["Data de Término"] = st.column_config.DateColumn("Data de Término", format="DD/MM/YYYY", disabled=True)

                key_dinamica_ac = f"editor_acoes_v{st.session_state['version_ed_ac']}"
                tabela_ac = st.data_editor(df_tab_ac, hide_index=True, use_container_width=True, column_config=colunas_travadas_ac, key=key_dinamica_ac)

                # Captura seleções
                if pode_editar and st.session_state[key_dinamica_ac] and "edited_rows" in st.session_state[key_dinamica_ac]:
                    for idx_l, alt in st.session_state[key_dinamica_ac]["edited_rows"].items():
                        if "Selecionar" in alt:
                            alvo_ac = df_tab_ac.iloc[int(idx_l)]
                            id_r_ac = str(alvo_ac["Id"])
                            uf_l_ac = str(alvo_ac.get("UF_Acao_PNAPA", "")).strip()
                            if perfil_usuario == "Editor Regional" and uf_l_ac != uf_usuario and alt["Selecionar"] is True:
                                st.error(f"⛔ Acesso Negado: Como Editor Regional ({uf_usuario}), você não tem permissão para editar registros da UF: {uf_l_ac}.")
                                st.session_state["selecoes_acoes"][id_r_ac] = False
                            else:
                                st.session_state["selecoes_acoes"][id_r_ac] = alt["Selecionar"]
                            st.rerun()

                ids_marcados_ac = [k for k, v in st.session_state["selecoes_acoes"].items() if v]
                df_ac_sel = df_exib_ac[df_exib_ac["Id"].astype(str).isin(ids_marcados_ac)]

                # --- PAINEL DE OPERAÇÃO DE AÇÕES ---
                if not pode_editar:
                    st.info("👁️ **Modo Somente Leitura:** Apenas Administradores e Editores Regionais podem editar Ações.")
                elif df_ac_sel.empty:
                    st.caption("💡 *Selecione uma Ação acima para alterar Ponto Focal, Papel da UF, Metas ou excluir.*")
                else:
                    ids_ac_lista = df_ac_sel["Id"].astype(str).tolist()
                    st.markdown("---")
                    st.markdown(f"### 🛠️ Central de Operações da Ação ({len(ids_ac_lista)} item(ns) selecionado(s))")
                    
                    with st.popover("🗑️ Remover Ação(ões) Selecionada(s)", use_container_width=True):
                        st.markdown(f"⚠️ Deseja apagar definitivamente a(s) Ação(ões) ID: **{', '.join(ids_ac_lista)}**?")
                        if st.button("Confirmar Exclusão de Ações", type="primary", key="btn_del_ac_tab"):
                            payloads_del = [{"Acao": "Excluir", "Id": str(id_del)} for id_del in ids_ac_lista]
                            for p_del in payloads_del: requests.post(URL_FLOW_PRINCIPAL, json=p_del, timeout=20)
                            st.cache_data.clear()
                            if "df" in st.session_state: del st.session_state.df
                            st.session_state["selecoes_acoes"] = {}
                            st.success("Ação(ões) removida(s) com sucesso!")
                            time.sleep(1.5)
                            st.rerun()

                    # Edição Individual de Ação
                    if len(ids_ac_lista) == 1:
                        reg_ac_alvo = df_ac_sel.iloc[0]
                        id_ac_ref = str(reg_ac_alvo["Id"])
                        st.markdown(f"#### 📝 Edição do Planejamento da Ação (ID: **{id_ac_ref}**)")

                        val_ano_ac = int(pd.to_numeric(reg_ac_alvo.get("Ano da Ação"), errors='coerce') or 2026)
                        val_num_acao_ac = str(reg_ac_alvo.get("Número da Ação PNAPA", ""))
                        val_nome_acao_ac = str(reg_ac_alvo.get("Nome da Ação PNAPA", ""))
                        val_indicador_ac = str(reg_ac_alvo.get("Indicador", ""))
                        importancia_ac = str(reg_ac_alvo.get("Importância da Atividade", "Ordinária"))

                        aba1_ac, aba2_ac, aba4_ac, aba5_ac = st.tabs(["1. Governança Estadual", "2. Detalhes & Metas", "4. Cronograma & Custos", "5. Justificativas"])
                        with aba1_ac:
                            st.text_input("Ano da Ação", value=str(val_ano_ac), disabled=True, key=f"t1_ac_ano_{id_ac_ref}")
                            st.text_input("Número da Ação PNAPA", value=val_num_acao_ac, disabled=True, key=f"t1_ac_num_{id_ac_ref}")
                            st.text_input("Nome da Ação PNAPA", value=val_nome_acao_ac, disabled=True, key=f"t1_ac_nome_{id_ac_ref}")
                            
                            c_ac_p1, c_ac_p2 = st.columns(2)
                            with c_ac_p1:
                                val_papel_atual = str(reg_ac_alvo.get("Papel_Institucional", "Coordenação")).strip()
                                idx_pap = LISTA_PAPEIS_INSTITUCIONAIS.index(val_papel_atual) if val_papel_atual in LISTA_PAPEIS_INSTITUCIONAIS else 0
                                ed_papel_inst = st.selectbox("Papel da UF nesta Ação:", LISTA_PAPEIS_INSTITUCIONAIS, index=idx_pap, key=f"t1_ac_papel_{id_ac_ref}")
                            with c_ac_p2:
                                uf_alvo_ac = str(reg_ac_alvo.get("UF_Acao_PNAPA", uf_usuario)).strip()
                                srvs_uf_lista = df_servidores[df_servidores["UF_Servidor"] == uf_alvo_ac]["Servidor"].dropna().unique().tolist()
                                if ed_papel_inst == "Coordenação":
                                    val_foc_atual = str(reg_ac_alvo.get("Servidor", "")).strip()
                                    idx_foc = srvs_uf_lista.index(val_foc_atual) if val_foc_atual in srvs_uf_lista else 0
                                    ed_servidor_ac = st.selectbox(f"Ponto Focal da Ação em {uf_alvo_ac}:", srvs_uf_lista if srvs_uf_lista else [val_foc_atual], index=idx_foc, key=f"t1_ac_focal_{id_ac_ref}")
                                    ed_uf_srv_ac, ed_lot_ac, ed_eq_ac = uf_alvo_ac, "Sede Superintendência", "Sim"
                                else:
                                    st.info(f"ℹ️ Atuação em Apoio: Sem coordenador estadual.")
                                    ed_servidor_ac, ed_uf_srv_ac, ed_lot_ac, ed_eq_ac = "", "", "", "Não"

                            lista_and_ac = ["Planejada", "Cancelada", "Não Demandada", "Não Executada"]
                            idx_and_ac = lista_and_ac.index(reg_ac_alvo["Andamento"]) if reg_ac_alvo.get("Andamento") in lista_and_ac else 0
                            ed_andamento_ac = st.selectbox("Andamento da Ação:", lista_and_ac, index=idx_and_ac, key=f"t1_ac_and_{id_ac_ref}")

                        with aba2_ac:
                            st.text_input("Indicador Oficial", value=val_indicador_ac, disabled=True, key=f"t1_ac_ind_{id_ac_ref}")
                            meta_val_ac = obter_float_limpo(reg_ac_alvo.get("Meta_Indicador", 1.0))
                            ed_meta_ac = st.number_input(f"Meta da Ação para a UF ({uf_alvo_ac}):", min_value=0.0, value=meta_val_ac, step=1.0, key=f"t1_ac_meta_{id_ac_ref}")
                            uf_acao_val = st.text_input("UF da Ação", value=uf_alvo_ac, disabled=True, key=f"t1_ac_uf_{id_ac_ref}")
                            st.text_input("Importância", value=importancia_ac, disabled=True, key=f"t1_ac_imp_{id_ac_ref}")
                            ed_tema_ac = st.selectbox("Tema da Atividade:", LISTA_TEMAS, index=LISTA_TEMAS.index(reg_ac_alvo["Tema da Atividade"]) if reg_ac_alvo.get("Tema da Atividade") in LISTA_TEMAS else 0, key=f"t1_ac_tema_{id_ac_ref}")
                            ed_obj_ac = st.selectbox("Objetivo:", LISTA_OBJETIVOS, index=LISTA_OBJETIVOS.index(reg_ac_alvo["Objetivo da Atividade"]) if reg_ac_alvo.get("Objetivo da Atividade") in LISTA_OBJETIVOS else 0, key=f"t1_ac_obj_{id_ac_ref}")
                            ed_tipo_ac = st.selectbox("Tipo:", LISTA_TIPOS_ATIVIDADE, index=LISTA_TIPOS_ATIVIDADE.index(reg_ac_alvo["Tipo de Atividade"]) if reg_ac_alvo.get("Tipo de Atividade") in LISTA_TIPOS_ATIVIDADE else 0, key=f"t1_ac_tipo_{id_ac_ref}")

                        with aba4_ac:
                            val_dti_ac = converter_para_data_segura(reg_ac_alvo.get("Data de Início"))
                            val_dtf_ac = converter_para_data_segura(reg_ac_alvo.get("Data de Término"))
                            ed_dt_i_ac = st.date_input("Data de Início:", value=val_dti_ac, format="DD/MM/YYYY", key=f"t1_ac_dti_{id_ac_ref}")
                            ed_dt_f_ac = st.date_input("Data de Término:", value=val_dtf_ac, format="DD/MM/YYYY", key=f"t1_ac_dtf_{id_ac_ref}")
                            ed_dias_pl_ac = st.number_input("Dias Gastos Plan:", min_value=0.0, value=obter_float_limpo(reg_ac_alvo.get("Dias_Gastos_Plan")), step=0.5, format="%.1f", key=f"t1_ac_dpl_{id_ac_ref}")
                            ed_orig_ac = st.selectbox("Origem do Recurso:", LISTA_ORIGENS_RECURSO, index=LISTA_ORIGENS_RECURSO.index(reg_ac_alvo["Origem do Recurso"]) if reg_ac_alvo.get("Origem do Recurso") in LISTA_ORIGENS_RECURSO else 0, key=f"t1_ac_orig_{id_ac_ref}")
                            
                            st.markdown("<p style='font-weight:bold; color:#03170a;'>Valores Planejados</p>", unsafe_allow_html=True)
                            ed_rp_d_ac = st.number_input("Rec_Plan_Diarias:", min_value=0.0, value=obter_float_limpo(reg_ac_alvo.get("Rec_Plan_Diarias")), step=50.0, format="%.2f", key=f"t1_ac_rpd_{id_ac_ref}")
                            ed_rp_p_ac = st.number_input("Rec_Plan_Passagens:", min_value=0.0, value=obter_float_limpo(reg_ac_alvo.get("Rec_Plan_Passagens")), step=50.0, format="%.2f", key=f"t1_ac_rpp_{id_ac_ref}")
                            ed_rp_o_ac = st.number_input("Rec_Plan_Outras_Despesas:", min_value=0.0, value=obter_float_limpo(reg_ac_alvo.get("Rec_Plan_Outras_Despesas")), step=50.0, format="%.2f", key=f"t1_ac_rpo_{id_ac_ref}")
                            st.text_input("Rec_Plan_Total:", value=f"{(ed_rp_d_ac + ed_rp_p_ac + ed_rp_o_ac):,.2f}", disabled=True, key=f"t1_ac_rptot_{id_ac_ref}")

                        with aba5_ac:
                            ed_obs_ac = st.text_area("Observações:", value=str(reg_ac_alvo.get("Observações", "")), key=f"t1_ac_obs_{id_ac_ref}")
                            if ed_andamento_ac in ["Cancelada", "Não Demandada", "Não Executada"]:
                                idx_j_ac = LISTA_JUSTIFICATIVAS_ACAO.index(reg_ac_alvo["Justificativa_Acao_PNAPA"]) if reg_ac_alvo.get("Justificativa_Acao_PNAPA") in LISTA_JUSTIFICATIVAS_ACAO else 0
                                ed_just_ac = st.selectbox("Justificativa:", LISTA_JUSTIFICATIVAS_ACAO, index=idx_j_ac, key=f"t1_ac_just_{id_ac_ref}")
                            else:
                                ed_just_ac = ""

                        if st.button("💾 Gravar Alterações da Ação", type="primary", key=f"btn_salvar_ac_{id_ac_ref}"):
                            payload_ac = payload_gerador(
                                val_ano_ac, val_num_acao_ac, val_nome_acao_ac, val_indicador_ac, "Ação",
                                "", ed_andamento_ac, "", "", uf_acao_val,
                                importancia_ac, ed_tema_ac, ed_obj_ac, ed_tipo_ac, "Não se Aplica", ed_servidor_ac,
                                ed_uf_srv_ac, ed_lot_ac, ed_eq_ac, "", "Brasil", "",
                                "", "", ed_dt_i_ac, ed_dt_f_ac, ed_dias_pl_ac, 0.0,
                                ed_orig_ac, ed_rp_d_ac, ed_rp_p_ac, ed_rp_o_ac, 0.0,
                                0.0, 0.0, ed_obs_ac, ed_just_ac, id_ac_ref, "📝 Editar Linha Existente", df_atual,
                                papel_institucional=ed_papel_inst, coordenador_operacao="", meta_indicador=ed_meta_ac,
                                codigo_atividade=""
                            )
                            executar_envio_sharepoint([payload_ac])
                            st.session_state["selecoes_acoes"] = {}
                            st.session_state["version_ed_ac"] += 1
                            st.rerun()
                    
                    # Edição em Lote de Ações (Restrita ao Status)
                    else:
                        st.warning(f"ℹ️ **Edição em Lote Restrita:** {len(ids_ac_lista)} ações selecionadas. Apenas o status pode ser alterado em massa.")
                        novo_and_ac_lote = st.selectbox("Alterar Andamento para TODAS as Ações:", ["Planejada", "Cancelada", "Não Demandada", "Não Executada"], key="lt_ac_and")
                        if st.button(f"💾 Atualizar Andamento de {len(ids_ac_lista)} Ações", type="primary", key="btn_salvar_lote_ac"):
                            payloads_lote_ac = []
                            for _, row_orig in df_ac_sel.iterrows():
                                p_item = {col: row_orig[col] for col in df_atual.columns if col in row_orig}
                                p_item["Acao"] = "Editar"
                                p_item["Id"] = str(row_orig["Id"])
                                p_item["Andamento"] = str(novo_and_ac_lote)
                                payload_sanit = {k: (0.0 if pd.isna(v) and ("Rec_" in k or "Dias_" in k) else ("" if pd.isna(v) else v)) for k, v in p_item.items()}
                                payloads_lote_ac.append(payload_sanit)
                            executar_envio_sharepoint(payloads_lote_ac)
                            st.session_state["selecoes_acoes"] = {}
                            st.session_state["version_ed_ac"] += 1
                            st.rerun()

        # =====================================================================
        # SUBPÁGINA 2: ATIVIDADES DE CAMPO
        # =====================================================================
        with tab_sub_atividades:
            df_base_atvs = df_trabalho[df_trabalho["Nível"].astype(str).str.strip() == "Atividade"].copy()
            st.caption(f"📌 Total de Atividades de Campo cadastradas: **{len(df_base_atvs)}** registros.")

            if df_base_atvs.empty:
                st.info("Nenhuma Atividade de Campo cadastrada na base.")
            else:
                # --- DICIONÁRIO DE ESTADO ATUAL DOS FILTROS DE ATIVIDADES ---
                filtros_at = {
                    "ano": ("Ano da Ação", st.session_state.get("f_ano_at", "Todos")),
                    "pna": ("Número da Ação PNAPA", st.session_state.get("f_pna_at", "Todas")),
                    "cod": ("Codigo_Atividade", st.session_state.get("f_cod_at", "Todos")),
                    "uf": ("UF_Acao_PNAPA", st.session_state.get("f_uf_at", "Todas")),
                    "srv": ("Servidor", st.session_state.get("f_srv_at", "Todos")),
                    "func": ("Coordenador_Operacao", st.session_state.get("f_func_at", "Todas")),
                    "and": ("Andamento", st.session_state.get("f_and_at", "Todos")),
                    "tema": ("Tema da Atividade", st.session_state.get("f_tema_at", "Todos")),
                    "data": ("Data_Inicio_Datetime", st.session_state.get("f_slider_dts_at", None))
                }

                # --- LINHA 1 DE FILTROS RESPONSIVOS ---
                col_at1, col_at2, col_at3, col_at4 = st.columns(4)
                with col_at1:
                    df_p_ano_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "ano")
                    anos_at = sorted([str(a).split('.')[0] for a in df_p_ano_at["Ano da Ação"].dropna().unique() if str(a).strip() != ""], reverse=True)
                    opcs_ano_at = ["Todos"] + anos_at
                    idx_ano_at = opcs_ano_at.index(filtros_at["ano"][1]) if filtros_at["ano"][1] in opcs_ano_at else 0
                    f_ano_at = st.selectbox("📅 Ano:", opcs_ano_at, index=idx_ano_at, key="f_ano_at")
                    filtros_at["ano"] = ("Ano da Ação", f_ano_at)

                with col_at2:
                    df_p_pna_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "pna")
                    acoes_at = sorted(df_p_pna_at["Número da Ação PNAPA"].dropna().astype(str).unique().tolist())
                    opcs_pna_at = ["Todas"] + acoes_at
                    idx_pna_at = opcs_pna_at.index(filtros_at["pna"][1]) if filtros_at["pna"][1] in opcs_pna_at else 0
                    f_pna_at = st.selectbox("🗂️ Ação PNAPA:", opcs_pna_at, index=idx_pna_at, key="f_pna_at")
                    filtros_at["pna"] = ("Número da Ação PNAPA", f_pna_at)

                with col_at3:
                    df_p_cod_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "cod")
                    cods_at = sorted([str(c).strip() for c in df_p_cod_at["Codigo_Atividade"].dropna().unique() if str(c).strip() != ""])
                    opcs_cod_at = ["Todos"] + cods_at
                    idx_cod_at = opcs_cod_at.index(filtros_at["cod"][1]) if filtros_at["cod"][1] in opcs_cod_at else 0
                    f_cod_at = st.selectbox("🏷️ Código Atividade:", opcs_cod_at, index=idx_cod_at, key="f_cod_at")
                    filtros_at["cod"] = ("Codigo_Atividade", f_cod_at)

                with col_at4:
                    df_p_uf_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "uf")
                    ufs_at = sorted([str(u).strip() for u in df_p_uf_at["UF_Acao_PNAPA"].dropna().unique() if str(u).strip() != ""])
                    opcs_uf_at = ["Todas"] + ufs_at
                    idx_uf_at = opcs_uf_at.index(filtros_at["uf"][1]) if filtros_at["uf"][1] in opcs_uf_at else 0
                    f_uf_at = st.selectbox("📍 UF da Ação:", opcs_uf_at, index=idx_uf_at, key="f_uf_at")
                    filtros_at["uf"] = ("UF_Acao_PNAPA", f_uf_at)

                # --- LINHA 2 DE FILTROS RESPONSIVOS ---
                col_at5, col_at6, col_at7, col_at8 = st.columns(4)
                with col_at5:
                    df_p_srv_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "srv")
                    srvs_at = sorted([str(s).strip() for s in df_p_srv_at["Servidor"].dropna().unique() if str(s).strip() != ""])
                    opcs_srv_at = ["Todos"] + srvs_at
                    idx_srv_at = opcs_srv_at.index(filtros_at["srv"][1]) if filtros_at["srv"][1] in opcs_srv_at else 0
                    f_srv_at = st.selectbox("👤 Servidor:", opcs_srv_at, index=idx_srv_at, key="f_srv_at")
                    filtros_at["srv"] = ("Servidor", f_srv_at)

                with col_at6:
                    df_p_func_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "func")
                    funcs_disp = [f for f in LISTA_FUNCOES_CAMPO if f in df_p_func_at["Coordenador_Operacao"].astype(str).str.strip().unique()]
                    opcs_func_at = ["Todas"] + (funcs_disp if funcs_disp else LISTA_FUNCOES_CAMPO)
                    idx_func_at = opcs_func_at.index(filtros_at["func"][1]) if filtros_at["func"][1] in opcs_func_at else 0
                    f_func_at = st.selectbox("🎖️ Função de Campo:", opcs_func_at, index=idx_func_at, key="f_func_at")
                    filtros_at["func"] = ("Coordenador_Operacao", f_func_at)

                with col_at7:
                    df_p_and_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "and")
                    ands_at = sorted([str(a).strip() for a in df_p_and_at["Andamento"].dropna().unique() if str(a).strip() != ""])
                    opcs_and_at = ["Todos"] + ands_at
                    idx_and_at = opcs_and_at.index(filtros_at["and"][1]) if filtros_at["and"][1] in opcs_and_at else 0
                    f_and_at = st.selectbox("🔄 Andamento:", opcs_and_at, index=idx_and_at, key="f_and_at")
                    filtros_at["and"] = ("Andamento", f_and_at)

                with col_at8:
                    df_p_tema_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "tema")
                    temas_at = sorted([str(t).strip() for t in df_p_tema_at["Tema da Atividade"].dropna().unique() if str(t).strip() != ""])
                    opcs_tema_at = ["Todos"] + temas_at
                    idx_tema_at = opcs_tema_at.index(filtros_at["tema"][1]) if filtros_at["tema"][1] in opcs_tema_at else 0
                    f_tema_at = st.selectbox("🏷️ Tema:", opcs_tema_at, index=idx_tema_at, key="f_tema_at")
                    filtros_at["tema"] = ("Tema da Atividade", f_tema_at)

                # --- LINHA 3: SLIDER DE DATAS RESPONSIVO DE ATIVIDADES ---
                dts_validas_at = df_base_atvs["Data_Inicio_Datetime"].dropna()
                if not dts_validas_at.empty:
                    min_dt_at = dts_validas_at.min().date()
                    max_dt_at = dts_validas_at.max().date()
                else:
                    min_dt_at, max_dt_at = date(2025, 1, 1), date(2026, 12, 31)
                if min_dt_at >= max_dt_at:
                    max_dt_at = min_dt_at + pd.Timedelta(days=1)

                f_slider_dts_at = st.slider(
                    "⏳ Período (Data de Início da Atividade):",
                    min_value=min_dt_at,
                    max_value=max_dt_at,
                    value=(min_dt_at, max_dt_at),
                    format="DD/MM/YYYY",
                    key="f_slider_dts_at"
                )
                filtros_at["data"] = ("Data_Inicio_Datetime", f_slider_dts_at)

                # Aplicação final de todos os filtros
                df_exib_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, None)

                df_exib_at["Data de Início"] = df_exib_at["Data_Inicio_Datetime"].dt.date
                df_exib_at["Data de Término"] = df_exib_at["Data_Termino_Datetime"].dt.date

                # 📋 COLUNAS RELEVANTES PARA ATIVIDADES (Incluindo Avaliação)
                COLS_TABELA_ATIVIDADES = [
                    "Id", "Ano da Ação", "Número da Ação PNAPA", "Codigo_Atividade", 
                    "Nome da Atividade", "Papel_Institucional", "Coordenador_Operacao", 
                    "Servidor", "UF_Servidor", "Lotação", "UF_Acao_PNAPA", 
                    "Municipio Onde Ocorreu/Ocorrerá a Ação", "Andamento", "Indicador", 
                    "Resultado_Indicador", "Doc_Probatorio_Exec", "Data de Início", 
                    "Data de Término", "Dias_Gastos_Plan", "Dias_Gastos_Exec", 
                    "Origem do Recurso", "Rec_Plan_Total", "Rec_Exec_Total", 
                    "Número da PCDP", "Periculosidade/Insalubridade", "Tema da Atividade", 
                    "Objetivo da Atividade", "Tipo de Atividade", 
                    "Avaliacao_Qualidade", "Avaliacao_Feedback", "Observações"
                ]

                cols_at_validas = [c for c in COLS_TABELA_ATIVIDADES if c in df_exib_at.columns]
                df_tab_at = df_exib_at[cols_at_validas].copy()
                
                cols_numericas_at = [
                    "Id", "Resultado_Indicador", "Dias_Gastos_Plan", "Dias_Gastos_Exec", 
                    "Rec_Plan_Total", "Rec_Exec_Total"
                ]
                for c_num in cols_numericas_at:
                    if c_num in df_tab_at.columns:
                        df_tab_at[c_num] = pd.to_numeric(df_tab_at[c_num], errors='coerce')
                
                # 🚀 ORDENAÇÃO PADRÃO: DATA DE INÍCIO CRESCENTE (Cronológica Real)
                df_tab_at = df_tab_at.sort_values(by=["Data de Início", "Id"], ascending=[True, True], na_position='last').reset_index(drop=True)

                # =================================================================
                # 🔒 BLINDAGEM DE PRIVACIDADE: Ocultar avaliações para não-autorizados
                # =================================================================
                if "Avaliacao_Qualidade" not in df_tab_at.columns: df_tab_at["Avaliacao_Qualidade"] = "Não Avaliada"
                if "Avaliacao_Feedback" not in df_tab_at.columns: df_tab_at["Avaliacao_Feedback"] = ""

                # Mapeia as atividades onde o usuário logado é o Coordenador de Campo
                atividades_coordenadas = set(df_atual[
                    (df_atual["Servidor"].astype(str).str.strip() == str(nome_usuario_logado)) & 
                    (df_atual["Coordenador_Operacao"].astype(str).str.strip() == "Coordenador de Campo")
                ]["Codigo_Atividade"].astype(str).str.strip())

                def visibilidade_avaliacao(row):
                    # 1. Administrador ou Editor Regional (Coordenador Estadual)
                    if perfil_usuario in ["Administrador", "Editor Regional"]: return True
                    # 2. Próprio Avaliado
                    if str(row.get("Servidor", "")).strip() == str(nome_usuario_logado): return True
                    # 3. Liderança Direta (Coordenador de Campo da Atividade)
                    if str(row.get("Codigo_Atividade", "")).strip() in atividades_coordenadas: return True
                    return False

                mascara_visibilidade = df_tab_at.apply(visibilidade_avaliacao, axis=1)
                df_tab_at.loc[~mascara_visibilidade, "Avaliacao_Qualidade"] = "🔒 Restrito"
                df_tab_at.loc[~mascara_visibilidade, "Avaliacao_Feedback"] = "🔒 Restrito"
                # =================================================================

                if "selecoes_atividades" not in st.session_state: st.session_state["selecoes_atividades"] = {}
                if "version_ed_at" not in st.session_state: st.session_state["version_ed_at"] = 0

                if [k for k, v in st.session_state["selecoes_atividades"].items() if v]:
                    if st.button("✕ Desmarcar Todas as Atividades", type="secondary", key="btn_desm_at"):
                        st.session_state["selecoes_atividades"] = {}
                        st.session_state["version_ed_at"] += 1
                        st.rerun()

                if pode_editar:
                    df_tab_at.insert(0, "Selecionar", [st.session_state["selecoes_atividades"].get(str(int(row_id)), False) if pd.notna(row_id) else False for row_id in df_tab_at["Id"]])
                    colunas_travadas_at = {col: st.column_config.Column(disabled=True) for col in df_tab_at.columns if col != "Selecionar"}
                else:
                    colunas_travadas_at = {col: st.column_config.Column(disabled=True) for col in df_tab_at.columns}

                # Configuração Visual das Colunas
                colunas_travadas_at["Id"] = st.column_config.NumberColumn("Id", format="%d", disabled=True)
                colunas_travadas_at["Resultado_Indicador"] = st.column_config.NumberColumn("Resultado Indicador", format="%.1f", disabled=True)
                colunas_travadas_at["Dias_Gastos_Plan"] = st.column_config.NumberColumn("Dias Plan.", format="%.1f", disabled=True)
                colunas_travadas_at["Dias_Gastos_Exec"] = st.column_config.NumberColumn("Dias Exec.", format="%.1f", disabled=True)
                colunas_travadas_at["Rec_Plan_Total"] = st.column_config.NumberColumn("Rec. Plan. Total", format="R$ %.2f", disabled=True)
                colunas_travadas_at["Rec_Exec_Total"] = st.column_config.NumberColumn("Rec. Exec. Total", format="R$ %.2f", disabled=True)
                colunas_travadas_at["Data de Início"] = st.column_config.DateColumn("Data de Início", format="DD/MM/YYYY", disabled=True)
                colunas_travadas_at["Data de Término"] = st.column_config.DateColumn("Data de Término", format="DD/MM/YYYY", disabled=True)
                colunas_travadas_at["Avaliacao_Qualidade"] = st.column_config.TextColumn("Nota Qualidade", disabled=True)
                colunas_travadas_at["Avaliacao_Feedback"] = st.column_config.TextColumn("Feedback Liderança", disabled=True)

                key_dinamica_at = f"editor_atividades_v{st.session_state['version_ed_at']}"
                tabela_at = st.data_editor(df_tab_at, hide_index=True, use_container_width=True, column_config=colunas_travadas_at, key=key_dinamica_at)

                if pode_editar and st.session_state[key_dinamica_at] and "edited_rows" in st.session_state[key_dinamica_at]:
                    for idx_l, alt in st.session_state[key_dinamica_at]["edited_rows"].items():
                        if "Selecionar" in alt:
                            alvo_at = df_tab_at.iloc[int(idx_l)]
                            id_r_at = str(alvo_at["Id"])
                            uf_l_at = str(alvo_at.get("UF_Acao_PNAPA", "")).strip()
                            if perfil_usuario == "Editor Regional" and uf_l_at != uf_usuario and alt["Selecionar"] is True:
                                st.error(f"⛔ Acesso Negado: Como Editor Regional ({uf_usuario}), você não tem permissão para editar registros da UF: {uf_l_at}.")
                                st.session_state["selecoes_atividades"][id_r_at] = False
                            else:
                                st.session_state["selecoes_atividades"][id_r_at] = alt["Selecionar"]
                            st.rerun()

                ids_marcados_at = [k for k, v in st.session_state["selecoes_atividades"].items() if v]
                df_at_sel = df_exib_at[df_exib_at["Id"].astype(str).isin(ids_marcados_at)]

                # --- PAINEL DE OPERAÇÃO DE ATIVIDADES ---
                if not pode_editar:
                    st.info("👁️ **Modo Somente Leitura:** Apenas Administradores e Editores Regionais podem editar Atividades.")
                elif df_at_sel.empty:
                    st.caption("💡 *Selecione uma ou mais atividades acima para editar ou excluir.*")
                else:
                    ids_at_lista = df_at_sel["Id"].astype(str).tolist()
                    qtd_at_sel = len(ids_at_lista)
                    st.markdown("---")
                    st.markdown(f"### 🛠️ Central de Operações de Atividades ({qtd_at_sel} item(ns) selecionado(s))")
                    
                    with st.popover("🗑️ Remover Atividade(s) Selecionada(s)", use_container_width=True):
                        st.markdown(f"⚠️ Deseja apagar definitivamente a(s) Atividade(s) ID: **{', '.join(ids_at_lista)}**?")
                        if st.button("Confirmar Exclusão de Atividades", type="primary", key="btn_del_at_tab"):
                            payloads_del = [{"Acao": "Excluir", "Id": str(id_del)} for id_del in ids_at_lista]
                            for p_del in payloads_del: requests.post(URL_FLOW_PRINCIPAL, json=p_del, timeout=20)
                            st.cache_data.clear()
                            if "df" in st.session_state: del st.session_state.df
                            st.session_state["selecoes_atividades"] = {}
                            st.success("Atividade(s) removida(s) com sucesso!")
                            time.sleep(1.5)
                            st.rerun()

                    # =================================================================
                    # EDIÇÃO INDIVIDUAL DE ATIVIDADE (1 LINHA)
                    # =================================================================
                    if qtd_at_sel == 1:
                        reg_at_alvo = df_at_sel.iloc[0]
                        id_at_ref = str(reg_at_alvo["Id"])
                        st.markdown(f"#### 📝 Edição Individual da Atividade (ID: **{id_at_ref}**)")

                        val_ano_at = int(pd.to_numeric(reg_at_alvo.get("Ano da Ação"), errors='coerce') or 2026)
                        val_num_acao_at = str(reg_at_alvo.get("Número da Ação PNAPA", ""))
                        val_nome_acao_at = str(reg_at_alvo.get("Nome da Ação PNAPA", ""))
                        val_indicador_at = str(reg_at_alvo.get("Indicador", ""))
                        importancia_at = str(reg_at_alvo.get("Importância da Atividade", "Ordinária"))
                        uf_acao_at = str(reg_at_alvo.get("UF_Acao_PNAPA", uf_usuario)).strip()

                        aba1_at, aba2_at, aba3_at, aba4_at, aba5_at, aba6_at = st.tabs([
                            "1. Identificação & Agrupador", "2. Detalhes & Indicadores", 
                            "3. Recursos Humanos & Liderança", "4. Cronograma & Custos", "5. Observações",
                            "6. Avaliação da Liderança"
                        ])
                        
                        with aba1_at:
                            st.markdown("##### 🗂️ Ação PNAPA Vinculada (Pai)")
                            lista_opcoes_vinc = sorted((df_pnapas["Acao_Ano"].astype(str) + " - " + df_pnapas["Nome_Acao_Apelido"].astype(str)).tolist()) if not df_pnapas.empty else []
                            cod_atual_salvo = str(reg_at_alvo.get("Número da Ação PNAPA", "")).strip()
                            
                            idx_pna_atual = 0
                            for i, opc in enumerate(lista_opcoes_vinc):
                                if opc.startswith(cod_atual_salvo + " - ") or opc.startswith(cod_atual_salvo + "-") or opc == cod_atual_salvo:
                                    idx_pna_atual = i
                                    break
                            
                            sel_acao_pai = st.selectbox("Ação PNAPA (Pode ser alterada):", lista_opcoes_vinc if lista_opcoes_vinc else ["Nenhuma Ação Cadastrada"], index=idx_pna_atual, key=f"t1_at_sel_pna_{id_at_ref}")
                            
                            if lista_opcoes_vinc:
                                cod_novo_pai = sel_acao_pai.split(" - ")[0].strip()
                                dados_novo_pai = df_pnapas[df_pnapas["Acao_Ano"].astype(str) == cod_novo_pai].iloc[0]
                                val_ano_at = int(dados_novo_pai["Ano"])
                                val_num_acao_at = str(dados_novo_pai.get("Acao_Ano", dados_novo_pai["Num_Acao_PNAPA"]))
                                apel_tmp = str(dados_novo_pai.get("Nome_Acao_Apelido", ""))
                                val_nome_acao_at = apel_tmp if apel_tmp and apel_tmp.lower() != "nan" else str(dados_novo_pai.get("Nome_Acao_Completo", "")).strip()
                                val_indicador_at = str(dados_novo_pai["Indicador"])
                                importancia_at = str(dados_novo_pai.get("Importância", "Ordinária")).strip()

                            c_pna1, c_pna2 = st.columns(2)
                            with c_pna1: st.text_input("Ano da Ação", value=str(val_ano_at), disabled=True, key=f"t1_at_ano_{id_at_ref}")
                            with c_pna2: st.text_input("Nome da Ação", value=val_nome_acao_at, disabled=True, key=f"t1_at_nomepna_{id_at_ref}")
                            
                            ponto_focal_estado_at, papel_estado_at = obter_ponto_focal_acao(df_atual, val_num_acao_at, uf_acao_at)
                            
                            st.markdown("##### 🏷️ Código e Agrupador da Atividade")
                            cod_atv_atual = str(reg_at_alvo.get("Codigo_Atividade", "")).strip().upper()
                            
                            df_atvs_acao_uf = df_atual[
                                (df_atual["Nível"] == "Atividade") &
                                (df_atual["UF_Acao_PNAPA"].astype(str).str.strip().str.upper() == str(uf_acao_at).strip().upper()) &
                                (
                                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == str(val_num_acao_at).strip().upper()) |
                                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == str(val_num_acao_at).split("-")[0].strip().upper())
                                ) &
                                (df_atual["Codigo_Atividade"].astype(str).str.strip() != "")
                            ]

                            import re
                            maior_num_atv = 0
                            for cod_exist in df_atvs_acao_uf["Codigo_Atividade"].dropna().unique():
                                match = re.search(r'ATV(\d+)', str(cod_exist).upper())
                                if match:
                                    num_extraido = int(match.group(1))
                                    if num_extraido > maior_num_atv:
                                        maior_num_atv = num_extraido

                            cod_base_acao = val_num_acao_at if "-" in str(val_num_acao_at) else f"{val_num_acao_at}-{val_ano_at}"
                            prox_num_atv_str = f"ATV{maior_num_atv + 1:02d}"
                            codigo_novo_gerado = f"{cod_base_acao}-{uf_acao_at}-{prox_num_atv_str}"

                            opcoes_atvs_existentes = []
                            mapa_dados_atv_existente = {}
                            for cod_unic in sorted(df_atvs_acao_uf["Codigo_Atividade"].dropna().unique()):
                                linhas_deste_cod = df_atvs_acao_uf[df_atvs_acao_uf["Codigo_Atividade"] == cod_unic]
                                nome_deste_cod = str(linhas_deste_cod["Nome da Atividade"].iloc[0]).strip()
                                label_opc = f"{cod_unic} — {nome_deste_cod}"
                                opcoes_atvs_existentes.append(label_opc)
                                mapa_dados_atv_existente[label_opc] = linhas_deste_cod.iloc[0]

                            modo_codigo = st.radio(
                                "Definição da Atividade:", 
                                ["✏️ Manter/Editar Código Atual", "➕ Gerar Novo Código Automático", "🔗 Vincular a Outro Existente"],
                                horizontal=True,
                                key=f"rad_modo_cod_{id_at_ref}"
                            )

                            nome_atv_prefill = str(reg_at_alvo.get("Nome da Atividade", "")).strip()

                            if modo_codigo == "✏️ Manter/Editar Código Atual":
                                cod_sug = cod_atv_atual if cod_atv_atual else codigo_novo_gerado
                                ed_cod_atv = st.text_input("Código da Atividade/Missão:", value=cod_sug, key=f"t1_at_cod_{id_at_ref}").strip().upper()
                            elif modo_codigo == "➕ Gerar Novo Código Automático":
                                ed_cod_atv = st.text_input("Novo Código Gerado:", value=codigo_novo_gerado, key=f"t1_cod_novo_txt_{id_at_ref}").strip().upper()
                                st.caption("💡 Código gerado com base no sequencial do estado.")
                            else:
                                if not opcoes_atvs_existentes:
                                    st.warning("⚠️ Nenhuma atividade cadastrada para este estado. Usando o código sugerido.")
                                    ed_cod_atv = codigo_novo_gerado
                                else:
                                    atv_escolhida_lbl = st.selectbox("Selecione a Atividade Existente:", opcoes_atvs_existentes, key=f"t1_sel_exist_{id_at_ref}")
                                    dados_atv_sel = mapa_dados_atv_existente[atv_escolhida_lbl]
                                    ed_cod_atv = str(dados_atv_sel["Codigo_Atividade"]).strip().upper()
                                    nome_atv_prefill = str(dados_atv_sel.get("Nome da Atividade", "")).strip()
                                    st.success(f"✅ Vinculando à atividade **{ed_cod_atv}**.")

                            ed_nome_atv = st.text_input("Nome da Atividade / Operação:", value=nome_atv_prefill, key=f"t1_at_nomeatv_{id_at_ref}").strip()
                            lista_and_at = ["Prevista", "Concluída"]
                            idx_and_at = lista_and_at.index(reg_at_alvo["Andamento"]) if reg_at_alvo.get("Andamento") in lista_and_at else 0
                            ed_andamento_at = st.selectbox("Andamento da Atividade:", lista_and_at, index=idx_and_at, key=f"t1_at_and_{id_at_ref}")

                        with aba2_at:
                            st.text_input("Indicador Oficial", value=val_indicador_at, disabled=True, key=f"t1_at_ind_{id_at_ref}")
                            ed_res_ind_at = st.text_input("Resultado do Indicador (Aferição Real):", value=str(reg_at_alvo.get("Resultado_Indicador", "")), key=f"t1_at_resind_{id_at_ref}")
                            ed_doc_at = st.text_input("Doc_Probatorio_Exec (SEI):", value=str(reg_at_alvo.get("Doc_Probatorio_Exec", "")), key=f"t1_at_doc_{id_at_ref}")
                            st.text_input("UF da Ação PNAPA", value=uf_acao_at, disabled=True, key=f"t1_at_uf_{id_at_ref}")
                            st.text_input("Importância da Atividade (Herdada)", value=importancia_at, disabled=True, key=f"t1_at_imp_{id_at_ref}")
                            ed_tema_at = st.selectbox("Tema da Atividade:", LISTA_TEMAS, index=LISTA_TEMAS.index(reg_at_alvo["Tema da Atividade"]) if reg_at_alvo.get("Tema da Atividade") in LISTA_TEMAS else 0, key=f"t1_at_tema_{id_at_ref}")
                            ed_obj_at = st.selectbox("Objetivo da Atividade:", LISTA_OBJETIVOS, index=LISTA_OBJETIVOS.index(reg_at_alvo["Objetivo da Atividade"]) if reg_at_alvo.get("Objetivo da Atividade") in LISTA_OBJETIVOS else 0, key=f"t1_at_obj_{id_at_ref}")
                            ed_tipo_at = st.selectbox("Tipo de Atividade:", LISTA_TIPOS_ATIVIDADE, index=LISTA_TIPOS_ATIVIDADE.index(reg_at_alvo["Tipo de Atividade"]) if reg_at_alvo.get("Tipo de Atividade") in LISTA_TIPOS_ATIVIDADE else 0, key=f"t1_at_tipo_{id_at_ref}")
                            ed_perigo_at = st.selectbox("Periculosidade/Insalubridade:", LISTA_PERIGOS, index=LISTA_PERIGOS.index(reg_at_alvo["Periculosidade/Insalubridade"]) if reg_at_alvo.get("Periculosidade/Insalubridade") in LISTA_PERIGOS else 0, key=f"t1_at_perigo_{id_at_ref}")

                        with aba3_at:
                            df_srv_at = df_servidores[df_servidores["UF_Servidor"] == uf_acao_at]
                            lista_nomes_servidores = sorted(df_srv_at["Servidor"].dropna().unique().tolist()) if not df_srv_at.empty else [email_logado]
                            
                            c_at_rh1, c_at_rh2 = st.columns(2)
                            with c_at_rh1:
                                srv_atual_at = str(reg_at_alvo.get("Servidor", "")).strip()
                                idx_srv_at = lista_nomes_servidores.index(srv_atual_at) if srv_atual_at in lista_nomes_servidores else 0
                                ed_servidor_at = st.selectbox("Servidor Integrante / Responsável:", lista_nomes_servidores, index=idx_srv_at, key=f"t1_at_srv_{id_at_ref}")
                            with c_at_rh2:
                                func_salva_at = str(reg_at_alvo.get("Coordenador_Operacao", "")).strip()
                                if func_salva_at in LISTA_FUNCOES_CAMPO:
                                    idx_func_at = LISTA_FUNCOES_CAMPO.index(func_salva_at)
                                else:
                                    eh_focal_at = bool(ponto_focal_estado_at and str(ed_servidor_at).strip().lower() == str(ponto_focal_estado_at).strip().lower())
                                    idx_func_at = 0 if eh_focal_at else 1
                                ed_funcao_campo = st.selectbox("Função na Atividade de Campo:", LISTA_FUNCOES_CAMPO, index=idx_func_at, key=f"t1_at_func_{id_at_ref}_{ed_servidor_at}")

                            if not df_srv_at.empty and ed_servidor_at in df_srv_at["Servidor"].values:
                                dados_s_linha = df_srv_at[df_srv_at["Servidor"] == ed_servidor_at].iloc[0]
                                ed_uf_srv_at = str(dados_s_linha.get("UF_Servidor", uf_acao_at))
                                ed_lot_at = str(dados_s_linha.get("Lotacao", "Sede Superintendência"))
                                ed_eq_at = str(dados_s_linha.get("Equipe_Emergencias", "Não"))
                            else:
                                ed_uf_srv_at, ed_lot_at, ed_eq_at = uf_acao_at, "Sede Superintendência", "Não"

                            st.text_input("UF do Servidor (Automático)", value=ed_uf_srv_at, disabled=True, key=f"t1_at_ufsrv_{id_at_ref}")
                            st.text_input("Lotação (Automático)", value=ed_lot_at, disabled=True, key=f"t1_at_lot_{id_at_ref}")
                            st.text_input("Faz parte da Equipe de Emergências? (Automático)", value=ed_eq_at, disabled=True, key=f"t1_at_eq_{id_at_ref}")
                            ed_pcdp_at = st.text_input("Número da PCDP:", value=str(reg_at_alvo.get("Número da PCDP", "")), key=f"t1_at_pcdp_{id_at_ref}")
                            
                            st.markdown("<p style='font-weight:bold; color:#03170a;'>📍 Geolocalização da Atividade</p>", unsafe_allow_html=True)
                            st.text_input("País", value="Brasil", disabled=True, key=f"t1_at_pais_{id_at_ref}")
                            uf_oc_atual = str(reg_at_alvo.get("UF Onde Ocorreu/Ocorrerá a Ação", "SP"))
                            idx_uf_oc_at = LISTA_UFS_COMPLETA.index(uf_oc_atual) if uf_oc_atual in LISTA_UFS_COMPLETA else 0
                            ed_uf_oc_at = st.selectbox("UF Onde Ocorreu/Ocorrerá a Ação:", LISTA_UFS_COMPLETA, index=idx_uf_oc_at, key=f"t1_at_ufoc_{id_at_ref}")
                            ed_est_loc_at = MAPEAMENTO_ESTADOS_COMPLETO.get(ed_uf_oc_at, "")
                            st.text_input("Estado_Local_Acao (Automático)", value=ed_est_loc_at, disabled=True, key=f"t1_at_est_{id_at_ref}")
                            
                            mun_lista_at = obter_municipios_ibge(ed_uf_oc_at)
                            mun_atual_at = str(reg_at_alvo.get("Municipio Onde Ocorreu/Ocorrerá a Ação", ""))
                            idx_mun_at = mun_lista_at.index(mun_atual_at) if mun_atual_at in mun_lista_at else 0
                            ed_mun_at = st.selectbox("Municipio Onde Ocorreu/Ocorrerá a Ação:", mun_lista_at if mun_lista_at else ["Superintendência Sede"], index=idx_mun_at, key=f"t1_at_mun_{id_at_ref}_{ed_uf_oc_at}")

                        with aba4_at:
                            val_dti_at = converter_para_data_segura(reg_at_alvo.get("Data de Início"))
                            val_dtf_at = converter_para_data_segura(reg_at_alvo.get("Data de Término"))
                            ed_dt_i_at = st.date_input("Data de Início:", value=val_dti_at, format="DD/MM/YYYY", key=f"t1_at_dti_{id_at_ref}")
                            ed_dt_f_at = st.date_input("Data de Término:", value=val_dtf_at, format="DD/MM/YYYY", key=f"t1_at_dtf_{id_at_ref}")
                            
                            c_at_d1, c_at_d2 = st.columns(2)
                            with c_at_d1:
                                ed_dias_pl_at = st.number_input("Dias Gastos Plan:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Dias_Gastos_Plan")), step=0.5, format="%.1f", key=f"t1_at_dpl_{id_at_ref}")
                            with c_at_d2:
                                ed_dias_ex_at = st.number_input("Dias Gastos Exec:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Dias_Gastos_Exec")), step=0.5, format="%.1f", key=f"t1_at_dex_{id_at_ref}")
                                
                            ed_orig_at = st.selectbox("Origem do Recurso:", LISTA_ORIGENS_RECURSO, index=LISTA_ORIGENS_RECURSO.index(reg_at_alvo["Origem do Recurso"]) if reg_at_alvo.get("Origem do Recurso") in LISTA_ORIGENS_RECURSO else 0, key=f"t1_at_orig_{id_at_ref}")
                            
                            st.markdown("<p style='font-weight:bold; color:#03170a;'>Valores Orçamentários (Planejado vs Executado)</p>", unsafe_allow_html=True)
                            c_at_pl, c_at_ex = st.columns(2)
                            with c_at_pl:
                                st.caption("Planejado")
                                ed_rp_d_at = st.number_input("Rec_Plan_Diarias:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Plan_Diarias")), step=50.0, format="%.2f", key=f"t1_at_rpd_{id_at_ref}")
                                ed_rp_p_at = st.number_input("Rec_Plan_Passagens:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Plan_Passagens")), step=50.0, format="%.2f", key=f"t1_at_rpp_{id_at_ref}")
                                ed_rp_o_at = st.number_input("Rec_Plan_Outras_Despesas:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Plan_Outras_Despesas")), step=50.0, format="%.2f", key=f"t1_at_rpo_{id_at_ref}")
                                st.text_input("Rec_Plan_Total (Soma):", value=f"{(ed_rp_d_at + ed_rp_p_at + ed_rp_o_ac if 'ed_rp_o_ac' in locals() else ed_rp_d_at + ed_rp_p_at + ed_rp_o_at):,.2f}", disabled=True, key=f"t1_at_totpl_{id_at_ref}")
                            with c_at_ex:
                                st.caption("Executado")
                                ed_re_d_at = st.number_input("Rec_Exec_Diarias:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Exec_Diarias")), step=50.0, format="%.2f", key=f"t1_at_red_{id_at_ref}")
                                ed_re_p_at = st.number_input("Rec_Exec_Passagens:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Exec_Passagens")), step=50.0, format="%.2f", key=f"t1_at_rep_{id_at_ref}")
                                ed_re_o_at = st.number_input("Rec_Exec_Outras_Despesas:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Exec_Outras_Despesas")), step=50.0, format="%.2f", key=f"t1_at_reo_{id_at_ref}")
                                st.text_input("Rec_Exec_Total (Soma):", value=f"{(ed_re_d_at + ed_re_p_at + ed_re_o_at):,.2f}", disabled=True, key=f"t1_at_totex_{id_at_ref}")

                        with aba5_at:
                            ed_obs_at = st.text_area("Observações:", value=str(reg_at_alvo.get("Observações", "")), key=f"t1_at_obs_{id_at_ref}")

                        with aba6_at:
                            st.markdown("##### ⭐ Avaliação de Desempenho do Servidor")
                            st.caption("Apenas o Coordenador da Atividade, Ponto Focal da UF ou Administrador podem avaliar.")
                            
                            # Lógica de Autorização (Trava de Segurança)
                            is_coord = not df_atual[
                                (df_atual["Codigo_Atividade"].astype(str).str.strip().str.upper() == str(ed_cod_atv).strip().upper()) & 
                                (df_atual["Servidor"].astype(str).str.strip() == str(nome_usuario_logado)) & 
                                (df_atual["Coordenador_Operacao"].astype(str).str.strip() == "Coordenador de Campo")
                            ].empty
                            
                            is_focal = (str(nome_usuario_logado).strip() == str(ponto_focal_estado_at).strip())
                            pode_avaliar = is_coord or is_focal or perfil_usuario == "Administrador"

                            val_qualidade = str(reg_at_alvo.get("Avaliacao_Qualidade", "Não Avaliada")).strip()
                            if val_qualidade == "" or val_qualidade == "nan": val_qualidade = "Não Avaliada"
                            val_feedback = str(reg_at_alvo.get("Avaliacao_Feedback", "")).strip()

                            lista_notas = ["Não Avaliada", "0 - Insatisfatória", "1 - Satisfatória"]
                            idx_nota = lista_notas.index(val_qualidade) if val_qualidade in lista_notas else 0

                            ed_qual = st.selectbox("Nota de Qualidade / Entrega:", lista_notas, index=idx_nota, disabled=not pode_avaliar, key=f"t1_at_qual_{id_at_ref}")
                            ed_feed = st.text_area("Feedback Privado da Liderança:", value=val_feedback, disabled=not pode_avaliar, key=f"t1_at_feed_{id_at_ref}")
                            
                            if not pode_avaliar:
                                st.error("🔒 Você não tem permissão de liderança para avaliar este servidor nesta missão.")

                        ed_papel_heranca = papel_estado_at if papel_estado_at in LISTA_PAPEIS_INSTITUCIONAIS else ""

                        if st.button("💾 Gravar Alterações da Atividade", type="primary", key=f"btn_salvar_at_{id_at_ref}"):
                            bloqueio_coord = False
                            if ed_funcao_campo == "Coordenador de Campo":
                                coordenadores_existentes = df_atual[
                                    (df_atual["Nível"].astype(str).str.strip() == "Atividade") &
                                    (df_atual["Codigo_Atividade"].astype(str).str.strip().str.upper() == str(ed_cod_atv).strip().upper()) &
                                    (df_atual["Coordenador_Operacao"].astype(str).str.strip() == "Coordenador de Campo") &
                                    (df_atual["Id"].astype(str) != id_at_ref)
                                ]
                                if not coordenadores_existentes.empty:
                                    nome_outro = coordenadores_existentes["Servidor"].iloc[0]
                                    st.error(f"⛔ **Conflito de Liderança:** A atividade `{ed_cod_atv}` já possui **{nome_outro}** como Coordenador de Campo.")
                                    bloqueio_coord = True

                            if not bloqueio_coord:
                                payload_at = payload_gerador(
                                    val_ano_at, val_num_acao_at, val_nome_acao_at, val_indicador_at, "Atividade",
                                    ed_nome_atv, ed_andamento_at, ed_res_ind_at, ed_doc_at, uf_acao_at,
                                    importancia_at, ed_tema_at, ed_obj_at, ed_tipo_at, ed_perigo_at, ed_servidor_at,
                                    ed_uf_srv_at, ed_lot_at, ed_eq_at, ed_pcdp_at, "Brasil", ed_uf_oc_at,
                                    ed_est_loc_at, ed_mun_at, ed_dt_i_at, ed_dt_f_at, ed_dias_pl_at, ed_dias_ex_at,
                                    ed_orig_at, ed_rp_d_at, ed_rp_p_at, ed_rp_o_at, ed_re_d_at,
                                    ed_re_p_at, ed_re_o_at, ed_obs_at, "", id_at_ref, "📝 Editar Linha Existente", df_atual,
                                    papel_institucional=ed_papel_heranca, coordenador_operacao=ed_funcao_campo, meta_indicador="",
                                    codigo_atividade=ed_cod_atv, aval_qualidade=ed_qual, aval_feedback=ed_feed
                                )
                                executar_envio_sharepoint([payload_at])
                                st.session_state["selecoes_atividades"] = {}
                                st.session_state["version_ed_at"] += 1
                                st.rerun()

                    # =================================================================
                    # EDIÇÃO EM LOTE DE ATIVIDADES (CHECKBOX + RESUMO REATIVO)
                    # =================================================================
                    else:
                        st.info(f"👥 **Edição em Lote:** {qtd_at_sel} atividades selecionadas. Marque os campos nas abas abaixo para habilitar a edição seletiva em massa.")
                        
                        edicoes_lote = {}
                        
                        l_aba1, l_aba2, l_aba3, l_aba4, l_aba5, l_aba6 = st.tabs([
                            "1. Identificação & Agrupador", "2. Detalhes & Indicadores", 
                            "3. Recursos Humanos & Liderança", "4. Cronograma & Custos", "5. Observações",
                            "6. Avaliação"
                        ])

                        with l_aba1:
                            st.markdown("##### 🗂️ Ação PNAPA Vinculada (Pai)")
                            if st.checkbox("Alterar Ação PNAPA Vinculada?", key="chk_acao_lt"):
                                lista_opcoes_vinc_lt = sorted((df_pnapas["Acao_Ano"].astype(str) + " - " + df_pnapas["Nome_Acao_Apelido"].astype(str)).tolist()) if not df_pnapas.empty else []
                                sel_acao_pai_lt = st.selectbox("Selecione a Nova Ação PNAPA:", lista_opcoes_vinc_lt if lista_opcoes_vinc_lt else ["Nenhuma Ação Cadastrada"], key="in_acao_lt")
                                
                                if lista_opcoes_vinc_lt:
                                    cod_novo_pai_lt = sel_acao_pai_lt.split(" - ")[0].strip()
                                    dados_novo_pai_lt = df_pnapas[df_pnapas["Acao_Ano"].astype(str) == cod_novo_pai_lt].iloc[0]
                                    
                                    edicoes_lote["Ano da Ação"] = int(dados_novo_pai_lt["Ano"])
                                    edicoes_lote["Número da Ação PNAPA"] = str(dados_novo_pai_lt.get("Acao_Ano", dados_novo_pai_lt["Num_Acao_PNAPA"]))
                                    apel_lt = str(dados_novo_pai_lt.get("Nome_Acao_Apelido", ""))
                                    edicoes_lote["Nome da Ação PNAPA"] = apel_lt if apel_lt and apel_lt.lower() != "nan" else str(dados_novo_pai_lt.get("Nome_Acao_Completo", "")).strip()
                                    edicoes_lote["Indicador"] = str(dados_novo_pai_lt["Indicador"])
                                    edicoes_lote["Importância da Atividade"] = str(dados_novo_pai_lt.get("Importância", "Ordinária")).strip()

                            st.markdown("##### 🏷️ Código e Agrupador da Atividade")
                            if st.checkbox("Alterar Código da Atividade/Missão?", key="chk_cod_lt"):
                                acao_base_lt = edicoes_lote.get("Número da Ação PNAPA", str(df_at_sel.iloc[0].get("Número da Ação PNAPA", "")).strip())
                                uf_base_lt = uf_usuario if uf_usuario != "Acesso Restrito" else "SP"
                                
                                df_atvs_acao_uf_lt = df_atual[
                                    (df_atual["Nível"] == "Atividade") &
                                    (df_atual["UF_Acao_PNAPA"].astype(str).str.strip().str.upper() == str(uf_base_lt).strip().upper()) &
                                    (
                                        (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == acao_base_lt.upper()) |
                                        (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == acao_base_lt.split("-")[0].strip().upper())
                                    ) &
                                    (df_atual["Codigo_Atividade"].astype(str).str.strip() != "")
                                ]
                                
                                import re
                                maior_num_lt = 0
                                for cod_exist in df_atvs_acao_uf_lt["Codigo_Atividade"].dropna().unique():
                                    match = re.search(r'ATV(\d+)', str(cod_exist).upper())
                                    if match:
                                        num_extraido = int(match.group(1))
                                        if num_extraido > maior_num_lt:
                                            maior_num_lt = num_extraido
                                
                                cod_base_ano_lt = acao_base_lt if "-" in str(acao_base_lt) else f"{acao_base_lt}-{df_at_sel.iloc[0].get('Ano da Ação', 2026)}"
                                cod_sug_lt = f"{cod_base_ano_lt}-{uf_base_lt}-ATV{maior_num_lt + 1:02d}"
                                
                                opcoes_atvs_existentes_lt = []
                                mapa_dados_atv_lt = {}
                                for cod_unic in sorted(df_atvs_acao_uf_lt["Codigo_Atividade"].dropna().unique()):
                                    linhas_deste_cod = df_atvs_acao_uf_lt[df_atvs_acao_uf_lt["Codigo_Atividade"] == cod_unic]
                                    nome_atv_ex = str(linhas_deste_cod["Nome da Atividade"].iloc[0]).strip()
                                    label_ex_lt = f"{cod_unic} — {nome_atv_ex}"
                                    opcoes_atvs_existentes_lt.append(label_ex_lt)
                                    mapa_dados_atv_lt[label_ex_lt] = nome_atv_ex
                                
                                modo_cod_lt = st.radio("Definição do Novo Código:", ["➕ Digitar Manualmente / Automático", "🔗 Vincular a Atividade Existente"], horizontal=True)
                                
                                if modo_cod_lt == "➕ Digitar Manualmente / Automático":
                                    edicoes_lote["Codigo_Atividade"] = st.text_input("Novo Código:", value=cod_sug_lt, key="in_cod_lt_man").strip().upper()
                                else:
                                    if not opcoes_atvs_existentes_lt:
                                        st.warning("⚠️ Nenhuma atividade encontrada para esta Ação/UF. Digite manualmente.")
                                        edicoes_lote["Codigo_Atividade"] = st.text_input("Novo Código:", value=cod_sug_lt, key="in_cod_lt_fallback").strip().upper()
                                    else:
                                        sel_cod_exist_lt = st.selectbox("Selecione a Atividade Existente:", opcoes_atvs_existentes_lt, key="in_cod_lt_sel")
                                        edicoes_lote["Codigo_Atividade"] = sel_cod_exist_lt.split(" — ")[0].strip()
                                        if st.button("Puxar 'Nome da Atividade' vinculada", key="btn_puxar_nome_lt"):
                                            st.session_state["lote_nome_puxado"] = mapa_dados_atv_lt[sel_cod_exist_lt]

                            val_nome_lt_ui = st.session_state.get("lote_nome_puxado", "")
                            if st.checkbox("Alterar Nome da Atividade / Operação?", key="chk_nome_lt"):
                                edicoes_lote["Nome da Atividade"] = st.text_input("Novo Nome da Atividade:", value=val_nome_lt_ui, key="in_nome_lt").strip()
                            if st.checkbox("Alterar Andamento?", key="chk_and_lt"):
                                edicoes_lote["Andamento"] = st.selectbox("Novo Andamento:", ["Prevista", "Concluída"], key="in_and_lt")

                        with l_aba2:
                            if st.checkbox("Alterar Resultado do Indicador (Aferição Real)?", key="chk_res_lt"):
                                edicoes_lote["Resultado_Indicador"] = st.text_input("Novo Resultado:", key="in_res_lt").strip()
                            if st.checkbox("Alterar Doc_Probatorio_Exec (SEI)?", key="chk_doc_lt"):
                                edicoes_lote["Doc_Probatorio_Exec"] = st.text_input("Novo SEI:", key="in_doc_lt").strip()
                            if st.checkbox("Alterar Tema da Atividade?", key="chk_tema_lt"):
                                edicoes_lote["Tema da Atividade"] = st.selectbox("Novo Tema:", LISTA_TEMAS, key="in_tema_lt")
                            if st.checkbox("Alterar Objetivo da Atividade?", key="chk_obj_lt"):
                                edicoes_lote["Objetivo da Atividade"] = st.selectbox("Novo Objetivo:", LISTA_OBJETIVOS, key="in_obj_lt")
                            if st.checkbox("Alterar Tipo de Atividade?", key="chk_tipo_lt"):
                                edicoes_lote["Tipo de Atividade"] = st.selectbox("Novo Tipo:", LISTA_TIPOS_ATIVIDADE, key="in_tipo_lt")
                            if st.checkbox("Alterar Periculosidade/Insalubridade?", key="chk_perigo_lt"):
                                edicoes_lote["Periculosidade/Insalubridade"] = st.selectbox("Nova Periculosidade:", LISTA_PERIGOS, key="in_perigo_lt")

                        with l_aba3:
                            st.caption("Atenção: Alterar dados de Recursos Humanos aplicará o mesmo valor a todas as linhas selecionadas.")
                            if st.checkbox("Alterar Servidor Integrante / Responsável?", key="chk_srv_lt"):
                                lista_todos_srvs = sorted(df_servidores["Servidor"].dropna().unique().tolist())
                                edicoes_lote["Servidor"] = st.selectbox("Novo Servidor:", lista_todos_srvs, key="in_srv_lt")
                            if st.checkbox("Alterar Função na Atividade de Campo?", key="chk_func_lt"):
                                edicoes_lote["Coordenador_Operacao"] = st.selectbox("Nova Função:", LISTA_FUNCOES_CAMPO, key="in_func_lt")
                            if st.checkbox("Alterar Número da PCDP?", key="chk_pcdp_lt"):
                                edicoes_lote["Número da PCDP"] = st.text_input("Nova PCDP:", key="in_pcdp_lt").strip()
                            
                            st.markdown("##### Geolocalização da Atividade")
                            if st.checkbox("Alterar Localidade (UF e Município Ocorrência)?", key="chk_loc_lt"):
                                ed_uf_oc = st.selectbox("Nova UF Onde Ocorreu/Ocorrerá a Ação:", LISTA_UFS_COMPLETA, key="in_ufoc_lt")
                                edicoes_lote["UF Onde Ocorreu/Ocorrerá a Ação"] = ed_uf_oc
                                edicoes_lote["Estado_Local_Acao"] = MAPEAMENTO_ESTADOS_COMPLETO.get(ed_uf_oc, "")
                                mun_lista_lote = obter_municipios_ibge(ed_uf_oc)
                                edicoes_lote["Municipio Onde Ocorreu/Ocorrerá a Ação"] = st.selectbox("Novo Municipio Onde Ocorreu/Ocorrerá a Ação:", mun_lista_lote if mun_lista_lote else ["Superintendência Sede"], key="in_mun_lt")

                        with l_aba4:
                            col_ld1, col_ld2 = st.columns(2)
                            with col_ld1:
                                if st.checkbox("Alterar Data de Início?", key="chk_dti_lt"):
                                    edicoes_lote["Data de Início"] = st.date_input("Nova Data de Início:", format="DD/MM/YYYY", key="in_dti_lt")
                                if st.checkbox("Alterar Data de Término?", key="chk_dtf_lt"):
                                    edicoes_lote["Data de Término"] = st.date_input("Nova Data de Término:", format="DD/MM/YYYY", key="in_dtf_lt")
                                if st.checkbox("Alterar Origem do Recurso?", key="chk_orig_lt"):
                                    edicoes_lote["Origem do Recurso"] = st.selectbox("Nova Origem do Recurso:", LISTA_ORIGENS_RECURSO, key="in_orig_lt")
                            with col_ld2:
                                if st.checkbox("Alterar Dias_Gastos_Plan?", key="chk_dpl_lt"):
                                    edicoes_lote["Dias_Gastos_Plan"] = st.number_input("Novos Dias Gastos Plan:", min_value=0.0, step=0.5, format="%.1f", key="in_dpl_lt")
                                if st.checkbox("Alterar Dias_Gastos_Exec?", key="chk_dex_lt"):
                                    edicoes_lote["Dias_Gastos_Exec"] = st.number_input("Novos Dias Gastos Exec:", min_value=0.0, step=0.5, format="%.1f", key="in_dex_lt")

                            st.markdown("##### Valores Orçamentários (Planejado vs Executado)")
                            col_lpl, col_lex = st.columns(2)
                            with col_lpl:
                                if st.checkbox("Alterar Rec_Plan_Diarias?", key="chk_rpd_lt"):
                                    edicoes_lote["Rec_Plan_Diarias"] = st.number_input("Novo Rec_Plan_Diarias:", min_value=0.0, step=50.0, format="%.2f", key="in_rpd_lt")
                                if st.checkbox("Alterar Rec_Plan_Passagens?", key="chk_rpp_lt"):
                                    edicoes_lote["Rec_Plan_Passagens"] = st.number_input("Novo Rec_Plan_Passagens:", min_value=0.0, step=50.0, format="%.2f", key="in_rpp_lt")
                                if st.checkbox("Alterar Rec_Plan_Outras_Despesas?", key="chk_rpo_lt"):
                                    edicoes_lote["Rec_Plan_Outras_Despesas"] = st.number_input("Novo Rec_Plan_Outras_Despesas:", min_value=0.0, step=50.0, format="%.2f", key="in_rpo_lt")
                            with col_lex:
                                if st.checkbox("Alterar Rec_Exec_Diarias?", key="chk_red_lt"):
                                    edicoes_lote["Rec_Exec_Diarias"] = st.number_input("Novo Rec_Exec_Diarias:", min_value=0.0, step=50.0, format="%.2f", key="in_red_lt")
                                if st.checkbox("Alterar Rec_Exec_Passagens?", key="chk_rep_lt"):
                                    edicoes_lote["Rec_Exec_Passagens"] = st.number_input("Novo Rec_Exec_Passagens:", min_value=0.0, step=50.0, format="%.2f", key="in_rep_lt")
                                if st.checkbox("Alterar Rec_Exec_Outras_Despesas?", key="chk_reo_lt"):
                                    edicoes_lote["Rec_Exec_Outras_Despesas"] = st.number_input("Novo Rec_Exec_Outras_Despesas:", min_value=0.0, step=50.0, format="%.2f", key="in_reo_lt")

                        with l_aba5:
                            if st.checkbox("Alterar Observações?", key="chk_obs_lt"):
                                edicoes_lote["Observações"] = st.text_area("Novas Observações:", key="in_obs_lt").strip()

                        with l_aba6:
                            st.caption("Atenção: A nota e o feedback dados aqui serão aplicados a todos os servidores marcados no lote.")
                            if st.checkbox("Avaliar a Equipe Selecionada em Massa?", key="chk_aval_lt"):
                                edicoes_lote["Avaliacao_Qualidade"] = st.selectbox("Nota de Qualidade Geral:",
                                                                                   ["Não Avaliada","0 - Insatisfatória", "1 - Satisfatória"],
                                                                                   key="in_qual_lt")
                                edicoes_lote["Avaliacao_Feedback"] = st.text_area("Feedback da Liderança (Aplicado a todos):", key="in_feed_lt")

                        st.markdown("---")
                        st.markdown("### 📋 Resumo das Alterações (Serão aplicadas a todas as linhas selecionadas)")
                        if edicoes_lote:
                            st.json({k: str(v) if isinstance(v, (date, datetime)) else v for k, v in edicoes_lote.items()})
                            
                            if st.button("🚀 Confirmar e Aplicar Alterações em Massa", type="primary", key="btn_confirm_lote_at"):
                                payloads_lote = []
                                bloqueio_lote = False
                                
                                if edicoes_lote.get("Coordenador_Operacao") == "Coordenador de Campo":
                                    codigos_no_lote = df_at_sel["Codigo_Atividade"].unique()
                                    if "Codigo_Atividade" in edicoes_lote or len(codigos_no_lote) == 1:
                                        if qtd_at_sel > 1:
                                            st.error("⛔ **Conflito de Liderança:** Você não pode definir 'Coordenador de Campo' para múltiplos servidores em lote. Apenas um servidor pode coordenar a atividade.")
                                            bloqueio_lote = True

                                if not bloqueio_lote:
                                    for _, row in df_at_sel.iterrows():
                                        v_ano = edicoes_lote.get("Ano da Ação", row.get("Ano da Ação", 2026))
                                        v_num_acao = edicoes_lote.get("Número da Ação PNAPA", row.get("Número da Ação PNAPA", ""))
                                        v_nome_acao = edicoes_lote.get("Nome da Ação PNAPA", row.get("Nome da Ação PNAPA", ""))
                                        v_indicador = edicoes_lote.get("Indicador", row.get("Indicador", ""))
                                        v_imp = edicoes_lote.get("Importância da Atividade", row.get("Importância da Atividade", "Ordinária"))
                                        v_uf_acao = str(row.get("UF_Acao_PNAPA", uf_usuario)).strip()
                                        v_papel = str(row.get("Papel_Institucional", "")).strip()
                                        
                                        v_cod_atv = edicoes_lote.get("Codigo_Atividade", str(row.get("Codigo_Atividade", "")).strip())
                                        v_nome_atv = edicoes_lote.get("Nome da Atividade", str(row.get("Nome da Atividade", "")).strip())
                                        v_and = edicoes_lote.get("Andamento", str(row.get("Andamento", "Prevista")).strip())
                                        v_res_ind = edicoes_lote.get("Resultado_Indicador", str(row.get("Resultado_Indicador", "")).strip())
                                        v_doc = edicoes_lote.get("Doc_Probatorio_Exec", str(row.get("Doc_Probatorio_Exec", "")).strip())
                                        v_tema = edicoes_lote.get("Tema da Atividade", str(row.get("Tema da Atividade", "Dutos")).strip())
                                        v_obj = edicoes_lote.get("Objetivo da Atividade", str(row.get("Objetivo da Atividade", "Atendimento a Acidentes")).strip())
                                        v_tipo = edicoes_lote.get("Tipo de Atividade", str(row.get("Tipo de Atividade", "Operação")).strip())
                                        v_perigo = edicoes_lote.get("Periculosidade/Insalubridade", str(row.get("Periculosidade/Insalubridade", "Não se Aplica")).strip())
                                        
                                        v_srv = edicoes_lote.get("Servidor", str(row.get("Servidor", "")).strip())
                                        v_func = edicoes_lote.get("Coordenador_Operacao", str(row.get("Coordenador_Operacao", "Apoio de Campo")).strip())
                                        v_pcdp = edicoes_lote.get("Número da PCDP", str(row.get("Número da PCDP", "")).strip())
                                        
                                        if "Servidor" in edicoes_lote:
                                            df_srv_lt = df_servidores[df_servidores["Servidor"] == v_srv]
                                            if not df_srv_lt.empty:
                                                v_uf_srv = str(df_srv_lt.iloc[0].get("UF_Servidor", ""))
                                                v_lot = str(df_srv_lt.iloc[0].get("Lotacao", ""))
                                                v_eq = str(df_srv_lt.iloc[0].get("Equipe_Emergencias", "Não"))
                                            else:
                                                v_uf_srv, v_lot, v_eq = "", "", "Não"
                                        else:
                                            v_uf_srv = str(row.get("UF_Servidor", ""))
                                            v_lot = str(row.get("Lotação", ""))
                                            v_eq = str(row.get("Faz parte da Equipe de Emergências", "Não"))
                                            
                                        v_pais = "Brasil"
                                        v_uf_oc = edicoes_lote.get("UF Onde Ocorreu/Ocorrerá a Ação", str(row.get("UF Onde Ocorreu/Ocorrerá a Ação", "SP")))
                                        v_est_oc = edicoes_lote.get("Estado_Local_Acao", str(row.get("Estado_Local_Acao", "São Paulo")))
                                        v_mun_oc = edicoes_lote.get("Municipio Onde Ocorreu/Ocorrerá a Ação", str(row.get("Municipio Onde Ocorreu/Ocorrerá a Ação", "")))
                                        
                                        v_dti = edicoes_lote.get("Data de Início", converter_para_data_segura(row.get("Data de Início")))
                                        v_dtf = edicoes_lote.get("Data de Término", converter_para_data_segura(row.get("Data de Término")))
                                        
                                        # Conversão segura de todos os numéricos da linha
                                        v_dpl = obter_float_limpo(edicoes_lote.get("Dias_Gastos_Plan", row.get("Dias_Gastos_Plan", 0.0)))
                                        v_dex = obter_float_limpo(edicoes_lote.get("Dias_Gastos_Exec", row.get("Dias_Gastos_Exec", 0.0)))
                                        v_origem = edicoes_lote.get("Origem do Recurso", str(row.get("Origem do Recurso", "SP")))
                                        
                                        v_rpd = obter_float_limpo(edicoes_lote.get("Rec_Plan_Diarias", row.get("Rec_Plan_Diarias", 0.0)))
                                        v_rpp = obter_float_limpo(edicoes_lote.get("Rec_Plan_Passagens", row.get("Rec_Plan_Passagens", 0.0)))
                                        v_rpo = obter_float_limpo(edicoes_lote.get("Rec_Plan_Outras_Despesas", row.get("Rec_Plan_Outras_Despesas", 0.0)))
                                        v_red = obter_float_limpo(edicoes_lote.get("Rec_Exec_Diarias", row.get("Rec_Exec_Diarias", 0.0)))
                                        v_rep = obter_float_limpo(edicoes_lote.get("Rec_Exec_Passagens", row.get("Rec_Exec_Passagens", 0.0)))
                                        v_reo = obter_float_limpo(edicoes_lote.get("Rec_Exec_Outras_Despesas", row.get("Rec_Exec_Outras_Despesas", 0.0)))
                                        
                                        v_obs = edicoes_lote.get("Observações", str(row.get("Observações", "")))
                                        
                                        payload_linha = payload_gerador(
                                            v_ano, v_num_acao, v_nome_acao, v_indicador, "Atividade",
                                            v_nome_atv, v_and, v_res_ind, v_doc, v_uf_acao,
                                            v_imp, v_tema, v_obj, v_tipo, v_perigo, v_srv,
                                            v_uf_srv, v_lot, v_eq, v_pcdp, v_pais, v_uf_oc,
                                            v_est_oc, v_mun_oc, v_dti, v_dtf, v_dpl, v_dex,
                                            v_origem, v_rpd, v_rpp, v_rpo, v_red,
                                            v_rep, v_reo, v_obs, "", str(row["Id"]), "📝 Editar Linha Existente", df_atual,
                                            papel_institucional=v_papel, coordenador_operacao=v_func, meta_indicador="",
                                            codigo_atividade=v_cod_atv
                                        )
                                        payloads_lote.append(payload_linha)
                                    
                                    executar_envio_sharepoint(payloads_lote)
                                    st.session_state["selecoes_atividades"] = {}
                                    st.session_state["version_ed_at"] += 1
                                    st.session_state.pop("lote_nome_puxado", None)
                                    st.rerun()
                        else:
                            st.info("💡 Nenhum campo foi marcado para edição. Marque as opções acima para visualizar o resumo e habilitar a gravação.")

# --- TELA 2: FORMULÁRIO DA PLANILHA MACRO (INSERIR NOVA LINHA) ---
elif modo == "➕ Inserir Nova Linha":
    st.markdown(f"<h3 style='color: #03170a;'>Formulário de Dados PNAPA — Modo: {modo}</h3>", unsafe_allow_html=True)
    
    idx_nivel_padrao = 0 if registro_selecionado is None or str(registro_selecionado.get("Nível", "")) == "Ação" else 1
    nivel_selecionado = st.selectbox("O que deseja cadastrar?", ["Ação", "Atividade"], index=idx_nivel_padrao, key="main_txt_nivel")
    
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
                if opc.startswith(num_acao_gravada + " - ") or opc.startswith(num_acao_gravada + "-") or (num_acao_gravada and opc.startswith(num_acao_gravada)):
                    idx_pna_vinc = i
                    break
            
            opcao_vinc_sel = st.selectbox("Selecione a Ação PNAPA correspondente:", lista_opcoes_vinc, index=idx_pna_vinc, key="form_pna_vinculo_sel")
            
            acao_ano_detectado = opcao_vinc_sel.split(" - ")[0]
            dados_aux_linha = df_pnapas_ano[df_pnapas_ano["Acao_Ano"].astype(str) == acao_ano_detectado].iloc[0]
            
            val_ano = int(dados_aux_linha["Ano"])
            val_num_acao = str(dados_aux_linha.get("Acao_Ano", dados_aux_linha["Num_Acao_PNAPA"]))
            cod_prefixo_puro = val_num_acao.split("-")[0].strip()
            apelido_ins = str(dados_aux_linha.get("Nome_Acao_Apelido", "")).strip()
            val_nome_acao = apelido_ins if apelido_ins and apelido_ins.lower() != "nan" else str(dados_aux_linha.get("Nome_Acao_Completo", "")).strip()
            val_indicador = str(dados_aux_linha["Indicador"])
            importancia = str(dados_aux_linha.get("Importância", "Ordinária")).strip()
            dono_nacional = str(dados_aux_linha.get("Dono_Acao", "Ceneac")).strip()
            uf_dono_nac = str(dados_aux_linha.get("UF_Dono", "Ceneac")).strip()
            meta_nac_info = dados_aux_linha.get("Meta_Nacional", "")

            # 💡 IDENTIFICAÇÃO DO PONTO FOCAL DA UF (COM FUNÇÃO BLINDADA)
            uf_filtro_pna = uf_usuario if uf_usuario != "Acesso Restrito" else "SP"
            ponto_focal_estado, papel_estado_acao = obter_ponto_focal_acao(df_atual, val_num_acao, uf_filtro_pna)

            st.info(f"👑 **Liderança Nacional:** `{dono_nacional} ({uf_dono_nac})` | **Meta Global:** `{meta_nac_info}`  \n📍 **Governança em {uf_filtro_pna}:** Papel: `{papel_estado_acao}` | Ponto Focal Estadual: `{ponto_focal_estado if ponto_focal_estado else 'Não Definido'}`")
        else:
            st.warning("⚠️ Nenhuma ação cadastrada para este ano no catálogo auxiliar.")
            val_ano, val_num_acao, val_nome_acao, val_indicador, importancia = None, "", "", "", "Ordinária"
            ponto_focal_estado = ""
    else:
        st.error("⚠️ O catálogo auxiliar de Ações PNAPA está vazio.")
        val_ano, val_num_acao, val_nome_acao, val_indicador, importancia = None, "", "", "", "Ordinária"
        ponto_focal_estado = ""

    st.markdown("---")
    
    dt_inicio_convertida = pd.to_datetime(registro_selecionado["Data de Início"], errors='coerce') if registro_selecionado is not None else pd.NaT
    val_dt_inicio = dt_inicio_convertida.date() if pd.notna(dt_inicio_convertida) else date.today()
    dt_termino_convertida = pd.to_datetime(registro_selecionado["Data de Término"], errors='coerce') if registro_selecionado is not None else pd.NaT
    val_dt_termino = dt_termino_convertida.date() if pd.notna(dt_termino_convertida) else date.today()

    def obter_num_seguro(registro, coluna):
        if registro is not None and coluna in registro:
            val = pd.to_numeric(registro[coluna], errors='coerce')
            return float(val) if pd.notna(val) else 0.0
        return 0.0

    st.text_input("ID do Registro", value=id_atual if id_atual else "Definido no envio", disabled=True)
    
    # =================================================================
    # CONDICIONAL: SE FOR AÇÃO (PLANEJAMENTO DA UF)
    # =================================================================
    if nivel_selecionado == "Ação":
        aba1, aba2, aba4, aba5 = st.tabs(["1. Identificação & Governança", "2. Detalhes & Metas", "4. Cronograma & Custos", "5. Justificativas"])
        
        with aba1:
            st.text_input("Ano da Ação (Automático)", value=str(val_ano if val_ano else ""), disabled=True)
            st.text_input("Número da Ação PNAPA (Automático)", value=val_num_acao, disabled=True)
            st.text_input("Nome da Ação PNAPA (Automático)", value=val_nome_acao, disabled=True)
            
            c_pap1, c_pap2 = st.columns(2)
            with c_pap1:
                papel_inst = st.selectbox("Papel da UF nesta Ação:", LISTA_PAPEIS_INSTITUCIONAIS, key="pna_papel_acao")
            with c_pap2:
                srvs_uf_pna = df_servidores[df_servidores["UF_Servidor"] == uf_filtro_pna]["Servidor"].dropna().unique().tolist()
                if papel_inst == "Coordenação":
                    servidor = st.selectbox(f"Ponto Focal / Coordenador da Ação na UF ({uf_filtro_pna}):", srvs_uf_pna if srvs_uf_pna else [email_logado], key="pna_focal_acao")
                    uf_servidor, lotacao, equipe_emergencia = uf_filtro_pna, "Sede Superintendência", "Sim"
                else:
                    st.info(f"ℹ️ **Atuação em Apoio:** A UF ({uf_filtro_pna}) não indicará Coordenador Estadual.")
                    servidor, uf_servidor, lotacao, equipe_emergencia = "", "", "", "Não"

            lista_andamentos_acao = ["Planejada", "Cancelada", "Não Demandada", "Não Executada"]
            try: idx_and = lista_andamentos_acao.index(registro_selecionado["Andamento"]) if registro_selecionado is not None else 0
            except: idx_and = 0
            andamento = st.selectbox("Andamento da Ação", lista_andamentos_acao, index=idx_and, key="pna_sel_andamento_acao")

        with aba2:
            st.text_input("Indicador Oficial (Herdado)", value=val_indicador, disabled=True)
            meta_indicador = st.number_input(f"Meta da Ação para a UF ({uf_usuario}):", min_value=0.0, value=1.0, step=1.0, key="pna_meta_uf_input")
            uf_acao = st.text_input("UF da Ação PNAPA", value=str(uf_usuario if uf_usuario != "Acesso Restrito" else "SP"), disabled=True)
            st.text_input("Importância da Atividade (Herdada do Catálogo)", value=importancia, disabled=True)
            
            tema = st.selectbox("Tema da Atividade", LISTA_TEMAS, key="pna_sel_tema_acao")
            objetivo = st.selectbox("Objetivo da Atividade", LISTA_OBJETIVOS, key="pna_sel_obj_acao")
            tipo_atividade = st.selectbox("Tipo de Atividade", LISTA_TIPOS_ATIVIDADE, key="pna_sel_tipo_acao")

        with aba4:
            dt_inicio = st.date_input("Data de Início:", value=val_dt_inicio, format="DD/MM/YYYY", key="pna_dt_ini_acao")
            dt_termino = st.date_input("Data de Término:", value=val_dt_termino, format="DD/MM/YYYY", key="pna_dt_fim_acao")
            
            dias_plan = st.number_input("Dias Gastos Plan", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Plan"), step=0.5, format="%.1f", key="pna_dias_pl_acao")
            # 🚀 Feedback imediato do Nível
            nivel_calculado = classificar_nivel_acao(dias_plan)
            st.metric("Classificação de Esforço:", nivel_calculado)
            
            origem_recurso = st.selectbox("Origem do Recurso", LISTA_ORIGENS_RECURSO, key="pna_orig_acao")
            
            st.markdown("<p style='font-weight: bold; margin-top:15px; color:#03170a;'>Valores Orçamentários Planejados</p>", unsafe_allow_html=True)
            rec_p_diarias = st.number_input("Rec_Plan_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Diarias"), step=50.0, format="%.2f", key="pna_rpd_acao")
            rec_p_passagens = st.number_input("Rec_Plan_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Passagens"), step=50.0, format="%.2f", key="pna_rpp_acao")
            rec_p_outras = st.number_input("Rec_Plan_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Outras_Despesas"), step=50.0, format="%.2f", key="pna_rpo_acao")
            
            calc_plan_acao = float(rec_p_diarias + rec_p_passagens + rec_p_outras)
            st.number_input("Rec_Plan_Total (Soma Automática)", value=calc_plan_acao, disabled=True, format="%.2f")

        with aba5:
            obs = st.text_area("Observações", value=str(registro_selecionado["Observações"]) if registro_selecionado is not None else "", key="pna_obs_acao")
            if andamento in ["Cancelada", "Não Demandada", "Não Executada"]:
                justificativa = st.selectbox("Justificativa_Acao_PNAPA", LISTA_JUSTIFICATIVAS_ACAO, key="pna_just_acao")
            else:
                justificativa = ""
                st.info("ℹ️ Justificativa habilitada apenas para ações com andamento Cancelada, Não Demandada ou Não Executada.")

        nome_atividade, resultado_indicador, doc_probatorio, periculosidade = "", "", "", "Não se Aplica"
        coordenador_operacao, num_pcdp, codigo_atividade = "", "", ""
        pais, uf_ocorrencia, estado_local, municipio, dias_exec = "Brasil", "", "", "", 0.0
        rec_e_diarias, rec_e_passagens, rec_e_outras = 0.0, 0.0, 0.0

    # =================================================================
    # CONDICIONAL: SE FOR ATIVIDADE (CÓDIGO INTELIGENTE E REATIVO)
    # =================================================================
    elif nivel_selecionado == "Atividade":
        aba1, aba2, aba3, aba4, aba5 = st.tabs(["1. Identificação & Agrupador", "2. Detalhes & Indicadores", "3. Recursos Humanos & Liderança", "4. Cronograma & Custos", "5. Justificativas"])
        
        with aba1:
            st.text_input("Ano da Ação (Automático)", value=str(val_ano if val_ano else ""), disabled=True)
            st.text_input("Número da Ação PNAPA (Automático)", value=val_num_acao, disabled=True)
            st.text_input("Nome da Ação PNAPA (Automático)", value=val_nome_acao, disabled=True)
            
            # 🚀 GESTOR INTELIGENTE DE CÓDIGO DA ATIVIDADE (REATIVO POR AÇÃO)
            st.markdown("##### 🏷️ Código e Agrupador da Atividade")
            
            if "Codigo_Atividade" not in df_atual.columns:
                df_atual["Codigo_Atividade"] = ""
            
            # 1. Filtra as atividades existentes DAQUELA AÇÃO e DAQUELA UF
            df_atvs_acao_uf = df_atual[
                (df_atual["Nível"] == "Atividade") &
                (df_atual["UF_Acao_PNAPA"].astype(str).str.strip().str.upper() == str(uf_filtro_pna).strip().upper()) &
                (
                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == str(val_num_acao).strip().upper()) |
                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == str(val_num_acao).split("-")[0].strip().upper())
                ) &
                (df_atual["Codigo_Atividade"].astype(str).str.strip() != "")
            ]
            
            # 2. Localiza o maior número ATVxx usado por ESTA UF para esta ação
            import re
            maior_num_atv = 0
            for cod_exist in df_atvs_acao_uf["Codigo_Atividade"].dropna().unique():
                match = re.search(r'ATV(\d+)', str(cod_exist).upper())
                if match:
                    num_extraido = int(match.group(1))
                    if num_extraido > maior_num_atv:
                        maior_num_atv = num_extraido
            
            # 3. Monta o código oficial canônico: CEN001-2026-SP-ATV01
            cod_base_acao = val_num_acao if "-" in str(val_num_acao) else f"{val_num_acao}-{val_ano}"
            prox_num_atv_str = f"ATV{maior_num_atv + 1:02d}"
            codigo_novo_sugerido = f"{cod_base_acao}-{uf_filtro_pna}-{prox_num_atv_str}"
            
            opcoes_atvs_existentes = []
            mapa_dados_atv_existente = {}
            
            for cod_unic in sorted(df_atvs_acao_uf["Codigo_Atividade"].dropna().unique()):
                linhas_deste_cod = df_atvs_acao_uf[df_atvs_acao_uf["Codigo_Atividade"] == cod_unic]
                nome_deste_cod = str(linhas_deste_cod["Nome da Atividade"].iloc[0]).strip()
                label_opc = f"{cod_unic} — {nome_deste_cod}"
                opcoes_atvs_existentes.append(label_opc)
                mapa_dados_atv_existente[label_opc] = linhas_deste_cod.iloc[0]
            
            # 🚀 CHAVES DINÂMICAS COM {val_num_acao} PARA RESETAR AO TROCAR DE AÇÃO
            modo_codigo = st.radio(
                "Definição da Atividade:", 
                ["➕ Criar Nova Atividade", "🔗 Vincular a Atividade já Existente (Mesma Equipe/Missão)"],
                horizontal=True,
                key=f"radio_modo_cod_atv_{val_num_acao}"
            )
            
            nome_atv_prefill = ""
            if modo_codigo == "➕ Criar Nova Atividade":
                codigo_atividade = st.text_input(
                    "Código Gerado Automaticamente:", 
                    value=codigo_novo_sugerido, 
                    key=f"input_novo_cod_atv_{val_num_acao}_{prox_num_atv_str}"
                ).strip().upper()
                st.caption(f"💡 Este código agrupará todos os servidores que participarem desta nova atividade.")
            else:
                if not opcoes_atvs_existentes:
                    st.warning(f"⚠️ Nenhuma atividade cadastrada anteriormente para a Ação {val_num_acao}. Um novo código foi gerado.")
                    codigo_atividade = codigo_novo_sugerido
                else:
                    atv_escolhida_lbl = st.selectbox(
                        "Selecione a Atividade Existente para integrar a equipe:", 
                        opcoes_atvs_existentes, 
                        key=f"sel_atv_existente_{val_num_acao}"
                    )
                    dados_atv_sel = mapa_dados_atv_existente[atv_escolhida_lbl]
                    codigo_atividade = str(dados_atv_sel["Codigo_Atividade"]).strip().upper()
                    nome_atv_prefill = str(dados_atv_sel.get("Nome da Atividade", "")).strip()
                    st.success(f"✅ Integrando à atividade **{codigo_atividade}**. Dados gerais espelhados.")

            nome_atividade = st.text_input(
                "Nome da Atividade / Operação:", 
                value=nome_atv_prefill if nome_atv_prefill else (str(registro_selecionado["Nome da Atividade"]) if registro_selecionado is not None else ""), 
                key=f"atv_nome_input_{val_num_acao}_{codigo_atividade}"
            ).strip()
            
            lista_andamentos_atividade = ["Prevista", "Concluída"]
            try: idx_and_atv = lista_andamentos_atividade.index(registro_selecionado["Andamento"]) if registro_selecionado is not None else 0
            except: idx_and_atv = 0
            andamento = st.selectbox("Andamento da Atividade", lista_andamentos_atividade, index=idx_and_atv, key="atv_sel_andamento")

        with aba2:
            st.text_input("Indicador (Automático)", value=val_indicador, disabled=True)
            resultado_indicador = st.text_input("Resultado do Indicador (Aferição Real):", value=str(registro_selecionado["Resultado_Indicador"]) if registro_selecionado is not None else "", key="atv_res_ind")
            doc_probatorio = st.text_input("Doc_Probatorio_Exec (SEI):", value=str(registro_selecionado["Doc_Probatorio_Exec"]) if registro_selecionado is not None else "", key="atv_doc_sei")
            uf_acao = st.text_input("UF da Ação PNAPA", value=str(uf_usuario if uf_usuario != "Acesso Restrito" else "SP"), disabled=True)
            st.text_input("Importância da Atividade (Herdada)", value=importancia, disabled=True)
            
            tema = st.selectbox("Tema da Atividade", LISTA_TEMAS, key="atv_sel_tema")
            objetivo = st.selectbox("Objetivo da Atividade", LISTA_OBJETIVOS, key="atv_sel_obj")
            tipo_atividade = st.selectbox("Tipo de Atividade", LISTA_TIPOS_ATIVIDADE, key="atv_sel_tipo")
            periculosidade = st.selectbox("Periculosidade/Insalubridade", LISTA_PERIGOS, key="atv_sel_perigo")

        with aba3:
            st.markdown("##### 👥 Recursos Humanos & Liderança da Operação")
            
            uf_filtro_servidor = uf_usuario if uf_usuario != "Acesso Restrito" else "SP"
            df_servidores_filtrados = df_servidores[df_servidores["UF_Servidor"] == uf_filtro_servidor]
            lista_nomes_servidores = sorted(df_servidores_filtrados["Servidor"].dropna().unique().tolist()) if not df_servidores_filtrados.empty else [email_logado]
            
            # 🚀 1. SELEÇÃO DO SERVIDOR (PRIMEIRO)
            c_rh1, c_rh2 = st.columns(2)
            with c_rh1:
                servidor = st.selectbox("Servidor Integrante / Responsável:", lista_nomes_servidores, key=f"atv_sel_servidor_{val_num_acao}")

            # 🚀 2. FUNÇÃO NO CAMPO COM SUGESTÃO AUTOMÁTICA REATIVA (SEGUNDO)
            with c_rh2:
                eh_ponto_focal = bool(ponto_focal_estado and str(servidor).strip().lower() == str(ponto_focal_estado).strip().lower())
                idx_funcao_sugerida = 0 if eh_ponto_focal else 1
                
                funcao_campo = st.selectbox(
                    "Função na Atividade de Campo:", 
                    LISTA_FUNCOES_CAMPO, 
                    index=idx_funcao_sugerida, 
                    key=f"atv_funcao_campo_{val_num_acao}_{servidor}_{codigo_atividade}"
                )

            if not df_servidores_filtrados.empty and servidor in df_servidores_filtrados["Servidor"].values:
                dados_serv_linha = df_servidores_filtrados[df_servidores_filtrados["Servidor"] == servidor].iloc[0]
                uf_servidor = str(dados_serv_linha.get("UF_Servidor", uf_filtro_servidor))
                lotacao = str(dados_serv_linha.get("Lotacao", "Sede Superintendência"))
                equipe_emergencia = str(dados_serv_linha.get("Equipe_Emergencias", "Não"))
            else:
                uf_servidor, lotacao, equipe_emergencia = uf_filtro_servidor, "Sede Superintendência", "Não"

            st.text_input("UF do Servidor (Automático)", value=uf_servidor, disabled=True)
            st.text_input("Lotação (Automático)", value=lotacao, disabled=True)
            st.text_input("Faz parte da Equipe de Emergências? (Automático)", value=equipe_emergencia, disabled=True)
            num_pcdp = st.text_input("Número da PCDP", value=str(registro_selecionado["Número da PCDP"]) if registro_selecionado is not None else "", key="atv_num_pcdp")
            
            st.markdown("<p style='font-weight: bold; margin-top:10px; color:#03170a;'>📍 Geolocalização da Atividade</p>", unsafe_allow_html=True)
            pais = st.text_input("País", value="Brasil", disabled=True)
            
            uf_ocorrencia = st.selectbox("UF Onde Ocorreu/Ocorrerá a Ação", LISTA_UFS_COMPLETA, key="atv_sel_uf_ocorrencia")
            estado_local = MAPEAMENTO_ESTADOS_COMPLETO[uf_ocorrencia]
            st.text_input("Estado_Local_Acao (Automático)", value=estado_local, disabled=True)
            
            lista_municipios_uf = obter_municipios_ibge(uf_ocorrencia)
            municipio = st.selectbox("Municipio Onde Ocorreu/Ocorrerá a Ação", lista_municipios_uf if lista_municipios_uf else ["Superintendência Sede"], key="atv_sel_municipio")

        with aba4:
            dt_inicio = st.date_input("Data de Início:", value=val_dt_inicio, format="DD/MM/YYYY", key="atv_dt_ini")
            dt_termino = st.date_input("Data de Término:", value=val_dt_termino, format="DD/MM/YYYY", key="atv_dt_fim")
            
            c_d1_ins, c_d2_ins = st.columns(2)
            with c_d1_ins:
                dias_plan = st.number_input("Dias_Gastos_Plan", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Plan"), step=0.5, format="%.1f", key="atv_dias_pl")
            with c_d2_ins:
                dias_exec = st.number_input("Dias_Gastos_Exec", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Exec"), step=0.5, format="%.1f", key="atv_dias_ex")
                
            origem_recurso = st.selectbox("Origem do Recurso", LISTA_ORIGENS_RECURSO, key="atv_sel_origem")
            
            st.markdown("<p style='font-weight: bold; margin-top:15px; color:#03170a;'>Valores Orçamentários (Planejado vs Executado)</p>", unsafe_allow_html=True)
            c_pl, c_ex = st.columns(2)
            with c_pl:
                st.caption("Planejado")
                rec_p_diarias = st.number_input("Rec_Plan_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Diarias"), step=50.0, format="%.2f", key="atv_rpd")
                rec_p_passagens = st.number_input("Rec_Plan_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Passagens"), step=50.0, format="%.2f", key="atv_rpp")
                rec_p_outras = st.number_input("Rec_Plan_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Outras_Despesas"), step=50.0, format="%.2f", key="atv_rpo")
                calc_tot_p_atv = float(rec_p_diarias + rec_p_passagens + rec_p_outras)
                st.number_input("Rec_Plan_Total (Soma Automática)", value=calc_tot_p_atv, disabled=True, format="%.2f")

            with c_ex:
                st.caption("Executado")
                rec_e_diarias = st.number_input("Rec_Exec_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Diarias"), step=50.0, format="%.2f", key="atv_red")
                rec_e_passagens = st.number_input("Rec_Exec_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Passagens"), step=50.0, format="%.2f", key="atv_rep")
                rec_e_outras = st.number_input("Rec_Exec_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Outras_Despesas"), step=50.0, format="%.2f", key="atv_reo")
                calc_tot_e_atv = float(rec_e_diarias + rec_e_passagens + rec_e_outras)
                st.number_input("Rec_Exec_Total (Soma Automática)", value=calc_tot_e_atv, disabled=True, format="%.2f")

        with aba5:
            obs = st.text_area("Observações", value=str(registro_selecionado["Observações"]) if registro_selecionado is not None else "", key="atv_obs")
            justificativa = ""
            st.info("ℹ️ Campo Justificativa ocultado. Regra aplicada: Habilitado apenas para cadastro de Ações.")

        papel_inst = papel_estado_acao if papel_estado_acao in LISTA_PAPEIS_INSTITUCIONAIS else ""
        meta_indicador = ""

    st.markdown("<br>", unsafe_allow_html=True)
    btn_enviar_individual = st.button("🚀 Gravar Registro no SharePoint", type="primary", key="btn_gravar_individual_reativo")

    # =================================================================
    # PROCESSAMENTO DO ENVIO: INDIVIDUAL OU EM LOTE
    # =================================================================
    if btn_enviar_individual:
        bloquear_envio = False
        
        # -------------------------------------------------------------
        # 🔒 1. VALIDAÇÃO DE UNICIDADE DA AÇÃO ESTADUAL (POR ANO E UF)
        # -------------------------------------------------------------
        if nivel_selecionado == "Ação":
            coord_op_final = ""
            cod_atv_final = ""
            
            cod_puro = str(val_num_acao).split("-")[0].strip().upper()
            cod_comp = str(val_num_acao).strip().upper()
            uf_limpa = str(uf_filtro_pna).strip().upper()
            ano_alvo_str = str(val_ano).strip()
            
            # Valida se já existe uma Ação com este código, neste mesmo ANO e nesta mesma UF
            acao_estadual_ja_existe = df_atual[
                (df_atual["Nível"].astype(str).str.strip() == "Ação") &
                (df_atual["UF_Acao_PNAPA"].astype(str).str.strip().str.upper() == uf_limpa) &
                (df_atual["Ano da Ação"].astype(str).str.split('.').str[0].str.strip() == ano_alvo_str) &
                (
                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == cod_comp) |
                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == f"{cod_puro}-{ano_alvo_str}") |
                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == cod_puro)
                )
            ]
            
            if not acao_estadual_ja_existe.empty:
                st.error(f"⛔ **Ação Já Cadastrada:** A UF **{uf_limpa}** já possui planejamento registrado para a Ação **{val_num_acao}** no ano de **{ano_alvo_str}**. Para alterar o Ponto Focal, Papel ou Meta, utilize a tela de **📊 Visualizar Base**.")
                bloquear_envio = True

        # -------------------------------------------------------------
        # 🔒 2. VALIDAÇÃO DE LIDERANÇA ÚNICA NA ATIVIDADE DE CAMPO
        # -------------------------------------------------------------
        elif nivel_selecionado == "Atividade":
            coord_op_final = funcao_campo
            cod_atv_final = str(codigo_atividade)
            
            if funcao_campo == "Coordenador de Campo":
                coordenadores_existentes = df_atual[
                    (df_atual["Nível"].astype(str).str.strip() == "Atividade") &
                    (df_atual["Codigo_Atividade"].astype(str).str.strip().str.upper() == str(codigo_atividade).strip().upper()) &
                    (df_atual["Coordenador_Operacao"].astype(str).str.strip() == "Coordenador de Campo")
                ]
                if not coordenadores_existentes.empty:
                    nome_outro_coord = coordenadores_existentes["Servidor"].iloc[0]
                    st.error(f"⛔ **Conflito de Liderança:** A atividade `{codigo_atividade}` já possui **{nome_outro_coord}** cadastrado como Coordenador de Campo. Uma mesma atividade só pode ter 1 coordenador.")
                    bloquear_envio = True

        # -------------------------------------------------------------
        # 🚀 3. DISPARO DO ENVIO
        # -------------------------------------------------------------
        if not bloquear_envio:
            payload_unico = payload_gerador(
                val_ano, val_num_acao, val_nome_acao, val_indicador, nivel_selecionado, 
                nome_atividade, andamento, resultado_indicador, doc_probatorio, uf_acao, 
                importancia, tema, objetivo, tipo_atividade, periculosidade, servidor, 
                uf_servidor, lotacao, equipe_emergencia, num_pcdp, pais, uf_ocorrencia, 
                estado_local, municipio, dt_inicio, dt_termino, dias_plan, dias_exec, 
                origem_recurso, rec_p_diarias, rec_p_passagens, rec_p_outras, rec_e_diarias, 
                rec_e_passagens, rec_e_outras, obs, justificativa, id_atual, modo, df_atual,
                papel_institucional=papel_inst, coordenador_operacao=coord_op_final, meta_indicador=meta_indicador,
                codigo_atividade=cod_atv_final
            )
            executar_envio_sharepoint([payload_unico])

    # 2. CARGA EM LOTE (ATIVIDADE)
    if modo == "➕ Inserir Nova Linha" and nivel_selecionado == "Atividade":
        st.markdown("---")
        with st.popover("👥 Deseja cadastrar esta atividade para múltiplos servidores? (Carga em Lote)", use_container_width=True):
            st.markdown("### 👥 Cadastro Multi-Servidor / Lote")
            
            lista_servidores_lote = st.text_area(
                "Digite os nomes dos Servidores (um por linha):", 
                value=servidor,
                help="Cada linha gerará uma atividade idêntica no SharePoint com o mesmo Código de Atividade."
            )
            
            servidores_finais = [s.strip() for s in lista_servidores_lote.split("\n") if s.strip()]
            st.info(f"📋 Serão gerados **{len(servidores_finais)}** registros simultâneos para o código `{codigo_atividade}`.")
            
            st.markdown("---")
            st.markdown("### 🎯 Espelhamento de Campos")
            st.caption("Desmarque os campos que deseja enviar EM BRANCO para edição posterior:")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if st.button("✓ Marcar Todos", key="btn_lote_marcar_todos"): 
                    st.session_state["chk_lote_all"] = True
            with col_c2:
                if st.button("✕ Desmarcar Todos", key="btn_lote_desmarcar_todos"): 
                    st.session_state["chk_lote_all"] = False
            
            status_padrao = st.session_state.get("chk_lote_all", True)
            
            espelhar_detalhes = st.checkbox("Espelhar Detalhes da Atividade e Documentos SEI", value=status_padrao, key="lote_chk_detalhes")
            espelhar_local = st.checkbox("Espelhar Localidade (País, UF, Estado, Município)", value=status_padrao, key="lote_chk_local")
            espelhar_crono = st.checkbox("Espelhar Cronograma (Datas e Dias Gastos)", value=status_padrao, key="lote_chk_crono")
            espelhar_custos = st.checkbox("Espelhar Custos (Valores Planejados e Executados)", value=status_padrao, key="lote_chk_custos")
            espelhar_just = st.checkbox("Espelhar Justificativas e Observações", value=status_padrao, key="lote_chk_just")
            
            if st.button("🔥 Disparar Carga em Lote para o SharePoint", type="primary", use_container_width=True, key="btn_disparar_lote_final"):
                payloads_lote = []
                id_base_calculado = int(pd.to_numeric(df_atual["Id"], errors='coerce').dropna().max() + 1) if not df_atual.empty else 1
                
                for idx, serv_lote in enumerate(servidores_finais):
                    id_loop = str(id_base_calculado + idx)
                    funcao_lote = funcao_campo if serv_lote == servidor else "Apoio de Campo"
                    
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
                        "Codigo_Atividade": str(codigo_atividade),
                        "Ano da Ação": int(val_ano) if val_ano else 2026,
                        "Número da Ação PNAPA": str(val_num_acao), 
                        "Nome da Ação PNAPA": str(val_nome_acao), 
                        "Nível": nivel_selecionado, 
                        "Papel_Institucional": papel_inst,
                        "Coordenador_Operacao": funcao_lote,
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

# --- TELA 5: GERENCIAR UNIDADES (COM PREENCHIMENTO AUTOMÁTICO E CASCATA) ---
elif modo == "🏢 Gerenciar Unidades":
    st.markdown("<h3 style='color: #03170a;'>🏢 Gerenciamento de Unidades / Lotações (Tabela Auxiliar)</h3>", unsafe_allow_html=True)
    st.caption("Catálogo corporativo de setores e unidades de lotação dos servidores.")
    
    # 1. VISUALIZAÇÃO CONDICIONAL POR PERFIL
    df_visualizacao_uni = df_lotacoes if perfil_usuario == "Administrador" else df_lotacoes[df_lotacoes["UF"] == uf_usuario]
    
    st.write("#### 📋 Unidades Ativas Cadastradas")
    if df_visualizacao_uni.empty:
        st.info(f"Nenhuma unidade cadastrada para a UF {uf_usuario}.")
    else:
        colunas_validas = [col for col in ["ID_UF", "UF", "Unidade"] if col in df_visualizacao_uni.columns]
        df_limpo_uni = df_visualizacao_uni[colunas_validas]
        def estilar_uni(linha): return [f'background-color: {"#f0f5df" if linha.name % 2 == 0 else "#ffffff"}; color: #03170a;' for _ in linha]
        st.dataframe(df_limpo_uni.reset_index(drop=True).style.apply(estilar_uni, axis=1), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    t_add, t_edit, t_del = st.tabs(["➕ Adicionar Unidade", "📝 Alterar Unidade", "🗑️ Excluir Unidade"])

    # =================================================================
    # ABA 1: ADICIONAR NOVA UNIDADE
    # =================================================================
    with t_add:
        st.markdown("##### ➕ Cadastro de Nova Lotação")
        c_add1, c_add2 = st.columns(2)
        with c_add1:
            if perfil_usuario == "Administrador":
                uf_uni_add = st.selectbox("UF / Órgão da Unidade:", LISTA_UFS_COMPLETA, key="uni_add_uf")
            else:
                st.text_input("UF da Lotação (Travada):", value=uf_usuario, disabled=True, key="uni_add_uf_rep")
                uf_uni_add = uf_usuario
        with c_add2:
            nova_uni = st.text_input("Nome da Nova Unidade (Ex: Nupaem-SP, SUPES-RJ):", key="uni_add_nome").strip()
            
        if st.button("🚀 Gravar Unidade", type="primary", key="btn_salvar_nova_uni"):
            if not nova_uni:
                st.error("⚠️ O nome da unidade é obrigatório.")
            else:
                with st.spinner("Sincronizando nova unidade com o SharePoint..."):
                    executar_api_unidades({"Acao": "Inserir", "UF": uf_uni_add, "Unidade": nova_uni})
                    time.sleep(2)
                    st.cache_data.clear()
                st.success(f"✅ Unidade '{nova_uni}' salva com sucesso!")
                st.rerun()

    # =================================================================
    # ABA 2: ALTERAR UNIDADE (PREENCHIMENTO REATIVO E CASCATA COMPLETA)
    # =================================================================
    with t_edit:
        st.markdown("##### 📝 Alteração de Dados da Unidade")
        
        # 1. Filtro de UF para o Administrador localizar a unidade
        if perfil_usuario == "Administrador":
            lista_ufs_uni = sorted(df_lotacoes["UF"].dropna().unique().tolist())
            uf_filtrada_edit = st.selectbox("1. Filtrar Unidades por UF/Órgão:", lista_ufs_uni, key="uf_filt_edit")
        else:
            uf_filtrada_edit = uf_usuario

        df_unidades_filtradas = df_lotacoes[df_lotacoes["UF"] == uf_filtrada_edit]
            
        if df_unidades_filtradas.empty:
            st.warning(f"⚠️ Nenhuma unidade encontrada para a UF: {uf_filtrada_edit}")
        else:
            # 2. Dropdown de Seleção da Unidade
            lista_nomes_unidades = sorted(df_unidades_filtradas["Unidade"].dropna().unique().tolist())
            sel_uni = st.selectbox("2. Selecione a Unidade para visualizar/alterar:", lista_nomes_unidades, key="uni_sel_edit")
            
            linha_filtrada = df_unidades_filtradas[df_unidades_filtradas["Unidade"].astype(str).str.strip() == str(sel_uni).strip()]
            
            if not linha_filtrada.empty:
                dados_alvo_uni = linha_filtrada.iloc[0]
                id_uf_edit = int(float(dados_alvo_uni["ID_UF"]))
                val_atual_uf_uni = str(dados_alvo_uni.get("UF", uf_filtrada_edit)).strip()
                val_atual_nome_uni = str(dados_alvo_uni.get("Unidade", sel_uni)).strip()

                st.markdown(f"#### 🏢 Ficha da Unidade: **{val_atual_nome_uni}** `(ID: {id_uf_edit})`")
                st.caption("Modificações nesta unidade atualizarão automaticamente a tabela de Equipes e as Atividades vinculadas na base principal.")

                # Campos com chaves dinâmicas para recarregamento instantâneo
                col_ed_u1, col_ed_u2 = st.columns(2)
                with col_ed_u1:
                    if perfil_usuario == "Administrador":
                        try:
                            idx_uf_ed = LISTA_UFS_COMPLETA.index(val_atual_uf_uni)
                        except ValueError:
                            idx_uf_ed = 0
                        nova_uf_uni = st.selectbox(
                            "UF / Órgão da Unidade:", 
                            LISTA_UFS_COMPLETA, 
                            index=idx_uf_ed, 
                            key=f"ed_uf_uni_sel_{id_uf_edit}"
                        )
                    else:
                        st.text_input(
                            "UF da Lotação (Travada para Editor Regional):", 
                            value=val_atual_uf_uni, 
                            disabled=True, 
                            key=f"ed_uf_uni_dis_{id_uf_edit}"
                        )
                        nova_uf_uni = val_atual_uf_uni

                with col_ed_u2:
                    novo_nome_uni = st.text_input(
                        "Nome da Unidade:", 
                        value=val_atual_nome_uni, 
                        key=f"ed_nome_uni_txt_{id_uf_edit}"
                    ).strip()

                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- DISPARO DA ATUALIZAÇÃO EM CASCATA ---
                from concurrent.futures import ThreadPoolExecutor

                if st.button("💾 Salvar Alterações e Sincronizar Equipes/Base Principal", type="primary", key=f"btn_salvar_uni_{id_uf_edit}"):
                    if not novo_nome_uni:
                        st.error("⚠️ O Nome da Unidade não pode ficar em branco.")
                    else:
                        # 1. Atualiza a Tabela Auxiliar de Unidades
                        with st.spinner(f"1/3 Atualizando Unidade '{novo_nome_uni}' no SharePoint..."):
                            executar_api_unidades({
                                "Acao": "Editar", 
                                "ID_UF": id_uf_edit, 
                                "UF": nova_uf_uni, 
                                "Unidade": novo_nome_uni
                            })

                        # 2. Atualiza em Cascata os Servidores (Equipes.xlsx)
                        servidores_afetados = df_servidores[
                            (df_servidores["Lotacao"].astype(str).str.strip() == str(sel_uni).strip()) &
                            (df_servidores["UF_Servidor"].astype(str).str.strip() == str(val_atual_uf_uni).strip())
                        ]
                        qtd_srv_afetados = len(servidores_afetados)

                        if qtd_srv_afetados > 0:
                            with st.spinner(f"2/3 Atualizando lotação de {qtd_srv_afetados} servidor(es) na tabela de equipes..."):
                                for _, srv_row in servidores_afetados.iterrows():
                                    payload_srv_cascata = {
                                        "Acao": "Editar",
                                        "ID_SERV": int(float(srv_row["ID_SERV"])),
                                        "Servidor": str(srv_row.get("Servidor", "")),
                                        "UF_Servidor": str(nova_uf_uni),
                                        "Lotacao": str(novo_nome_uni),
                                        "Equipe_Emergencias": str(srv_row.get("Equipe_Emergencias", "Não")),
                                        "Fiscal": str(srv_row.get("Fiscal", "Não")),
                                        "AEAC": str(srv_row.get("AEAC", "Não")),
                                        "E_mail": str(srv_row.get("E_mail", "")),
                                        "Funcao": str(srv_row.get("Funcao", "")),
                                        "Perfil": str(srv_row.get("Perfil", "Visualização")),
                                        "Token": str(srv_row.get("Token", ""))
                                    }
                                    executar_api_equipes(payload_srv_cascata)

                        # 3. Atualiza em Cascata as Atividades na Planilha Principal (Macro)
                        linhas_macro_afetadas = df_atual[
                            (df_atual["Lotação"].astype(str).str.strip() == str(sel_uni).strip()) &
                            (df_atual["UF_Servidor"].astype(str).str.strip() == str(val_atual_uf_uni).strip())
                        ]
                        qtd_macro_afetadas = len(linhas_macro_afetadas)
                        sucessos_macro = 0

                        if qtd_macro_afetadas > 0:
                            with st.spinner(f"3/3 Atualizando {qtd_macro_afetadas} atividade(s) vinculadas na Planilha Principal..."):
                                payloads_cascata_macro = []
                                for _, row_orig in linhas_macro_afetadas.iterrows():
                                    p_item = {col: row_orig[col] for col in df_atual.columns if col in row_orig}
                                    p_item["Acao"] = "Editar"
                                    p_item["Id"] = str(row_orig["Id"])
                                    p_item["Lotação"] = str(novo_nome_uni)
                                    p_item["UF_Servidor"] = str(nova_uf_uni)
                                    
                                    payload_sanit = {
                                        k: (0.0 if pd.isna(v) and ("Rec_" in k or "Dias_" in k) else ("" if pd.isna(v) else v)) 
                                        for k, v in p_item.items()
                                    }
                                    payloads_cascata_macro.append(payload_sanit)

                                def enviar_req_macro(p):
                                    try:
                                        r = requests.post(URL_FLOW_PRINCIPAL, json=p, timeout=20)
                                        return 1 if r.status_code in [200, 202] else 0
                                    except:
                                        return 0

                                with ThreadPoolExecutor(max_workers=10) as executor:
                                    resultados = list(executor.map(enviar_req_macro, payloads_cascata_macro))
                                    sucessos_macro = sum(resultados)

                        # 4. Limpeza de cache e feedback
                        time.sleep(2.0)
                        st.cache_data.clear()
                        if "df" in st.session_state:
                            del st.session_state.df

                        msg_sucesso = f"🎉 Unidade **{novo_nome_uni}** atualizada com sucesso!"
                        if qtd_srv_afetados > 0 or qtd_macro_afetadas > 0:
                            msg_sucesso += f" ({qtd_srv_afetados} servidores e {sucessos_macro}/{qtd_macro_afetadas} atividades sincronizados em cascata)."
                        st.success(msg_sucesso)
                        
                        time.sleep(1.5)
                        st.rerun()

    # =================================================================
    # ABA 3: EXCLUIR UNIDADE (COM VERIFICAÇÃO DE DEPENDÊNCIAS)
    # =================================================================
    with t_del:
        st.markdown("##### 🗑️ Exclusão de Unidade")
        if perfil_usuario == "Administrador":
            uf_filtrada_del = st.selectbox("1. Filtrar Unidades por UF/Órgão:", sorted(df_lotacoes["UF"].dropna().unique().tolist()), key="uf_filt_del")
        else:
            uf_filtrada_del = uf_usuario

        df_unidades_filtradas_del = df_lotacoes[df_lotacoes["UF"] == uf_filtrada_del]
            
        if not df_unidades_filtradas_del.empty:
            del_uni = st.selectbox("2. Selecione a Unidade para REMOVER:", df_unidades_filtradas_del["Unidade"].tolist(), key="uni_sel_del")
            linha_filtrada_del = df_unidades_filtradas_del[df_unidades_filtradas_del["Unidade"].astype(str).str.strip() == str(del_uni).strip()]
            
            if not linha_filtrada_del.empty:
                id_uf_del = int(float(linha_filtrada_del["ID_UF"].iloc[0]))
                
                # Alerta de dependências (se houver servidores ativos nela)
                servidores_nesta_unidade = df_servidores[
                    (df_servidores["Lotacao"].astype(str).str.strip() == str(del_uni).strip()) &
                    (df_servidores["UF_Servidor"].astype(str).str.strip() == str(uf_filtrada_del).strip())
                ]
                
                if not servidores_nesta_unidade.empty:
                    st.warning(f"⚠️ **Atenção:** Existem **{len(servidores_nesta_unidade)} servidor(es)** cadastrados nesta unidade. Recomenda-se remanejá-los antes de excluir.")
                
                if st.button("❌ Confirmar Exclusão Permanente", disabled=not st.checkbox(f"Confirmo que desejo excluir a unidade {del_uni} ({uf_filtrada_del})", key=f"chk_del_uni_{id_uf_del}")):
                    with st.spinner("Removendo registro do SharePoint..."):
                        executar_api_unidades({"Acao": "Excluir", "ID_UF": id_uf_del})
                        time.sleep(2)
                        st.cache_data.clear()
                    st.success(f"💥 Unidade '{del_uni}' removida com sucesso!")
                    time.sleep(1.5)
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

    # =================================================================
    # ABA 2: ALTERAR CADASTRO (PREENCHIMENTO AUTOMÁTICO REATIVO)
    # =================================================================
    with ts_edit:
        if not df_visualizacao_srv.empty:
            # 1. Seletor do Servidor Alvo
            lista_servidores_edit = sorted(df_visualizacao_srv["Servidor"].dropna().unique().tolist())
            sel_srv = st.selectbox("Selecione o Servidor para visualizar/alterar:", lista_servidores_edit, key="srv_sel_edit")
            
            # 2. Extração dos Dados Atuais do Servidor Selecionado
            dados_atuais_srv = df_visualizacao_srv[df_visualizacao_srv["Servidor"] == sel_srv].iloc[0]
            id_srv_edit = int(float(dados_atuais_srv["ID_SERV"]))
            
            # Dados atuais brutos
            val_atual_nome = str(dados_atuais_srv.get("Servidor", "")).strip()
            val_atual_email = str(dados_atuais_srv.get("E_mail", "")).strip()
            val_atual_uf = str(dados_atuais_srv.get("UF_Servidor", uf_usuario)).strip()
            val_atual_lotacao = str(dados_atuais_srv.get("Lotacao", "")).strip()
            val_atual_funcao = str(dados_atuais_srv.get("Funcao", "")).strip()
            val_atual_token = str(dados_atuais_srv.get("Token", "")).strip()
            val_atual_emerg = str(dados_atuais_srv.get("Equipe_Emergencias", "Não")).strip().capitalize()
            val_atual_fiscal = str(dados_atuais_srv.get("Fiscal", "Não")).strip().capitalize()
            val_atual_aeac = str(dados_atuais_srv.get("AEAC", "Não")).strip().capitalize()
            val_atual_perfil = str(dados_atuais_srv.get("Perfil", "Visualização")).strip()

            st.markdown(f"#### 👤 Ficha Cadastral: **{val_atual_nome}** `(ID: {id_srv_edit})`")
            st.caption("Altere os campos necessários abaixo. As alterações serão refletidas em cascata na base macro.")

            # --- LINHA 1: IDENTIFICAÇÃO BÁSICA ---
            col_id1, col_id2 = st.columns(2)
            with col_id1:
                novo_nome_srv = st.text_input(
                    "Nome Completo do Servidor:", 
                    value=val_atual_nome, 
                    key=f"srv_ed_nome_{id_srv_edit}"
                ).strip()
            with col_id2:
                novo_email = st.text_input(
                    "E-mail Institucional (@ibama.gov.br):", 
                    value=val_atual_email, 
                    key=f"srv_ed_email_{id_srv_edit}"
                ).strip()

            # --- LINHA 2: UF E LOTAÇÃO (COM TRAVA DE PERFIL) ---
            col_loc1, col_loc2 = st.columns(2)
            with col_loc1:
                if perfil_usuario == "Administrador":
                    try:
                        idx_uf = LISTA_UFS_COMPLETA.index(val_atual_uf)
                    except ValueError:
                        idx_uf = 0
                    nova_uf_srv = st.selectbox(
                        "UF/Órgão de Lotação:", 
                        LISTA_UFS_COMPLETA, 
                        index=idx_uf, 
                        key=f"srv_ed_uf_{id_srv_edit}"
                    )
                else:
                    st.text_input(
                        "UF de Lotação (Travada para Editor Regional):", 
                        value=val_atual_uf, 
                        disabled=True, 
                        key=f"srv_ed_uf_dis_{id_srv_edit}"
                    )
                    nova_uf_srv = val_atual_uf

            with col_loc2:
                # Carrega as unidades disponíveis para a UF selecionada
                unidades_disponiveis = df_lotacoes[df_lotacoes["UF"] == nova_uf_srv]["Unidade"].tolist()
                if not unidades_disponiveis:
                    unidades_disponiveis = ["Sede Superintendência"]
                
                try:
                    idx_lot = unidades_disponiveis.index(val_atual_lotacao)
                except ValueError:
                    idx_lot = 0
                
                nova_lot_srv = st.selectbox(
                    "Unidade de Lotação Relacionada:", 
                    unidades_disponiveis, 
                    index=idx_lot, 
                    key=f"srv_ed_lot_{id_srv_edit}_{nova_uf_srv}"
                )

            # --- LINHA 3: CARGO E CREDENCIAIS ---
            col_cr1, col_cr2 = st.columns(2)
            with col_cr1:
                nova_funcao = st.text_input(
                    "Função / Cargo Interno:", 
                    value=val_atual_funcao, 
                    key=f"srv_ed_funcao_{id_srv_edit}"
                )
            with col_cr2:
                novo_token = st.text_input(
                    "Token/Senha de Acesso:", 
                    value=val_atual_token, 
                    type="password", 
                    key=f"srv_ed_token_{id_srv_edit}"
                )

            # --- LINHA 4: ATRIBUTOS OPERACIONAIS ---
            col_eq_ed1, col_eq_ed2, col_eq_ed3 = st.columns(3)
            
            with col_eq_ed1:
                idx_emerg = 0 if val_atual_emerg == "Sim" else 1
                n_eq_emerg = st.selectbox(
                    "Equipe de Emergências?", 
                    ["Sim", "Não"], 
                    index=idx_emerg, 
                    key=f"srv_ed_emerg_{id_srv_edit}"
                )
            with col_eq_ed2:
                idx_fisc = 0 if val_atual_fiscal == "Sim" else 1
                n_eq_fiscal = st.selectbox(
                    "Fiscal de Campo?", 
                    ["Sim", "Não"], 
                    index=idx_fisc, 
                    key=f"srv_ed_fiscal_{id_srv_edit}"
                )
            with col_eq_ed3:
                idx_aeac = 0 if val_atual_aeac == "Sim" else 1
                n_eq_aeac = st.selectbox(
                    "Possui AEAC?", 
                    ["Sim", "Não"], 
                    index=idx_aeac, 
                    key=f"srv_ed_aeac_{id_srv_edit}"
                )
            
            # --- LINHA 5: PERFIL DE ACESSO ---
            if perfil_usuario == "Administrador":
                try:
                    idx_perf = LISTA_PERFIS.index(val_atual_perfil)
                except ValueError:
                    idx_perf = 0
                n_perf = st.selectbox(
                    "Perfil de Acesso no Sistema:", 
                    LISTA_PERFIS, 
                    index=idx_perf, 
                    key=f"srv_ed_perf_{id_srv_edit}"
                )
            else:
                perfis_editor = ["Visualização", "Editor Regional"]
                idx_perf = 1 if val_atual_perfil == "Editor Regional" else 0
                n_perf = st.selectbox(
                    "Perfil de Acesso no Sistema:", 
                    perfis_editor, 
                    index=idx_perf, 
                    key=f"srv_ed_perf_{id_srv_edit}"
                )

            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- DISPARO DE ATUALIZAÇÃO COM CASCATA ULTRA-RÁPIDA (PARALELA) ---
            from concurrent.futures import ThreadPoolExecutor

            if st.button("💾 Salvar Modificações e Sincronizar Base Principal", type="primary", key=f"btn_salvar_srv_{id_srv_edit}"):
                if not novo_nome_srv:
                    st.error("⚠️ O Nome do Servidor não pode ficar vazio.")
                else:
                    # 1. Payload da tabela de Equipes
                    payload_editar_srv = {
                        "Acao": "Editar", 
                        "ID_SERV": id_srv_edit, 
                        "Servidor": novo_nome_srv, 
                        "UF_Servidor": nova_uf_srv, 
                        "Lotacao": nova_lot_srv, 
                        "Equipe_Emergencias": n_eq_emerg, 
                        "Fiscal": n_eq_fiscal, 
                        "AEAC": n_eq_aeac, 
                        "E_mail": novo_email, 
                        "Funcao": nova_funcao, 
                        "Perfil": n_perf, 
                        "Token": novo_token
                    }
                    
                    with st.spinner(f"1/2 Atualizando cadastro de '{novo_nome_srv}'..."):
                        executar_api_equipes(payload_editar_srv)

                    # 2. Busca atividades vinculadas pelo NOME ANTERIOR (sel_srv)
                    linhas_servidor_macro = df_atual[df_atual["Servidor"].astype(str).str.strip() == str(sel_srv).strip()]
                    qtd_vinculadas = len(linhas_servidor_macro)
                    sucessos_cascata = 0

                    if qtd_vinculadas > 0:
                        with st.spinner(f"2/2 Atualizando {qtd_vinculadas} atividade(s) na Planilha Principal..."):
                            payloads_cascata = []
                            for _, row_orig in linhas_servidor_macro.iterrows():
                                p_item = {col: row_orig[col] for col in df_atual.columns if col in row_orig}
                                p_item["Acao"] = "Editar"
                                p_item["Id"] = str(row_orig["Id"])
                                
                                # Atualiza dados do servidor em todas as atividades
                                p_item["Servidor"] = str(novo_nome_srv)
                                p_item["UF_Servidor"] = str(nova_uf_srv)
                                p_item["Lotação"] = str(nova_lot_srv)
                                p_item["Faz parte da Equipe de Emergências"] = str(n_eq_emerg)
                                
                                # Sanitização
                                payload_sanit = {
                                    k: (0.0 if pd.isna(v) and ("Rec_" in k or "Dias_" in k) else ("" if pd.isna(v) else v)) 
                                    for k, v in p_item.items()
                                }
                                payloads_cascata.append(payload_sanit)

                            # Disparo concorrente
                            def enviar_req(p):
                                try:
                                    r = requests.post(URL_FLOW_PRINCIPAL, json=p, timeout=20)
                                    return 1 if r.status_code in [200, 202] else 0
                                except:
                                    return 0

                            with ThreadPoolExecutor(max_workers=10) as executor:
                                resultados = list(executor.map(enviar_req, payloads_cascata))
                                sucessos_cascata = sum(resultados)

                    # 3. Limpeza de cache e recarga
                    time.sleep(2.0)
                    st.cache_data.clear()
                    if "df" in st.session_state:
                        del st.session_state.df

                    if qtd_vinculadas > 0:
                        st.success(f"🎉 Cadastro atualizado e **{sucessos_cascata}/{qtd_vinculadas}** atividades sincronizadas!")
                    else:
                        st.success(f"🎉 Cadastro de **{novo_nome_srv}** atualizado com sucesso!")
                    
                    time.sleep(1.5)
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

# --- TELA AUXILIAR: GERENCIAR AÇÕES PNAPA ---
elif modo == "🗂️ Gerenciar Ações PNAPA":
    st.markdown("<h3 style='color: #03170a;'>🗂️ Catálogo Oficial de Ações PNAPA</h3>", unsafe_allow_html=True)
    st.caption("Tabela auxiliar corporativa para governança nacional, vinculação e padronização das ações.")
    
    pode_administrar_catalogo = (perfil_usuario == "Administrador") and acesso_liberado

    if df_pnapas.empty:
        st.warning("⚠️ O catálogo de Ações PNAPA está vazio no momento.")
    else:
        st.dataframe(df_pnapas, use_container_width=True, hide_index=True)

    if not pode_administrar_catalogo:
        st.info("👁️ **Modo Somente Leitura:** Como Editor Regional, você pode consultar o catálogo de ações. A criação, alteração e exclusão de Ações PNAPA são operações de governança restritas ao **Administrador**.")
    else:
        st.markdown("---")
        st.markdown("### ⚙️ Painel de Governança do Catálogo (Exclusivo Administrador)")
        
        tab_cad_pna, tab_edt_pna, tab_exc_pna = st.tabs([
            "➕ Cadastrar Nova Ação", 
            "📝 Editar Ação Existente", 
            "🗑️ Excluir Ação"
        ])
        
        # =================================================================
        # ABA 1: CADASTRAR NOVA AÇÃO
        # =================================================================
        with tab_cad_pna:
            st.markdown("##### ➕ Nova Ação PNAPA")
            c_ano, c_num = st.columns(2)
            with c_ano:
                novo_ano_pna = st.number_input("Ano da Ação", min_value=2020, max_value=2040, value=2026, step=1, key="cad_pna_ano")
            with c_num:
                novo_num_pna = st.text_input("Código/Número (Ex: CEN001)", value="", key="cad_pna_num").strip().upper()
                
            novo_nome_comp = st.text_input("Nome Completo da Ação (Descrição Oficial):", key="cad_pna_nome_comp").strip()
            novo_nome_apelido = st.text_input("Nome Resumido / Apelido (Exibição Amigável):", key="cad_pna_nome_apelido").strip()
            
            # 🚀 LIDERANÇA NACIONAL (DONO DA AÇÃO)
            st.markdown("###### 👑 Liderança Nacional da Ação")
            c_dn1, c_dn2, c_dn3 = st.columns([1, 2, 1])
            with c_dn1:
                novo_uf_dono = st.selectbox("UF/Órgão do Dono:", ["Ceneac"] + LISTA_UFS_COMPLETA, key="cad_pna_uf_dono")
            with c_dn2:
                srvs_dono_disp = df_servidores[df_servidores["UF_Servidor"] == novo_uf_dono]["Servidor"].dropna().unique().tolist()
                novo_dono_acao = st.selectbox("Servidor Especialista (Dono da Ação):", srvs_dono_disp if srvs_dono_disp else ["Guttemberg"], key="cad_pna_dono")
            with c_dn3:
                nova_meta_nac = st.number_input("Meta Global Nacional:", min_value=0.0, value=12.0, step=1.0, key="cad_pna_meta_nac")

            c_ind, c_imp = st.columns(2)
            with c_ind:
                novo_indicador = st.text_input("Indicador Associado:", key="cad_pna_ind").strip()
            with c_imp:
                nova_importancia = st.selectbox("Importância Padrão:", LISTA_IMPORTANCIA, index=0, key="cad_pna_imp")
                
            if st.button("🚀 Gravar Nova Ação no Catálogo", type="primary", key="btn_gravar_nova_acao_pna"):
                if not novo_num_pna or not novo_nome_comp:
                    st.error("⚠️ O Código e o Nome Completo da Ação são obrigatórios.")
                else:
                    chave_acao_ano = f"{novo_num_pna}-{novo_ano_pna}"
                    id_col_nome = "ID_PNAPA" if "ID_PNAPA" in df_pnapas.columns else "Id"
                    id_novo_pna = int(pd.to_numeric(df_pnapas[id_col_nome], errors='coerce').max() + 1) if not df_pnapas.empty else 1
                    
                    payload_nova_acao = {
                        "Acao": "Inserir",
                        "Id": str(id_novo_pna),
                        "ID_PNAPA": id_novo_pna,
                        "Ano": int(novo_ano_pna),
                        "Num_Acao_PNAPA": novo_num_pna,
                        "Acao_Ano": chave_acao_ano,
                        "Nome_Acao_Completo": novo_nome_comp,
                        "Nome_Acao_Apelido": novo_nome_apelido if novo_nome_apelido else novo_nome_comp,
                        "Indicador": novo_indicador,
                        "Importância": nova_importancia,
                        "UF_Dono": str(novo_uf_dono),
                        "Dono_Acao": str(novo_dono_acao),
                        "Meta_Nacional": float(nova_meta_nac)
                    }
                    
                    with st.spinner("Gravando no catálogo do SharePoint..."):
                        try:
                            r = requests.post(URL_FLOW_PNAPAS, json=payload_nova_acao, timeout=20)
                            if r.status_code in [200, 202]:
                                time.sleep(2)
                                st.cache_data.clear()
                                st.success(f"✅ Ação **{chave_acao_ano}** cadastrada com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Falha na resposta do Power Automate.")
                        except Exception as e:
                            st.error(f"❌ Erro de conexão: {e}")

        # =================================================================
        # ABA 2: EDITAR AÇÃO EXISTENTE (REATIVO E CASCATA)
        # =================================================================
        with tab_edt_pna:
            st.markdown("##### 📝 Atualizar Dados de Ação PNAPA")
            if not df_pnapas.empty:
                lista_acoes_edt = sorted((df_pnapas["Acao_Ano"].astype(str) + " - " + df_pnapas["Nome_Acao_Apelido"].astype(str)).tolist())
                acao_edt_sel = st.selectbox("Selecione a Ação para visualizar/alterar:", lista_acoes_edt, key="edt_pna_sel")
                
                cod_alvo_edt = acao_edt_sel.split(" - ")[0].strip()
                dados_alvo_edt = df_pnapas[df_pnapas["Acao_Ano"].astype(str) == cod_alvo_edt].iloc[0]
                
                id_col_nome = "ID_PNAPA" if "ID_PNAPA" in dados_alvo_edt else "Id"
                id_pna_edit = int(float(dados_alvo_edt[id_col_nome]))
                
                val_atual_ano = int(dados_alvo_edt.get("Ano", 2026))
                val_atual_num = str(dados_alvo_edt.get("Num_Acao_PNAPA", "")).strip().upper()
                val_atual_comp = str(dados_alvo_edt.get("Nome_Acao_Completo", "")).strip()
                val_atual_apelido = str(dados_alvo_edt.get("Nome_Acao_Apelido", "")).strip()
                val_atual_ind = str(dados_alvo_edt.get("Indicador", "")).strip()
                val_atual_imp = str(dados_alvo_edt.get("Importância", "Ordinária")).strip()
                val_atual_uf_dono = str(dados_alvo_edt.get("UF_Dono", "Ceneac")).strip()
                val_atual_dono = str(dados_alvo_edt.get("Dono_Acao", "")).strip()
                val_atual_meta_nac = float(pd.to_numeric(dados_alvo_edt.get("Meta_Nacional", 0), errors='coerce') or 0.0)

                st.markdown(f"#### 🗂️ Ficha da Ação: **{cod_alvo_edt}** `(ID: {id_pna_edit})`")

                c_e_ano, c_e_num = st.columns(2)
                with c_e_ano:
                    e_ano = st.number_input("Ano da Ação:", min_value=2020, max_value=2040, value=val_atual_ano, step=1, key=f"edt_pna_ano_{id_pna_edit}")
                with c_e_num:
                    e_num = st.text_input("Código/Número:", value=val_atual_num, key=f"edt_pna_num_{id_pna_edit}").strip().upper()

                e_comp = st.text_input("Nome Completo da Ação:", value=val_atual_comp, key=f"edt_pna_comp_{id_pna_edit}").strip()
                e_apelido = st.text_input("Nome Resumido / Apelido:", value=val_atual_apelido, key=f"edt_pna_apelido_{id_pna_edit}").strip()

                # 🚀 EDIÇÃO DA LIDERANÇA NACIONAL
                st.markdown("###### 👑 Liderança Nacional da Ação")
                c_edn1, c_edn2, c_edn3 = st.columns([1, 2, 1])
                with c_edn1:
                    lista_ufs_dono_edit = ["Ceneac"] + LISTA_UFS_COMPLETA
                    idx_uf_dn = lista_ufs_dono_edit.index(val_atual_uf_dono) if val_atual_uf_dono in lista_ufs_dono_edit else 0
                    e_uf_dono = st.selectbox("UF/Órgão do Dono:", lista_ufs_dono_edit, index=idx_uf_dn, key=f"edt_pna_uf_dn_{id_pna_edit}")
                with c_edn2:
                    srvs_dono_edit = df_servidores[df_servidores["UF_Servidor"] == e_uf_dono]["Servidor"].dropna().unique().tolist()
                    idx_dn = srvs_dono_edit.index(val_atual_dono) if val_atual_dono in srvs_dono_edit else 0
                    e_dono = st.selectbox("Servidor Dono da Ação:", srvs_dono_edit if srvs_dono_edit else [val_atual_dono], index=idx_dn, key=f"edt_pna_dn_{id_pna_edit}")
                with c_edn3:
                    e_meta_nac = st.number_input("Meta Global Nacional:", min_value=0.0, value=val_atual_meta_nac, step=1.0, key=f"edt_pna_meta_nac_{id_pna_edit}")

                c_e_ind, c_e_imp = st.columns(2)
                with c_e_ind:
                    e_ind = st.text_input("Indicador Associado:", value=val_atual_ind, key=f"edt_pna_ind_{id_pna_edit}").strip()
                with c_e_imp:
                    try: idx_imp = LISTA_IMPORTANCIA.index(val_atual_imp)
                    except ValueError: idx_imp = 0
                    e_imp = st.selectbox("Importância Padrão:", LISTA_IMPORTANCIA, index=idx_imp, key=f"edt_pna_imp_{id_pna_edit}")

                st.markdown("<br>", unsafe_allow_html=True)
                
                from concurrent.futures import ThreadPoolExecutor

                if st.button("💾 Salvar Alterações e Sincronizar Base Principal", type="primary", key=f"btn_salvar_edt_pna_{id_pna_edit}"):
                    if not e_num or not e_comp:
                        st.error("⚠️ O Código e o Nome Completo da Ação são obrigatórios.")
                    else:
                        nova_chave_acao_ano = f"{e_num}-{e_ano}"
                        novo_nome_display = e_apelido if e_apelido else e_comp

                        payload_edt = {
                            "Acao": "Editar",
                            "Id": str(id_pna_edit),
                            "ID_PNAPA": id_pna_edit,
                            "Ano": int(e_ano),
                            "Num_Acao_PNAPA": e_num,
                            "Acao_Ano": nova_chave_acao_ano,
                            "Nome_Acao_Completo": e_comp,
                            "Nome_Acao_Apelido": novo_nome_display,
                            "Indicador": e_ind,
                            "Importância": e_imp,
                            "UF_Dono": str(e_uf_dono),
                            "Dono_Acao": str(e_dono),
                            "Meta_Nacional": float(e_meta_nac)
                        }
                        
                        with st.spinner(f"1/2 Atualizando Ação '{nova_chave_acao_ano}' no Catálogo..."):
                            try:
                                requests.post(URL_FLOW_PNAPAS, json=payload_edt, timeout=20)
                            except Exception as e:
                                st.error(f"Erro ao conectar ao catálogo: {e}")

                        cod_antigo_acao_ano = str(dados_alvo_edt.get("Acao_Ano", "")).strip()
                        cod_antigo_num = str(dados_alvo_edt.get("Num_Acao_PNAPA", "")).strip()

                        linhas_macro_afetadas = df_atual[
                            (df_atual["Número da Ação PNAPA"].astype(str).str.strip() == cod_antigo_acao_ano) |
                            (df_atual["Número da Ação PNAPA"].astype(str).str.strip() == cod_antigo_num)
                        ]
                        qtd_macro_afetadas = len(linhas_macro_afetadas)
                        sucessos_macro = 0

                        if qtd_macro_afetadas > 0:
                            with st.spinner(f"2/2 Sincronizando {qtd_macro_afetadas} registro(s) vinculados na Planilha Principal..."):
                                payloads_cascata_pna = []
                                for _, row_orig in linhas_macro_afetadas.iterrows():
                                    p_item = {col: row_orig[col] for col in df_atual.columns if col in row_orig}
                                    p_item["Acao"] = "Editar"
                                    p_item["Id"] = str(row_orig["Id"])
                                    p_item["Ano da Ação"] = int(e_ano)
                                    p_item["Número da Ação PNAPA"] = str(nova_chave_acao_ano)
                                    p_item["Nome da Ação PNAPA"] = str(novo_nome_display)
                                    p_item["Indicador"] = str(e_ind)
                                    p_item["Importância da Atividade"] = str(e_imp)
                                    
                                    payload_sanit = {
                                        k: (0.0 if pd.isna(v) and ("Rec_" in k or "Dias_" in k) else ("" if pd.isna(v) else v)) 
                                        for k, v in p_item.items()
                                    }
                                    payloads_cascata_pna.append(payload_sanit)

                                def enviar_req_pna_macro(p):
                                    try:
                                        r = requests.post(URL_FLOW_PRINCIPAL, json=p, timeout=20)
                                        return 1 if r.status_code in [200, 202] else 0
                                    except:
                                        return 0

                                with ThreadPoolExecutor(max_workers=10) as executor:
                                    resultados = list(executor.map(enviar_req_pna_macro, payloads_cascata_pna))
                                    sucessos_macro = sum(resultados)

                        time.sleep(2.0)
                        st.cache_data.clear()
                        if "df" in st.session_state:
                            del st.session_state.df

                        st.success(f"🎉 Ação **{nova_chave_acao_ano}** e {sucessos_macro}/{qtd_macro_afetadas} atividades sincronizadas com sucesso!")
                        time.sleep(1.5)
                        st.rerun()

        # =================================================================
        # ABA 3: EXCLUIR AÇÃO
        # =================================================================
        with tab_exc_pna:
            st.markdown("##### 🗑️ Exclusão de Ação PNAPA")
            if not df_pnapas.empty:
                lista_acoes_del = sorted((df_pnapas["Acao_Ano"].astype(str) + " - " + df_pnapas["Nome_Acao_Apelido"].astype(str)).tolist())
                acao_del_sel = st.selectbox("Selecione a Ação para EXCLUIR:", lista_acoes_del, key="del_pna_sel")
                
                cod_alvo_del = acao_del_sel.split(" - ")[0].strip()
                dados_alvo_del = df_pnapas[df_pnapas["Acao_Ano"].astype(str) == cod_alvo_del].iloc[0]
                id_col_del = "ID_PNAPA" if "ID_PNAPA" in dados_alvo_del else "Id"
                id_pna_del = int(float(dados_alvo_del[id_col_del]))
                
                linhas_dependentes = df_atual[
                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip() == cod_alvo_del) |
                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip() == str(dados_alvo_del.get("Num_Acao_PNAPA", "")).strip())
                ]
                
                if not linhas_dependentes.empty:
                    st.warning(f"⚠️ **Atenção:** Existem **{len(linhas_dependentes)} registro(s)** vinculados a esta Ação na Planilha Principal.")
                
                if st.button("🔥 Confirmar Exclusão Permanente", type="primary", disabled=not st.checkbox(f"Confirmo que desejo excluir a ação {cod_alvo_del}", key=f"chk_del_pna_{id_pna_del}")):
                    payload_del_pna = {
                        "Acao": "Excluir",
                        "Id": str(id_pna_del),
                        "ID_PNAPA": id_pna_del
                    }
                    with st.spinner("Removendo ação do catálogo..."):
                        try:
                            r = requests.post(URL_FLOW_PNAPAS, json=payload_del_pna, timeout=20)
                            if r.status_code in [200, 202]:
                                time.sleep(2)
                                st.cache_data.clear()
                                st.success(f"💥 Ação {cod_alvo_del} removida com sucesso!")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("❌ Falha ao excluir no SharePoint.")
                        except Exception as e:
                            st.error(f"❌ Erro de conexão: {e}")

# --- TELA: CENTRAL DE SUGESTÕES E MELHORIAS ---
elif modo == "💡 Sugestões & Melhorias":
    st.markdown("<h2 style='color: #03170a;'>💡 Central de Feedback & Sugestões de Melhoria</h2>", unsafe_allow_html=True)
    st.caption("Espaço colaborativo para que testadores e usuários enviem inconsistências, ideias e solicitações.")
    
    # 1. Cartões de Métricas no Topo
    total_feedbacks = len(df_sugestoes)
    abertos = len(df_sugestoes[df_sugestoes["Status"].astype(str).str.strip().isin(["Aberto", "Em Desenvolvimento"])]) if not df_sugestoes.empty else 0
    concluidos = len(df_sugestoes[df_sugestoes["Status"].astype(str).str.strip() == "Concluído"]) if not df_sugestoes.empty else 0
    
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("📋 Total de Sugestões", f"{total_feedbacks}")
    c_m2.metric("⏳ Pendentes / Em Análise", f"{abertos}", delta_color="inverse")
    c_m3.metric("✅ Concluídas / Implementadas", f"{concluidos}")
    
    st.markdown("---")

    tab_enviar, tab_quadro = st.tabs(["➕ Enviar Nova Sugestão", "📋 Quadro de Acompanhamento"])

    # =================================================================
    # ABA 1: FORMULÁRIO DE ENVIO (TESTADORES E USUÁRIOS)
    # =================================================================
    with tab_enviar:
        st.markdown("##### ✍️ Descreva sua sugestão ou problema identificado")
        
        c_mod, c_prio = st.columns([2, 1])
        with c_mod:
            sug_modulo = st.selectbox(
                "Módulo / Tela Relacionada:", 
                [
                    "📊 Visualização de Dados & Filtros", 
                    "➕ Inserção de Atividades/Ações", 
                    "🛠️ Edição Individual / em Lote", 
                    "🏢 Tabelas Auxiliares (Equipes/Ações/Unidades)", 
                    "📈 Dashboards", 
                    "🎨 Layout & Desempenho", 
                    "Outro"
                ],
                key="sug_input_modulo"
            )
        with c_prio:
            sug_prio = st.selectbox(
                "Prioridade Sugerida:", 
                ["Média", "Alta (Impede o trabalho / Erro grave)", "Baixa (Ajuste visual / Ideia futura)"],
                index=0,
                key="sug_input_prio"
            )
            prioridade_limpa = "Alta" if "Alta" in sug_prio else ("Baixa" if "Baixa" in sug_prio else "Média")

        sug_titulo = st.text_input("Título Resumido:", placeholder="Ex: Erro no filtro de municípios ao alternar abas", key="sug_input_titulo")
        sug_descricao = st.text_area(
            "Detalhamento Completo:", 
            placeholder="Descreva o comportamento observado, passos para reproduzir ou o que gostaria de ver no sistema...",
            height=130,
            key="sug_input_desc"
        )
        
        st.caption(f"👤 **Autor Identificado:** `{email_logado}` | **UF:** `{uf_usuario}` | **Data:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        if st.button("🚀 Enviar Sugestão", type="primary", key="btn_enviar_sugestao"):
            if not sug_titulo.strip() or not sug_descricao.strip():
                st.error("⚠️ Por favor, preencha o Título e o Detalhamento antes de enviar.")
            else:
                id_nova_sug = int(pd.to_numeric(df_sugestoes["Id"], errors='coerce').max() + 1) if not df_sugestoes.empty else 1
                data_hora_envio = datetime.now().strftime('%d/%m/%Y %H:%M')
                
                payload_sugestao = {
                    "Acao": "Inserir",
                    "Id": str(id_nova_sug),
                    "Data_Registro": data_hora_envio,
                    "Autor": str(email_logado),
                    "UF_Autor": str(uf_usuario),
                    "Modulo": str(sug_modulo),
                    "Titulo": str(sug_titulo).strip(),
                    "Descricao": str(sug_descricao).strip(),
                    "Prioridade": prioridade_limpa,
                    "Status": "Aberto",
                    "Resposta_Admin": ""
                }
                
                with st.spinner("Gravando no SharePoint e indexando na planilha..."):
                    try:
                        r = requests.post(URL_FLOW_SUGESTOES, json=payload_sugestao, timeout=20)
                        if r.status_code in [200, 202]:
                            # 🚀 Tempo seguro para o Excel Online gravar a linha antes do reload
                            time.sleep(2.5)
                            st.cache_data.clear()
                            st.success("🎉 Sugestão registrada com sucesso! Ela já consta no quadro de acompanhamento.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ O Power Automate rejeitou a solicitação (Status {r.status_code}).")
                    except Exception as e:
                        st.error(f"❌ Erro de comunicação: {e}")

    # =================================================================
    # ABA 2: QUADRO GERAL & PAINEL DE GOVERNANÇA (ADMIN)
    # =================================================================
    with tab_quadro:
        c_q_tit, c_q_ref = st.columns([4, 1])
        with c_q_tit:
            st.markdown("##### 📌 Acompanhamento Geral das Demandas")
        with c_q_ref:
            if st.button("🔄 Atualizar Lista", key="btn_ref_sug_tab"):
                st.cache_data.clear()
                st.rerun()
        
        if df_sugestoes.empty:
            st.info("ℹ️ Nenhuma sugestão carregada no momento. Caso tenha acabado de enviar, clique em '🔄 Atualizar Lista'.")
        else:
            # Filtros visuais da tabela
            c_f_st, c_f_pr = st.columns(2)
            with c_f_st:
                filtro_status = st.selectbox("Filtrar por Status:", ["Todos", "Aberto", "Em Desenvolvimento", "Concluído", "Descartado"], key="f_sug_status")
            with c_f_pr:
                filtro_prio = st.selectbox("Filtrar por Prioridade:", ["Todas", "Alta", "Média", "Baixa"], key="f_sug_prio")
                
            df_sug_exib = df_sugestoes.copy()
            if filtro_status != "Todos":
                df_sug_exib = df_sug_exib[df_sug_exib["Status"].astype(str).str.strip() == filtro_status]
            if filtro_prio != "Todas":
                df_sug_exib = df_sug_exib[df_sug_exib["Prioridade"].astype(str).str.strip() == filtro_prio]
                
            cols_exib = [c for c in ["Id", "Data_Registro", "Prioridade", "Status", "Modulo", "Titulo", "Descricao", "Autor", "Resposta_Admin"] if c in df_sug_exib.columns]
            st.dataframe(df_sug_exib[cols_exib], use_container_width=True, hide_index=True)
            
            # --- PAINEL EXCLUSIVO DO ADMINISTRADOR (ATUALIZAR STATUS E PRIORIDADE) ---
            if perfil_usuario == "Administrador":
                st.markdown("---")
                with st.expander("⚙️ **Painel de Governança (Exclusivo Administrador)**", expanded=True):
                    st.caption("Altere a prioridade real, atualize o status da demanda e dê um parecer técnico ao autor.")
                    
                    lista_ids_sug = df_sugestoes["Id"].astype(str).tolist()
                    id_gestao_sel = st.selectbox("Selecione a Sugestão para Gerenciar (ID):", lista_ids_sug, key="sel_sug_admin_id")
                    
                    sug_linha_alvo = df_sugestoes[df_sugestoes["Id"].astype(str) == str(id_gestao_sel)].iloc[0]
                    
                    st.markdown(f"**Item selecionado:** `ID {id_gestao_sel}` — *{sug_linha_alvo.get('Titulo', '')}* (Autor: `{sug_linha_alvo.get('Autor', '')}`)")
                    st.markdown(f"> *{sug_linha_alvo.get('Descricao', '')}*")
                    
                    c_adm_pr, c_adm_st = st.columns(2)
                    with c_adm_pr:
                        prio_atual = str(sug_linha_alvo.get("Prioridade", "Média")).strip()
                        idx_pr = ["Alta", "Média", "Baixa"].index(prio_atual) if prio_atual in ["Alta", "Média", "Baixa"] else 1
                        nova_prio_adm = st.selectbox("Definir Prioridade Oficial:", ["Alta", "Média", "Baixa"], index=idx_pr, key="adm_sug_prio")
                    with c_adm_st:
                        status_atual = str(sug_linha_alvo.get("Status", "Aberto")).strip()
                        lista_st_opcs = ["Aberto", "Em Desenvolvimento", "Concluído", "Descartado"]
                        idx_st = lista_st_opcs.index(status_atual) if status_atual in lista_st_opcs else 0
                        novo_status_adm = st.selectbox("Definir Status de Atendimento:", lista_st_opcs, index=idx_st, key="adm_sug_status")
                        
                    nova_resp_adm = st.text_area(
                        "Parecer da Gestão / Resposta Técnica:", 
                        value=str(sug_linha_alvo.get("Resposta_Admin", "")),
                        placeholder="Ex: Funcionalidade implementada na versão recente / Inconsistência corrigida...",
                        key="adm_sug_resp"
                    )
                    
                    c_btn_salvar, c_btn_excluir = st.columns([3, 1])
                    with c_btn_salvar:
                        if st.button("💾 Gravar Atualização no SharePoint", type="primary", key="btn_salvar_gestao_sug"):
                            # 🚀 Envio do payload completo para evitar erro 502 de campos nulos no Excel
                            payload_edt_sug = {
                                "Acao": "Editar",
                                "Id": str(id_gestao_sel),
                                "Data_Registro": str(sug_linha_alvo.get("Data_Registro", "")),
                                "Autor": str(sug_linha_alvo.get("Autor", "")),
                                "UF_Autor": str(sug_linha_alvo.get("UF_Autor", "")),
                                "Modulo": str(sug_linha_alvo.get("Modulo", "")),
                                "Titulo": str(sug_linha_alvo.get("Titulo", "")),
                                "Descricao": str(sug_linha_alvo.get("Descricao", "")),
                                "Prioridade": str(nova_prio_adm),
                                "Status": str(novo_status_adm),
                                "Resposta_Admin": str(nova_resp_adm).strip()
                            }
                            
                            with st.spinner("Atualizando sugestão no SharePoint..."):
                                try:
                                    r = requests.post(URL_FLOW_SUGESTOES, json=payload_edt_sug, timeout=20)
                                    if r.status_code in [200, 202]:
                                        time.sleep(2)
                                        st.cache_data.clear()
                                        st.success(f"✅ Sugestão ID {id_gestao_sel} atualizada com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Erro ao atualizar (Status {r.status_code}): {r.text}")
                                except Exception as e:
                                    st.error(f"❌ Erro de conexão: {e}")

                    with c_btn_excluir:
                        with st.popover("🗑️ Excluir"):
                            st.caption(f"Excluir sugestão ID {id_gestao_sel}?")
                            if st.button("Confirmar exclusão", type="primary", key="btn_del_sug_conf"):
                                try:
                                    r = requests.post(URL_FLOW_SUGESTOES, json={"Acao": "Excluir", "Id": str(id_gestao_sel)}, timeout=20)
                                    if r.status_code in [200, 202]:
                                        time.sleep(2)
                                        st.cache_data.clear()
                                        st.success("Sugestão excluída.")
                                        time.sleep(1)
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Erro: {e}")
