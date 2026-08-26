import streamlit as st
import pandas as pd
import time
from datetime import date, datetime
import plotly.express as px
import hashlib
import threading
import requests
import google.generativeai as genai
import unicodedata

st.set_page_config(page_title="SisPNAPA - Emergências Ambientais e Climáticas", layout="wide")

# =================================================================
# 1. ENDPOINTS DO POWER AUTOMATE & CREDENCIAIS (SHAREPOINT)
# =================================================================
# URLs das tabelas auxiliares (Gerenciamento de Infraestrutura)
URL_FLOW_UNIDADES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/05/workflows/de96be2cef1c48b99b61005f28bbb84d/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=rULGxo8iAOe85Xo0fuGID2fvd6lKuyj6eK4zv4pt844"
URL_FLOW_EQUIPES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/00/workflows/c65b398e3480498ca870173471ad0b78/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=euLSevYSyc_C08h6S6DquuzHIJYUyP-Q7QrDRSMU6jE"
URL_FLOW_PNAPAS = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/01/workflows/6350e4d182da4db08634de11b9713704/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=VJkNLYyxvQGnc9Re8eS4r49-F3bF_5emdm8LWdb561w"
URL_FLOW_SUGESTOES = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/09/workflows/715e0d18ec76442ba29aece310dbcd23/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=zW0WvjSuT7aPDct3TlbtDHOJfmRZm7UE1mOsQARZvZ0"
URL_FLOW_EMAIL_360 = "https://default6ae3f5e7541942a780758c1490c72b.25.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/24/workflows/a2a7b0526f8e4730853282bf013e5603/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=57OBkb0svwTTghUCsEjVkVxF2zMYVke_gDtcT3upaGI"

# URL da Planilha Macro Principal (Movidas para o topo para evitar NameError)
URL_FLOW_PRINCIPAL = st.secrets["power_automate"]["URL_PRINCIPAL"]

# =================================================================
# PARÂMETROS DINÂMICOS DE GOVERNANÇA (PRÉ vs PÓS PNAPA E EQUIPARAÇÃO SEDE)
# =================================================================
DEFAULT_GOV_PARAMS = {
    "ano_inicio_trava": 2027,
    "teto_titular_pre": 90.0,
    "teto_substituto_pre": 60.0,
    "teto_membro_pre": 40.0,
    "fator_pos_pnapa": 1.50,          # +50% de expansão de capacidade na execução
    "pct_ordinarias": 50,             # Cota máxima de ordinárias (%)
    "teto_coord_total": 10,
    "teto_coord_n3": 3,
    "dias_corte_n3": 20.0,
    "unidades_sede_equiparadas": [
        "ceneac", "seplog", "cprev", "seprev", "coate", "secoate", "sede", "brasília", "brasilia"
    ]
}

if "gov_params" not in st.session_state:
    st.session_state["gov_params"] = DEFAULT_GOV_PARAMS.copy()

# --- FUNÇÃO DE LOG SILENCIOSO (DECLARAR AQUI NO TOPO) ---
def registrar_log_pergunta(usuario, uf, pergunta):
    """Envia a dúvida do chat para a aba Logs_Chat da planilha Sugestoes.xlsx."""
    try:
        payload = {
            "Acao": "Inserir_Log",
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "Usuario": str(usuario),
            "UF": str(uf),
            "Pergunta": str(pergunta)
        }
        requests.post(URL_FLOW_SUGESTOES, json=payload, timeout=5)
    except Exception:
        pass

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
    aval_qualidade="", aval_feedback="",fiscal="", aeac="", funcao_servidor=""
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
        "Avaliacao_Feedback": str(aval_feedback),
        "Fiscal": str(fiscal),
        "AEAC": str(aeac),
        "Funcao": str(funcao_servidor)
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

def disparar_email_360(codigo_atv, nome_atv, lista_servidores_equipe, df_serv_aux):
    """Envia o comando de e-mail ao PA se a equipe for >= 3 membros."""
    
    # 🚀 PAUSA DO ALFA: Aborta o disparo de e-mails até o módulo ser oficialmente lançado
    return
    
    equipe_unica = list(set(lista_servidores_equipe))
    
    if len(equipe_unica) >= 3:
        emails = df_serv_aux[df_serv_aux["Servidor"].isin(equipe_unica)]["E_mail"].dropna().tolist()
        
        # 🚀 DEDUPLICA OS E-MAILS (Evita que o Outlook bloqueie o envio por destinatários repetidos)
        emails_unicos = list(set([str(e).strip() for e in emails if str(e).strip()]))
        
        if emails_unicos:
            payload_email = {
                "destinatarios": ";".join(emails_unicos),
                "codigo": str(codigo_atv),
                "nome": str(nome_atv)
            }
            try:
                r = requests.post(URL_FLOW_EMAIL_360, json=payload_email, timeout=10)
                if r.status_code in [200, 202]:
                    # 🚀 ALERTA VISUAL PARA O SEU TESTE
                    st.toast(f"📧 E-mail 360º enviado com sucesso para {len(emails_unicos)} endereço(s)!", icon="✅")
                else:
                    st.toast(f"❌ Falha no E-mail (Status {r.status_code})", icon="⚠️")
            except:
                st.toast("❌ Erro de conexão ao enviar E-mail 360º", icon="⚠️")
        else:
            st.toast("⚠️ Missão c/ 3 membros, mas nenhum e-mail cadastrado na base.", icon="⚠️")


# =================================================================
# FUNÇÃO AUXILIAR: CARREGAR SUGESTÕES & MELHORIAS
# =================================================================
@st.cache_data(ttl=300, show_spinner=False)
def carregar_sugestoes():
    cols_padrao = [
        "Id", "Data_Registro", "Prioridade", "Status", "Modulo", 
        "Titulo", "Descricao", "Autor", "UF_Autor", "Resposta_Admin"
    ]
    try:
        # 🚀 Alterado de "Listar" para "Ler"
        r = requests.post(URL_FLOW_SUGESTOES, json={"Acao": "Ler"}, timeout=35)
        if r.status_code in [200, 202]:
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
    except requests.exceptions.Timeout:
        st.warning("⏳ O servidor do Power Automate demorou para responder (Timeout). Clique em '🔄 Atualizar Lista' para tentar novamente.")
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


def normalizar_texto(txt):
    """
    Remove acentos, espaços extras e padroniza para minúsculas:
    Ex: '  SEPREV / CENEAC - Brasília ' -> 'seprev / ceneac - brasilia'
    """
    if txt is None or pd.isna(txt):
        return ""
    txt_str = str(txt).strip().lower()
    return unicodedata.normalize('NFKD', txt_str).encode('ASCII', 'ignore').decode('utf-8')

# =================================================================
# FUNÇÃO AUXILIAR: FILTRO ESTRITO DE SERVIDORES POR UF
# =================================================================
def obter_servidores_por_uf(df_srv, uf_alvo):
    """
    Retorna estritamente a lista de servidores lotados na UF selecionada:
    - Editor Regional: Vê apenas servidores da sua UF.
    - Administrador: Vê apenas servidores da UF que escolheu no filtro do topo.
    """
    if df_srv is None or df_srv.empty or not uf_alvo:
        return []
    
    uf_norm = str(uf_alvo).strip().upper()
    df_filtrado = df_srv[df_srv["UF_Servidor"].astype(str).str.strip().str.upper() == uf_norm]
    
    return sorted(df_filtrado["Servidor"].dropna().unique().tolist())

# =================================================================
# REGRA DE GOVERNANÇA: MOTOR DO TERMÔMETRO DE CAPACIDADE E LIDERANÇA
# =================================================================
def calcular_termometro_carga(
    df, df_srv_base, nome_servidor, ano_alvo, dias_novos=0.0, 
    importancia_nova="Ordinária", funcao_campo="Apoio de Campo", 
    nivel_registro="Atividade", id_excluir=None, num_acao_alvo=None,
    fase_registro="Pré-PNAPA"
):
    """
    Calcula capacidade operacional e limites de liderança:
    - Sede Ceneac (Ceneac, Seplog, CPrev, Seprev, Coate, Secoate): Equiparado a Titular (90d / 135d).
    - Pré-PNAPA: Trava no Teto Base (90d / 60d / 40d).
    - Pós-PNAPA: Expansão do Teto (+50% -> 135d / 90d / 60d).
    - Hard Limit ativo apenas para Ano >= ano_inicio_trava (2027+).
    """
    params = st.session_state.get("gov_params", DEFAULT_GOV_PARAMS)
    ano_corte_trava = int(params.get("ano_inicio_trava", 2027))
    teto_coord_total = int(params.get("teto_coord_total", 10))
    teto_coord_n3 = int(params.get("teto_coord_n3", 3))
    dias_corte_n3 = float(params.get("dias_corte_n3", 20.0))
    pct_ord = float(params.get("pct_ordinarias", 50)) / 100.0
    fator_pos = float(params.get("fator_pos_pnapa", 1.50))

    try:
        ano_num = int(str(ano_alvo).split('.')[0].strip())
    except Exception:
        ano_num = 2026

    eh_planejamento_rigido = (ano_num >= ano_corte_trava)

    # 1. Identificação do Servidor, Cargo e Lotação (100% Imune a Caixa/Acentuação)
    cargo_srv = ""
    lotacao_srv = ""
    uf_srv = ""
    
    if df_srv_base is not None and not df_srv_base.empty and nome_servidor:
        srv_alvo_norm = normalizar_texto(nome_servidor)
        match_srv = df_srv_base[df_srv_base["Servidor"].apply(normalizar_texto) == srv_alvo_norm]
        
        if not match_srv.empty:
            row_s = match_srv.iloc[0]
            cargo_srv = normalizar_texto(row_s.get("Funcao", ""))
            val_lot = row_s.get("Lotacao", row_s.get("Lotação", ""))
            lotacao_srv = normalizar_texto(val_lot)
            uf_srv = normalizar_texto(row_s.get("UF_Servidor", row_s.get("UF", "")))

    unidades_sede_norm = [normalizar_texto(u) for u in params.get("unidades_sede_equiparadas", []) if str(u).strip()]

    # Verificação de equiparação da Sede Ceneac
    pertence_sede_ceneac = False
    if lotacao_srv:
        pertence_sede_ceneac = any(u in lotacao_srv for u in unidades_sede_norm)
    if not pertence_sede_ceneac:
        pertence_sede_ceneac = any(u in cargo_srv for u in unidades_sede_norm) or (uf_srv == "df" and any(u in lotacao_srv for u in ["sede", "nacional", "brasilia"]))

    eh_substituto = any(termo in cargo_srv for termo in ["substituto", "substituta", "subst", "vice"])
    eh_titular = any(termo in cargo_srv for termo in ["responsavel", "coordenador", "chefe", "ponto focal"]) and not eh_substituto

    if pertence_sede_ceneac:
        perfil_desc = "Equipe Sede Ceneac / Nacional (Equiparado a Responsável)"
        teto_pre = float(params.get("teto_titular_pre", 90.0))
    elif eh_titular:
        perfil_desc = "Responsável / Coordenador Titular"
        teto_pre = float(params.get("teto_titular_pre", 90.0))
    elif eh_substituto:
        perfil_desc = "Coordenador / Responsável Substituto"
        teto_pre = float(params.get("teto_substituto_pre", 60.0))
    else:
        perfil_desc = "Membro de Equipe"
        teto_pre = float(params.get("teto_membro_pre", 40.0))

    teto_pos = teto_pre * fator_pos
    teto_dias_ativo = teto_pre if fase_registro == "Pré-PNAPA" else teto_pos
    teto_ordinarias = teto_dias_ativo * pct_ord

    if df is None or df.empty or not nome_servidor:
        return {
            "perfil_dedicacao": perfil_desc, "teto_dias": teto_dias_ativo, "teto_pre": teto_pre, "teto_pos": teto_pos,
            "teto_dias_ativo": teto_dias_ativo, "teto_ordinarias": teto_ordinarias,
            "dias_totais_atuais": 0.0, "dias_totais_projetados": dias_novos,
            "dias_ord_atuais": 0.0, "dias_ord_projetados": dias_novos if importancia_nova == "Ordinária" else 0.0,
            "acoes_coord_totais": 0, "acoes_coord_n3": 0, "teto_coord_total": teto_coord_total, "teto_coord_n3": teto_coord_n3,
            "status_geral": "OK", "mensagens_erro": [], "mensagens_aviso": [], "eh_planejamento_rigido": eh_planejamento_rigido
        }

    col_num_pna = "Número da Ação PNAPA" if "Número da Ação PNAPA" in df.columns else ("Número da Ação" if "Número da Ação" in df.columns else None)

    # 2. Filtragem Histórica no Ano
    df_ano = df[df["Ano da Ação"].astype(str).str.split('.').str[0] == str(ano_num)].copy()
    if id_excluir is not None and not df_ano.empty and "Id" in df_ano.columns:
        df_ano = df_ano[df_ano["Id"].astype(str).str.strip() != str(id_excluir).strip()]

    df_ano_srv = df_ano[df_ano["Servidor"].astype(str).str.strip().str.lower() == str(nome_servidor).strip().lower()].copy()

    # 3. Eixo de Dias (Atividades)
    df_atvs_srv = df_ano_srv[df_ano_srv["Nível"].astype(str).str.strip() == "Atividade"]
    dias_totais_atuais = pd.to_numeric(df_atvs_srv["Dias_Gastos_Plan"], errors='coerce').fillna(0).sum() if "Dias_Gastos_Plan" in df_atvs_srv.columns else 0.0
    
    df_ord_srv = df_atvs_srv[df_atvs_srv["Importância da Atividade"].astype(str).str.strip() == "Ordinária"] if "Importância da Atividade" in df_atvs_srv.columns else pd.DataFrame()
    dias_ord_atuais = pd.to_numeric(df_ord_srv["Dias_Gastos_Plan"], errors='coerce').fillna(0).sum() if not df_ord_srv.empty and "Dias_Gastos_Plan" in df_ord_srv.columns else 0.0

    dias_totais_proj = dias_totais_atuais + (dias_novos if nivel_registro == "Atividade" else 0.0)
    dias_ord_proj = dias_ord_atuais + (dias_novos if (nivel_registro == "Atividade" and importancia_nova == "Ordinária") else 0.0)

    # 4. Eixo de Liderança (Ações Coordenadas & Nível 3)
    df_acoes_coord = df_ano[
        (df_ano["Nível"].astype(str).str.strip() == "Ação") &
        (df_ano["Servidor"].astype(str).str.strip().str.lower() == str(nome_servidor).strip().lower())
    ]
    codigos_acoes = df_acoes_coord[col_num_pna].dropna().unique().tolist() if (col_num_pna and col_num_pna in df_acoes_coord.columns) else []
    
    acoes_n3_atuais = 0
    if col_num_pna and col_num_pna in df_ano.columns:
        for cod_ac in codigos_acoes:
            df_bloco = df_ano[df_ano[col_num_pna].astype(str).str.strip() == str(cod_ac).strip()]
            dias_bloco = pd.to_numeric(df_bloco["Dias_Gastos_Plan"], errors='coerce').fillna(0).sum() if "Dias_Gastos_Plan" in df_bloco.columns else 0.0
            if dias_bloco >= dias_corte_n3:
                acoes_n3_atuais += 1

    acoes_coord_totais_proj = len(codigos_acoes)
    acoes_coord_n3_proj = acoes_n3_atuais

    if nivel_registro == "Ação":
        if not num_acao_alvo or str(num_acao_alvo) not in codigos_acoes:
            acoes_coord_totais_proj += 1
            if dias_novos >= dias_corte_n3:
                acoes_coord_n3_proj += 1
        else:
            if dias_novos >= dias_corte_n3:
                acoes_coord_n3_proj += 1

    # 5. Avaliação de Travas e Mensagens
    mensagens_erro = []
    mensagens_aviso = []

    # Validação A: Regra de Ouro (Ações Nível 3)
    if acoes_coord_n3_proj > teto_coord_n3:
        msg = f"Regra de Liderança: Coordenará {acoes_coord_n3_proj} Ações Nível 3 (Máximo permitido: {teto_coord_n3})."
        if eh_planejamento_rigido: mensagens_erro.append(msg)
        else: mensagens_aviso.append(msg + " (Revisar distribuição).")

    # Validação B: Teto Global de Coordenações
    if acoes_coord_totais_proj > teto_coord_total:
        msg = f"Teto de Coordenações excedido: {acoes_coord_totais_proj} ações sob responsabilidade (Máximo permitido: {teto_coord_total})."
        if eh_planejamento_rigido: mensagens_erro.append(msg)
        else: mensagens_aviso.append(msg)

    # Validação C: Teto de Dias Anuais
    if dias_totais_proj > teto_dias_ativo:
        msg = f"Teto de dias ({fase_registro}) excedido: Projetado {dias_totais_proj:.1f} d / Limite {teto_dias_ativo:.0f} d."
        if eh_planejamento_rigido: mensagens_erro.append(msg)
        else: mensagens_aviso.append(msg + f" ({fase_registro} em execução).")

    # Validação D: Trava Anti-Rotina (50% Ordinárias)
    if dias_ord_proj > teto_ordinarias:
        msg = f"Cota de ordinárias ({fase_registro}) excedida: Projetado {dias_ord_proj:.1f} d / Máximo {teto_ordinarias:.0f} d ({int(pct_ord*100)}%)."
        if eh_planejamento_rigido: mensagens_erro.append(msg)
        else: mensagens_aviso.append(msg + " (Priorize ações estratégicas/prioritárias).")

    if eh_planejamento_rigido and len(mensagens_erro) > 0:
        status_geral = "BLOQUEADO"
    elif len(mensagens_aviso) > 0 or len(mensagens_erro) > 0:
        status_geral = "ALERTA"
    else:
        status_geral = "OK"

    return {
        "perfil_dedicacao": perfil_desc,
        "teto_dias": teto_dias_ativo,
        "teto_pre": teto_pre,
        "teto_pos": teto_pos,
        "teto_dias_ativo": teto_dias_ativo,
        "teto_ordinarias": teto_ordinarias,
        "teto_coord_total": teto_coord_total,
        "teto_coord_n3": teto_coord_n3,
        "dias_totais_atuais": dias_totais_atuais,
        "dias_totais_projetados": dias_totais_proj,
        "dias_ord_atuais": dias_ord_atuais,
        "dias_ord_projetados": dias_ord_proj,
        "acoes_coord_totais": acoes_coord_totais_proj,
        "acoes_coord_n3": acoes_coord_n3_proj,
        "status_geral": status_geral,
        "mensagens_erro": mensagens_erro,
        "mensagens_aviso": mensagens_aviso,
        "eh_planejamento_rigido": eh_planejamento_rigido
    }

# =================================================================
# FUNÇÕES UTILITÁRIAS DE FORMATAÇÃO NO PADRÃO BRASILEIRO (BRL)
# =================================================================
def formatar_moeda_br(val, casas=2, incluir_cifrao=True):
    """Converte qualquer número para formato de moeda brasileira (ex: R$ 413.049,20)."""
    if pd.isna(val) or val is None:
        return "R$ 0,00" if incluir_cifrao else "0,00"
    try:
        val_f = float(val)
    except (ValueError, TypeError):
        return str(val)
    fmt = f"{val_f:,.{casas}f}" if casas > 0 else f"{val_f:,.0f}"
    s_br = fmt.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s_br}" if incluir_cifrao else s_br

def formatar_numero_br(val, casas=1):
    """Converte qualquer número/decimal para o padrão BR com vírgula (ex: 1.486,5)."""
    if pd.isna(val) or val is None:
        return "0,0" if casas > 0 else "0"
    try:
        val_f = float(val)
    except (ValueError, TypeError):
        return str(val)
    fmt = f"{val_f:,.{casas}f}" if casas > 0 else f"{val_f:,.0f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")

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

# 🛡️ SANITIZAÇÃO DE TIPOS NO CATÁLOGO DE AÇÕES PNAPA
if not df_pnapas.empty:
    if "Ano" in df_pnapas.columns:
        df_pnapas["Ano_Num"] = pd.to_numeric(df_pnapas["Ano"], errors='coerce').fillna(0).astype(int)
    else:
        df_pnapas["Ano_Num"] = 0
    if "Orcamento_Nacional" not in df_pnapas.columns:
        df_pnapas["Orcamento_Nacional"] = 0.0
    else:
        df_pnapas["Orcamento_Nacional"] = pd.to_numeric(df_pnapas["Orcamento_Nacional"], errors='coerce').fillna(0.0)
    if "Meta_Nacional" not in df_pnapas.columns:
        df_pnapas["Meta_Nacional"] = 0.0
    else:
        df_pnapas["Meta_Nacional"] = pd.to_numeric(df_pnapas["Meta_Nacional"], errors='coerce').fillna(0.0)

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

# Funções de criptografia
def hash_senha(senha: str) -> str:
    """Gera o hash SHA-256 da senha."""
    if not senha:
        return ""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def validar_senha(senha_digitada: str, token_armazenado: str, senha_padrao="pnapa123") -> bool:
    """Valida senha digitada contra hash SHA-256 ou texto puro (legado)."""
    token_limpo = str(token_armazenado).strip()
    
    # 1. Se estiver vazio no Excel, compara com a senha padrão
    if not token_limpo or token_limpo.lower() in ["nan", "none"]:
        return senha_digitada == senha_padrao
        
    # 2. Se já for um hash SHA-256 (64 caracteres hexadecimais)
    if len(token_limpo) == 64 and all(c in "0123456789abcdefABCDEF" for c in token_limpo):
        return hash_senha(senha_digitada).lower() == token_limpo.lower()
        
    # 3. Retrocompatibilidade: se ainda for texto puro no Excel
    return senha_digitada == token_limpo

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
        
        /* Selectboxes e Popovers */
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] > div,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] > div,
        div[data-testid="stPopoverBody"] div[data-testid="stSelectbox"] > div,
        div[data-testid="stPopoverBody"] div[data-baseweb="select"] > div {
            background-color: #ffffff !important; border: 1px solid #cbd5e1 !important;
        }
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] *,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] *,
        div[data-testid="stPopoverBody"] div[data-testid="stSelectbox"] *,
        div[data-testid="stPopoverBody"] div[data-baseweb="select"] * {
            color: #03170a !important; background-color: transparent !important;
        }
        div[data-testid="stAppViewContainer"] div[data-testid="stSelectbox"] svg,
        div[data-testid="stAppViewContainer"] div[data-baseweb="select"] svg,
        div[data-testid="stPopoverBody"] div[data-testid="stSelectbox"] svg,
        div[data-testid="stPopoverBody"] div[data-baseweb="select"] svg { 
            fill: #03170a !important; 
        }
        
        div[data-baseweb="popover"] ul { background-color: #ffffff !important; }
        div[data-baseweb="popover"] ul li { color: #03170a !important; background-color: transparent !important; }
        div[data-baseweb="popover"] ul li:hover { background-color: #f1f5f9 !important; }
        
        div[data-testid="stNumberInput"] input { background-color: #ffffff !important; color: #03170a !important; }
        div[data-testid="stNumberInput"] > div { border: 1px solid #cbd5e1 !important; background-color: #ffffff !important; }
        div[data-testid="stNumberInput"] button { background-color: #f1f5f9 !important; color: #03170a !important; border: 1px solid #cbd5e1 !important; }
        
        /* 🚀 CORREÇÃO CIRÚRGICA: Caixas de Data com fundo branco e texto escuro */
        div[data-testid="stDateInput"] > div,
        div[data-testid="stDateInput"] div[data-baseweb="input"],
        div[data-testid="stDateInput"] div[data-baseweb="base-input"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
        }
        div[data-testid="stDateInput"] *,
        div[data-testid="stDateInput"] input {
            color: #03170a !important;
            background-color: transparent !important;
        }
        div[data-testid="stDateInput"] svg {
            fill: #03170a !important;
        }
        
        button[data-baseweb="tab"] p { color: #4a5568 !important; font-weight: 500; }
        button[aria-selected="true"] p { color: #03170a !important; font-weight: 700 !important; }
        div[data-baseweb="tab-highlight"] { background-color: #4d6b53 !important; }
        
        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea {
            border: 1px solid #cbd5e1 !important; background-color: #ffffff !important; color: #03170a !important;
        }
        
        div[data-testid="stAppViewContainer"] label[data-testid="stWidgetLabel"] p,
        div[data-testid="stPopoverBody"] label[data-testid="stWidgetLabel"] p { 
            color: #03170a !important; font-weight: 500; 
        }
        h2, h3, [data-testid="stHeader"] { color: #03170a !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# =================================================================
# IV. SISTEMA DE LOGIN CORPORATIVO (APP PÚBLICO COM PORTA TRANCADA)
# =================================================================
EMAIL_ADMIN = "tiago.farani@ibama.gov.br"
SENHA_PADRAO = "pnapa123"
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["email_logado"] = ""
    st.session_state["perfil_usuario"] = ""
    st.session_state["uf_usuario"] = ""
    st.session_state["nome_usuario"] = ""
    st.session_state["id_serv_logado"] = 0


# --- TELA DE LOGIN ---
if not st.session_state["autenticado"]:
    st.markdown("<h1 style='text-align: center; color: #03170a; margin-top: 5vh;'>🔐 SisPNAPA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #4a5568;'>Emergências Ambientais e Climáticas</p>", unsafe_allow_html=True)
    
    c_login_space1, c_login, c_login_space2 = st.columns([1, 1.5, 1])
    with c_login:
        with st.container(border=True):
            st.markdown("#### Login do Servidor")
            email_input = st.text_input("E-mail Institucional (@ibama.gov.br):").strip().lower()
            senha_input = st.text_input("Senha / Token:", type="password").strip()
            
            st.info(f"💡 **Primeiro acesso?** Se você já foi cadastrado na equipe pelo seu Coordenador, use a senha padrão: **{SENHA_PADRAO}**")
            
            if st.button("Entrar no Sistema", type="primary", use_container_width=True):
                if not email_input or not senha_input:
                    st.warning("⚠️ Preencha e-mail e senha.")
                else:
                    # Busca o usuário na base de dados
                    srv_match = df_servidores[df_servidores["E_mail"].astype(str).str.strip().str.lower() == email_input]
                    
                    if srv_match.empty:
                        st.error("❌ E-mail não encontrado. Solicite seu cadastro ao Administrador.")
                    else:
                        dados_usuario = srv_match.iloc[0]
                        token_banco = str(dados_usuario.get("Token", "")).strip()
                        
                        # 🚀 Validação segura com suporte a hash e texto puro legado
                        if validar_senha(senha_input, token_banco, SENHA_PADRAO):
                            st.session_state["autenticado"] = True
                            st.session_state["email_logado"] = email_input
                            st.session_state["perfil_usuario"] = str(dados_usuario.get("Perfil", "Visualização")).strip()
                            st.session_state["uf_usuario"] = str(dados_usuario.get("UF_Servidor", "SP")).strip()
                            st.session_state["nome_usuario"] = str(dados_usuario.get("Servidor", "Desconhecido")).strip()
                            st.session_state["id_serv_logado"] = int(float(dados_usuario.get("ID_SERV", 0)))
                            st.rerun()
                        else:
                            st.error("❌ Senha incorreta.")
    
    # 🚀 O comando st.stop() é o "Cadeado". Ele impede que o resto do código abaixo seja executado se não estiver logado.
    st.stop() 

# --- RESGATE DAS VARIÁVEIS PARA O APP FUNCIONAR ---
email_logado = st.session_state["email_logado"]
perfil_usuario = st.session_state["perfil_usuario"]
uf_usuario = st.session_state["uf_usuario"]
nome_usuario_logado = st.session_state["nome_usuario"]
id_serv_logado = st.session_state["id_serv_logado"]

acesso_liberado = True if perfil_usuario in ["Administrador", "Editor Regional"] else False

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

# Montagem Dinâmica do Menu Lateral
opcoes_menu = [
    "📈 Dashboards Executivos", 
    "📊 Visualizar Base",
    "🤝 Pactuação Pré-PNAPA" 
]

if acesso_liberado:
    opcoes_menu.extend([
        "➕ Inserir Nova Linha", 
        "🏢 Gerenciar Unidades", 
        "👥 Gerenciar Equipes", 
        "🗂️ Gerenciar Ações PNAPA"
    ])

# opcoes_menu.append("⭐ Meus Feedbacks (360º)")
opcoes_menu.append("💡 Sugestões & Melhorias")
opcoes_menu.append("📖 Base de Conhecimento (FAQ)")
opcoes_menu.append("🤖 Assistente Virtual")

st.sidebar.markdown("## 🕹️ Painel de Controle")
modo = st.sidebar.radio("Navegação:", opcoes_menu)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Atualizar Base (Refresh)", use_container_width=True):
    st.cache_data.clear()
    if "df" in st.session_state: del st.session_state.df
    st.rerun()

st.sidebar.markdown("---")
# Painel do Usuário (Identidade, Troca de Senha e Logout)
st.sidebar.markdown(f"👤 **{nome_usuario_logado}**")
st.sidebar.caption(f"Perfil: {perfil_usuario} | UF: {uf_usuario}")

with st.sidebar.popover("🔑 Trocar Minha Senha", use_container_width=True):
    st.caption("Crie uma nova senha de acesso exclusiva.")
    nova_senha = st.text_input("Nova Senha:", type="password", key="input_nova_senha")
    if st.button("Salvar Nova Senha", type="primary", use_container_width=True):
        if len(nova_senha) < 4:
            st.error("A senha deve ter pelo menos 4 caracteres.")
        else:
            linha_srv = df_servidores[pd.to_numeric(df_servidores["ID_SERV"], errors='coerce').fillna(0).astype(int) == id_serv_logado]
            if not linha_srv.empty:
                linha_srv = linha_srv.iloc[0]
                payload_senha = {
                    "Acao": "Editar",
                    "ID_SERV": id_serv_logado,
                    "Servidor": str(linha_srv.get("Servidor", "")),
                    "UF_Servidor": str(linha_srv.get("UF_Servidor", "")),
                    "Lotacao": str(linha_srv.get("Lotacao", "")),
                    "Equipe_Emergencias": str(linha_srv.get("Equipe_Emergencias", "Não")),
                    "Fiscal": str(linha_srv.get("Fiscal", "Não")),
                    "AEAC": str(linha_srv.get("AEAC", "Não")),
                    "Funcao": str(linha_srv.get("Funcao", "")),
                    "E_mail": email_logado,
                    "Perfil": perfil_usuario,
                    "Token": hash_senha(nova_senha)  # 🚀 Salva apenas o HASH no Excel
                }
                with st.spinner("Atualizando senha no banco..."):
                    executar_api_equipes(payload_senha)
                    time.sleep(1.5)
                    st.cache_data.clear()
                st.success("✅ Senha atualizada! Terá efeito no próximo login.")
            else:
                st.error("Erro ao localizar seu cadastro no banco.")


# =========================================================================
# ⚙️ PAINEL DE CALIBRAGEM DA GOVERNANÇA (EXCLUSIVO ADMINISTRADOR)
# =========================================================================
if perfil_usuario == "Administrador":
    with st.sidebar.popover("⚙️ Calibrar Regras & Limites (Admin)", use_container_width=True):
        # 🎨 ESTILIZAÇÃO: FUNDO VERDE CLARO + BOTÕES CLAROS DE ALTO CONTRASTE
        st.markdown("""
            <style>
            div[data-testid="stPopoverBody"] {
                background-color: #f2f8f4 !important;
                color: #0f172a !important;
                border: 1px solid #bbf7d0 !important;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25) !important;
                border-radius: 8px !important;
            }
            div[data-testid="stPopoverBody"] label, 
            div[data-testid="stPopoverBody"] p, 
            div[data-testid="stPopoverBody"] span {
                color: #0f291e !important;
                font-weight: 600 !important;
            }
            div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] {
                color: #2d5a43 !important;
                font-weight: normal !important;
            }
            div[data-testid="stPopoverBody"] input,
            div[data-testid="stPopoverBody"] textarea {
                color: #0f172a !important;
                background-color: #ffffff !important;
                border: 1px solid #94a3b8 !important;
            }
            /* Botão 'Aplicar Regras' (Verde Claro Destacado) */
            div[data-testid="stPopoverBody"] button[kind="primary"] {
                background-color: #dcfce7 !important;
                color: #064e3b !important;
                border: 1px solid #86efac !important;
                font-weight: 700 !important;
            }
            div[data-testid="stPopoverBody"] button[kind="primary"]:hover {
                background-color: #bbf7d0 !important;
                border-color: #4ade80 !important;
                color: #022c22 !important;
            }
            /* Botão 'Restaurar Padrão' (Branco / Neutro Claro) */
            div[data-testid="stPopoverBody"] button[kind="secondary"] {
                background-color: #ffffff !important;
                color: #1e293b !important;
                border: 1px solid #cbd5e1 !important;
                font-weight: 600 !important;
            }
            div[data-testid="stPopoverBody"] button[kind="secondary"]:hover {
                background-color: #f1f5f9 !important;
                border-color: #94a3b8 !important;
                color: #0f172a !important;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("<h4 style='color: #03170a !important; margin-bottom: 2px; font-weight: 700;'>⚖️ Governança Operacional PNAPA</h4>", unsafe_allow_html=True)
        st.caption("Ajuste em tempo real os tetos do Pré/Pós-PNAPA e equiparação das unidades nacionais.")

        p_atual = st.session_state["gov_params"]

        novo_ano_trava = st.number_input("Ano de Início da Trava Rígida:", min_value=2025, max_value=2035, value=int(p_atual["ano_inicio_trava"]), step=1)
        
        st.markdown("<h5 style='color: #04431b !important; margin-top: 12px; margin-bottom: 4px; font-weight: 700;'>📅 Tetos Pré-PNAPA (Planejamento Inicial)</h5>", unsafe_allow_html=True)
        c_g1, c_g2, c_g3 = st.columns(3)
        with c_g1:
            n_teto_tit = st.number_input("Titular/Sede:", min_value=10.0, max_value=200.0, value=float(p_atual["teto_titular_pre"]), step=5.0)
        with c_g2:
            n_teto_sub = st.number_input("Substituto:", min_value=10.0, max_value=200.0, value=float(p_atual["teto_substituto_pre"]), step=5.0)
        with c_g3:
            n_teto_mem = st.number_input("Membro:", min_value=10.0, max_value=200.0, value=float(p_atual["teto_membro_pre"]), step=5.0)

        st.markdown("<h5 style='color: #04431b !important; margin-top: 12px; margin-bottom: 4px; font-weight: 700;'>🚀 Expansão Pós-PNAPA (Execução / Ao Longo do Ano)</h5>", unsafe_allow_html=True)
        n_fator_pos = st.slider("Fator Multiplicador Pós-PNAPA:", min_value=1.0, max_value=2.0, value=float(p_atual["fator_pos_pnapa"]), step=0.05, format="%.2fx")
        st.caption(f"💡 Tetos Pós-PNAPA resultantes: Titular/Sede: {n_teto_tit*n_fator_pos:.0f}d | Substituto: {n_teto_sub*n_fator_pos:.0f}d | Membro: {n_teto_mem*n_fator_pos:.0f}d")

        n_pct_ord = st.slider("Cota Máxima em Atividades Ordinárias (%):", min_value=10, max_value=100, value=int(p_atual["pct_ordinarias"]), step=5)

        st.markdown("<h5 style='color: #04431b !important; margin-top: 12px; margin-bottom: 4px; font-weight: 700;'>👑 Limites de Liderança</h5>", unsafe_allow_html=True)
        c_l1, c_l2 = st.columns(2)
        with c_l1:
            n_coord_tot = st.number_input("Máx Ações Totais:", min_value=1, max_value=30, value=int(p_atual["teto_coord_total"]), step=1)
        with c_l2:
            n_coord_n3 = st.number_input("Máx Ações Nível 3:", min_value=1, max_value=10, value=int(p_atual["teto_coord_n3"]), step=1)

        n_corte_n3 = st.number_input("Corte de Dias para Nível 3:", min_value=5.0, max_value=50.0, value=float(p_atual["dias_corte_n3"]), step=1.0)

        st.markdown("<h5 style='color: #04431b !important; margin-top: 12px; margin-bottom: 4px; font-weight: 700;'>🏢 Unidades da Sede Equiparadas (Ceneac/Brasília)</h5>", unsafe_allow_html=True)
        lista_unidades_str = ", ".join(p_atual.get("unidades_sede_equiparadas", []))
        txt_unidades = st.text_area("Termos de Reconhecimento (separados por vírgula):", value=lista_unidades_str, help="Servidores lotados nessas unidades recebem automaticamente o teto de Titular/Responsável.")

        col_btn_g1, col_btn_g2 = st.columns(2)
        with col_btn_g1:
            if st.button("💾 Aplicar Regras", type="primary", use_container_width=True):
                st.session_state["gov_params"] = {
                    "ano_inicio_trava": novo_ano_trava,
                    "teto_titular_pre": n_teto_tit,
                    "teto_substituto_pre": n_teto_sub,
                    "teto_membro_pre": n_teto_mem,
                    "fator_pos_pnapa": n_fator_pos,
                    "pct_ordinarias": n_pct_ord,
                    "teto_coord_total": n_coord_tot,
                    "teto_coord_n3": n_coord_n3,
                    "dias_corte_n3": n_corte_n3,
                    "unidades_sede_equiparadas": [u.strip().lower() for u in txt_unidades.split(",") if u.strip()]
                }
                st.success("Regras de governança atualizadas!")
                time.sleep(1)
                st.rerun()
        with col_btn_g2:
            if st.button("🔄 Restaurar Padrão", type="secondary", use_container_width=True):
                st.session_state["gov_params"] = DEFAULT_GOV_PARAMS.copy()
                st.info("Parâmetros restaurados.")
                time.sleep(1)
                st.rerun()


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
        # 1. ESTILIZAÇÃO CSS: BARRA DE FILTROS SUPERIOR FIXA (STICKY TOP BAR)
        # =====================================================================
        st.markdown("""
            <style>
            div[data-testid="stVerticalBlock"] > div:has(.sticky-bar-marker),
            div.st-key-sticky_filter_container {
                position: sticky !important;
                top: 2.875rem !important;
                z-index: 999 !important;
                background-color: #f8fafc !important; 
                padding: 10px 0px 10px 0px !important;
                border-bottom: 1px solid #cbd5e1 !important;
                margin-bottom: 1rem !important;
            }
            </style>
        """, unsafe_allow_html=True)

        hoje = pd.Timestamp(date.today())

        # =====================================================================
        # 2. PREPARAÇÃO DE DADOS E LÓGICA DE STATUS
        # =====================================================================
        
        # 🚀 Função blindada para converter texto, data normal e serial do Excel (ex: 46023)
        def converter_dt_seguro(valor):
            if pd.isna(valor) or valor is None: return pd.NaT
            if isinstance(valor, (datetime, pd.Timestamp)): return pd.to_datetime(valor)
            val_str = str(valor).strip()
            if val_str == "" or val_str.lower() in ["none", "nat", "nan"]: return pd.NaT
            if val_str.replace('.', '', 1).isdigit():
                try: return pd.to_datetime(int(float(val_str)), unit='D', origin='1899-12-30')
                except: pass
            return pd.to_datetime(val_str, errors='coerce', dayfirst=True)

        # --- ATIVIDADES (Micro) ---
        df_dash_atv = df_atual[df_atual["Nível"].astype(str).str.strip() == "Atividade"].copy()
        df_dash_atv["Data_Inicio_DT"] = df_dash_atv["Data de Início"].apply(converter_dt_seguro)
        df_dash_atv["Data_Fim_DT"] = df_dash_atv["Data de Término"].apply(converter_dt_seguro)
        df_dash_atv["Mes_Inicio"] = df_dash_atv["Data_Inicio_DT"].dt.month
        df_dash_atv["Dias_Gastos_Plan"] = pd.to_numeric(df_dash_atv["Dias_Gastos_Plan"], errors='coerce').fillna(0)
        df_dash_atv["Dias_Gastos_Exec"] = pd.to_numeric(df_dash_atv["Dias_Gastos_Exec"], errors='coerce').fillna(0)
        df_dash_atv["Resultado_Indicador"] = pd.to_numeric(df_dash_atv["Resultado_Indicador"], errors='coerce').fillna(0)
        df_dash_atv["Rec_Exec_Total"] = pd.to_numeric(df_dash_atv["Rec_Exec_Total"], errors='coerce').fillna(0)
        df_dash_atv["Rec_Plan_Total"] = pd.to_numeric(df_dash_atv["Rec_Plan_Total"], errors='coerce').fillna(0)
        
        meses_pt = {1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril', 5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto', 9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'}
        df_dash_atv["Mes_Nome"] = df_dash_atv["Mes_Inicio"].map(meses_pt)

        def classificar_status_atv(row):
            andamento = str(row.get("Andamento", "")).strip()
            doc = str(row.get("Doc_Probatorio_Exec", "")).strip()
            dt_fim = row.get("Data_Fim_DT")
            if andamento == "Concluída":
                if not doc or doc.lower() == "nan" or doc == "none": return "Sem Documento de Execução"
                return "Concluída"
            elif andamento == "Prevista":
                if pd.notna(dt_fim) and hoje > dt_fim: return "Atrasada"
                return "Prevista"
            return andamento
            
        df_dash_atv["Status_Atividade"] = df_dash_atv.apply(classificar_status_atv, axis=1)

        # 🚀 Agrega previamente as atividades concluídas por Ação e UF para alimentar a classificação
        atv_concluidas_prev = df_dash_atv[df_dash_atv["Andamento"] == "Concluída"]
        agg_atv_acao = atv_concluidas_prev.groupby(["Número da Ação PNAPA", "UF_Acao_PNAPA"]).agg(
            Resultado_Indicador_Agregado=('Resultado_Indicador', 'sum'),
            Dias_Gastos_Exec_Agregado=('Dias_Gastos_Exec', 'sum')
        ).reset_index()

        # --- AÇÕES (Macro) ---
        df_dash_acao = df_atual[df_atual["Nível"].astype(str).str.strip() == "Ação"].copy()
        df_dash_acao["Data_Inicio_DT"] = df_dash_acao["Data de Início"].apply(converter_dt_seguro)
        df_dash_acao["Data_Fim_DT"] = df_dash_acao["Data de Término"].apply(converter_dt_seguro)
        df_dash_acao["Meta_Indicador"] = pd.to_numeric(df_dash_acao["Meta_Indicador"], errors='coerce').fillna(0)
        df_dash_acao["Rec_Plan_Total"] = pd.to_numeric(df_dash_acao["Rec_Plan_Total"], errors='coerce').fillna(0)
        df_dash_acao["Dias_Gastos_Plan"] = pd.to_numeric(df_dash_acao["Dias_Gastos_Plan"], errors='coerce').fillna(0)
        df_dash_acao["Justificativa_Acao_PNAPA"] = df_dash_acao.get("Justificativa_Acao_PNAPA", "").fillna("")

        # Cruza as métricas agregadas na tabela de Ações
        df_dash_acao = pd.merge(df_dash_acao, agg_atv_acao, on=["Número da Ação PNAPA", "UF_Acao_PNAPA"], how="left")
        df_dash_acao["Resultado_Indicador_Agregado"] = df_dash_acao["Resultado_Indicador_Agregado"].fillna(0)
        df_dash_acao["Dias_Gastos_Exec_Agregado"] = df_dash_acao["Dias_Gastos_Exec_Agregado"].fillna(0)

        def classificar_status_acao(row):
            andamento = str(row.get("Andamento", "")).strip()
            justif = str(row.get("Justificativa_Acao_PNAPA", "")).strip()
            if justif.lower() in ["nan", "none", "null"]: justif = ""
            dt_fim = row.get("Data_Fim_DT")
            
            meta = float(row.get("Meta_Indicador", 0) or 0)
            res = float(row.get("Resultado_Indicador_Agregado", 0) or 0)
            dias_exec = float(row.get("Dias_Gastos_Exec_Agregado", 0) or 0)
            
            # 1. Trata andamentos especiais
            if andamento in ["Não Demandada", "Não demandada", "Não_demandada"]:
                return "Não Demandada"
                
            if andamento == "Cancelada":
                return "Cancelada - Sem Justificativa" if justif == "" else "Cancelada (Justificada)"
            
            # 2. Avalia se a Ação atingiu o critério de Executada (Meta >= 80% OU Meta=0 com dias > 0)
            atingiu_meta = False
            if meta > 0:
                if (res / meta) >= 0.8:
                    atingiu_meta = True
            elif meta == 0 and dias_exec > 0:
                atingiu_meta = True
                
            if atingiu_meta:
                return "Executada"

            # 3. Se não atingiu, avalia prazo (data de término) e justificativa
            if andamento in ["Planejada", "Planejado", "Planejadas", "Não Executada", ""]:
                if pd.notna(dt_fim):
                    if dt_fim >= hoje:
                        return "Planejada"
                    else:
                        return "Não Executada - Sem Justificativa" if justif == "" else "Não Executada - Justificada"
                else:
                    ano_str = str(row.get("Ano da Ação", "")).split('.')[0]
                    if ano_str.isdigit() and int(ano_str) < hoje.year:
                        return "Não Executada - Sem Justificativa" if justif == "" else "Não Executada - Justificada"
                    return "Planejada"
                    
            return andamento

        df_dash_acao["Status de Execução"] = df_dash_acao.apply(classificar_status_acao, axis=1)

        # 🚀 Mapeamento composto seguro (Ação + UF) para propagar o status para as atividades
        mapa_status_acao = df_dash_acao.set_index(["Número da Ação PNAPA", "UF_Acao_PNAPA"])["Status de Execução"].to_dict()
        df_dash_atv["Status de Execução"] = df_dash_atv.apply(
            lambda r: mapa_status_acao.get((r["Número da Ação PNAPA"], r["UF_Acao_PNAPA"]), "Planejada"), axis=1
        )

        
        # =====================================================================
        # 3. BARRA SUPERIOR DE FILTROS FIXA (STICKY TOP BAR)
        # =====================================================================
        todas_chaves_filtros = [
            "fd_ano", "fd_uf", "fd_lot", "fd_srv", "fd_origem",
            "fd_pna", "fd_tema", "fd_imp", "fd_obj", 
            "fd_tipo", "fd_perigo", "fd_and", "fd_status_acao"
        ]

        def aplicar_filtros_dash(df_orig, dict_filtros, chave_ignorar=None):
            df_res = df_orig.copy()
            for k, (col_nome, val) in dict_filtros.items():
                if k == chave_ignorar or val in ["Todos", "Todas", None, ""]: continue
                if col_nome == "Ano da Ação":
                    df_res = df_res[df_res["Ano da Ação"].astype(str).str.split('.').str[0] == str(val)]
                elif col_nome == "Data_Inicio_DT":
                    if isinstance(val, (tuple, list)) and len(val) == 2:
                        ts_ini = pd.to_datetime(val[0])
                        ts_fim = pd.to_datetime(val[1]) + pd.Timedelta(hours=23, minutes=59, seconds=59)
                        df_res = df_res[df_res["Data_Inicio_DT"].isna() | ((df_res["Data_Inicio_DT"] >= ts_ini) & (df_res["Data_Inicio_DT"] <= ts_fim))]
                else:
                    if col_nome in df_res.columns:
                        df_res = df_res[df_res[col_nome].astype(str).str.strip() == str(val).strip()]
            return df_res

        def limpar_filtros_dashboard():
            for k in todas_chaves_filtros: st.session_state[k] = "Todos"
            if "valor_slider_data" in st.session_state: del st.session_state["valor_slider_data"]
            if "clique_mes" in st.session_state: del st.session_state["clique_mes"]
            if "clique_atv" in st.session_state: del st.session_state["clique_atv"]

        for k in todas_chaves_filtros:
            if k not in st.session_state: st.session_state[k] = "Todos"

        filtros_d = {
            "ano": ("Ano da Ação", st.session_state["fd_ano"]),
            "uf": ("UF_Acao_PNAPA", st.session_state["fd_uf"]),
            "lot": ("Lotação", st.session_state["fd_lot"]),
            "srv": ("Servidor", st.session_state["fd_srv"]),
            "origem": ("Origem do Recurso", st.session_state["fd_origem"]),
            "pna": ("Número da Ação PNAPA", st.session_state["fd_pna"]),
            "tema": ("Tema da Atividade", st.session_state["fd_tema"]),
            "imp": ("Importância da Atividade", st.session_state["fd_imp"]),
            "obj": ("Objetivo da Atividade", st.session_state["fd_obj"]),
            "tipo": ("Tipo de Atividade", st.session_state["fd_tipo"]),
            "perigo": ("Periculosidade/Insalubridade", st.session_state["fd_perigo"]),
            "and": ("Andamento", st.session_state["fd_and"]),
            "status_acao": ("Status de Execução", st.session_state["fd_status_acao"]),
            "data": ("Data_Inicio_DT", st.session_state.get("valor_slider_data", None))
        }

        with st.container(key="sticky_filter_container"):
            c_filt1, c_filt2, c_filt3, c_filt4 = st.columns([1, 1.2, 1.2, 0.5])
            
            with c_filt1:
                with st.popover("📅 Período Considerado", use_container_width=True):
                    df_p_ano = aplicar_filtros_dash(df_dash_atv, filtros_d, "ano")
                    anos_disp = ["Todos"] + sorted([str(int(a)) for a in df_p_ano["Ano da Ação"].dropna().unique() if str(a).strip().isdigit()], reverse=True)
                    idx_ano = anos_disp.index(filtros_d["ano"][1]) if filtros_d["ano"][1] in anos_disp else 0
                    f_ano = st.selectbox("Ano da Ação:", anos_disp, index=idx_ano, key="fd_ano")
                    filtros_d["ano"] = ("Ano da Ação", f_ano)

                    df_p_data = aplicar_filtros_dash(df_dash_atv, filtros_d, "data")
                    dts_validas = df_p_data["Data_Inicio_DT"].dropna()
                    
                    min_dt_val = dts_validas.min().date() if not dts_validas.empty else date(2025, 1, 1)
                    max_dt_val = dts_validas.max().date() if not dts_validas.empty else date(2026, 12, 31)
                    if min_dt_val >= max_dt_val: max_dt_val = min_dt_val + pd.Timedelta(days=1)
                    
                    val_atual = st.session_state.get("valor_slider_data", (min_dt_val, max_dt_val))
                    v_start = max(min_dt_val, min(val_atual[0], max_dt_val))
                    v_end = max(min_dt_val, min(val_atual[1], max_dt_val))
                    if v_start > v_end: v_start = min_dt_val

                    f_dt = st.slider("Data de Início:", min_value=min_dt_val, max_value=max_dt_val, value=(v_start, v_end), format="DD/MM/YYYY")
                    st.session_state["valor_slider_data"] = f_dt
                    filtros_d["data"] = ("Data_Inicio_DT", f_dt)

            with c_filt2:
                with st.popover("🗺️ UF / Lotação / Servidor / Recurso", use_container_width=True):
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

                    df_p_origem = aplicar_filtros_dash(df_dash_atv, filtros_d, "origem")
                    origens_disp = ["Todos"] + sorted([o for o in df_p_origem["Origem do Recurso"].dropna().astype(str).str.strip().unique() if o != ""])
                    idx_origem = origens_disp.index(filtros_d["origem"][1]) if filtros_d["origem"][1] in origens_disp else 0
                    f_origem = st.selectbox("Origem do Recurso:", origens_disp, index=idx_origem, key="fd_origem")
                    filtros_d["origem"] = ("Origem do Recurso", f_origem)

            with c_filt3:
                with st.popover("🏷️ Classificação Temática", use_container_width=True):
                    df_p_status_acao = aplicar_filtros_dash(df_dash_acao, filtros_d, "status_acao")
                    status_acao_disp = ["Todos"] + sorted([s for s in df_p_status_acao["Status de Execução"].dropna().astype(str).unique() if s != ""])
                    idx_status_acao = status_acao_disp.index(filtros_d["status_acao"][1]) if filtros_d["status_acao"][1] in status_acao_disp else 0
                    f_status_acao = st.selectbox("Status da Ação (Macro):", status_acao_disp, index=idx_status_acao, key="fd_status_acao")
                    filtros_d["status_acao"] = ("Status de Execução", f_status_acao)

                    df_p_and = aplicar_filtros_dash(df_dash_atv, filtros_d, "and")
                    ands_disp = ["Todos"] + sorted([a for a in df_p_and["Andamento"].dropna().astype(str).str.strip().unique() if a != ""])
                    idx_and = ands_disp.index(filtros_d["and"][1]) if filtros_d["and"][1] in ands_disp else 0
                    f_and = st.selectbox("Andamento (Atividades):", ands_disp, index=idx_and, key="fd_and")
                    filtros_d["and"] = ("Andamento", f_and)

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

                    df_p_imp = aplicar_filtros_dash(df_dash_atv, filtros_d, "imp")
                    imps_disp = ["Todos"] + sorted([i for i in df_p_imp["Importância da Atividade"].dropna().astype(str).str.strip().unique() if i != ""])
                    idx_imp = imps_disp.index(filtros_d["imp"][1]) if filtros_d["imp"][1] in imps_disp else 0
                    f_imp = st.selectbox("Importância da Atividade:", imps_disp, index=idx_imp, key="fd_imp")
                    filtros_d["imp"] = ("Importância da Atividade", f_imp)

                    df_p_obj = aplicar_filtros_dash(df_dash_atv, filtros_d, "obj")
                    objs_disp = ["Todos"] + sorted([o for o in df_p_obj["Objetivo da Atividade"].dropna().astype(str).str.strip().unique() if o != ""])
                    idx_obj = objs_disp.index(filtros_d["obj"][1]) if filtros_d["obj"][1] in objs_disp else 0
                    f_obj = st.selectbox("Objetivo da Atividade:", objs_disp, index=idx_obj, key="fd_obj")
                    filtros_d["obj"] = ("Objetivo da Atividade", f_obj)

                    df_p_tipo = aplicar_filtros_dash(df_dash_atv, filtros_d, "tipo")
                    tipos_disp = ["Todos"] + sorted([t for t in df_p_tipo["Tipo de Atividade"].dropna().astype(str).str.strip().unique() if t != ""])
                    idx_tipo = tipos_disp.index(filtros_d["tipo"][1]) if filtros_d["tipo"][1] in tipos_disp else 0
                    f_tipo = st.selectbox("Tipo de Atividade:", tipos_disp, index=idx_tipo, key="fd_tipo")
                    filtros_d["tipo"] = ("Tipo de Atividade", f_tipo)

                    df_p_perigo = aplicar_filtros_dash(df_dash_atv, filtros_d, "perigo")
                    perigos_disp = ["Todos"] + sorted([p for p in df_p_perigo["Periculosidade/Insalubridade"].dropna().astype(str).str.strip().unique() if p != ""])
                    idx_perigo = perigos_disp.index(filtros_d["perigo"][1]) if filtros_d["perigo"][1] in perigos_disp else 0
                    f_perigo = st.selectbox("Periculosidade/Insalubridade:", perigos_disp, index=idx_perigo, key="fd_perigo")
                    filtros_d["perigo"] = ("Periculosidade/Insalubridade", f_perigo)

            with c_filt4:
                st.button("🧹 Limpar", use_container_width=True, on_click=limpar_filtros_dashboard)

        # --- APLICAÇÃO GERAL DOS FILTROS ---
        df_filt_atv = aplicar_filtros_dash(df_dash_atv, filtros_d, None)
        df_filt_acao = aplicar_filtros_dash(df_dash_acao, filtros_d, chave_ignorar="and") 

        # Filtros Cruzados Visuais
        c_mes = st.session_state.get("clique_mes")
        c_atv = st.session_state.get("clique_atv")
        
        df_for_gantt = df_filt_atv.copy()
        if c_mes: df_for_gantt = df_for_gantt[df_for_gantt["Mes_Nome"] == c_mes]

        df_for_metrics = df_for_gantt.copy()
        if c_atv: df_for_metrics = df_for_metrics[df_for_metrics["Nome da Atividade"] == c_atv]

        if c_mes or c_atv:
            msg = "👆 Filtros Visuais Ativos na Aba Operacional: "
            if c_mes: msg += f"**Mês: {c_mes.capitalize()}** | "
            if c_atv: msg += f"**Atividade: {c_atv}**"
            st.warning(msg)
            if st.button("✕ Remover Seleções Visuais"):
                if "clique_mes" in st.session_state: del st.session_state["clique_mes"]
                if "clique_atv" in st.session_state: del st.session_state["clique_atv"]
                st.rerun()

        st.markdown("---")

        # =====================================================================
        # 4. NAVEGAÇÃO POR ABAS TEMÁTICAS
        # =====================================================================
        tab_exec, tab_oper, tab_gov, tab_desemp = st.tabs([
            "📊 Visão Executiva (Nacional)", 
            "🗓️ Operações & Calendário", 
            "⚖️ Governança & Carga (Ações)", 
            "⭐ Desempenho de Equipes"
        ])

        # ---------------------------------------------------------------------
        # ABA 1: VISÃO EXECUTIVA E CONSOLIDAÇÃO DO PNAPA
        # ---------------------------------------------------------------------
        with tab_exec:
            st.markdown("### Visão Geral do Portfólio")
            
            visao_consolidacao = st.radio(
                "Selecione a perspectiva de cálculo da Execução:", 
                [
                    "🎯 Metas Físicas (Atingimento de Indicadores)", 
                    "💰 Orçamento (Execução Financeira)",
                    "⏳ Esforço Operacional (Dias Gastos)"
                ], 
                horizontal=True
            )

            # 1. Definição de Parâmetros e Limiares
            if "Metas Físicas" in visao_consolidacao:
                st.caption("Consolidação baseada no atingimento de **80% ou mais** da meta dos indicadores (considera apenas atividades concluídas).")
                atv_base = df_filt_atv[df_filt_atv["Andamento"] == "Concluída"]
                col_meta = "Meta_Indicador"
                col_res = "Resultado_Indicador"
                nome_col_pct = "% de Ações Executadas (Meta Física ≥ 80%)"
                nome_col_atingidas = "Ações c/ Meta Atingida"
                card_atingidas_label = "🏆 Ações c/ Meta Atingida (Nac.)"
                limiar_execucao = 0.8
            elif "Orçamento" in visao_consolidacao:
                st.caption("Consolidação baseada na execução de **50% ou mais** do orçamento planejado (considera os gastos de todas as atividades do período).")
                atv_base = df_filt_atv 
                col_meta = "Rec_Plan_Total"
                col_res = "Rec_Exec_Total"
                nome_col_pct = "% de Ações Executadas (Orçamento ≥ 50%)"
                nome_col_atingidas = "Ações c/ Orçamento Executado"
                card_atingidas_label = "💳 Ações Executadas (Nac. ≥ 50%)"
                limiar_execucao = 0.5
            else:
                st.caption("Consolidação baseada na execução de **50% ou mais** dos dias planejados (considera o esforço de todas as atividades do período).")
                atv_base = df_filt_atv 
                col_meta = "Dias_Gastos_Plan"
                col_res = "Dias_Gastos_Exec"
                nome_col_pct = "% de Ações Executadas (Esforço ≥ 50%)"
                nome_col_atingidas = "Ações c/ Esforço Executado"
                card_atingidas_label = "⏳ Ações Executadas (Nac. ≥ 50%)"
                limiar_execucao = 0.5

            # 2. Processamento e Cálculo
            if not df_filt_acao.empty:
                meta_uf = df_filt_acao.groupby(["Número da Ação PNAPA", "UF_Acao_PNAPA"])[col_meta].sum().reset_index()
                res_uf = atv_base.groupby(["Número da Ação PNAPA", "UF_Acao_PNAPA"])[col_res].sum().reset_index()
                
                df_uf_calc = pd.merge(meta_uf, res_uf, on=["Número da Ação PNAPA", "UF_Acao_PNAPA"], how="left").fillna(0)
                
                def calc_pct(row):
                    m = float(row[col_meta])
                    r = float(row[col_res])
                    if m > 0: return r / m
                    if r > 0: return 1.0
                    return 0.0
                    
                df_uf_calc["Pct_Exec"] = df_uf_calc.apply(calc_pct, axis=1)
                df_uf_calc["Executada"] = (df_uf_calc["Pct_Exec"] >= limiar_execucao).astype(int)
                
                tab1_uf = df_uf_calc.groupby("UF_Acao_PNAPA").agg(
                    Acoes_Planejadas=('Número da Ação PNAPA', 'count'),
                    Acoes_Executadas=('Executada', 'sum')
                ).reset_index()
                tab1_uf.rename(columns={"UF_Acao_PNAPA": "UF / Nível"}, inplace=True)
                tab1_uf = tab1_uf[tab1_uf["UF / Nível"].astype(str).str.strip() != ""]
                tab1_uf[nome_col_pct] = (tab1_uf["Acoes_Executadas"] / tab1_uf["Acoes_Planejadas"]) * 100
                
                meta_nac = df_filt_acao.groupby("Número da Ação PNAPA")[col_meta].sum().reset_index()
                res_nac = atv_base.groupby("Número da Ação PNAPA")[col_res].sum().reset_index()
                
                df_nac_calc = pd.merge(meta_nac, res_nac, on="Número da Ação PNAPA", how="left").fillna(0)
                df_nac_calc["Pct_Exec"] = df_nac_calc.apply(calc_pct, axis=1)
                df_nac_calc["Executada"] = (df_nac_calc["Pct_Exec"] >= limiar_execucao).astype(int)
                
                total_nac_plan = len(df_nac_calc)
                total_nac_exec = int(df_nac_calc["Executada"].sum())
                pct_nac_exec = (total_nac_exec / total_nac_plan * 100) if total_nac_plan > 0 else 0
            else:
                total_nac_plan, total_nac_exec, pct_nac_exec = 0, 0, 0
                df_nac_calc, tab1_uf = pd.DataFrame(), pd.DataFrame()

            # 3. Totais Financeiros e de Dias
            rec_plan_total = pd.to_numeric(df_filt_acao["Rec_Plan_Total"], errors='coerce').fillna(0).sum()
            dias_plan_total = pd.to_numeric(df_filt_acao["Dias_Gastos_Plan"], errors='coerce').fillna(0).sum()
            
            rec_exec_total = pd.to_numeric(df_filt_atv["Rec_Exec_Total"], errors='coerce').fillna(0).sum()
            dias_exec_total = pd.to_numeric(df_filt_atv["Dias_Gastos_Exec"], errors='coerce').fillna(0).sum()
            
            pct_rec_exec = (rec_exec_total / rec_plan_total * 100) if rec_plan_total > 0 else 0.0
            pct_dias_exec = (dias_exec_total / dias_plan_total * 100) if dias_plan_total > 0 else 0.0

            # --- CARTÕES DE MÉTRICAS FORMATADOS NO PADRÃO BR ---
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("🎯 Ações Planejadas (Nacional)", f"{total_nac_plan}")
            col_m2.metric("💰 Orçamento Planejado (Ações)", formatar_moeda_br(rec_plan_total))
            col_m3.metric("📅 Dias Planejados (Ações)", formatar_numero_br(dias_plan_total, 1))
            
            col_m4, col_m5, col_m6 = st.columns(3)
            col_m4.metric(card_atingidas_label, f"{total_nac_exec}", f"{formatar_numero_br(pct_nac_exec, 1)}% do total")
            col_m5.metric("💳 Orçamento Executado (Ativ.)", formatar_moeda_br(rec_exec_total), f"{formatar_numero_br(pct_rec_exec, 1)}% do planejado")
            col_m6.metric("⏳ Dias Executados (Ativ.)", formatar_numero_br(dias_exec_total, 1), f"{formatar_numero_br(pct_dias_exec, 1)}% do planejado")
            
            st.markdown("---")
            st.markdown("### 🏆 Status de Execução Geral do PNAPA (Por UF e Nacional)")

            if not df_filt_acao.empty:
                linha_nacional = pd.DataFrame([{
                    "UF / Nível": "🇧🇷 NACIONAL (Consolidado Global)",
                    nome_col_pct: pct_nac_exec,
                    "Acoes_Planejadas": total_nac_plan,
                    "Acoes_Executadas": total_nac_exec
                }])
                
                tab1_uf = pd.concat([tab1_uf, linha_nacional], ignore_index=True)
                tab1_uf = tab1_uf[["UF / Nível", nome_col_pct, "Acoes_Planejadas", "Acoes_Executadas"]]
                tab1_uf.columns = ["UF / Nível", nome_col_pct, "No. Ações Planejadas", nome_col_atingidas]
                
                def cor_percentual(val):
                    if pd.isna(val) or isinstance(val, str): return ''
                    if val < 50: return 'background-color: #fca5a5; color: black; font-weight: bold;'
                    elif val < 80: return 'background-color: #fde047; color: black; font-weight: bold;'
                    elif val < 90: return 'background-color: #86efac; color: black; font-weight: bold;'
                    else: return 'background-color: #93c5fd; color: black; font-weight: bold;'

                try:
                    t1_styled = tab1_uf.style.applymap(cor_percentual, subset=[nome_col_pct]).format({nome_col_pct: lambda v: f"{formatar_numero_br(v, 1)}%"})
                except AttributeError:
                    t1_styled = tab1_uf.style.map(cor_percentual, subset=[nome_col_pct]).format({nome_col_pct: lambda v: f"{formatar_numero_br(v, 1)}%"})
                    
                st.dataframe(t1_styled, use_container_width=True, hide_index=True)
                
                # --- Tabela 2: Por Ação Nacional Formatada no Padrão BR ---
                st.markdown("<br>#### 🎯 Status de Execução Geral do PNAPA (Por Ação Nacional)", unsafe_allow_html=True)
                nomes_acoes = df_filt_acao[["Número da Ação PNAPA", "Nome da Ação PNAPA"]].drop_duplicates("Número da Ação PNAPA")
                tab2_acao = pd.merge(df_nac_calc, nomes_acoes, on="Número da Ação PNAPA", how="left")
                
                tab2_acao["Ação PNAPA"] = tab2_acao["Número da Ação PNAPA"] + " - " + tab2_acao["Nome da Ação PNAPA"]
                tab2_acao["% Execução"] = tab2_acao["Pct_Exec"] * 100
                tab2_acao = tab2_acao[["Ação PNAPA", "% Execução", col_meta, col_res]]
                
                if "Metas Físicas" in visao_consolidacao:
                    tab2_acao.columns = ["Ação PNAPA", "% Execução", "Meta (Física)", "Resultado (Físico)"]
                    format_dict = {
                        "% Execução": lambda v: f"{formatar_numero_br(v, 1)}%",
                        "Meta (Física)": lambda v: formatar_numero_br(v, 1),
                        "Resultado (Físico)": lambda v: formatar_numero_br(v, 1)
                    }
                elif "Orçamento" in visao_consolidacao:
                    tab2_acao.columns = ["Ação PNAPA", "% Execução", "Orçamento Planejado", "Orçamento Executado"]
                    format_dict = {
                        "% Execução": lambda v: f"{formatar_numero_br(v, 1)}%",
                        "Orçamento Planejado": lambda v: formatar_moeda_br(v),
                        "Orçamento Executado": lambda v: formatar_moeda_br(v)
                    }
                else:
                    tab2_acao.columns = ["Ação PNAPA", "% Execução", "Dias Planejados", "Dias Executados"]
                    format_dict = {
                        "% Execução": lambda v: f"{formatar_numero_br(v, 1)}%",
                        "Dias Planejados": lambda v: formatar_numero_br(v, 1),
                        "Dias Executados": lambda v: formatar_numero_br(v, 1)
                    }

                tab2_acao = tab2_acao.sort_values("% Execução", ascending=False).reset_index(drop=True)
                
                try:
                    t2_styled = tab2_acao.style.applymap(cor_percentual, subset=['% Execução']).format(format_dict)
                except AttributeError:
                    t2_styled = tab2_acao.style.map(cor_percentual, subset=['% Execução']).format(format_dict)
                    
                st.dataframe(t2_styled, use_container_width=True, hide_index=True)

                # --- Tabela 3: Pendências Críticas de Ações ---
                st.markdown("<br>#### 🚨 Pendências de Justificativa nas Ações (Mural de Atenção)", unsafe_allow_html=True)
                st.caption("Filtro automático das Ações não executadas/canceladas cujo prazo venceu sem inserção de justificativa.")
                
                tab3_acao = df_filt_acao.copy()
                if not tab3_acao.empty:
                    tab3_acao = tab3_acao[tab3_acao["Status de Execução"].isin(["Não Executada - Sem Justificativa", "Cancelada - Sem Justificativa"])]
                    
                    if not tab3_acao.empty:
                        tab3_acao["Ação PNAPA"] = tab3_acao["Número da Ação PNAPA"] + " - " + tab3_acao["Nome da Ação PNAPA"]
                        tab3_acao.rename(columns={"UF_Acao_PNAPA": "UF", "Justificativa_Acao_PNAPA": "Justificativa"}, inplace=True)
                        tab3_acao = tab3_acao[["UF", "Ação PNAPA", "Status de Execução", "Justificativa"]]
                        tab3_acao = tab3_acao.sort_values(by=["UF", "Ação PNAPA"])
                        
                        def cor_status_acao(val):
                            if pd.isna(val) or not isinstance(val, str): return ''
                            return 'background-color: #fca5a5; color: black; font-weight: bold;'
                            
                        try:
                            t3_styled = tab3_acao.style.applymap(cor_status_acao, subset=['Status de Execução'])
                        except AttributeError:
                            t3_styled = tab3_acao.style.map(cor_status_acao, subset=['Status de Execução'])
                            
                        st.dataframe(t3_styled, use_container_width=True, hide_index=True)
                    else:
                        st.success("🎉 Excelente! Nenhuma pendência de justificativa encontrada nos filtros selecionados.")
                else:
                    st.info("Nenhuma Ação encontrada para o filtro selecionado.")

            else:
                st.info("Nenhuma Ação encontrada para o filtro selecionado.")

        # ---------------------------------------------------------------------
        # ABA 2: OPERAÇÕES & CALENDÁRIO
        # ---------------------------------------------------------------------
        with tab_oper:
            st.markdown("### 🗓️ Gestão Operacional & Execução de Atividades")
            
            # 1. Classificação de Status
            def classificar_status_operacional(row):
                andamento = str(row.get("Andamento", "")).strip()
                doc = str(row.get("Doc_Probatorio_Exec", "")).strip()
                if doc.lower() in ["nan", "none", "null"]: doc = ""
                dt_fim = row.get("Data_Fim_DT")
                
                if andamento == "Concluída":
                    if not doc: return "Sem Documento de Conclusão"
                    return "Concluída"
                else:
                    if pd.notna(dt_fim) and hoje > dt_fim: return "Atrasada"
                    return "Prevista"

            df_filt_atv_oper = df_filt_atv.copy()
            df_filt_atv_oper["Status_Operacional"] = df_filt_atv_oper.apply(classificar_status_operacional, axis=1)

            # 2. Métricas do Topo
            id_atv_series = df_filt_atv_oper["Codigo_Atividade"].replace("", pd.NA).fillna(df_filt_atv_oper["Nome da Atividade"])
            total_atv_unicas_plan = int(id_atv_series.nunique())
            
            atv_exec_df = df_filt_atv_oper[df_filt_atv_oper["Status_Operacional"].isin(["Concluída", "Sem Documento de Conclusão"])]
            id_atv_exec_series = atv_exec_df["Codigo_Atividade"].replace("", pd.NA).fillna(atv_exec_df["Nome da Atividade"])
            total_atv_unicas_exec = int(id_atv_exec_series.nunique())
            pct_atv_unicas_exec = (total_atv_unicas_exec / total_atv_unicas_plan * 100) if total_atv_unicas_plan > 0 else 0.0

            rec_plan_atv = pd.to_numeric(df_filt_atv_oper["Rec_Plan_Total"], errors='coerce').fillna(0).sum()
            rec_exec_atv = pd.to_numeric(df_filt_atv_oper["Rec_Exec_Total"], errors='coerce').fillna(0).sum()
            pct_rec_atv = (rec_exec_atv / rec_plan_atv * 100) if rec_plan_atv > 0 else 0.0

            dias_plan_atv = pd.to_numeric(df_filt_atv_oper["Dias_Gastos_Plan"], errors='coerce').fillna(0).sum()
            dias_exec_atv = pd.to_numeric(df_filt_atv_oper["Dias_Gastos_Exec"], errors='coerce').fillna(0).sum()
            pct_dias_atv = (dias_exec_atv / dias_plan_atv * 100) if dias_plan_atv > 0 else 0.0

            # Cartões de Métricas Formatados em Padrão BR
            col_op1, col_op2, col_op3 = st.columns(3)
            col_op1.metric("📌 Atividades Únicas Planejadas", f"{total_atv_unicas_plan}")
            col_op2.metric("💰 Orçamento Planejado (Ativ.)", formatar_moeda_br(rec_plan_atv))
            col_op3.metric("📅 Dias Planejados (Ativ.)", formatar_numero_br(dias_plan_atv, 1))

            col_op4, col_op5, col_op6 = st.columns(3)
            col_op4.metric("✅ Atividades Únicas Executadas", f"{total_atv_unicas_exec}", f"{formatar_numero_br(pct_atv_unicas_exec, 1)}% do planejado")
            col_op5.metric("💳 Orçamento Executado (Ativ.)", formatar_moeda_br(rec_exec_atv), f"{formatar_numero_br(pct_rec_atv, 1)}% do planejado")
            col_op6.metric("⏳ Dias Executados (Ativ.)", formatar_numero_br(dias_exec_atv, 1), f"{formatar_numero_br(pct_dias_atv, 1)}% do planejado")

            st.markdown("---")

            # 3. Sub-Abas
            subtab_cal, subtab_fin, subtab_esf = st.tabs([
                "🗓️ 1. Calendário & Cronograma", 
                "💰 2. Execução Financeira", 
                "⏳ 3. Esforço & Dedicação"
            ])

            cor_mapa_gantt = {
                "Concluída": "#22c55e",
                "Sem Documento de Conclusão": "#facc15",
                "Atrasada": "#ef4444",
                "Prevista": "#60a5fa"
            }

            # =================================================================
            # SUB-ABA 1: CALENDÁRIO
            # =================================================================
            with subtab_cal:
                st.markdown("#### 🗓️ Cronograma e Linha do Tempo das Atividades")
                
                df_gantt_base = df_filt_atv_oper.dropna(subset=["Data_Inicio_DT", "Data_Fim_DT"]).copy()
                
                if not df_gantt_base.empty:
                    ano_ref_series = df_gantt_base["Data_Inicio_DT"].dt.year.dropna()
                    ano_ref = int(ano_ref_series.mode()[0]) if not ano_ref_series.empty else hoje.year

                    col_nav1, col_nav2 = st.columns([1, 1.8])
                    
                    with col_nav1:
                        modo_escala = st.radio(
                            "Escala de Visualização:", 
                            ["🗓️ Mensal", "📊 Trimestral", "🌐 Anual (Completo)"], 
                            horizontal=True,
                            key="gantt_escala_modo"
                        )
                    
                    lista_meses_nomes = [
                        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                    ]

                    with col_nav2:
                        if modo_escala == "🗓️ Mensal":
                            mes_idx_padrao = (hoje.month - 1) if hoje.year == ano_ref else 0
                            mes_selecionado = st.selectbox("Selecione o Mês:", lista_meses_nomes, index=mes_idx_padrao, key="gantt_mes_sel")
                            num_mes = lista_meses_nomes.index(mes_selecionado) + 1
                            
                            ts_ini = pd.Timestamp(year=ano_ref, month=num_mes, day=1)
                            ts_fim = (ts_ini + pd.offsets.MonthEnd(1)) + pd.Timedelta(hours=23, minutes=59, seconds=59)
                            label_periodo = f"{mes_selecionado} de {ano_ref}"
                            formato_data_eixo = "%d/%m"
                            
                        elif modo_escala == "📊 Trimestral":
                            trimestres = [
                                "1º Trimestre (Jan - Mar)", 
                                "2º Trimestre (Abr - Jun)", 
                                "3º Trimestre (Jul - Set)", 
                                "4º Trimestre (Out - Dez)"
                            ]
                            trim_selecionado = st.selectbox("Selecione o Trimestre:", trimestres, index=0, key="gantt_trim_sel")
                            num_trim = trimestres.index(trim_selecionado) + 1
                            
                            mes_ini_trim = (num_trim - 1) * 3 + 1
                            mes_fim_trim = num_trim * 3
                            
                            ts_ini = pd.Timestamp(year=ano_ref, month=mes_ini_trim, day=1)
                            ts_fim = (pd.Timestamp(year=ano_ref, month=mes_fim_trim, day=1) + pd.offsets.MonthEnd(1)) + pd.Timedelta(hours=23, minutes=59, seconds=59)
                            label_periodo = f"{trim_selecionado} de {ano_ref}"
                            formato_data_eixo = "%d/%m"
                            
                        else:
                            ts_ini = pd.Timestamp(year=ano_ref, month=1, day=1)
                            ts_fim = pd.Timestamp(year=ano_ref, month=12, day=31, hour=23, minute=59, second=59)
                            label_periodo = f"Ano Completo de {ano_ref}"
                            formato_data_eixo = "%b %Y"

                    df_gantt_periodo = df_gantt_base[
                        (df_gantt_base["Data_Inicio_DT"] <= ts_fim) & 
                        (df_gantt_base["Data_Fim_DT"] >= ts_ini)
                    ].copy()

                    if not df_gantt_periodo.empty:
                        df_gantt_agg = df_gantt_periodo.groupby(["Codigo_Atividade", "Nome da Atividade", "Status_Operacional"]).agg(
                            Data_Inicio=('Data_Inicio_DT', 'min'),
                            Data_Fim=('Data_Fim_DT', 'max'),
                            Equipe=('Servidor', lambda x: ", ".join(sorted([str(s) for s in x.dropna().unique()]))),
                            UF_Acao=('UF_Acao_PNAPA', 'first'),
                            SEI=('Doc_Probatorio_Exec', 'first')
                        ).reset_index()
                        
                        df_gantt_agg["Rotulo_Atividade"] = df_gantt_agg["Codigo_Atividade"].replace("", "S/C") + " - " + df_gantt_agg["Nome da Atividade"]
                        df_gantt_agg["Início"] = df_gantt_agg["Data_Inicio"].dt.strftime('%d/%m/%Y')
                        df_gantt_agg["Término"] = df_gantt_agg["Data_Fim"].dt.strftime('%d/%m/%Y')
                        df_gantt_agg["Data_Fim_Plot"] = df_gantt_agg["Data_Fim"] + pd.Timedelta(hours=23, minutes=59, seconds=59)
                        df_gantt_agg = df_gantt_agg.sort_values(by="Data_Inicio", ascending=True).reset_index(drop=True)

                        fig_gantt = px.timeline(
                            df_gantt_agg, 
                            x_start="Data_Inicio", 
                            x_end="Data_Fim_Plot", 
                            y="Rotulo_Atividade", 
                            color="Status_Operacional",
                            color_discrete_map=cor_mapa_gantt,
                            hover_data={
                                "Início": True, "Término": True, "Equipe": True, 
                                "UF_Acao": True, "SEI": True, "Rotulo_Atividade": False, 
                                "Data_Fim_Plot": False, "Data_Inicio": False
                            }
                        )
                        fig_gantt.update_yaxes(autorange="reversed", title_text="", showticklabels=True)
                        fig_gantt.update_xaxes(
                            title_text="", rangeslider_visible=False, tickformat=formato_data_eixo,
                            range=[ts_ini, ts_fim] if modo_escala != "🌐 Anual (Completo)" else None
                        )
                        
                        altura_dinamica = max(280, min(800, len(df_gantt_agg) * 36 + 100))
                        fig_gantt.update_layout(
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title_text=""),
                            margin=dict(t=10, b=0, l=0, r=0), height=altura_dinamica, plot_bgcolor="white",
                            hoverlabel=dict(align="left", bgcolor="white", font_size=12)
                        )
                        st.plotly_chart(fig_gantt, use_container_width=True)
                    else:
                        st.info(f"ℹ️ Nenhuma atividade com execução prevista ou realizada para **{label_periodo}**.")
                else:
                    st.info("Não há atividades com datas válidas de início e término no período filtrado.")

                st.markdown("<br>##### 📋 Detalhamento das Atividades Filtradas", unsafe_allow_html=True)
                
                def badge_status(val):
                    if val == "Concluída": return "🟢 Concluída"
                    if val == "Sem Documento de Conclusão": return "🟡 Sem Doc. Conclusão"
                    if val == "Atrasada": return "🔴 Atrasada"
                    return "🔵 Prevista"

                cols_tab_cal = ["Id", "Codigo_Atividade", "Nome da Atividade", "Status_Operacional", "Servidor", "UF_Acao_PNAPA", "Data_Inicio_DT", "Data_Fim_DT", "Doc_Probatorio_Exec"]
                df_tab_cal = df_filt_atv_oper[[c for c in cols_tab_cal if c in df_filt_atv_oper.columns]].copy()
                df_tab_cal["Status"] = df_tab_cal["Status_Operacional"].apply(badge_status)
                df_tab_cal["Data de Início"] = df_tab_cal["Data_Inicio_DT"].dt.date
                df_tab_cal["Data de Término"] = df_tab_cal["Data_Fim_DT"].dt.date
                df_tab_cal = df_tab_cal.drop(columns=["Status_Operacional", "Data_Inicio_DT", "Data_Fim_DT"])
                
                ordem_cols = ["Id", "Codigo_Atividade", "Nome da Atividade", "Servidor", "UF_Acao_PNAPA", "Data de Início", "Data de Término", "Doc_Probatorio_Exec", "Status"]
                df_tab_cal = df_tab_cal[[c for c in ordem_cols if c in df_tab_cal.columns]].sort_values(by=["Data de Início", "Id"], ascending=[True, True]).reset_index(drop=True)
                
                config_cols_cal = {
                    "Data de Início": st.column_config.DateColumn("Data de Início", format="DD/MM/YYYY"),
                    "Data de Término": st.column_config.DateColumn("Data de Término", format="DD/MM/YYYY"),
                }
                st.dataframe(df_tab_cal, use_container_width=True, hide_index=True, column_config=config_cols_cal)

            # =================================================================
            # SUB-ABA 2: FINANCEIRO FORMATADA NO PADRÃO BR
            # =================================================================
            with subtab_fin:
                st.markdown("#### 💰 Acompanhamento Financeiro das Atividades")
                
                st.markdown("##### 📅 Execução Orçamentária Mensal (R$)")
                df_fin_mensal = df_filt_atv_oper.groupby("Mes_Inicio")[["Rec_Plan_Total", "Rec_Exec_Total"]].sum().reset_index()
                df_fin_mensal["Mes_Nome"] = df_fin_mensal["Mes_Inicio"].map(meses_pt)
                df_fin_mensal = df_fin_mensal.sort_values("Mes_Inicio")
                
                fig_fin = go.Figure()
                fig_fin.add_trace(go.Bar(
                    x=df_fin_mensal["Mes_Nome"], 
                    y=df_fin_mensal["Rec_Plan_Total"], 
                    name='Planejado', 
                    marker_color='#94b396', 
                    text=df_fin_mensal["Rec_Plan_Total"].apply(lambda v: formatar_moeda_br(v, casas=0)), 
                    textposition='outside'
                ))
                fig_fin.add_trace(go.Bar(
                    x=df_fin_mensal["Mes_Nome"], 
                    y=df_fin_mensal["Rec_Exec_Total"], 
                    name='Executado', 
                    marker_color='#4f7942', 
                    text=df_fin_mensal["Rec_Exec_Total"].apply(lambda v: formatar_moeda_br(v, casas=0)), 
                    textposition='outside'
                ))
                fig_fin.update_layout(
                    barmode='group', plot_bgcolor='rgba(0,0,0,0)', 
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), 
                    margin=dict(t=30, b=0, l=0, r=0), height=360
                )
                st.plotly_chart(fig_fin, use_container_width=True)

                st.markdown("<br>##### 📊 Orçamento por Categoria de Despesa", unsafe_allow_html=True)
                cols_custos = [
                    ("Diárias", "Rec_Plan_Diarias", "Rec_Exec_Diarias"),
                    ("Passagens", "Rec_Plan_Passagens", "Rec_Exec_Passagens"),
                    ("Outras Despesas", "Rec_Plan_Outras_Despesas", "Rec_Exec_Outras_Despesas")
                ]
                resumo_custos = []
                for label_c, col_p, col_e in cols_custos:
                    v_p = pd.to_numeric(df_filt_atv_oper[col_p], errors='coerce').fillna(0).sum()
                    v_e = pd.to_numeric(df_filt_atv_oper[col_e], errors='coerce').fillna(0).sum()
                    pct_c = (v_e / v_p * 100) if v_p > 0 else 0.0
                    resumo_custos.append({
                        "Categoria de Despesa": label_c,
                        "Orçamento Planejado": formatar_moeda_br(v_p),
                        "Orçamento Executado": formatar_moeda_br(v_e),
                        "% Executado": f"{formatar_numero_br(pct_c, 1)}%"
                    })
                st.dataframe(pd.DataFrame(resumo_custos), use_container_width=True, hide_index=True)

            # =================================================================
            # SUB-ABA 3: ESFORÇO FORMATADA NO PADRÃO BR
            # =================================================================
            with subtab_esf:
                st.markdown("#### ⏳ Acompanhamento do Esforço Operacional (Dias)")
                
                st.markdown("##### 📅 Esforço Mensal (Dias Gastos)")
                df_esf_mensal = df_filt_atv_oper.groupby("Mes_Inicio")[["Dias_Gastos_Plan", "Dias_Gastos_Exec"]].sum().reset_index()
                df_esf_mensal["Mes_Nome"] = df_esf_mensal["Mes_Inicio"].map(meses_pt)
                df_esf_mensal = df_esf_mensal.sort_values("Mes_Inicio")
                
                fig_esf = go.Figure()
                fig_esf.add_trace(go.Bar(
                    x=df_esf_mensal["Mes_Nome"], 
                    y=df_esf_mensal["Dias_Gastos_Plan"], 
                    name='Previstos', 
                    marker_color='#a3c1ad', 
                    text=df_esf_mensal["Dias_Gastos_Plan"].apply(lambda v: formatar_numero_br(v, 1)), 
                    textposition='outside'
                ))
                fig_esf.add_trace(go.Bar(
                    x=df_esf_mensal["Mes_Nome"], 
                    y=df_esf_mensal["Dias_Gastos_Exec"], 
                    name='Executados', 
                    marker_color='#557056', 
                    text=df_esf_mensal["Dias_Gastos_Exec"].apply(lambda v: formatar_numero_br(v, 1)), 
                    textposition='outside'
                ))
                fig_esf.update_layout(
                    barmode='group', plot_bgcolor='rgba(0,0,0,0)', 
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5), 
                    margin=dict(t=30, b=0, l=0, r=0), height=360
                )
                st.plotly_chart(fig_esf, use_container_width=True)

                st.markdown("<br>##### 👥 Esforço por Servidor", unsafe_allow_html=True)
                df_esf_srv = df_filt_atv_oper.groupby("Servidor").agg(
                    Atividades=('Id', 'count'),
                    Dias_Previstos=('Dias_Gastos_Plan', 'sum'),
                    Dias_Executados=('Dias_Gastos_Exec', 'sum')
                ).reset_index()
                df_esf_srv["% Cumprido"] = ((df_esf_srv["Dias_Executados"] / df_esf_srv["Dias_Previstos"]) * 100).fillna(0).apply(lambda v: f"{formatar_numero_br(v, 1)}%")
                df_esf_srv["Dias_Previstos"] = df_esf_srv["Dias_Previstos"].apply(lambda v: formatar_numero_br(v, 1))
                df_esf_srv["Dias_Executados"] = df_esf_srv["Dias_Executados"].apply(lambda v: formatar_numero_br(v, 1))
                df_esf_srv = df_esf_srv.sort_values(by="Atividades", ascending=False).reset_index(drop=True)
                st.dataframe(df_esf_srv, use_container_width=True, hide_index=True)

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

        

# --- TELA 1: VISUALIZAÇÃO E EDIÇÃO EM DUAS SUBPÁGINAS (AÇÕES vs ATIVIDADES) ---
elif modo == "📊 Visualizar Base":
    st.markdown("<h3 style='color: #03170a;'>📊 Central de Visualização & Gestão de Registros</h3>", unsafe_allow_html=True)
    
    if df_atual.empty:
        st.info("A base de dados do SharePoint está vazia.")
    else:
        hoje = pd.Timestamp(date.today())

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
            df_base_acoes = df_trabalho[
                (df_trabalho["Nível"].astype(str).str.strip() == "Ação") &
                (df_trabalho["Número da Ação PNAPA"].astype(str).str.strip().str.upper() != "DIPRO_GLOBAL")
            ].copy()
            st.caption(f"🎯 Total de Ações Estaduais cadastradas: **{len(df_base_acoes)}** registros.")
            
            if df_base_acoes.empty:
                st.info("Nenhuma Ação Estadual cadastrada na base.")
            else:
                # 1. CÁLCULO E PROPAGAÇÃO DO RESULTADO, % E STATUS DE EXECUÇÃO
                df_atv_temp = df_trabalho[df_trabalho["Nível"].astype(str).str.strip() == "Atividade"].copy()
                atv_concluidas_temp = df_atv_temp[df_atv_temp["Andamento"].astype(str).str.strip() == "Concluída"]
                
                agg_atv_pna = atv_concluidas_temp.groupby(["Número da Ação PNAPA", "UF_Acao_PNAPA"]).agg(
                    Resultado_Agregado=('Resultado_Indicador', lambda x: pd.to_numeric(x, errors='coerce').fillna(0).sum()),
                    Dias_Exec_Agregado=('Dias_Gastos_Exec', lambda x: pd.to_numeric(x, errors='coerce').fillna(0).sum())
                ).reset_index()

                df_base_acoes = pd.merge(df_base_acoes, agg_atv_pna, on=["Número da Ação PNAPA", "UF_Acao_PNAPA"], how="left")
                df_base_acoes["Resultado_Agregado"] = df_base_acoes["Resultado_Agregado"].fillna(0)
                df_base_acoes["Dias_Exec_Agregado"] = df_base_acoes["Dias_Exec_Agregado"].fillna(0)
                df_base_acoes["Resultado_Indicador"] = df_base_acoes["Resultado_Agregado"]

                def calc_pct_exec_acao_t1(row):
                    meta = float(pd.to_numeric(row.get("Meta_Indicador", 0), errors='coerce') or 0.0)
                    res = float(pd.to_numeric(row.get("Resultado_Agregado", 0), errors='coerce') or 0.0)
                    dias_exec = float(pd.to_numeric(row.get("Dias_Exec_Agregado", 0), errors='coerce') or 0.0)
                    if meta > 0:
                        return (res / meta) * 100.0
                    elif meta == 0 and (dias_exec > 0 or res > 0):
                        return 100.0
                    return 0.0

                df_base_acoes["% de Execução da Ação"] = df_base_acoes.apply(calc_pct_exec_acao_t1, axis=1)

                def calc_status_acao_t1(row):
                    andamento = str(row.get("Andamento", "")).strip()
                    justif = str(row.get("Justificativa_Acao_PNAPA", "")).strip()
                    if justif.lower() in ["nan", "none", "null"]: justif = ""
                    dt_fim = row.get("Data_Termino_Datetime")
                    
                    meta = float(pd.to_numeric(row.get("Meta_Indicador", 0), errors='coerce') or 0.0)
                    res = float(row.get("Resultado_Agregado", 0.0) or 0.0)
                    dias_exec = float(row.get("Dias_Exec_Agregado", 0.0) or 0.0)
                    
                    if andamento in ["Não Demandada", "Não demandada", "Não_demandada"]:
                        return "🟡 Não Demandada"
                    if andamento == "Cancelada":
                        return "🔴 Cancelada - Sem Justificativa" if justif == "" else "🟡 Cancelada (Justificada)"
                        
                    atingiu = False
                    if meta > 0:
                        if (res / meta) >= 0.8:
                            atingiu = True
                    elif meta == 0 and (dias_exec > 0 or res > 0):
                        atingiu = True
                        
                    if atingiu:
                        return "🟢 Executada"
                        
                    if andamento in ["Planejada", "Planejado", "Planejadas", "Não Executada", ""]:
                        if pd.notna(dt_fim):
                            if dt_fim >= hoje:
                                return "⚪ Planejada"
                            else:
                                return "🔴 Não Executada - Sem Justificativa" if justif == "" else "🟡 Não Executada - Justificada"
                        else:
                            ano_str = str(row.get("Ano da Ação", "")).split('.')[0]
                            if ano_str.isdigit() and int(ano_str) < hoje.year:
                                return "🔴 Não Executada - Sem Justificativa" if justif == "" else "🟡 Não Executada - Justificada"
                            return "⚪ Planejada"
                    return andamento

                df_base_acoes["Status de Execução"] = df_base_acoes.apply(calc_status_acao_t1, axis=1)

                # 2. INICIALIZAÇÃO SEGURA DOS FILTROS POPOVER
                for k in ["f_ano_ac", "f_pna_ac", "f_uf_ac", "f_papel_ac", "f_focal_ac", "f_status_ac", "f_and_ac", "f_tema_ac"]:
                    if k not in st.session_state:
                        st.session_state[k] = "Todas" if k in ["f_pna_ac", "f_uf_ac"] else "Todos"

                def limpar_filtros_acoes_t1():
                    for k in ["f_ano_ac", "f_pna_ac", "f_uf_ac", "f_papel_ac", "f_focal_ac", "f_status_ac", "f_and_ac", "f_tema_ac"]:
                        st.session_state[k] = "Todas" if k in ["f_pna_ac", "f_uf_ac"] else "Todos"
                    if "f_slider_dts_ac" in st.session_state:
                        del st.session_state["f_slider_dts_ac"]

                filtros_ac = {
                    "ano": ("Ano da Ação", st.session_state["f_ano_ac"]),
                    "pna": ("Número da Ação PNAPA", st.session_state["f_pna_ac"]),
                    "uf": ("UF_Acao_PNAPA", st.session_state["f_uf_ac"]),
                    "papel": ("Papel_Institucional", st.session_state["f_papel_ac"]),
                    "focal": ("Servidor", st.session_state["f_focal_ac"]),
                    "status": ("Status de Execução", st.session_state["f_status_ac"]),
                    "and": ("Andamento", st.session_state["f_and_ac"]),
                    "tema": ("Tema da Atividade", st.session_state["f_tema_ac"]),
                    "data": ("Data_Inicio_Datetime", st.session_state.get("f_slider_dts_ac", None))
                }

                # 3. BARRA DE FILTROS SUPERIOR COM POPOVERS
                c_fac1, c_fac2, c_fac3, c_fac4 = st.columns([1, 1.2, 1.2, 0.5])
                
                with c_fac1:
                    with st.popover("📅 Período Considerado", use_container_width=True):
                        df_p_ano = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "ano")
                        anos_ac = sorted([str(a).split('.')[0] for a in df_p_ano["Ano da Ação"].dropna().unique() if str(a).strip() != ""], reverse=True)
                        opcs_ano_ac = ["Todos"] + anos_ac
                        idx_ano_ac = opcs_ano_ac.index(filtros_ac["ano"][1]) if filtros_ac["ano"][1] in opcs_ano_ac else 0
                        f_ano_ac = st.selectbox("Ano:", opcs_ano_ac, index=idx_ano_ac, key="f_ano_ac")
                        filtros_ac["ano"] = ("Ano da Ação", f_ano_ac)

                        df_p_data = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "data")
                        dts_validas_ac = df_p_data["Data_Inicio_Datetime"].dropna()
                        min_dt_ac = dts_validas_ac.min().date() if not dts_validas_ac.empty else date(2025, 1, 1)
                        max_dt_ac = dts_validas_ac.max().date() if not dts_validas_ac.empty else date(2026, 12, 31)
                        if min_dt_ac >= max_dt_ac: max_dt_ac = min_dt_ac + pd.Timedelta(days=1)
                        
                        val_atual_sl = st.session_state.get("f_slider_dts_ac", (min_dt_ac, max_dt_ac))
                        v_start = max(min_dt_ac, min(val_atual_sl[0], max_dt_ac))
                        v_end = max(min_dt_ac, min(val_atual_sl[1], max_dt_ac))
                        if v_start > v_end: v_start = min_dt_ac

                        f_slider_dts_ac = st.slider("Data de Início:", min_value=min_dt_ac, max_value=max_dt_ac, value=(v_start, v_end), format="DD/MM/YYYY")
                        st.session_state["f_slider_dts_ac"] = f_slider_dts_ac
                        filtros_ac["data"] = ("Data_Inicio_Datetime", f_slider_dts_ac)

                with c_fac2:
                    with st.popover("🗺️ UF / Governança", use_container_width=True):
                        df_p_uf = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "uf")
                        ufs_ac = sorted([str(u).strip() for u in df_p_uf["UF_Acao_PNAPA"].dropna().unique() if str(u).strip() != ""])
                        opcs_uf_ac = ["Todas"] + ufs_ac
                        idx_uf_ac = opcs_uf_ac.index(filtros_ac["uf"][1]) if filtros_ac["uf"][1] in opcs_uf_ac else 0
                        f_uf_ac = st.selectbox("UF da Ação:", opcs_uf_ac, index=idx_uf_ac, key="f_uf_ac")
                        filtros_ac["uf"] = ("UF_Acao_PNAPA", f_uf_ac)

                        df_p_papel = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "papel")
                        papeis_disp = [p for p in ["Coordenação", "Apoio"] if p in df_p_papel["Papel_Institucional"].astype(str).str.strip().unique()]
                        opcs_papel_ac = ["Todos"] + (papeis_disp if papeis_disp else ["Coordenação", "Apoio"])
                        idx_papel_ac = opcs_papel_ac.index(filtros_ac["papel"][1]) if filtros_ac["papel"][1] in opcs_papel_ac else 0
                        f_papel_ac = st.selectbox("Papel da UF:", opcs_papel_ac, index=idx_papel_ac, key="f_papel_ac")
                        filtros_ac["papel"] = ("Papel_Institucional", f_papel_ac)

                        df_p_focal = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "focal")
                        focais_ac = sorted([str(s).strip() for s in df_p_focal["Servidor"].dropna().unique() if str(s).strip() != ""])
                        opcs_focal_ac = ["Todos"] + focais_ac
                        idx_focal_ac = opcs_focal_ac.index(filtros_ac["focal"][1]) if filtros_ac["focal"][1] in opcs_focal_ac else 0
                        f_focal_ac = st.selectbox("Ponto Focal:", opcs_focal_ac, index=idx_focal_ac, key="f_focal_ac")
                        filtros_ac["focal"] = ("Servidor", f_focal_ac)

                with c_fac3:
                    with st.popover("🏷️ Classificação & Status", use_container_width=True):
                        df_p_st = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "status")
                        status_disp_ac = ["Todos"] + sorted([s for s in df_p_st["Status de Execução"].dropna().astype(str).unique() if s != ""])
                        idx_st_ac = status_disp_ac.index(filtros_ac["status"][1]) if filtros_ac["status"][1] in status_disp_ac else 0
                        f_status_ac = st.selectbox("Status de Execução:", status_disp_ac, index=idx_st_ac, key="f_status_ac")
                        filtros_ac["status"] = ("Status de Execução", f_status_ac)

                        df_p_pna = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "pna")
                        acoes_ac = sorted(df_p_pna["Número da Ação PNAPA"].dropna().astype(str).unique().tolist())
                        opcs_pna_ac = ["Todas"] + acoes_ac
                        idx_pna_ac = opcs_pna_ac.index(filtros_ac["pna"][1]) if filtros_ac["pna"][1] in opcs_pna_ac else 0
                        f_pna_ac = st.selectbox("Ação PNAPA:", opcs_pna_ac, index=idx_pna_ac, key="f_pna_ac")
                        filtros_ac["pna"] = ("Número da Ação PNAPA", f_pna_ac)

                        df_p_tema = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "tema")
                        temas_ac = sorted([str(t).strip() for t in df_p_tema["Tema da Atividade"].dropna().unique() if str(t).strip() != ""])
                        opcs_tema_ac = ["Todos"] + temas_ac
                        idx_tema_ac = opcs_tema_ac.index(filtros_ac["tema"][1]) if filtros_ac["tema"][1] in opcs_tema_ac else 0
                        f_tema_ac = st.selectbox("Tema:", opcs_tema_ac, index=idx_tema_ac, key="f_tema_ac")
                        filtros_ac["tema"] = ("Tema da Atividade", f_tema_ac)

                        df_p_and = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, "and")
                        ands_ac = sorted([str(a).strip() for a in df_p_and["Andamento"].dropna().unique() if str(a).strip() != ""])
                        opcs_and_ac = ["Todos"] + ands_ac
                        idx_and_ac = opcs_and_ac.index(filtros_ac["and"][1]) if filtros_ac["and"][1] in opcs_and_ac else 0
                        f_and_ac = st.selectbox("Andamento (Cadastro):", opcs_and_ac, index=idx_and_ac, key="f_and_ac")
                        filtros_ac["and"] = ("Andamento", f_and_ac)

                with c_fac4:
                    st.button("🧹 Limpar", use_container_width=True, on_click=limpar_filtros_acoes_t1)

                # Aplicação final de todos os filtros
                df_exib_ac = aplicar_filtros_responsivos(df_base_acoes, filtros_ac, None)

                df_exib_ac["Data de Início"] = df_exib_ac["Data_Inicio_Datetime"].dt.date
                df_exib_ac["Data de Término"] = df_exib_ac["Data_Termino_Datetime"].dt.date

                # 4. COLUNAS REORDENADAS
                COLS_TABELA_ACOES = [
                    "Id", "Ano da Ação", "Número da Ação PNAPA", "Nome da Ação PNAPA", 
                    "Status de Execução", "Indicador", "Meta_Indicador", "Resultado_Indicador", 
                    "% de Execução da Ação", "Papel_Institucional", "Servidor", "UF_Acao_PNAPA", 
                    "Importância da Atividade", "Tema da Atividade", "Objetivo da Atividade", 
                    "Tipo de Atividade", "Andamento", "Data de Início", "Data de Término", 
                    "Dias_Gastos_Plan", "Origem do Recurso", "Rec_Plan_Total", 
                    "Observações", "Justificativa_Acao_PNAPA"
                ]

                cols_ac_validas = [c for c in COLS_TABELA_ACOES if c in df_exib_ac.columns]
                df_tab_ac = df_exib_ac[cols_ac_validas].copy()
                
                # 🚀 FORMATAÇÃO DIRETA NO PADRÃO BR (Elimina None e ponto decimal)
                df_tab_ac["Meta_Indicador"] = df_tab_ac["Meta_Indicador"].apply(lambda v: formatar_numero_br(v, 1))
                df_tab_ac["Resultado_Indicador"] = df_tab_ac["Resultado_Indicador"].apply(lambda v: formatar_numero_br(v, 1))
                df_tab_ac["% de Execução da Ação"] = df_tab_ac["% de Execução da Ação"].apply(lambda v: f"{formatar_numero_br(v, 1)}%")
                df_tab_ac["Dias_Gastos_Plan"] = df_tab_ac["Dias_Gastos_Plan"].apply(lambda v: formatar_numero_br(v, 1))
                df_tab_ac["Rec_Plan_Total"] = df_tab_ac["Rec_Plan_Total"].apply(formatar_moeda_br)
                
                df_tab_ac = df_tab_ac.sort_values(by=["Data de Início", "Id"], ascending=[True, True], na_position='last').reset_index(drop=True)

                if "selecoes_acoes" not in st.session_state: st.session_state["selecoes_acoes"] = {}
                if "version_ed_ac" not in st.session_state: st.session_state["version_ed_ac"] = 0

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
                colunas_travadas_ac["Data de Início"] = st.column_config.DateColumn("Data de Início", format="DD/MM/YYYY", disabled=True)
                colunas_travadas_ac["Data de Término"] = st.column_config.DateColumn("Data de Término", format="DD/MM/YYYY", disabled=True)

                key_dinamica_ac = f"editor_acoes_v{st.session_state['version_ed_ac']}"
                tabela_ac = st.data_editor(df_tab_ac, hide_index=True, use_container_width=True, column_config=colunas_travadas_ac, key=key_dinamica_ac)

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
                            
                            # 🚀 UF, Papel e Ponto Focal juntos na Aba 1 para atualização instantânea
                            c_ac_uf, c_ac_pap, c_ac_foc = st.columns([1, 1.2, 1.8])
                            with c_ac_uf:
                                if perfil_usuario == "Administrador":
                                    uf_atual_salva = str(reg_ac_alvo.get("UF_Acao_PNAPA", uf_usuario)).strip()
                                    idx_uf_ac = LISTA_UFS_COMPLETA.index(uf_atual_salva) if uf_atual_salva in LISTA_UFS_COMPLETA else 0
                                    uf_acao_val = st.selectbox("UF da Ação:", LISTA_UFS_COMPLETA, index=idx_uf_ac, key=f"t1_ac_uf_sel_{id_ac_ref}")
                                else:
                                    uf_acao_val = str(reg_ac_alvo.get("UF_Acao_PNAPA", uf_usuario)).strip()
                                    st.text_input("UF da Ação:", value=uf_acao_val, disabled=True, key=f"t1_ac_uf_dis_{id_ac_ref}")

                            with c_ac_pap:
                                val_papel_atual = str(reg_ac_alvo.get("Papel_Institucional", "Coordenação")).strip()
                                idx_pap = LISTA_PAPEIS_INSTITUCIONAIS.index(val_papel_atual) if val_papel_atual in LISTA_PAPEIS_INSTITUCIONAIS else 0
                                ed_papel_inst = st.selectbox("Papel da UF:", LISTA_PAPEIS_INSTITUCIONAIS, index=idx_pap, key=f"t1_ac_papel_{id_ac_ref}")

                            with c_ac_foc:
                                srvs_uf_lista = obter_servidores_por_uf(df_servidores, uf_acao_val)
                                val_foc_atual = str(reg_ac_alvo.get("Servidor", "")).strip()
                                if val_foc_atual and val_foc_atual not in srvs_uf_lista and uf_acao_val == str(reg_ac_alvo.get("UF_Acao_PNAPA", "")):
                                    srvs_uf_lista.append(val_foc_atual)
                                    srvs_uf_lista = sorted(srvs_uf_lista)

                                if ed_papel_inst == "Coordenação":
                                    idx_foc = srvs_uf_lista.index(val_foc_atual) if val_foc_atual in srvs_uf_lista else 0
                                    # 🚀 Chave dinâmica atrelada à UF selecionada (recarga instantânea)
                                    ed_servidor_ac = st.selectbox(
                                        f"Ponto Focal ({uf_acao_val}):", 
                                        srvs_uf_lista if srvs_uf_lista else [email_logado], 
                                        index=idx_foc, 
                                        key=f"t1_ac_focal_{id_ac_ref}_{uf_acao_val}"
                                    )
                                    
                                    match_srv_coord_t1 = df_servidores[df_servidores["Servidor"].astype(str).str.strip() == str(ed_servidor_ac).strip()]
                                    if not match_srv_coord_t1.empty:
                                        d_coord_t1 = match_srv_coord_t1.iloc[0]
                                        ed_uf_srv_ac = str(d_coord_t1.get("UF_Servidor", uf_acao_val))
                                        ed_lot_ac = str(d_coord_t1.get("Lotacao", "Sede Superintendência"))
                                        ed_eq_ac = str(d_coord_t1.get("Equipe_Emergencias", "Sim"))
                                    else:
                                        ed_uf_srv_ac, ed_lot_ac, ed_eq_ac = uf_acao_val, "Sede Superintendência", "Sim"
                                else:
                                    st.info("Atuação em Apoio (Sem Ponto Focal Estadual)")
                                    ed_servidor_ac, ed_uf_srv_ac, ed_lot_ac, ed_eq_ac = "", "", "", "Não"

                            lista_and_ac = ["Planejada", "Cancelada", "Não Demandada", "Não Executada"]
                            idx_and_ac = lista_and_ac.index(reg_ac_alvo["Andamento"]) if reg_ac_alvo.get("Andamento") in lista_and_ac else 0
                            ed_andamento_ac = st.selectbox("Andamento da Ação:", lista_and_ac, index=idx_and_ac, key=f"t1_ac_and_{id_ac_ref}")

                            # Painel de Liderança do Coordenador
                            if ed_papel_inst == "Coordenação" and ed_servidor_ac:
                                dias_acao_ed_temp = st.session_state.get(f"t1_ac_dpl_{id_ac_ref}", obter_float_limpo(reg_ac_alvo.get("Dias_Gastos_Plan")))
                                dados_term_ac_ed = calcular_termometro_carga(
                                    df=df_atual,
                                    df_srv_base=df_servidores,
                                    nome_servidor=ed_servidor_ac,
                                    ano_alvo=val_ano_ac,
                                    dias_novos=float(dias_acao_ed_temp),
                                    nivel_registro="Ação",
                                    id_excluir=id_ac_ref,
                                    num_acao_alvo=val_num_acao_ac
                                )

                                with st.container(border=True):
                                    st.markdown(f"**👑 Painel de Liderança Pós-Edição — {ed_servidor_ac}** *({dados_term_ac_ed['perfil_dedicacao']})*")
                                    cl1, cl2, cl3 = st.columns(3)
                                    cl1.metric("📌 Total Coordenadas", f"{dados_term_ac_ed['acoes_coord_totais']} / {dados_term_ac_ed['teto_coord_total']} máx")
                                    cl2.metric("🔥 Ações Nível 3 (>=20d)", f"{dados_term_ac_ed['acoes_coord_n3']} / {dados_term_ac_ed['teto_coord_n3']} máx")
                                    cl3.metric("📅 Teto Anual de Dias", f"{dados_term_ac_ed['teto_dias']:.0f} d")

                                    for err in dados_term_ac_ed["mensagens_erro"]: st.error(f"⛔ **BLOQUEIO (2027+):** {err}")
                                    for avs in dados_term_ac_ed["mensagens_aviso"]: st.warning(f"⚠️ **ALERTA:** {avs}")

                        with aba2_ac:
                            st.text_input("Indicador Oficial", value=val_indicador_ac, disabled=True, key=f"t1_ac_ind_{id_ac_ref}")
                            meta_val_ac = obter_float_limpo(reg_ac_alvo.get("Meta_Indicador", 1.0))
                            ed_meta_ac = st.number_input(f"Meta da Ação para a UF ({uf_acao_val}):", min_value=0.0, value=meta_val_ac, step=1.0, key=f"t1_ac_meta_{id_ac_ref}")
                            
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
                            
                            # 🚀 RECALCULO REATIVO SEM TRAVA DE KEY
                            tot_pl_ac_calc = ed_rp_d_ac + ed_rp_p_ac + ed_rp_o_ac
                            st.text_input("Rec_Plan_Total (Soma Automática):", value=formatar_moeda_br(tot_pl_ac_calc), disabled=True)

                        with aba5_ac:
                            ed_obs_ac = st.text_area("Observações:", value=str(reg_ac_alvo.get("Observações", "")), key=f"t1_ac_obs_{id_ac_ref}")
                            if ed_andamento_ac in ["Cancelada", "Não Demandada", "Não Executada"]:
                                idx_j_ac = LISTA_JUSTIFICATIVAS_ACAO.index(reg_ac_alvo["Justificativa_Acao_PNAPA"]) if reg_ac_alvo.get("Justificativa_Acao_PNAPA") in LISTA_JUSTIFICATIVAS_ACAO else 0
                                ed_just_ac = st.selectbox("Justificativa:", LISTA_JUSTIFICATIVAS_ACAO, index=idx_j_ac, key=f"t1_ac_just_{id_ac_ref}")
                            else:
                                ed_just_ac = ""

                        if st.button("💾 Gravar Alterações da Ação", type="primary", key=f"btn_salvar_ac_{id_ac_ref}"):
                            # 🛡️ TRAVA DO TERMÔMETRO NA GRAVAÇÃO DA AÇÃO (2027+)
                            if ed_papel_inst == "Coordenação" and ed_servidor_ac:
                                res_chk_ac = calcular_termometro_carga(
                                    df=df_atual,
                                    df_srv_base=df_servidores,
                                    nome_servidor=ed_servidor_ac,
                                    ano_alvo=val_ano_ac,
                                    dias_novos=float(ed_dias_pl_ac),
                                    nivel_registro="Ação",
                                    id_excluir=id_ac_ref,
                                    num_acao_alvo=val_num_acao_ac
                                )
                                if res_chk_ac["status_geral"] == "BLOQUEADO":
                                    st.error("⛔ **Alteração Impedida (Governança 2027+):** O coordenador selecionado ultrapassará os limites permitidos de liderança.")
                                    st.stop()

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
            
            # 🚀 MÁGICA: CRUZAMENTO DINÂMICO (PROCV) COM A BASE DE SERVIDORES
            if not df_servidores.empty:
                df_s_aux = df_servidores[["Servidor", "Fiscal", "AEAC", "Funcao"]].drop_duplicates(subset=["Servidor"])
                df_base_atvs = pd.merge(df_base_atvs, df_s_aux, on="Servidor", how="left")
            
            # Preenche vazios caso algum servidor não tenha cadastro na base auxiliar
            for col_nova in ["Fiscal", "AEAC"]:
                if col_nova not in df_base_atvs.columns: df_base_atvs[col_nova] = "Não"
                df_base_atvs[col_nova] = df_base_atvs[col_nova].fillna("Não")
                
            if "Funcao" not in df_base_atvs.columns: df_base_atvs["Funcao"] = ""
            df_base_atvs["Funcao"] = df_base_atvs["Funcao"].fillna("")

            st.caption(f"📌 Total de Atividades de Campo cadastradas: **{len(df_base_atvs)}** registros.")

            if df_base_atvs.empty:
                st.info("Nenhuma Atividade de Campo cadastrada na base.")
            else:
                # 1. CÁLCULO DO STATUS DE CONCLUSÃO
                def calc_status_atv_t1(row):
                    andamento = str(row.get("Andamento", "")).strip()
                    doc = str(row.get("Doc_Probatorio_Exec", "")).strip()
                    if doc.lower() in ["nan", "none", "null"]: doc = ""
                    dt_fim = row.get("Data_Termino_Datetime")
                    
                    if andamento == "Concluída":
                        if not doc: return "🟡 Sem Documento de Conclusão"
                        return "🟢 Concluída"
                    else:
                        if pd.notna(dt_fim) and hoje > dt_fim: return "🔴 Atrasada"
                        return "🔵 Prevista"

                df_base_atvs["Status de Conclusão"] = df_base_atvs.apply(calc_status_atv_t1, axis=1)

                chaves_filtros_atv = ["f_ano_at", "f_pna_at", "f_cod_at", "f_uf_at", "f_srv_at", "f_func_at", "f_status_at", "f_tema_at", "f_fiscal_at", "f_aeac_at", "f_funcao_srv_at"]
                
                for k in chaves_filtros_atv:
                    if k not in st.session_state: 
                        st.session_state[k] = "Todas" if k in ["f_pna_at", "f_uf_at", "f_func_at", "f_funcao_srv_at"] else "Todos"

                def limpar_filtros_atividades_t1():
                    for k in chaves_filtros_atv:
                        st.session_state[k] = "Todas" if k in ["f_pna_at", "f_uf_at", "f_func_at", "f_funcao_srv_at"] else "Todos"
                    if "f_slider_dts_at" in st.session_state:
                        del st.session_state["f_slider_dts_at"]

                filtros_at = {
                    "ano": ("Ano da Ação", st.session_state["f_ano_at"]),
                    "pna": ("Número da Ação PNAPA", st.session_state["f_pna_at"]),
                    "cod": ("Codigo_Atividade", st.session_state["f_cod_at"]),
                    "uf": ("UF_Acao_PNAPA", st.session_state["f_uf_at"]),
                    "srv": ("Servidor", st.session_state["f_srv_at"]),
                    "func": ("Coordenador_Operacao", st.session_state["f_func_at"]),
                    "status": ("Status de Conclusão", st.session_state["f_status_at"]),
                    "tema": ("Tema da Atividade", st.session_state["f_tema_at"]),
                    "fiscal": ("Fiscal", st.session_state["f_fiscal_at"]),           
                    "aeac": ("AEAC", st.session_state["f_aeac_at"]),                  
                    "funcao_srv": ("Funcao", st.session_state["f_funcao_srv_at"]),    
                    "data": ("Data_Inicio_Datetime", st.session_state.get("f_slider_dts_at", None))
                }

                # 2. BARRA DE FILTROS (POPOVERS) PARA ATIVIDADES
                c_fat1, c_fat2, c_fat3, c_fat4 = st.columns([1, 1.2, 1.2, 0.5])
                
                with c_fat1:
                    with st.popover("📅 Período Considerado", use_container_width=True):
                        df_p_ano_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "ano")
                        anos_at = sorted([str(a).split('.')[0] for a in df_p_ano_at["Ano da Ação"].dropna().unique() if str(a).strip() != ""], reverse=True)
                        opcs_ano_at = ["Todos"] + anos_at
                        idx_ano_at = opcs_ano_at.index(filtros_at["ano"][1]) if filtros_at["ano"][1] in opcs_ano_at else 0
                        f_ano_at = st.selectbox("Ano:", opcs_ano_at, index=idx_ano_at, key="f_ano_at")
                        filtros_at["ano"] = ("Ano da Ação", f_ano_at)

                        df_p_data_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "data")
                        dts_validas_at = df_p_data_at["Data_Inicio_Datetime"].dropna()
                        min_dt_at = dts_validas_at.min().date() if not dts_validas_at.empty else date(2025, 1, 1)
                        max_dt_at = dts_validas_at.max().date() if not dts_validas_at.empty else date(2026, 12, 31)
                        if min_dt_at >= max_dt_at: max_dt_at = min_dt_at + pd.Timedelta(days=1)

                        val_atual_sl_at = st.session_state.get("f_slider_dts_at", (min_dt_at, max_dt_at))
                        v_start_at = max(min_dt_at, min(val_atual_sl_at[0], max_dt_at))
                        v_end_at = max(min_dt_at, min(val_atual_sl_at[1], max_dt_at))
                        if v_start_at > v_end_at: v_start_at = min_dt_at

                        f_slider_dts_at = st.slider(
                            "Data de Início:", min_value=min_dt_at, max_value=max_dt_at, value=(v_start_at, v_end_at), format="DD/MM/YYYY"
                        )
                        st.session_state["f_slider_dts_at"] = f_slider_dts_at
                        filtros_at["data"] = ("Data_Inicio_Datetime", f_slider_dts_at)

                with c_fat2:
                    with st.popover("🗺️ UF / Servidor / Função", use_container_width=True):
                        df_p_uf_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "uf")
                        ufs_at = sorted([str(u).strip() for u in df_p_uf_at["UF_Acao_PNAPA"].dropna().unique() if str(u).strip() != ""])
                        opcs_uf_at = ["Todas"] + ufs_at
                        idx_uf_at = opcs_uf_at.index(filtros_at["uf"][1]) if filtros_at["uf"][1] in opcs_uf_at else 0
                        f_uf_at = st.selectbox("UF da Ação:", opcs_uf_at, index=idx_uf_at, key="f_uf_at")
                        filtros_at["uf"] = ("UF_Acao_PNAPA", f_uf_at)

                        df_p_srv_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "srv")
                        srvs_at = sorted([str(s).strip() for s in df_p_srv_at["Servidor"].dropna().unique() if str(s).strip() != ""])
                        opcs_srv_at = ["Todos"] + srvs_at
                        idx_srv_at = opcs_srv_at.index(filtros_at["srv"][1]) if filtros_at["srv"][1] in opcs_srv_at else 0
                        f_srv_at = st.selectbox("Servidor:", opcs_srv_at, index=idx_srv_at, key="f_srv_at")
                        filtros_at["srv"] = ("Servidor", f_srv_at)

                        df_p_func_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "func")
                        funcs_disp = [f for f in LISTA_FUNCOES_CAMPO if f in df_p_func_at["Coordenador_Operacao"].astype(str).str.strip().unique()]
                        opcs_func_at = ["Todas"] + (funcs_disp if funcs_disp else LISTA_FUNCOES_CAMPO)
                        idx_func_at = opcs_func_at.index(filtros_at["func"][1]) if filtros_at["func"][1] in opcs_func_at else 0
                        f_func_at = st.selectbox("Função de Campo:", opcs_func_at, index=idx_func_at, key="f_func_at")
                        filtros_at["func"] = ("Coordenador_Operacao", f_func_at)

                        st.markdown("---")
                        st.caption("📋 Dados Institucionais do Servidor")
                        
                        df_p_fiscal = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "fiscal")
                        fiscais_disp = sorted([str(f).strip() for f in df_p_fiscal["Fiscal"].dropna().unique() if str(f).strip() != ""])
                        opcs_fiscal = ["Todos"] + fiscais_disp
                        idx_fiscal = opcs_fiscal.index(filtros_at["fiscal"][1]) if filtros_at["fiscal"][1] in opcs_fiscal else 0
                        f_fiscal_at = st.selectbox("É Fiscal?", opcs_fiscal, index=idx_fiscal, key="f_fiscal_at")
                        filtros_at["fiscal"] = ("Fiscal", f_fiscal_at)

                        df_p_aeac = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "aeac")
                        aeac_disp = sorted([str(a).strip() for a in df_p_aeac["AEAC"].dropna().unique() if str(a).strip() != ""])
                        opcs_aeac = ["Todos"] + aeac_disp
                        idx_aeac = opcs_aeac.index(filtros_at["aeac"][1]) if filtros_at["aeac"][1] in opcs_aeac else 0
                        f_aeac_at = st.selectbox("É AEAC?", opcs_aeac, index=idx_aeac, key="f_aeac_at")
                        filtros_at["aeac"] = ("AEAC", f_aeac_at)

                        df_p_func_srv = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "funcao_srv")
                        func_srv_disp = sorted([str(f).strip() for f in df_p_func_srv["Funcao"].dropna().unique() if str(f).strip() != ""])
                        opcs_func_srv = ["Todas"] + func_srv_disp
                        idx_func_srv = opcs_func_srv.index(filtros_at["funcao_srv"][1]) if filtros_at["funcao_srv"][1] in opcs_func_srv else 0
                        f_funcao_srv_at = st.selectbox("Cargo/Função Institucional:", opcs_func_srv, index=idx_func_srv, key="f_funcao_srv_at")
                        filtros_at["funcao_srv"] = ("Funcao", f_funcao_srv_at)

                with c_fat3:
                    with st.popover("🏷️ Classificação & Atividade", use_container_width=True):
                        df_p_status_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "status")
                        status_disp_at = ["Todos"] + sorted([s for s in df_p_status_at["Status de Conclusão"].dropna().astype(str).unique() if s != ""])
                        idx_status_at = status_disp_at.index(filtros_at["status"][1]) if filtros_at["status"][1] in status_disp_at else 0
                        f_status_at = st.selectbox("Status de Conclusão:", status_disp_at, index=idx_status_at, key="f_status_at")
                        filtros_at["status"] = ("Status de Conclusão", f_status_at)

                        df_p_pna_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "pna")
                        acoes_at = sorted(df_p_pna_at["Número da Ação PNAPA"].dropna().astype(str).unique().tolist())
                        opcs_pna_at = ["Todas"] + acoes_at
                        idx_pna_at = opcs_pna_at.index(filtros_at["pna"][1]) if filtros_at["pna"][1] in opcs_pna_at else 0
                        f_pna_at = st.selectbox("Ação PNAPA:", opcs_pna_at, index=idx_pna_at, key="f_pna_at")
                        filtros_at["pna"] = ("Número da Ação PNAPA", f_pna_at)

                        df_p_cod_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "cod")
                        cods_at = sorted([str(c).strip() for c in df_p_cod_at["Codigo_Atividade"].dropna().unique() if str(c).strip() != ""])
                        opcs_cod_at = ["Todos"] + cods_at
                        idx_cod_at = opcs_cod_at.index(filtros_at["cod"][1]) if filtros_at["cod"][1] in opcs_cod_at else 0
                        f_cod_at = st.selectbox("Código Atividade:", opcs_cod_at, index=idx_cod_at, key="f_cod_at")
                        filtros_at["cod"] = ("Codigo_Atividade", f_cod_at)

                        df_p_tema_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, "tema")
                        temas_at = sorted([str(t).strip() for t in df_p_tema_at["Tema da Atividade"].dropna().unique() if str(t).strip() != ""])
                        opcs_tema_at = ["Todos"] + temas_at
                        idx_tema_at = opcs_tema_at.index(filtros_at["tema"][1]) if filtros_at["tema"][1] in opcs_tema_at else 0
                        f_tema_at = st.selectbox("Tema:", opcs_tema_at, index=idx_tema_at, key="f_tema_at")
                        filtros_at["tema"] = ("Tema da Atividade", f_tema_at)

                with c_fat4:
                    st.button("🧹 Limpar", use_container_width=True, on_click=limpar_filtros_atividades_t1, key="btn_limpar_at_t1")

                df_exib_at = aplicar_filtros_responsivos(df_base_atvs, filtros_at, None)

                df_exib_at["Data de Início"] = df_exib_at["Data_Inicio_Datetime"].dt.date
                df_exib_at["Data de Término"] = df_exib_at["Data_Termino_Datetime"].dt.date

                # 4. COLUNAS REORDENADAS COM OS DADOS CRUZADOS NO FINAL
                COLS_TABELA_ATIVIDADES = [
                    "Id", "Ano da Ação", "Número da Ação PNAPA", "Codigo_Atividade", 
                    "Nome da Atividade", "Status de Conclusão", "Papel_Institucional", "Coordenador_Operacao", 
                    "Servidor", "UF_Servidor", "Lotação", "UF_Acao_PNAPA", 
                    "Municipio Onde Ocorreu/Ocorrerá a Ação", "Indicador", 
                    "Resultado_Indicador", "Doc_Probatorio_Exec", "Data de Início", 
                    "Data de Término", "Dias_Gastos_Plan", "Dias_Gastos_Exec", 
                    "Origem do Recurso", "Rec_Plan_Total", "Rec_Exec_Total", 
                    "Número da PCDP", "Periculosidade/Insalubridade", "Tema da Atividade", 
                    "Objetivo da Atividade", "Tipo de Atividade", 
                    "Avaliacao_Qualidade", "Avaliacao_Feedback", "Observações",
                    "Fiscal", "AEAC", "Funcao"
                ]

                cols_at_validas = [c for c in COLS_TABELA_ATIVIDADES if c in df_exib_at.columns]
                df_tab_at = df_exib_at[cols_at_validas].copy()
                
                df_tab_at["Resultado_Indicador"] = df_tab_at["Resultado_Indicador"].apply(lambda v: formatar_numero_br(v, 1))
                df_tab_at["Dias_Gastos_Plan"] = df_tab_at["Dias_Gastos_Plan"].apply(lambda v: formatar_numero_br(v, 1))
                df_tab_at["Dias_Gastos_Exec"] = df_tab_at["Dias_Gastos_Exec"].apply(lambda v: formatar_numero_br(v, 1))
                df_tab_at["Rec_Plan_Total"] = df_tab_at["Rec_Plan_Total"].apply(formatar_moeda_br)
                df_tab_at["Rec_Exec_Total"] = df_tab_at["Rec_Exec_Total"].apply(formatar_moeda_br)
                
                df_tab_at = df_tab_at.sort_values(by=["Data de Início", "Id"], ascending=[True, True], na_position='last').reset_index(drop=True)

                if "Avaliacao_Qualidade" not in df_tab_at.columns: df_tab_at["Avaliacao_Qualidade"] = "Não Avaliada"
                if "Avaliacao_Feedback" not in df_tab_at.columns: df_tab_at["Avaliacao_Feedback"] = ""

                atividades_coordenadas = set(df_atual[
                    (df_atual["Servidor"].astype(str).str.strip() == str(nome_usuario_logado)) & 
                    (df_atual["Coordenador_Operacao"].astype(str).str.strip() == "Coordenador de Campo")
                ]["Codigo_Atividade"].astype(str).str.strip())

                def visibilidade_avaliacao(row):
                    if perfil_usuario in ["Administrador", "Editor Regional"]: return True
                    if str(row.get("Servidor", "")).strip() == str(nome_usuario_logado): return True
                    if str(row.get("Codigo_Atividade", "")).strip() in atividades_coordenadas: return True
                    return False

                mascara_visibilidade = df_tab_at.apply(visibilidade_avaliacao, axis=1)
                df_tab_at.loc[~mascara_visibilidade, "Avaliacao_Qualidade"] = "🔒 Restrito"
                df_tab_at.loc[~mascara_visibilidade, "Avaliacao_Feedback"] = "🔒 Restrito"

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

                colunas_travadas_at["Id"] = st.column_config.NumberColumn("Id", format="%d", disabled=True)
                colunas_travadas_at["Status de Conclusão"] = st.column_config.TextColumn("Status de Conclusão", disabled=True)
                colunas_travadas_at["Resultado_Indicador"] = st.column_config.TextColumn("Resultado Indicador", disabled=True)
                colunas_travadas_at["Dias_Gastos_Plan"] = st.column_config.TextColumn("Dias Plan.", disabled=True)
                colunas_travadas_at["Dias_Gastos_Exec"] = st.column_config.TextColumn("Dias Exec.", disabled=True)
                colunas_travadas_at["Rec_Plan_Total"] = st.column_config.TextColumn("Rec. Plan. Total", disabled=True)
                colunas_travadas_at["Rec_Exec_Total"] = st.column_config.TextColumn("Rec. Exec. Total", disabled=True)

                colunas_travadas_at["Data de Início"] = st.column_config.DateColumn("Data de Início", format="DD/MM/YYYY", disabled=True)
                colunas_travadas_at["Data de Término"] = st.column_config.DateColumn("Data de Término", format="DD/MM/YYYY", disabled=True)

                colunas_travadas_at["Fiscal"] = st.column_config.TextColumn("Fiscal?", disabled=True)
                colunas_travadas_at["AEAC"] = st.column_config.TextColumn("AEAC?", disabled=True)
                colunas_travadas_at["Funcao"] = st.column_config.TextColumn("Cargo/Função", disabled=True)

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

                        aba1_at, aba2_at, aba3_at, aba4_at, aba5_at = st.tabs([
                            "1. Identificação & Agrupador", "2. Detalhes & Indicadores", 
                            "3. Recursos Humanos & Liderança", "4. Cronograma & Custos", "5. Observações"
                        ])
                        
                        with aba1_at:
                            st.markdown("##### 🗂️ Ação PNAPA Vinculada (Pai)")
                            df_pna_vinc_pool = df_pnapas[df_pnapas["Num_Acao_PNAPA"].astype(str).str.strip().str.upper() != "DIPRO_GLOBAL"].copy()
                            lista_opcoes_vinc = sorted((df_pna_vinc_pool["Acao_Ano"].astype(str) + " - " + df_pna_vinc_pool["Nome_Acao_Apelido"].astype(str)).tolist()) if not df_pna_vinc_pool.empty else []
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
                            
                            if perfil_usuario == "Administrador":
                                idx_uf_at_sel = LISTA_UFS_COMPLETA.index(uf_acao_at) if uf_acao_at in LISTA_UFS_COMPLETA else 0
                                ed_uf_acao_val = st.selectbox("UF da Ação PNAPA:", LISTA_UFS_COMPLETA, index=idx_uf_at_sel, key=f"t1_at_uf_sel_{id_at_ref}")
                            else:
                                ed_uf_acao_val = st.text_input("UF da Ação PNAPA", value=uf_acao_at, disabled=True, key=f"t1_at_uf_dis_{id_at_ref}")

                            st.text_input("Importância da Atividade (Herdada)", value=importancia_at, disabled=True, key=f"t1_at_imp_{id_at_ref}")
                            ed_tema_at = st.selectbox("Tema da Atividade:", LISTA_TEMAS, index=LISTA_TEMAS.index(reg_at_alvo["Tema da Atividade"]) if reg_at_alvo.get("Tema da Atividade") in LISTA_TEMAS else 0, key=f"t1_at_tema_{id_at_ref}")
                            ed_obj_at = st.selectbox("Objetivo da Atividade:", LISTA_OBJETIVOS, index=LISTA_OBJETIVOS.index(reg_at_alvo["Objetivo da Atividade"]) if reg_at_alvo.get("Objetivo da Atividade") in LISTA_OBJETIVOS else 0, key=f"t1_at_obj_{id_at_ref}")
                            ed_tipo_at = st.selectbox("Tipo de Atividade:", LISTA_TIPOS_ATIVIDADE, index=LISTA_TIPOS_ATIVIDADE.index(reg_at_alvo["Tipo de Atividade"]) if reg_at_alvo.get("Tipo de Atividade") in LISTA_TIPOS_ATIVIDADE else 0, key=f"t1_at_tipo_{id_at_ref}")
                            ed_perigo_at = st.selectbox("Periculosidade/Insalubridade:", LISTA_PERIGOS, index=LISTA_PERIGOS.index(reg_at_alvo["Periculosidade/Insalubridade"]) if reg_at_alvo.get("Periculosidade/Insalubridade") in LISTA_PERIGOS else 0, key=f"t1_at_perigo_{id_at_ref}")

                        with aba3_at:
                            # 1. LISTAGEM ESTRITA DE SERVIDORES DA NOVA UF
                            lista_nomes_servidores = obter_servidores_por_uf(df_servidores, ed_uf_acao_val)
                            
                            srv_atual_at = str(reg_at_alvo.get("Servidor", "")).strip()
                            
                            # Seleciona o servidor atual se ele pertencer à UF escolhida; senão, reseta para o 1º da lista
                            if srv_atual_at in lista_nomes_servidores:
                                idx_srv_at = lista_nomes_servidores.index(srv_atual_at)
                            else:
                                idx_srv_at = 0
                                
                            if not lista_nomes_servidores:
                                lista_nomes_servidores = [email_logado]
                                idx_srv_at = 0
                            
                            c_at_rh1, c_at_rh2 = st.columns(2)
                            with c_at_rh1:
                                # 🚀 Chave dinâmica vinculada à UF (recarrega limpo ao trocar de estado)
                                ed_servidor_at = st.selectbox(
                                    f"Servidor Integrante / Responsável ({ed_uf_acao_val}):", 
                                    lista_nomes_servidores, 
                                    index=idx_srv_at, 
                                    key=f"t1_at_srv_{id_at_ref}_{ed_uf_acao_val}"
                                )
                            with c_at_rh2:
                                func_salva_at = str(reg_at_alvo.get("Coordenador_Operacao", "")).strip()
                                if func_salva_at in LISTA_FUNCOES_CAMPO:
                                    idx_func_at = LISTA_FUNCOES_CAMPO.index(func_salva_at)
                                else:
                                    eh_focal_at = bool(ponto_focal_estado_at and str(ed_servidor_at).strip().lower() == str(ponto_focal_estado_at).strip().lower())
                                    idx_func_at = 0 if eh_focal_at else 1
                                ed_funcao_campo = st.selectbox(
                                    "Função na Atividade de Campo:", 
                                    LISTA_FUNCOES_CAMPO, 
                                    index=idx_func_at, 
                                    key=f"t1_at_func_{id_at_ref}_{ed_uf_acao_val}_{ed_servidor_at}"
                                )

                            # 🚀 2. RESGATE DINÂMICO DOS DADOS REAIS DO SERVIDOR
                            match_srv_at_t1 = df_servidores[df_servidores["Servidor"].astype(str).str.strip() == str(ed_servidor_at).strip()]
                            if not match_srv_at_t1.empty:
                                dados_s_linha = match_srv_at_t1.iloc[0]
                                ed_uf_srv_at = str(dados_s_linha.get("UF_Servidor", ed_uf_acao_val))
                                ed_lot_at = str(dados_s_linha.get("Lotacao", "Sede Superintendência"))
                                ed_eq_at = str(dados_s_linha.get("Equipe_Emergencias", "Não"))
                                cad_fiscal_t1 = str(dados_s_linha.get("Fiscal", "Não"))
                                cad_aeac_t1 = str(dados_s_linha.get("AEAC", "Não"))
                                cad_funcao_srv_t1 = str(dados_s_linha.get("Funcao", ""))
                            else:
                                ed_uf_srv_at, ed_lot_at, ed_eq_at = ed_uf_acao_val, "Sede Superintendência", "Não"
                                cad_fiscal_t1, cad_aeac_t1, cad_funcao_srv_t1 = "Não", "Não", ""

                            # 🌡️ TERMÔMETRO VISUAL NA EDIÇÃO DA ATIVIDADE
                            dias_ed_temp = st.session_state.get(f"t1_at_dpl_{id_at_ref}", obter_float_limpo(reg_at_alvo.get("Dias_Gastos_Plan")))
                            dados_term_at_ed = calcular_termometro_carga(
                                df=df_atual,
                                df_srv_base=df_servidores,
                                nome_servidor=ed_servidor_at,
                                ano_alvo=val_ano_at,
                                dias_novos=float(dias_ed_temp),
                                importancia_nova=importancia_at,
                                funcao_campo=ed_funcao_campo,
                                nivel_registro="Atividade",
                                id_excluir=id_at_ref
                            )

                            with st.container(border=True):
                                st.markdown(f"**🌡️ Capacidade Pós-Edição — {ed_servidor_at}** *({dados_term_at_ed['perfil_dedicacao']})*")
                                pct_dias_ed = min(1.0, dados_term_at_ed["dias_totais_projetados"] / dados_term_at_ed["teto_dias"]) if dados_term_at_ed["teto_dias"] > 0 else 0
                                
                                col_te1, col_te2, col_te3 = st.columns(3)
                                col_te1.metric("📅 Total Projetado", f"{dados_term_at_ed['dias_totais_projetados']:.1f} / {dados_term_at_ed['teto_dias']:.0f} d")
                                col_te2.metric("🔄 Ativ. Ordinárias (Máx 50%)", f"{dados_term_at_ed['dias_ord_projetados']:.1f} / {dados_term_at_ed['teto_ordinarias']:.0f} d")
                                col_te3.metric("👑 Coordenações Nível 3", f"{dados_term_at_ed['acoes_coord_n3']} / {dados_term_at_ed['teto_coord_n3']} máx")
                                
                                st.progress(pct_dias_ed, text=f"Consumo de Tempo: {pct_dias_ed*100:.1f}%")

                                for err in dados_term_at_ed["mensagens_erro"]: st.error(f"⛔ **BLOQUEIO (2027+):** {err}")
                                for avs in dados_term_at_ed["mensagens_aviso"]: st.warning(f"⚠️ **ALERTA:** {avs}")

                            # 🚀 3. CAMPOS AUTOMÁTICOS SEM KEY FIXA (Renderizam o valor real a cada alteração)
                            st.text_input("UF do Servidor (Automático)", value=ed_uf_srv_at, disabled=True)
                            st.text_input("Lotação (Automático)", value=ed_lot_at, disabled=True)
                            st.text_input("Faz parte da Equipe de Emergências? (Automático)", value=ed_eq_at, disabled=True)
                            ed_pcdp_at = st.text_input("Número da PCDP:", value=str(reg_at_alvo.get("Número da PCDP", "")), key=f"t1_at_pcdp_{id_at_ref}")
                            
                            st.markdown("<p style='font-weight:bold; color:#03170a;'>📍 Geolocalização da Atividade</p>", unsafe_allow_html=True)
                            st.text_input("País", value="Brasil", disabled=True)
                            uf_oc_atual = str(reg_at_alvo.get("UF Onde Ocorreu/Ocorrerá a Ação", "SP"))
                            idx_uf_oc_at = LISTA_UFS_COMPLETA.index(uf_oc_atual) if uf_oc_atual in LISTA_UFS_COMPLETA else 0
                            ed_uf_oc_at = st.selectbox("UF Onde Ocorreu/Ocorrerá a Ação:", LISTA_UFS_COMPLETA, index=idx_uf_oc_at, key=f"t1_at_ufoc_{id_at_ref}_{ed_uf_acao_val}")
                            ed_est_loc_at = MAPEAMENTO_ESTADOS_COMPLETO.get(ed_uf_oc_at, "")
                            st.text_input("Estado_Local_Acao (Automático)", value=ed_est_loc_at, disabled=True)
                            
                            mun_lista_at = obter_municipios_ibge(ed_uf_oc_at)
                            mun_atual_at = str(reg_at_alvo.get("Municipio Onde Ocorreu/Ocorrerá a Ação", ""))
                            idx_mun_at = mun_lista_at.index(mun_atual_at) if mun_atual_at in mun_lista_at else 0
                            ed_mun_at = st.selectbox("Municipio Onde Ocorreu/Ocorrerá a Ação:", mun_lista_at if mun_lista_at else ["Superintendência Sede"], index=idx_mun_at, key=f"t1_at_mun_{id_at_ref}_{ed_uf_oc_at}")

                        with aba4_at:
                            val_dti_at = converter_para_data_segura(reg_at_alvo.get("Data de Início"))
                            val_dtf_at = converter_para_data_segura(reg_at_alvo.get("Data de Término"))
                            ed_dt_i_at = st.date_input("Data de Início:", value=val_dti_at, format="DD/MM/YYYY", key=f"t1_at_dti_{id_at_ref}")
                            ed_dt_f_at = st.date_input("Data de Término:", value=val_dtf_at, format="DD/MM/YYYY", key=f"t1_at_dtf_{id_at_ref}")
                            ed_dias_pl_at = st.number_input("Dias Gastos Plan:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Dias_Gastos_Plan")), step=0.5, format="%.1f", key=f"t1_at_dpl_{id_at_ref}")
                            ed_dias_ex_at = st.number_input("Dias Gastos Exec:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Dias_Gastos_Exec")), step=0.5, format="%.1f", key=f"t1_at_dex_{id_at_ref}")
                            ed_orig_at = st.selectbox("Origem do Recurso:", LISTA_ORIGENS_RECURSO, index=LISTA_ORIGENS_RECURSO.index(reg_at_alvo["Origem do Recurso"]) if reg_at_alvo.get("Origem do Recurso") in LISTA_ORIGENS_RECURSO else 0, key=f"t1_at_orig_{id_at_ref}")
                            
                            st.markdown("<p style='font-weight:bold; color:#03170a;'>Valores Orçamentários (Planejado vs Executado)</p>", unsafe_allow_html=True)
                            c_at_pl, c_at_ex = st.columns(2)
                            with c_at_pl:
                                st.caption("Planejado")
                                ed_rp_d_at = st.number_input("Rec_Plan_Diarias:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Plan_Diarias")), step=50.0, format="%.2f", key=f"t1_at_rpd_{id_at_ref}")
                                ed_rp_p_at = st.number_input("Rec_Plan_Passagens:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Plan_Passagens")), step=50.0, format="%.2f", key=f"t1_at_rpp_{id_at_ref}")
                                ed_rp_o_at = st.number_input("Rec_Plan_Outras_Despesas:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Plan_Outras_Despesas")), step=50.0, format="%.2f", key=f"t1_at_rpo_{id_at_ref}")
                                tot_pl_calc = ed_rp_d_at + ed_rp_p_at + ed_rp_o_at
                                st.text_input("Rec_Plan_Total (Soma):", value=formatar_moeda_br(tot_pl_calc), disabled=True)
                            with c_at_ex:
                                st.caption("Executado")
                                ed_re_d_at = st.number_input("Rec_Exec_Diarias:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Exec_Diarias")), step=50.0, format="%.2f", key=f"t1_at_red_{id_at_ref}")
                                ed_re_p_at = st.number_input("Rec_Exec_Passagens:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Exec_Passagens")), step=50.0, format="%.2f", key=f"t1_at_rep_{id_at_ref}")
                                ed_re_o_at = st.number_input("Rec_Exec_Outras_Despesas:", min_value=0.0, value=obter_float_limpo(reg_at_alvo.get("Rec_Exec_Outras_Despesas")), step=50.0, format="%.2f", key=f"t1_at_reo_{id_at_ref}")
                                tot_ex_calc = ed_re_d_at + ed_re_p_at + ed_re_o_at
                                st.text_input("Rec_Exec_Total (Soma):", value=formatar_moeda_br(tot_ex_calc), disabled=True)

                        with aba5_at:
                            ed_obs_at = st.text_area("Observações:", value=str(reg_at_alvo.get("Observações", "")), key=f"t1_at_obs_{id_at_ref}")
                            
                            is_pendente_at = False
                            if ed_andamento_at == "Concluída" and not ed_doc_at.strip():
                                is_pendente_at = True
                            elif ed_andamento_at == "Prevista" and ed_dt_f_at < date.today():
                                is_pendente_at = True
                                
                            if is_pendente_at:
                                st.warning("⚠️ Esta atividade possui pendências (Atrasada ou Sem Documento). Por favor, justifique.")
                                idx_j_at = LISTA_JUSTIFICATIVAS_ACAO.index(reg_at_alvo.get("Justificativa_Acao_PNAPA", "")) if reg_at_alvo.get("Justificativa_Acao_PNAPA") in LISTA_JUSTIFICATIVAS_ACAO else 0
                                ed_just_at = st.selectbox("Justificativa:", LISTA_JUSTIFICATIVAS_ACAO, index=idx_j_at, key=f"t1_at_just_{id_at_ref}")
                            else:
                                ed_just_at = ""

                        ed_papel_heranca = papel_estado_at if papel_estado_at in LISTA_PAPEIS_INSTITUCIONAIS else ""

                        if st.button("💾 Gravar Alterações da Atividade", type="primary", key=f"btn_salvar_at_{id_at_ref}"):
                            bloqueio_coord = False
                            
                            # 🛡️ TRAVA DO TERMÔMETRO NA GRAVAÇÃO DA ATIVIDADE (2027+)
                            res_val_atv_ed = calcular_termometro_carga(
                                df=df_atual,
                                df_srv_base=df_servidores,
                                nome_servidor=ed_servidor_at,
                                ano_alvo=val_ano_at,
                                dias_novos=float(ed_dias_pl_at),
                                importancia_nova=importancia_at,
                                funcao_campo=ed_funcao_campo,
                                nivel_registro="Atividade",
                                id_excluir=id_at_ref
                            )
                            if res_val_atv_ed["status_geral"] == "BLOQUEADO":
                                st.error("⛔ **Alteração Impedida (Governança 2027+):** Esta alteração fará o servidor ultrapassar os limites de capacidade.")
                                st.stop()

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
                                original_andamento = str(reg_at_alvo.get("Andamento", "")).strip()
                                if ed_andamento_at == "Concluída" and original_andamento != "Concluída":
                                    equipe_atual = df_atual[df_atual["Codigo_Atividade"].astype(str).str.strip().str.upper() == ed_cod_atv.strip().upper()]["Servidor"].tolist()
                                    if ed_servidor_at not in equipe_atual: equipe_atual.append(ed_servidor_at)
                                    disparar_email_360(ed_cod_atv, ed_nome_atv, equipe_atual, df_servidores)
                                    
                                payload_at = payload_gerador(
                                    val_ano_at, val_num_acao_at, val_nome_acao_at, val_indicador_at, "Atividade",
                                    ed_nome_atv, ed_andamento_at, ed_res_ind_at, ed_doc_at, ed_uf_acao_val,
                                    importancia_at, ed_tema_at, ed_obj_at, ed_tipo_at, ed_perigo_at, ed_servidor_at,
                                    ed_uf_srv_at, ed_lot_at, ed_eq_at, ed_pcdp_at, "Brasil", ed_uf_oc_at,
                                    ed_est_loc_at, ed_mun_at, ed_dt_i_at, ed_dt_f_at, ed_dias_pl_at, ed_dias_ex_at,
                                    ed_orig_at, ed_rp_d_at, ed_rp_p_at, ed_rp_o_at, ed_re_d_at,
                                    ed_re_p_at, ed_re_o_at, ed_obs_at, ed_just_at, id_at_ref, "📝 Editar Linha Existente", df_atual,
                                    papel_institucional=ed_papel_heranca, coordenador_operacao=ed_funcao_campo, meta_indicador="",
                                    codigo_atividade=ed_cod_atv, aval_qualidade="", aval_feedback="",
                                    fiscal=cad_fiscal_t1, aeac=cad_aeac_t1, funcao_servidor=cad_funcao_srv_t1
                                )
                                executar_envio_sharepoint([payload_at])
                                st.session_state["selecoes_atividades"] = {}
                                st.session_state["version_ed_at"] += 1
                                st.rerun()

                    else:
                        st.info(f"👥 **Edição em Lote:** {qtd_at_sel} atividades selecionadas. Marque os campos nas abas abaixo para habilitar a edição seletiva em massa.")
                        edicoes_lote = {}
                        l_aba1, l_aba2, l_aba3, l_aba4, l_aba5 = st.tabs([
                            "1. Identificação & Agrupador", "2. Detalhes & Indicadores", 
                            "3. Recursos Humanos & Liderança", "4. Cronograma & Custos", "5. Observações"
                        ])

                        with l_aba1:
                            st.markdown("##### 🗂️ Ação PNAPA Vinculada (Pai)")
                            if st.checkbox("Alterar Ação PNAPA Vinculada?", key="chk_acao_lt"):
                                df_pna_vinc_pool = df_pnapas[df_pnapas["Num_Acao_PNAPA"].astype(str).str.strip().str.upper() != "DIPRO_GLOBAL"].copy()
                                lista_opcoes_vinc_lt = sorted((df_pna_vinc_pool["Acao_Ano"].astype(str) + " - " + df_pna_vinc_pool["Nome_Acao_Apelido"].astype(str)).tolist()) if not df_pna_vinc_pool.empty else []
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

                            if perfil_usuario == "Administrador":
                                st.markdown("##### 📍 UF da Ação")
                                if st.checkbox("Alterar UF da Ação PNAPA?", key="chk_uf_acao_lt"):
                                    uf_atual_lote = str(df_at_sel.iloc[0].get("UF_Acao_PNAPA", "SP")).strip()
                                    idx_uf_padrao = LISTA_UFS_COMPLETA.index(uf_atual_lote) if uf_atual_lote in LISTA_UFS_COMPLETA else 0
                                    edicoes_lote["UF_Acao_PNAPA"] = st.selectbox("Nova UF da Ação:", LISTA_UFS_COMPLETA, index=idx_uf_padrao, key="in_uf_acao_lt")

                            st.markdown("##### 🏷️ Código e Agrupador da Atividade")
                            if st.checkbox("Alterar Código da Atividade/Missão?", key="chk_cod_lt"):
                                acao_base_lt = edicoes_lote.get("Número da Ação PNAPA", str(df_at_sel.iloc[0].get("Número da Ação PNAPA", "")).strip())
                                uf_base_lt = edicoes_lote.get("UF_Acao_PNAPA", str(df_at_sel.iloc[0].get("UF_Acao_PNAPA", uf_usuario)).strip())
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
                                        if num_extraido > maior_num_lt: maior_num_lt = num_extraido
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
                                uf_alvo_lote = edicoes_lote.get("UF_Acao_PNAPA", str(df_at_sel.iloc[0].get("UF_Acao_PNAPA", uf_usuario)).strip())
                                lista_srvs_lote_uf = obter_servidores_por_uf(df_servidores, uf_alvo_lote)
                                if not lista_srvs_lote_uf:
                                    lista_srvs_lote_uf = sorted(df_servidores["Servidor"].dropna().unique().tolist())
                                edicoes_lote["Servidor"] = st.selectbox(f"Novo Servidor ({uf_alvo_lote}):", lista_srvs_lote_uf, key="in_srv_lt")
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
                            if st.checkbox("Alterar Justificativa (Em caso de Pendências)?", key="chk_just_lt"):
                                edicoes_lote["Justificativa_Acao_PNAPA"] = st.selectbox("Nova Justificativa:", LISTA_JUSTIFICATIVAS_ACAO, key="in_just_lt")

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

                                # 🛡️ VALIDAÇÃO DE CAPACIDADE DOS SERVIDORES NO LOTE (2027+)
                                if not bloqueio_lote and ("Dias_Gastos_Plan" in edicoes_lote or "Servidor" in edicoes_lote or "Tema da Atividade" in edicoes_lote):
                                    srvs_checar = [edicoes_lote["Servidor"]] if "Servidor" in edicoes_lote else df_at_sel["Servidor"].dropna().unique().tolist()
                                    ano_chk_lote = edicoes_lote.get("Ano da Ação", df_at_sel.iloc[0].get("Ano da Ação", 2026))

                                    for srv_lote_alvo in srvs_checar:
                                        dias_novos_lt = float(obter_float_limpo(edicoes_lote.get("Dias_Gastos_Plan", 0.0))) if "Dias_Gastos_Plan" in edicoes_lote else 0.0
                                        imp_lt = edicoes_lote.get("Tema da Atividade", "Ordinária")
                                        func_lt = edicoes_lote.get("Coordenador_Operacao", "Apoio de Campo")

                                        res_lt_srv = calcular_termometro_carga(
                                            df=df_atual,
                                            df_srv_base=df_servidores,
                                            nome_servidor=srv_lote_alvo,
                                            ano_alvo=ano_chk_lote,
                                            dias_novos=dias_novos_lt,
                                            importancia_nova=imp_lt,
                                            funcao_campo=func_lt,
                                            nivel_registro="Atividade"
                                        )
                                        if res_lt_srv["status_geral"] == "BLOQUEADO":
                                            st.error(f"⛔ **Lote Impedido (2027+):** O servidor **{srv_lote_alvo}** ultrapassará os limites operacionais com esta alteração.")
                                            bloqueio_lote = True
                                            break

                                if not bloqueio_lote:
                                    if edicoes_lote.get("Andamento", "") == "Concluída":
                                        cod_alvo_lt = edicoes_lote.get("Codigo_Atividade", str(df_at_sel.iloc[0].get("Codigo_Atividade", "")))
                                        nome_alvo_lt = edicoes_lote.get("Nome da Atividade", str(df_at_sel.iloc[0].get("Nome da Atividade", "")))
                                        equipe_pre_existente = df_atual[df_atual["Codigo_Atividade"].astype(str).str.strip().str.upper() == cod_alvo_lt.strip().upper()]["Servidor"].tolist()
                                        
                                        equipe_final = equipe_pre_existente + df_at_sel["Servidor"].tolist()
                                        if "Servidor" in edicoes_lote:
                                            equipe_final.append(edicoes_lote["Servidor"])
                                            
                                        disparar_email_360(cod_alvo_lt, nome_alvo_lt, equipe_final, df_servidores)
                                    
                                    for _, row in df_at_sel.iterrows():
                                        v_ano = edicoes_lote.get("Ano da Ação", row.get("Ano da Ação", 2026))
                                        v_num_acao = edicoes_lote.get("Número da Ação PNAPA", row.get("Número da Ação PNAPA", ""))
                                        v_nome_acao = edicoes_lote.get("Nome da Ação PNAPA", row.get("Nome da Ação PNAPA", ""))
                                        v_indicador = edicoes_lote.get("Indicador", row.get("Indicador", ""))
                                        v_imp = edicoes_lote.get("Importância da Atividade", row.get("Importância da Atividade", "Ordinária"))
                                        v_uf_acao = edicoes_lote.get("UF_Acao_PNAPA", str(row.get("UF_Acao_PNAPA", uf_usuario)).strip())
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
                                                v_fiscal_lt = str(df_srv_lt.iloc[0].get("Fiscal", "Não"))
                                                v_aeac_lt = str(df_srv_lt.iloc[0].get("AEAC", "Não"))
                                                v_funcao_srv_lt = str(df_srv_lt.iloc[0].get("Funcao", ""))
                                            else:
                                                v_uf_srv, v_lot, v_eq = "", "", "Não"
                                                v_fiscal_lt, v_aeac_lt, v_funcao_srv_lt = "Não", "Não", ""
                                        else:
                                            v_uf_srv = str(row.get("UF_Servidor", ""))
                                            v_lot = str(row.get("Lotação", ""))
                                            v_eq = str(row.get("Faz parte da Equipe de Emergências", "Não"))
                                            v_fiscal_lt = str(row.get("Fiscal", "Não"))
                                            v_aeac_lt = str(row.get("AEAC", "Não"))
                                            v_funcao_srv_lt = str(row.get("Funcao", ""))
                                            
                                        v_pais = "Brasil"
                                        v_uf_oc = edicoes_lote.get("UF Onde Ocorreu/Ocorrerá a Ação", str(row.get("UF Onde Ocorreu/Ocorrerá a Ação", "SP")))
                                        v_est_oc = edicoes_lote.get("Estado_Local_Acao", str(row.get("Estado_Local_Acao", "São Paulo")))
                                        v_mun_oc = edicoes_lote.get("Municipio Onde Ocorreu/Ocorrerá a Ação", str(row.get("Municipio Onde Ocorreu/Ocorrerá a Ação", "")))
                                        
                                        v_dti = edicoes_lote.get("Data de Início", converter_para_data_segura(row.get("Data de Início")))
                                        v_dtf = edicoes_lote.get("Data de Término", converter_para_data_segura(row.get("Data de Término")))
                                        
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
                                        v_just = edicoes_lote.get("Justificativa_Acao_PNAPA", str(row.get("Justificativa_Acao_PNAPA", "")))
                                        
                                        payload_linha = payload_gerador(
                                            v_ano, v_num_acao, v_nome_acao, v_indicador, "Atividade",
                                            v_nome_atv, v_and, v_res_ind, v_doc, v_uf_acao,
                                            v_imp, v_tema, v_obj, v_tipo, v_perigo, v_srv,
                                            v_uf_srv, v_lot, v_eq, v_pcdp, v_pais, v_uf_oc,
                                            v_est_oc, v_mun_oc, v_dti, v_dtf, v_dpl, v_dex,
                                            v_origem, v_rpd, v_rpp, v_rpo, v_red,
                                            v_rep, v_reo, v_obs, v_just, str(row["Id"]), "📝 Editar Linha Existente", df_atual,
                                            papel_institucional=v_papel, coordenador_operacao=v_func, meta_indicador="",
                                            codigo_atividade=v_cod_atv, aval_qualidade="", aval_feedback="",
                                            fiscal=v_fiscal_lt, aeac=v_aeac_lt, funcao_servidor=v_funcao_srv_lt
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
    registro_selecionado = None
    id_atual = ""
    st.markdown(f"<h3 style='color: #03170a;'>Formulário de Dados PNAPA — Modo: {modo}</h3>", unsafe_allow_html=True)
    
    idx_nivel_padrao = 0 if registro_selecionado is None or str(registro_selecionado.get("Nível", "")) == "Ação" else 1
    nivel_selecionado = st.selectbox("O que deseja cadastrar?", ["Ação", "Atividade"], index=idx_nivel_padrao, key="main_txt_nivel")
    
    st.markdown("#### 📍 Definição da Localidade (UF da Ação)")
    if perfil_usuario == "Administrador":
        idx_uf_padrao = LISTA_UFS_COMPLETA.index(uf_usuario) if uf_usuario in LISTA_UFS_COMPLETA else 0
        uf_filtro_pna = st.selectbox("Selecione a UF da Ação/Atividade:", LISTA_UFS_COMPLETA, index=idx_uf_padrao, key="form_uf_geral")
    else:
        uf_filtro_pna = uf_usuario if uf_usuario != "Acesso Restrito" else "SP"
        st.text_input("UF da Ação/Atividade (Sua UF):", value=uf_filtro_pna, disabled=True)

    st.markdown("#### 🔗 Vinculação Automática com o Catálogo de Ações PNAPA")
    
    # 🚀 Filtro estrito: remove qualquer registro técnico DIPRO
    df_pna_opcoes = df_pnapas[
        ~df_pnapas["Num_Acao_PNAPA"].astype(str).str.upper().str.contains("DIPRO") &
        ~df_pnapas["Acao_Ano"].astype(str).str.upper().str.contains("DIPRO")
    ].copy()
    
    if not df_pna_opcoes.empty:
        anos_aux_disponiveis = sorted([int(a) for a in pd.to_numeric(df_pna_opcoes["Ano"], errors='coerce').dropna().unique() if int(a) > 0], reverse=True)
        if not anos_aux_disponiveis:
            anos_aux_disponiveis = [2027, 2026]
            
        ano_padrao_form = int(pd.to_numeric(registro_selecionado.get("Ano da Ação"), errors='coerce') or anos_aux_disponiveis[0]) if registro_selecionado is not None else anos_aux_disponiveis[0]
        try: idx_ano_form = anos_aux_disponiveis.index(ano_padrao_form)
        except ValueError: idx_ano_form = 0
            
        ano_vinculo = st.selectbox("Selecione o Ano para filtrar as Ações:", anos_aux_disponiveis, index=idx_ano_form, key="form_pna_vinculo_ano")
        
        df_pnapas_ano = df_pna_opcoes[pd.to_numeric(df_pna_opcoes["Ano"], errors='coerce').fillna(0).astype(int) == int(ano_vinculo)]
        
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
            
            val_ano = int(pd.to_numeric(dados_aux_linha["Ano"], errors='coerce') or ano_vinculo)
            val_num_acao = str(dados_aux_linha.get("Acao_Ano", dados_novo_pai_lt["Num_Acao_PNAPA"])) if 'dados_novo_pai_lt' in locals() else str(dados_aux_linha.get("Acao_Ano", dados_aux_linha["Num_Acao_PNAPA"]))
            cod_prefixo_puro = val_num_acao.split("-")[0].strip()
            apelido_ins = str(dados_aux_linha.get("Nome_Acao_Apelido", ""))
            val_nome_acao = apelido_ins if apelido_ins and apelido_ins.lower() != "nan" else str(dados_aux_linha.get("Nome_Acao_Completo", "")).strip()
            val_indicador = str(dados_aux_linha["Indicador"])
            importancia = str(dados_aux_linha.get("Importância", "Ordinária")).strip()
            dono_nacional = str(dados_aux_linha.get("Dono_Acao", "Ceneac")).strip()
            uf_dono_nac = str(dados_aux_linha.get("UF_Dono", "DF")).strip()
            meta_nac_info = dados_aux_linha.get("Meta_Nacional", "")
            
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
                # 🚀 LISTAGEM REATIVA: Servidores da UF + Equipe Sede Ceneac/DF
                srvs_uf_pna = obter_servidores_por_uf(df_servidores, uf_filtro_pna)
                if papel_inst == "Coordenação":
                    servidor = st.selectbox(
                        f"Ponto Focal / Coordenador da Ação na UF ({uf_filtro_pna}):", 
                        srvs_uf_pna if srvs_uf_pna else [email_logado], 
                        key=f"pna_focal_acao_{uf_filtro_pna}"
                    )
                    
                    # 🚀 Resgata os dados cadastrais reais do coordenador
                    match_srv_coord = df_servidores[df_servidores["Servidor"].astype(str).str.strip() == str(servidor).strip()]
                    if not match_srv_coord.empty:
                        d_coord = match_srv_coord.iloc[0]
                        uf_servidor = str(d_coord.get("UF_Servidor", uf_filtro_pna))
                        lotacao = str(d_coord.get("Lotacao", "Sede Superintendência"))
                        equipe_emergencia = str(d_coord.get("Equipe_Emergencias", "Sim"))
                        cad_fiscal = str(d_coord.get("Fiscal", "Não"))
                        cad_aeac = str(d_coord.get("AEAC", "Não"))
                        cad_funcao_srv = str(d_coord.get("Funcao", ""))
                    else:
                        uf_servidor, lotacao, equipe_emergencia = uf_filtro_pna, "Sede Superintendência", "Sim"
                        cad_fiscal, cad_aeac, cad_funcao_srv = "Não", "Não", ""
                else:
                    st.info(f"ℹ️ **Atuação em Apoio:** A UF ({uf_filtro_pna}) não indicará Coordenador Estadual.")
                    servidor, uf_servidor, lotacao, equipe_emergencia = "", "", "", "Não"
                    cad_fiscal, cad_aeac, cad_funcao_srv = "Não", "Não", ""

            lista_andamentos_acao = ["Planejada", "Cancelada", "Não Demandada", "Não Executada"]
            try: idx_and = lista_andamentos_acao.index(registro_selecionado["Andamento"]) if registro_selecionado is not None else 0
            except: idx_and = 0
            andamento = st.selectbox("Andamento da Ação", lista_andamentos_acao, index=idx_and, key="pna_sel_andamento_acao")

            # 👑 PAINEL DE LIDERANÇA DO COORDENADOR DA AÇÃO
            if papel_inst == "Coordenação" and servidor:
                dias_acao_temp = st.session_state.get("pna_dias_pl_acao", obter_num_seguro(registro_selecionado, "Dias_Gastos_Plan"))
                dados_term_ac_form = calcular_termometro_carga(
                    df=df_atual,
                    df_srv_base=df_servidores,
                    nome_servidor=servidor,
                    ano_alvo=val_ano if val_ano else 2026,
                    dias_novos=float(dias_acao_temp),
                    nivel_registro="Ação",
                    num_acao_alvo=val_num_acao
                )

                with st.container(border=True):
                    st.markdown(f"**👑 Painel de Liderança — {servidor}** *({dados_term_ac_form['perfil_dedicacao']})*")
                    cl1, cl2, cl3 = st.columns(3)
                    cl1.metric("📌 Total Coordenadas", f"{dados_term_ac_form['acoes_coord_totais']} / {dados_term_ac_form['teto_coord_total']} máx")
                    cl2.metric("🔥 Ações Nível 3 (>=20d)", f"{dados_term_ac_form['acoes_coord_n3']} / {dados_term_ac_form['teto_coord_n3']} máx")
                    cl3.metric("📅 Teto Anual de Dias", f"{dados_term_ac_form['teto_dias']:.0f} d")

                    for err in dados_term_ac_form["mensagens_erro"]: st.error(f"⛔ **BLOQUEIO (2027+):** {err}")
                    for avs in dados_term_ac_form["mensagens_aviso"]: st.warning(f"⚠️ **ALERTA:** {avs}")

        with aba2:
            st.text_input("Indicador Oficial (Herdado)", value=val_indicador, disabled=True)
            meta_indicador = st.number_input(f"Meta da Ação para a UF ({uf_filtro_pna}):", min_value=0.0, value=1.0, step=1.0, key="pna_meta_uf_input")
            
            # 🚀 Herda a UF selecionada no topo como fonte única da verdade
            uf_acao = uf_filtro_pna
            st.text_input("UF da Ação PNAPA (Automático)", value=str(uf_acao), disabled=True)
            
            st.text_input("Importância da Atividade (Herdada do Catálogo)", value=importancia, disabled=True)
            
            tema = st.selectbox("Tema da Atividade", LISTA_TEMAS, key="pna_sel_tema_acao")
            objetivo = st.selectbox("Objetivo da Atividade", LISTA_OBJETIVOS, key="pna_sel_obj_acao")
            tipo_atividade = st.selectbox("Tipo de Atividade", LISTA_TIPOS_ATIVIDADE, key="pna_sel_tipo_acao")

        with aba4:
            dt_inicio = st.date_input("Data de Início:", value=val_dt_inicio, format="DD/MM/YYYY", key="pna_dt_ini_acao")
            dt_termino = st.date_input("Data de Término:", value=val_dt_termino, format="DD/MM/YYYY", key="pna_dt_fim_acao")
            
            dias_plan = st.number_input("Dias Gastos Plan", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Dias_Gastos_Plan"), step=0.5, format="%.1f", key="pna_dias_pl_acao")
            origem_recurso = st.selectbox("Origem do Recurso", LISTA_ORIGENS_RECURSO, key="pna_orig_acao")
            
            st.markdown("<p style='font-weight: bold; margin-top:15px; color:#03170a;'>Valores Orçamentários Planejados</p>", unsafe_allow_html=True)
            rec_p_diarias = st.number_input("Rec_Plan_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Diarias"), step=50.0, format="%.2f", key="pna_rpd_acao")
            rec_p_passagens = st.number_input("Rec_Plan_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Passagens"), step=50.0, format="%.2f", key="pna_rpp_acao")
            rec_p_outras = st.number_input("Rec_Plan_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Plan_Outras_Despesas"), step=50.0, format="%.2f", key="pna_rpo_acao")
            
            calc_plan_acao = float(rec_p_diarias + rec_p_passagens + rec_p_outras)
            st.text_input("Rec_Plan_Total (Soma Automática)", value=formatar_moeda_br(calc_plan_acao), disabled=True)

        with aba5:
            obs = st.text_area("Observações", value=str(registro_selecionado["Observações"]) if registro_selecionado is not None else "", key="pna_obs_acao")
            if andamento in ["Cancelada", "Não Demandada", "Não Executada"]:
                justificativa = st.selectbox("Justificativa_Acao_PNAPA", LISTA_JUSTIFICATIVAS_ACAO, key="pna_just_acao")
            else:
                justificativa = ""

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
            
            st.markdown("##### 🏷️ Código e Agrupador da Atividade")
            
            if "Codigo_Atividade" not in df_atual.columns:
                df_atual["Codigo_Atividade"] = ""
            
            df_atvs_acao_uf = df_atual[
                (df_atual["Nível"] == "Atividade") &
                (df_atual["UF_Acao_PNAPA"].astype(str).str.strip().str.upper() == str(uf_filtro_pna).strip().upper()) &
                (
                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == str(val_num_acao).strip().upper()) |
                    (df_atual["Número da Ação PNAPA"].astype(str).str.strip().str.upper() == str(val_num_acao).split("-")[0].strip().upper())
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
            
            # 🚀 Herda a UF selecionada no topo como fonte única da verdade
            uf_acao = uf_filtro_pna
            st.text_input("UF da Ação PNAPA (Automático)", value=str(uf_acao), disabled=True)
            
            st.text_input("Importância da Atividade (Herdada)", value=importancia, disabled=True)
            
            tema = st.selectbox("Tema da Atividade", LISTA_TEMAS, key="atv_sel_tema")
            objetivo = st.selectbox("Objetivo da Atividade", LISTA_OBJETIVOS, key="atv_sel_obj")
            tipo_atividade = st.selectbox("Tipo de Atividade", LISTA_TIPOS_ATIVIDADE, key="atv_sel_tipo")
            periculosidade = st.selectbox("Periculosidade/Insalubridade", LISTA_PERIGOS, key="atv_sel_perigo")

        with aba3:
            st.markdown("##### 👥 Recursos Humanos & Liderança da Operação")
            
            # 🚀 LISTAGEM REATIVA: Servidores da UF + Equipe Sede Ceneac/DF
            lista_nomes_servidores = obter_servidores_por_uf(df_servidores, uf_filtro_pna)
            if not lista_nomes_servidores:
                lista_nomes_servidores = [email_logado]
            
            c_rh1, c_rh2 = st.columns(2)
            with c_rh1:
                servidor = st.selectbox(
                    f"Servidor Integrante / Responsável ({uf_filtro_pna}):", 
                    lista_nomes_servidores, 
                    key=f"atv_sel_servidor_{val_num_acao}_{uf_filtro_pna}"
                )

            with c_rh2:
                eh_ponto_focal = bool(ponto_focal_estado and str(servidor).strip().lower() == str(ponto_focal_estado).strip().lower())
                idx_funcao_sugerida = 0 if eh_ponto_focal else 1
                funcao_campo = st.selectbox("Função na Atividade de Campo:", LISTA_FUNCOES_CAMPO, index=idx_funcao_sugerida, key=f"atv_funcao_campo_{val_num_acao}_{servidor}_{codigo_atividade}")

            # 🚀 RESGATA DADOS REAIS DO SERVIDOR (Busca direta em toda a base auxiliar)
            match_srv_atv = df_servidores[df_servidores["Servidor"].astype(str).str.strip() == str(servidor).strip()]
            if not match_srv_atv.empty:
                dados_serv_linha = match_srv_atv.iloc[0]
                uf_servidor = str(dados_serv_linha.get("UF_Servidor", uf_filtro_pna))
                lotacao = str(dados_serv_linha.get("Lotacao", "Sede Superintendência"))
                equipe_emergencia = str(dados_serv_linha.get("Equipe_Emergencias", "Não"))
                
                cad_fiscal = str(dados_serv_linha.get("Fiscal", "Não"))
                cad_aeac = str(dados_serv_linha.get("AEAC", "Não"))
                cad_funcao_srv = str(dados_serv_linha.get("Funcao", ""))
            else:
                uf_servidor, lotacao, equipe_emergencia = uf_filtro_pna, "Sede Superintendência", "Não"
                cad_fiscal, cad_aeac, cad_funcao_srv = "Não", "Não", ""

            # 🌡️ TERMÔMETRO VISUAL DE CAPACIDADE DA ATIVIDADE
            dias_atv_temp = st.session_state.get("atv_dias_pl", obter_num_seguro(registro_selecionado, "Dias_Gastos_Plan"))
            dados_term_atv_form = calcular_termometro_carga(
                df=df_atual,
                df_srv_base=df_servidores,
                nome_servidor=servidor,
                ano_alvo=val_ano if val_ano else 2026,
                dias_novos=float(dias_atv_temp),
                importancia_nova=importancia,
                funcao_campo=funcao_campo,
                nivel_registro="Atividade"
            )

            with st.container(border=True):
                st.markdown(f"**🌡️ Termômetro de Capacidade — {servidor}** *({dados_term_atv_form['perfil_dedicacao']})*")
                pct_dias = min(1.0, dados_term_atv_form["dias_totais_projetados"] / dados_term_atv_form["teto_dias"]) if dados_term_atv_form["teto_dias"] > 0 else 0
                
                col_t1, col_t2, col_t3 = st.columns(3)
                col_t1.metric("📅 Dias Planejados", f"{dados_term_atv_form['dias_totais_projetados']:.1f} / {dados_term_atv_form['teto_dias']:.0f} d")
                col_t2.metric("🔄 Ativ. Ordinárias (Máx 50%)", f"{dados_term_atv_form['dias_ord_projetados']:.1f} / {dados_term_atv_form['teto_ordinarias']:.0f} d")
                col_t3.metric("👑 Coordenações Nível 3", f"{dados_term_atv_form['acoes_coord_n3']} / {dados_term_atv_form['teto_coord_n3']} máx")
                
                st.progress(pct_dias, text=f"Consumo de Tempo: {pct_dias*100:.1f}%")

                for err in dados_term_atv_form["mensagens_erro"]: st.error(f"⛔ **BLOQUEIO (2027+):** {err}")
                for avs in dados_term_atv_form["mensagens_aviso"]: st.warning(f"⚠️ **ALERTA:** {avs}")

            st.text_input("UF do Servidor (Automático)", value=uf_servidor, disabled=True)
            st.text_input("Lotação (Automático)", value=lotacao, disabled=True)
            st.text_input("Faz parte da Equipe de Emergências? (Automático)", value=equipe_emergencia, disabled=True)
            num_pcdp = st.text_input("Número da PCDP", value=str(registro_selecionado["Número da PCDP"]) if registro_selecionado is not None else "", key="atv_num_pcdp")
            
            st.markdown("<p style='font-weight: bold; margin-top:10px; color:#03170a;'>📍 Geolocalização da Atividade</p>", unsafe_allow_html=True)
            pais = st.text_input("País", value="Brasil", disabled=True)
            
            idx_uf_oc = LISTA_UFS_COMPLETA.index(uf_filtro_pna) if uf_filtro_pna in LISTA_UFS_COMPLETA else 0
            uf_ocorrencia = st.selectbox("UF Onde Ocorreu/Ocorrerá a Ação", LISTA_UFS_COMPLETA, index=idx_uf_oc, key="atv_sel_uf_ocorrencia")
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
                st.text_input("Rec_Plan_Total (Soma Automática)", value=formatar_moeda_br(calc_tot_p_atv), disabled=True)

            with c_ex:
                st.caption("Executado")
                rec_e_diarias = st.number_input("Rec_Exec_Diarias", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Diarias"), step=50.0, format="%.2f", key="atv_red")
                rec_e_passagens = st.number_input("Rec_Exec_Passagens", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Passagens"), step=50.0, format="%.2f", key="atv_rep")
                rec_e_outras = st.number_input("Rec_Exec_Outras_Despesas", min_value=0.0, value=obter_num_seguro(registro_selecionado, "Rec_Exec_Outras_Despesas"), step=50.0, format="%.2f", key="atv_reo")
                calc_tot_e_atv = float(rec_e_diarias + rec_e_passagens + rec_e_outras)
                st.text_input("Rec_Exec_Total (Soma Automática)", value=formatar_moeda_br(calc_tot_e_atv), disabled=True)

        with aba5:
            obs = st.text_area("Observações", value=str(registro_selecionado["Observações"]) if registro_selecionado is not None else "", key="atv_obs")
            justificativa = ""

        papel_inst = papel_estado_acao if papel_estado_acao in LISTA_PAPEIS_INSTITUCIONAIS else ""
        meta_indicador = ""

    st.markdown("<br>", unsafe_allow_html=True)
    btn_enviar_individual = st.button("🚀 Gravar Registro no SharePoint", type="primary", key="btn_gravar_individual_reativo")

    # =================================================================
    # PROCESSAMENTO DO ENVIO: INDIVIDUAL OU EM LOTE
    # =================================================================
    if btn_enviar_individual:
        bloquear_envio = False
        
        if nivel_selecionado == "Ação":
            coord_op_final = ""
            cod_atv_final = ""
            
            cod_puro = str(val_num_acao).split("-")[0].strip().upper()
            cod_comp = str(val_num_acao).strip().upper()
            uf_limpa = str(uf_filtro_pna).strip().upper()
            ano_alvo_str = str(val_ano).strip()
            
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

        # 🛡️ TRAVA DO TERMÔMETRO NO ENVIO INDIVIDUAL (2027+)
        if not bloquear_envio and servidor:
            res_validacao_final = calcular_termometro_carga(
                df=df_atual,
                df_srv_base=df_servidores,
                nome_servidor=servidor,
                ano_alvo=val_ano if val_ano else 2026,
                dias_novos=float(dias_plan),
                importancia_nova=importancia,
                funcao_campo=coord_op_final,
                nivel_registro=nivel_selecionado,
                num_acao_alvo=val_num_acao
            )
            if res_validacao_final["status_geral"] == "BLOQUEADO":
                st.error("⛔ **Gravação Impedida pela Governança (2027+):** Limite de capacidade operacional ou de liderança excedido.")
                bloquear_envio = True

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
                codigo_atividade=cod_atv_final,
                fiscal=cad_fiscal if nivel_selecionado == "Atividade" else "Não",
                aeac=cad_aeac if nivel_selecionado == "Atividade" else "Não",
                funcao_servidor=cad_funcao_srv if nivel_selecionado == "Atividade" else ""
            )
            executar_envio_sharepoint([payload_unico])

    # =================================================================
    # 2. CARGA EM LOTE (ATIVIDADE) MULTI-SELECT BLINDADO
    # =================================================================
    if modo == "➕ Inserir Nova Linha" and nivel_selecionado == "Atividade":
        st.markdown("---")
        with st.popover("👥 Deseja cadastrar esta atividade para múltiplos servidores? (Carga em Lote)", use_container_width=True):
            st.markdown("### 👥 Cadastro Multi-Servidor / Lote")
            
            # 🚀 NOVO: MULTISELECT SUBSTITUINDO A TEXT_AREA (SEGURANÇA TOTAL)
            lista_todos_srvs_global = sorted(df_servidores["Servidor"].dropna().unique().tolist())
            servidores_finais = st.multiselect(
                "Selecione os Servidores da Equipe:", 
                options=lista_todos_srvs_global,
                default=[servidor] if servidor in lista_todos_srvs_global else [],
                help="Selecione apenas servidores cadastrados. Cada servidor gerará uma atividade idêntica no SharePoint."
            )
            
            st.info(f"📋 Serão gerados **{len(servidores_finais)}** registros simultâneos para o código `{codigo_atividade}`.")
            
            st.markdown("---")
            st.markdown("### 🎯 Espelhamento de Campos")
            st.caption("Desmarque os campos que deseja enviar EM BRANCO para edição posterior:")
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if st.button("✓ Marcar Todos", key="btn_lote_marcar_todos"): st.session_state["chk_lote_all"] = True
            with col_c2:
                if st.button("✕ Desmarcar Todos", key="btn_lote_desmarcar_todos"): st.session_state["chk_lote_all"] = False
            
            status_padrao = st.session_state.get("chk_lote_all", True)
            
            espelhar_detalhes = st.checkbox("Espelhar Detalhes da Atividade e Documentos SEI", value=status_padrao, key="lote_chk_detalhes")
            espelhar_local = st.checkbox("Espelhar Localidade (País, UF, Estado, Município)", value=status_padrao, key="lote_chk_local")
            espelhar_crono = st.checkbox("Espelhar Cronograma (Datas e Dias Gastos)", value=status_padrao, key="lote_chk_crono")
            espelhar_custos = st.checkbox("Espelhar Custos (Valores Planejados e Executados)", value=status_padrao, key="lote_chk_custos")
            espelhar_just = st.checkbox("Espelhar Justificativas e Observações", value=status_padrao, key="lote_chk_just")
            
            if st.button("🔥 Disparar Carga em Lote para o SharePoint", type="primary", use_container_width=True, key="btn_disparar_lote_final"):
                if not servidores_finais:
                    st.error("⚠️ Selecione pelo menos um servidor na lista acima.")
                else:
                    # 🛡️ VALIDAÇÃO DE CAPACIDADE DE CADA SERVIDOR DO LOTE (2027+)
                    bloqueio_lote = False
                    dias_lote_check = dias_plan if espelhar_crono else 0.0

                    for srv_lote_chk in servidores_finais:
                        func_chk = funcao_campo if srv_lote_chk == servidor else "Apoio de Campo"
                        res_chk_lt = calcular_termometro_carga(
                            df=df_atual,
                            df_srv_base=df_servidores,
                            nome_servidor=srv_lote_chk,
                            ano_alvo=val_ano if val_ano else 2026,
                            dias_novos=float(dias_lote_check),
                            importancia_nova=importancia,
                            funcao_campo=func_chk,
                            nivel_registro="Atividade"
                        )
                        if res_chk_lt["status_geral"] == "BLOQUEADO":
                            st.error(f"⛔ **Lote Impedido (2027+):** O servidor **{srv_lote_chk}** excederá os limites de capacidade.")
                            bloqueio_lote = True

                    if bloqueio_lote:
                        st.stop()

                    payloads_lote = []
                    id_base_calculado = int(pd.to_numeric(df_atual["Id"], errors='coerce').dropna().max() + 1) if not df_atual.empty else 1
                    
                    for idx, serv_lote in enumerate(servidores_finais):
                        id_loop = str(id_base_calculado + idx)
                        funcao_lote = funcao_campo if serv_lote == servidor else "Apoio de Campo"
                        
                        # 🚀 BUSCA OS DADOS (INCLUSIVE NOVOS) DO SERVIDOR NO LOOP DO LOTE
                        df_srv_lt = df_servidores[df_servidores["Servidor"] == serv_lote]
                        if not df_srv_lt.empty:
                            p_uf_srv = str(df_srv_lt.iloc[0].get("UF_Servidor", ""))
                            p_lot = str(df_srv_lt.iloc[0].get("Lotacao", ""))
                            p_eq = str(df_srv_lt.iloc[0].get("Equipe_Emergencias", "Não"))
                            p_fiscal = str(df_srv_lt.iloc[0].get("Fiscal", "Não"))
                            p_aeac = str(df_srv_lt.iloc[0].get("AEAC", "Não"))
                            p_funcao = str(df_srv_lt.iloc[0].get("Funcao", ""))
                        else:
                            p_uf_srv, p_lot, p_eq, p_fiscal, p_aeac, p_funcao = "", "", "Não", "Não", "Não", ""
                        
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
                            "UF_Servidor": p_uf_srv,
                            "Lotação": p_lot, 
                            "Faz parte da Equipe de Emergências": p_eq, 
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
                            "Justificativa_Acao_PNAPA": "",
                            "Fiscal": p_fiscal,            # 🚀 NOVO
                            "AEAC": p_aeac,                # 🚀 NOVO
                            "Funcao": p_funcao             # 🚀 NOVO
                        }
                        payloads_lote.append(payload_linha)
                    
                    executar_envio_sharepoint(payloads_lote)

# --- TELA 3: GERENCIAR UNIDADES (COM PREENCHIMENTO AUTOMÁTICO E CASCATA) ---
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
                # 🚀 CÁLCULO SEGURO DO PRÓXIMO ID_UF
                col_id_uf = "ID_UF" if "ID_UF" in df_lotacoes.columns else "Id"
                if not df_lotacoes.empty and col_id_uf in df_lotacoes.columns:
                    id_novo_uf = int(pd.to_numeric(df_lotacoes[col_id_uf], errors='coerce').fillna(0).max() + 1)
                else:
                    id_novo_uf = 1

                payload_uni = {
                    "Acao": "Inserir",
                    "ID_UF": id_novo_uf,       # 👈 Chave primária enviada
                    "UF": uf_uni_add,
                    "Unidade": nova_uni
                }

                with st.spinner("Sincronizando nova unidade com o SharePoint..."):
                    executar_api_unidades(payload_uni)
                    time.sleep(2)
                    st.cache_data.clear()
                st.success(f"✅ Unidade '{nova_uni}' (ID: {id_novo_uf}) salva com sucesso!")
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

# --- TELA 4: GERENCIAR EQUIPES ---
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
    
    # 🚀 NOVA LISTA RESTRITA DE FUNÇÕES
    LISTA_FUNCOES_SERVIDOR = [
        "",
        "Responsável Nupaem", 
        "Responsável Nupaem Substituto(a)", 
        "Coordenador(a) Geral Ceneac", 
        "Coordenador(a) CPrev", 
        "Coordenador(a) Coate"
    ]
    
    with ts_add:
        n_srv = st.text_input("Nome Completo do Servidor:")
        e_srv = st.text_input("E-mail Institucional (@ibama.gov.br):")
        uf_srv = st.selectbox("UF/Órgão de Lotação:", LISTA_UFS_COMPLETA, key="srv_add_uf") if perfil_usuario == "Administrador" else st.text_input("UF de Lotação:", value=uf_usuario, disabled=True, key="srv_add_uf_rep")
        unidades_lotacao_disponiveis = df_lotacoes[df_lotacoes["UF"] == uf_srv]["Unidade"].tolist()
        lot_srv = st.selectbox("Unidade de Lotação Relacionada:", unidades_lotacao_disponiveis if unidades_lotacao_disponiveis else ["Sede Superintendência"])
        
        # 🚀 SELETOR DE FUNÇÃO CORPORATIVA
        fun_srv = st.selectbox("Função / Cargo Institucional:", LISTA_FUNCOES_SERVIDOR)
        
        col_eq1, col_eq2, col_eq3 = st.columns(3)
        with col_eq1: eq_emerg = st.selectbox("Equipe de Emergências?", ["Sim", "Não"])
        with col_eq2: eq_fiscal = st.selectbox("Fiscal de Campo?", ["Sim", "Não"])
        with col_eq3: eq_aeac = st.selectbox("Possui AEAC?", ["Sim", "Não"])
        perf_srv = st.selectbox("Perfil de Acesso no Sistema:", LISTA_PERFIS) if perfil_usuario == "Administrador" else st.selectbox("Perfil de Acesso no Sistema:", ["Visualização", "Editor Regional"])
        tkn_srv = st.text_input("Definir Token/Senha de Acesso para o Usuário:", type="password")
        
        if st.button("Habilitar Servidor", type="primary"):
            if not n_srv or not e_srv:
                st.error("⚠️ O Nome e o E-mail do servidor são obrigatórios.")
            else:
                # 🚀 CÁLCULO SEGURO DO PRÓXIMO ID_SERV (max + 1)
                col_id_srv = "ID_SERV" if "ID_SERV" in df_servidores.columns else "Id"
                if not df_servidores.empty and col_id_srv in df_servidores.columns:
                    id_novo_serv = int(pd.to_numeric(df_servidores[col_id_srv], errors='coerce').fillna(0).max() + 1)
                else:
                    id_novo_serv = 1

                payload = {
                    "Acao": "Inserir",
                    "ID_SERV": id_novo_serv,   # 👈 ID gerado automaticamente
                    "Servidor": n_srv.strip(),
                    "UF_Servidor": uf_srv,
                    "Lotacao": lot_srv,
                    "Equipe_Emergencias": eq_emerg,
                    "Fiscal": eq_fiscal,
                    "AEAC": eq_aeac,
                    "Funcao": fun_srv,
                    "E_mail": e_srv.strip(),
                    "Perfil": perf_srv,
                    "Token": hash_senha(tkn_srv) if tkn_srv else ""
                }
                with st.spinner("Adicionando integrante da equipe..."):
                    executar_api_equipes(payload)
                    time.sleep(2)
                    st.cache_data.clear()
                st.success(f"✅ Servidor {n_srv} (ID: {id_novo_serv}) inserido com sucesso!")
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
            val_atual_emerg = str(dados_atuais_srv.get("Faz parte de Equipe de Emergências?", "Não")).strip().capitalize()
            val_atual_fiscal = str(dados_atuais_srv.get("É Fiscal?", "Não")).strip().capitalize()
            val_atual_aeac = str(dados_atuais_srv.get("É Agente de Emergências Ambientais e Climáticas?", "Não")).strip().capitalize()
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
                # 🚀 TROCA PARA SELECTBOX
                try:
                    idx_func_edit = LISTA_FUNCOES_SERVIDOR.index(val_atual_funcao)
                except ValueError:
                    idx_func_edit = 0
                    
                nova_funcao = st.selectbox(
                    "Função / Cargo Institucional:", 
                    LISTA_FUNCOES_SERVIDOR,
                    index=idx_func_edit,
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
                    "Faz parte de Equipe de Emergências?", 
                    ["Sim", "Não"], 
                    index=idx_emerg, 
                    key=f"srv_ed_emerg_{id_srv_edit}"
                )
            with col_eq_ed2:
                idx_fisc = 0 if val_atual_fiscal == "Sim" else 1
                n_eq_fiscal = st.selectbox(
                    "É Fiscal?", 
                    ["Sim", "Não"], 
                    index=idx_fisc, 
                    key=f"srv_ed_fiscal_{id_srv_edit}"
                )
            with col_eq_ed3:
                idx_aeac = 0 if val_atual_aeac == "Sim" else 1
                n_eq_aeac = st.selectbox(
                    "É Agente de Emergências Ambientais e Climáticas?", 
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

# --- TELA 5: GERENCIAR AÇÕES PNAPA ---
elif modo == "🗂️ Gerenciar Ações PNAPA":
    st.markdown("<h3 style='color: #03170a;'>🗂️ Catálogo Oficial de Ações PNAPA</h3>", unsafe_allow_html=True)
    st.caption("Tabela auxiliar corporativa para governança nacional, vinculação e padronização das ações.")
    
    pode_administrar_catalogo = (perfil_usuario == "Administrador") and acesso_liberado

    if df_pnapas.empty:
        st.warning("⚠️ O catálogo de Ações PNAPA está vazio no momento.")
    else:
        # Oculta a linha técnica DIPRO_GLOBAL da exibição geral
        df_pnapas_vis = df_pnapas[df_pnapas["Num_Acao_PNAPA"].astype(str).str.strip().str.upper() != "DIPRO_GLOBAL"]
        st.dataframe(df_pnapas_vis, use_container_width=True, hide_index=True)

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
            
            # 🚀 LIDERANÇA NACIONAL (DONO DA AÇÃO) E TETOS
            st.markdown("###### 👑 Liderança Nacional e Metas/Tetos Globais")
            c_dn1, c_dn2, c_dn3, c_dn4 = st.columns([1, 1.5, 1, 1.2])
            with c_dn1:
                novo_uf_dono = st.selectbox("UF/Órgão do Dono:", ["Ceneac"] + LISTA_UFS_COMPLETA, key="cad_pna_uf_dono")
            with c_dn2:
                srvs_dono_disp = df_servidores[df_servidores["UF_Servidor"] == novo_uf_dono]["Servidor"].dropna().unique().tolist()
                novo_dono_acao = st.selectbox("Servidor Especialista (Dono da Ação):", srvs_dono_disp if srvs_dono_disp else ["Guttemberg"], key="cad_pna_dono")
            with c_dn3:
                nova_meta_nac = st.number_input("Meta Global Física:", min_value=0.0, value=12.0, step=1.0, key="cad_pna_meta_nac")
            with c_dn4:
                # 🚀 TETO ORÇAMENTÁRIO ESTIMADO
                novo_orc_nac = st.number_input("Teto Orçamentário (R$):", min_value=0.0, value=0.0, step=5000.0, format="%.2f", key="cad_pna_orc_nac")

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
                        "Meta_Nacional": float(nova_meta_nac),
                        "Orcamento_Nacional": float(novo_orc_nac)
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
            df_pna_edt_pool = df_pnapas[
                ~df_pnapas["Num_Acao_PNAPA"].astype(str).str.upper().str.contains("DIPRO") &
                ~df_pnapas["Acao_Ano"].astype(str).str.upper().str.contains("DIPRO")
            ].copy()
            
            if not df_pna_edt_pool.empty:
                anos_disp_edt = ["Todos"] + sorted([str(int(a)) for a in pd.to_numeric(df_pna_edt_pool["Ano"], errors='coerce').dropna().unique() if int(a) > 0], reverse=True)
                c_fano_edt, _ = st.columns([1, 2])
                with c_fano_edt:
                    f_ano_pna_edt = st.selectbox("Filtrar Ações por Ano:", anos_disp_edt, key="f_ano_pna_edt")
                
                df_pna_edt_filtrado = df_pna_edt_pool.copy()
                if f_ano_pna_edt != "Todos":
                    df_pna_edt_filtrado = df_pna_edt_filtrado[pd.to_numeric(df_pna_edt_filtrado["Ano"], errors='coerce').fillna(0).astype(int) == int(f_ano_pna_edt)]
                
                lista_acoes_edt = sorted((df_pna_edt_filtrado["Acao_Ano"].astype(str) + " - " + df_pna_edt_filtrado["Nome_Acao_Apelido"].astype(str)).tolist())
                acao_edt_sel = st.selectbox("Selecione a Ação para visualizar/alterar:", lista_acoes_edt, key="edt_pna_sel")
                
                cod_alvo_edt = acao_edt_sel.split(" - ")[0].strip()
                dados_alvo_edt = df_pna_edt_filtrado[df_pna_edt_filtrado["Acao_Ano"].astype(str) == cod_alvo_edt].iloc[0]
                
                id_col_nome = "ID_PNAPA" if "ID_PNAPA" in dados_alvo_edt else "Id"
                id_pna_edit = int(float(dados_alvo_edt[id_col_nome]))
                
                val_atual_ano = int(pd.to_numeric(dados_alvo_edt.get("Ano"), errors='coerce') or 2026)
                val_atual_num = str(dados_alvo_edt.get("Num_Acao_PNAPA", "")).strip().upper()
                val_atual_comp = str(dados_alvo_edt.get("Nome_Acao_Completo", "")).strip()
                val_atual_apelido = str(dados_alvo_edt.get("Nome_Acao_Apelido", "")).strip()
                val_atual_ind = str(dados_alvo_edt.get("Indicador", "")).strip()
                val_atual_imp = str(dados_alvo_edt.get("Importância", "Ordinária")).strip()
                val_atual_uf_dono = str(dados_alvo_edt.get("UF_Dono", "DF")).strip()
                val_atual_dono = str(dados_alvo_edt.get("Dono_Acao", "")).strip()
                val_atual_meta_nac = float(pd.to_numeric(dados_alvo_edt.get("Meta_Nacional", 0), errors='coerce') or 0.0)
                val_atual_orc_nac = float(pd.to_numeric(dados_alvo_edt.get("Orcamento_Nacional", 0.0), errors='coerce') or 0.0)

                st.markdown(f"#### 🗂️ Ficha da Ação: **{cod_alvo_edt}** `(ID: {id_pna_edit})`")

                c_e_ano, c_e_num = st.columns(2)
                with c_e_ano:
                    e_ano = st.number_input("Ano da Ação:", min_value=2020, max_value=2040, value=val_atual_ano, step=1, key=f"edt_pna_ano_{id_pna_edit}")
                with c_e_num:
                    e_num = st.text_input("Código/Número:", value=val_atual_num, key=f"edt_pna_num_{id_pna_edit}").strip().upper()

                e_comp = st.text_input("Nome Completo da Ação:", value=val_atual_comp, key=f"edt_pna_comp_{id_pna_edit}").strip()
                e_apelido = st.text_input("Nome Resumido / Apelido:", value=val_atual_apelido, key=f"edt_pna_apelido_{id_pna_edit}").strip()

                st.markdown("###### 👑 Liderança Nacional e Metas/Tetos Globais")
                c_edn1, c_edn2, c_edn3, c_edn4 = st.columns([1, 1.5, 1, 1.2])
                with c_edn1:
                    lista_ufs_dono_edit = LISTA_UFS_COMPLETA
                    idx_uf_dn = lista_ufs_dono_edit.index(val_atual_uf_dono) if val_atual_uf_dono in lista_ufs_dono_edit else (lista_ufs_dono_edit.index("DF") if "DF" in lista_ufs_dono_edit else 0)
                    e_uf_dono = st.selectbox("UF do Dono:", lista_ufs_dono_edit, index=idx_uf_dn, key=f"edt_pna_uf_dn_{id_pna_edit}")
                with c_edn2:
                    srvs_dono_edit = df_servidores[df_servidores["UF_Servidor"] == e_uf_dono]["Servidor"].dropna().unique().tolist()
                    idx_dn = srvs_dono_edit.index(val_atual_dono) if val_atual_dono in srvs_dono_edit else 0
                    e_dono = st.selectbox("Servidor Dono da Ação:", srvs_dono_edit if srvs_dono_edit else [val_atual_dono], index=idx_dn, key=f"edt_pna_dn_{id_pna_edit}")
                with c_edn3:
                    e_meta_nac = st.number_input("Meta Global Física:", min_value=0.0, value=val_atual_meta_nac, step=1.0, key=f"edt_pna_meta_nac_{id_pna_edit}")
                with c_edn4:
                    e_orc_nac = st.number_input("Teto Orçamentário (R$):", min_value=0.0, value=val_atual_orc_nac, step=5000.0, format="%.2f", key=f"edt_pna_orc_nac_{id_pna_edit}")

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
                            "Meta_Nacional": float(e_meta_nac),
                            "Orcamento_Nacional": float(e_orc_nac)
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
            df_pna_del_pool = df_pnapas[
                ~df_pnapas["Num_Acao_PNAPA"].astype(str).str.upper().str.contains("DIPRO") &
                ~df_pnapas["Acao_Ano"].astype(str).str.upper().str.contains("DIPRO")
            ].copy()
            if not df_pna_del_pool.empty:
                lista_acoes_del = sorted((df_pna_del_pool["Acao_Ano"].astype(str) + " - " + df_pna_del_pool["Nome_Acao_Apelido"].astype(str)).tolist())
                acao_del_sel = st.selectbox("Selecione a Ação para EXCLUIR:", lista_acoes_del, key="del_pna_sel")
                
                cod_alvo_del = acao_del_sel.split(" - ")[0].strip()
                dados_alvo_del = df_pna_del_pool[df_pna_del_pool["Acao_Ano"].astype(str) == cod_alvo_del].iloc[0]
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



# =====================================================================
# --- TELA 6: PACTUAÇÃO PRÉ-PNAPA (DUPLO MATCHMAKER: FÍSICO & FINANCEIRO) ---
# =====================================================================
elif modo == "🤝 Pactuação Pré-PNAPA":
    st.markdown("<h3 style='color: #03170a;'>🤝 Painel de Pactuação Pré-PNAPA (Físico & Orçamentário)</h3>", unsafe_allow_html=True)
    st.caption("Pactuação estratégica entre as Metas e Tetos Globais do Ceneac (Top-Down) e as demandas inseridas pelos Estados (Bottom-Up).")

    if df_pnapas.empty:
        st.warning("⚠️ O Catálogo de Ações PNAPA está vazio. Cadastre ações no catálogo para iniciar a pactuação.")
    else:
        # 1. RECUPERAÇÃO E FILTRAGEM DO TETO GLOBAL DIPRO (OPÇÃO 1)
        if not df_pnapas.empty and "Ano" in df_pnapas.columns:
            anos_disponiveis = sorted(df_pnapas["Ano"].dropna().astype(int).unique().tolist(), reverse=True)
        else:
            anos_disponiveis = [2027, 2026]

        c_topo1, c_topo2, c_topo3 = st.columns([1, 1.3, 1.3])
        with c_topo1:
            ano_pact_sel = st.selectbox("📅 Ano de Planejamento:", anos_disponiveis, key="pact_ano_sel")

        # 1.1 Resgata a linha de configuração DIPRO_GLOBAL para o ano
        linha_dipro_ano = df_pnapas[
            (df_pnapas["Num_Acao_PNAPA"].astype(str).str.strip().str.upper() == "DIPRO_GLOBAL") &
            (pd.to_numeric(df_pnapas["Ano"], errors='coerce').fillna(0).astype(int) == int(ano_pact_sel))
        ]

        if not linha_dipro_ano.empty:
            teto_dipro_atual = float(pd.to_numeric(linha_dipro_ano.iloc[0].get("Orcamento_Nacional", 0.0), errors='coerce') or 1500000.0)
        else:
            teto_dipro_atual = float(st.session_state.get("gov_params", {}).get("orcamento_global_dipro", 1500000.0))

        st.session_state["teto_global_dipro"] = teto_dipro_atual

        # 1.2 Filtra apenas ações operacionais (ocultando a linha de metadados DIPRO_GLOBAL)
        df_pna_ano = df_pnapas[
            (pd.to_numeric(df_pnapas["Ano"], errors='coerce').fillna(0).astype(int) == int(ano_pact_sel)) &
            (df_pnapas["Num_Acao_PNAPA"].astype(str).str.strip().str.upper() != "DIPRO_GLOBAL")
        ].copy()

        with c_topo2:
            donos_disponiveis = ["Todos os Especialistas"] + sorted([d for d in df_pna_ano["Dono_Acao"].dropna().unique() if str(d).strip()])
            filtro_dono = st.selectbox("👑 Filtrar por Dono da Ação (Sede):", donos_disponiveis, key="pact_dono_sel")

        with c_topo3:
            status_pact_filtro = st.selectbox(
                "⚖️ Filtro de Alinhamento:", 
                [
                    "Todas as Ações", 
                    "Déficit Físico (<100%)", 
                    "Meta Física Atingida (100%)", 
                    "Superávit Físico (>100%)", 
                    "Orçamento Estourado (> Teto Ceneac)", 
                    "Sem Adesão Estadual (0%)"
                ], 
                key="pact_status_filtro"
            )

        # 1.3 Popover com Gravação Persistente no SharePoint (Administrador)
        if perfil_usuario == "Administrador":
            with st.popover("⚙️ Calibrar Orçamento Global Aprovado pela DIPRO", use_container_width=True):
                st.markdown("#### 🏛️ Envelope Orçamentário da Emergência Ambiental (DIPRO)")
                novo_teto_dipro = st.number_input(
                    f"Teto Orçamentário Global Autorizado pela DIPRO para {ano_pact_sel} (R$):",
                    min_value=0.0,
                    value=float(teto_dipro_atual),
                    step=50000.0,
                    format="%.2f",
                    key=f"input_teto_dipro_persist_{ano_pact_sel}"
                )
                
                if st.button("💾 Salvar Teto Global DIPRO no SharePoint", type="primary", key="btn_salvar_teto_dipro_db"):
                    col_id_pna = "ID_PNAPA" if "ID_PNAPA" in df_pnapas.columns else "Id"
                    if not linha_dipro_ano.empty:
                        id_dipro_ref = int(float(linha_dipro_ano.iloc[0][col_id_pna]))
                        acao_flow = "Editar"
                    else:
                        id_dipro_ref = int(pd.to_numeric(df_pnapas[col_id_pna], errors='coerce').fillna(0).max() + 1) if not df_pnapas.empty else 1
                        acao_flow = "Inserir"
                        
                    payload_dipro = {
                        "Acao": acao_flow,
                        "Id": str(id_dipro_ref),
                        "ID_PNAPA": id_dipro_ref,
                        "Ano": int(ano_pact_sel),
                        "Num_Acao_PNAPA": "DIPRO_GLOBAL",
                        "Acao_Ano": f"DIPRO_GLOBAL-{ano_pact_sel}",
                        "Nome_Acao_Completo": f"Orçamento Global Autorizado DIPRO {ano_pact_sel}",
                        "Nome_Acao_Apelido": f"Teto DIPRO {ano_pact_sel}",
                        "Indicador": "Orçamento Global",
                        "Importância": "Estratégica",
                        "UF_Dono": "Ceneac",
                        "Dono_Acao": "Diretoria DIPRO",
                        "Meta_Nacional": 0.0,
                        "Orcamento_Nacional": float(novo_teto_dipro)
                    }
                    
                    with st.spinner("Gravando Teto Global DIPRO no SharePoint..."):
                        try:
                            r = requests.post(URL_FLOW_PNAPAS, json=payload_dipro, timeout=35)
                            if r.status_code in [200, 202]:
                                time.sleep(2)
                                st.cache_data.clear()
                                st.session_state["teto_global_dipro"] = novo_teto_dipro
                                st.success(f"✅ Teto Global DIPRO para {ano_pact_sel} salvo com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Erro ao salvar no SharePoint (Status {r.status_code})")
                        except Exception as e:
                            st.error(f"❌ Erro de comunicação: {e}")

        if filtro_dono != "Todos os Especialistas":
            df_pna_ano = df_pna_ano[df_pna_ano["Dono_Acao"] == filtro_dono]

        # 2. CRUZAMENTO SEGURO DE DADOS COM AS AÇÕES ESTADUAIS (df_atual)
        df_acoes_cadastradas = df_atual[
            (df_atual["Nível"].astype(str).str.strip() == "Ação") &
            (df_atual["Ano da Ação"].astype(str).str.split('.').str[0] == str(ano_pact_sel))
        ].copy()

        if not df_acoes_cadastradas.empty:
            df_acoes_cadastradas["Meta_Num"] = pd.to_numeric(df_acoes_cadastradas["Meta_Indicador"], errors='coerce').fillna(0.0)
            
            r_d = pd.to_numeric(df_acoes_cadastradas.get("Rec_Plan_Diarias", 0), errors='coerce').fillna(0.0)
            r_p = pd.to_numeric(df_acoes_cadastradas.get("Rec_Plan_Passagens", 0), errors='coerce').fillna(0.0)
            r_o = pd.to_numeric(df_acoes_cadastradas.get("Rec_Plan_Outras_Despesas", 0), errors='coerce').fillna(0.0)
            df_acoes_cadastradas["Rec_Plan_Num"] = r_d + r_p + r_o
            
            # 🚀 Chave normalizada para cruzamento exato
            df_acoes_cadastradas["Num_Pna_Limpo"] = df_acoes_cadastradas["Número da Ação PNAPA"].astype(str).str.strip().str.upper()
        else:
            df_acoes_cadastradas["Num_Pna_Limpo"] = []

        # 3. CONSOLIDAÇÃO GLOBAL DO BALANÇO ORÇAMENTÁRIO E METAS
        total_acoes_catalogo = len(df_pna_ano)
        meta_fisica_global = pd.to_numeric(df_pna_ano["Meta_Nacional"], errors='coerce').fillna(0.0).sum()
        
        col_orc_nac = "Orcamento_Nacional" if "Orcamento_Nacional" in df_pna_ano.columns else ""
        teto_total_distribuido_ceneac = pd.to_numeric(df_pna_ano[col_orc_nac], errors='coerce').fillna(0.0).sum() if col_orc_nac else 0.0

        # Mapeamento de todas as chaves válidas do catálogo para este ano
        todas_chaves_catalogo = set()
        for _, r_pna in df_pna_ano.iterrows():
            c_num = str(r_pna.get("Num_Acao_PNAPA", "")).strip().upper()
            c_ano = str(r_pna.get("Acao_Ano", "")).strip().upper()
            if c_num: todas_chaves_catalogo.add(c_num)
            if c_ano: todas_chaves_catalogo.add(c_ano)
            if c_num: todas_chaves_catalogo.add(f"{c_num}-{ano_pact_sel}")

        df_pactuado_filtrado = df_acoes_cadastradas[df_acoes_cadastradas["Num_Pna_Limpo"].isin(todas_chaves_catalogo)] if not df_acoes_cadastradas.empty else pd.DataFrame()
        
        meta_fisica_demandada = df_pactuado_filtrado["Meta_Num"].sum() if not df_pactuado_filtrado.empty else 0.0
        orcamento_total_demandado_ufs = df_pactuado_filtrado["Rec_Plan_Num"].sum() if not df_pactuado_filtrado.empty else 0.0
        
        taxa_adesao_fisica = (meta_fisica_demandada / meta_fisica_global * 100.0) if meta_fisica_global > 0 else 0.0
        saldo_dipro_restante = teto_dipro_atual - orcamento_total_demandado_ufs

        st.markdown("---")
        # LINHA 1: BALANÇO ORÇAMENTÁRIO TRIPLO (DIPRO -> CENEAC -> ESTADOS)
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        c_m1.metric("🏛️ Teto Global DIPRO", formatar_moeda_br(teto_dipro_atual))
        c_m2.metric(
            "📋 Teto Alocado Ceneac", 
            formatar_moeda_br(teto_total_distribuido_ceneac), 
            delta=f"{formatar_moeda_br(teto_dipro_atual - teto_total_distribuido_ceneac)} do teto DIPRO"
        )
        c_m3.metric(
            "💰 Demandado pelas UFs", 
            formatar_moeda_br(orcamento_total_demandado_ufs), 
            delta=f"{(orcamento_total_demandado_ufs/teto_dipro_atual*100.0 if teto_dipro_atual > 0 else 0):.1f}% da DIPRO"
        )
        c_m4.metric(
            "⚖️ Saldo Restante DIPRO", 
            formatar_moeda_br(saldo_dipro_restante), 
            delta="Dentro do Limite" if saldo_dipro_restante >= 0 else "⚠️ Estouro de Teto",
            delta_color="normal" if saldo_dipro_restante >= 0 else "inverse"
        )
        
        # LINHA 2: COBERTURA FÍSICA E ADESÃO (ALTO CONTRASTE)
        c_sub1, c_sub2, c_sub3 = st.columns([1, 1.5, 1.5])
        with c_sub1:
            st.markdown(
                f"<div style='font-size: 0.88em; color: #334155; margin-top: 4px;'>"
                f"🎯 <strong>Ações Analisadas:</strong> "
                f"<span style='background-color: #e2e8f0; color: #0f172a; padding: 2px 7px; border-radius: 4px; font-weight: 700;'>{total_acoes_catalogo}</span>"
                f"</div>", 
                unsafe_allow_html=True
            )
        with c_sub2:
            st.markdown(
                f"<div style='font-size: 0.88em; color: #334155; margin-top: 4px;'>"
                f"📊 <strong>Cobertura Física Nacional:</strong> "
                f"<span style='background-color: #e2e8f0; color: #0f172a; padding: 2px 7px; border-radius: 4px; font-weight: 700;'>{taxa_adesao_fisica:.1f}%</span> "
                f"<span style='color: #64748b; font-weight: 500;'>({meta_fisica_demandada:.1f} de {meta_fisica_global:.1f})</span>"
                f"</div>", 
                unsafe_allow_html=True
            )
        with c_sub3:
            ufs_part_count = len(df_pactuado_filtrado["UF_Acao_PNAPA"].dropna().unique()) if not df_pactuado_filtrado.empty else 0
            pct_part_uf = (ufs_part_count / 26.0 * 100.0)
            st.markdown(
                f"<div style='font-size: 0.88em; color: #334155; margin-top: 4px;'>"
                f"🗺️ <strong>Adesão Federativa:</strong> "
                f"<span style='background-color: #e2e8f0; color: #0f172a; padding: 2px 7px; border-radius: 4px; font-weight: 700;'>{ufs_part_count}/26 UFs</span> "
                f"<span style='color: #64748b; font-weight: 500;'>({pct_part_uf:.0f}%)</span>"
                f"</div>", 
                unsafe_allow_html=True
            )
            
        st.markdown("---")

        # 4. CARDS POR AÇÃO COM DUPLA BARRA (FÍSICO + FINANCEIRO)
        todas_ufs_brasil = [u for u in LISTA_UFS_COMPLETA if u not in ["Ceneac", "DF"]]

        for _, acao_row in df_pna_ano.iterrows():
            cod_num = str(acao_row.get("Num_Acao_PNAPA", "")).strip().upper()
            cod_ano = str(acao_row.get("Acao_Ano", f"{cod_num}-{ano_pact_sel}")).strip().upper()
            chave_acao_ano = cod_ano if cod_ano else f"{cod_num}-{ano_pact_sel}"
            
            nome_acao = str(acao_row.get("Nome_Acao_Apelido", acao_row.get("Nome_Acao_Completo", "")))
            dono_acao = str(acao_row.get("Dono_Acao", "Ceneac"))
            uf_dono = str(acao_row.get("UF_Dono", "Ceneac"))
            indicador_acao = str(acao_row.get("Indicador", "Não informado"))
            
            # Metas e Tetos Nacionais (Top-Down)
            meta_nacional_fisica = float(pd.to_numeric(acao_row.get("Meta_Nacional", 0.0), errors='coerce') or 0.0)
            teto_nacional_orc = float(pd.to_numeric(acao_row.get(col_orc_nac, 0.0), errors='coerce') or 0.0) if col_orc_nac else 0.0

            # 🚀 FILTRAGEM EXATA: Apenas propostas vinculadas a ESTA AÇÃO
            chaves_desta_acao = {cod_num, cod_ano, f"{cod_num}-{ano_pact_sel}"} - {""}
            
            if not df_acoes_cadastradas.empty:
                df_propostas_ufs = df_acoes_cadastradas[df_acoes_cadastradas["Num_Pna_Limpo"].isin(chaves_desta_acao)].copy()
            else:
                df_propostas_ufs = pd.DataFrame()
            
            meta_demandada_ufs = df_propostas_ufs["Meta_Num"].sum() if not df_propostas_ufs.empty else 0.0
            orc_demandado_ufs = df_propostas_ufs["Rec_Plan_Num"].sum() if not df_propostas_ufs.empty else 0.0
            
            # % Físico
            pct_fisico = (meta_demandada_ufs / meta_nacional_fisica * 100.0) if meta_nacional_fisica > 0 else (100.0 if meta_demandada_ufs > 0 else 0.0)

            # Classificação Semafórica da Meta Física
            if meta_demandada_ufs == 0:
                badge_status = "⚪ Sem Adesão (0%)"
            elif pct_fisico < 100:
                badge_status = f"🟡 Déficit Físico ({pct_fisico:.0f}%)"
            elif pct_fisico == 100:
                badge_status = "🟢 Meta Pactuada (100%)"
            else:
                badge_status = f"🔵 Superávit Físico ({pct_fisico:.0f}%)"

            # Filtros de Alinhamento
            if status_pact_filtro != "Todas as Ações":
                if "Déficit Físico" in status_pact_filtro and (pct_fisico >= 100 or meta_demandada_ufs == 0): continue
                if "Meta Física Atingida" in status_pact_filtro and pct_fisico != 100: continue
                if "Superávit Físico" in status_pact_filtro and pct_fisico <= 100: continue
                if "Orçamento Estourado" in status_pact_filtro and (teto_nacional_orc == 0 or orc_demandado_ufs <= teto_nacional_orc): continue
                if "Sem Adesão" in status_pact_filtro and meta_demandada_ufs > 0: continue

            # RENDERIZAÇÃO DO EXPANDER DA AÇÃO COM ALTO CONTRASTE
            with st.expander(f"📌 **{chave_acao_ano}** — {nome_acao}  |  {badge_status}  |  Demandado: {formatar_moeda_br(orc_demandado_ufs)}", expanded=False):
                c_inf1, c_inf2, c_inf3 = st.columns([1.5, 1, 1])
                with c_inf1:
                    st.markdown(
                        f"👑 **Especialista Sede (Dono):** <span style='background-color: #e2e8f0; color: #0f172a; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.9em;'>{dono_acao} ({uf_dono})</span>", 
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"📈 **Indicador Oficial:** <span style='background-color: #e2e8f0; color: #0f172a; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.9em;'>{indicador_acao}</span>", 
                        unsafe_allow_html=True
                    )
                with c_inf2:
                    st.metric("Meta Física Nacional", f"{meta_nacional_fisica:.1f}")
                with c_inf3:
                    st.metric("Meta Física Demandada (UFs)", f"{meta_demandada_ufs:.1f}", delta=f"{meta_demandada_ufs - meta_nacional_fisica:+.1f}")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- BARRA 1: PACTUAÇÃO FÍSICA ---
                pct_bar_fisico = min(100.0, max(0.0, pct_fisico))
                cor_barra_fisica = "#15803d" if pct_fisico <= 100 else "#2563eb"
                
                st.markdown(f"""
                <div style='margin-bottom: 6px;'>
                    <strong>🎯 Alinhamento de Metas Físicas:</strong> 
                    <span style='background-color: #e2e8f0; color: #0f172a; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.9em;'>{pct_fisico:.1f}%</span> 
                    <span style='color: #475569; font-size: 0.92em; font-weight: 500;'>({meta_demandada_ufs:.1f} de {meta_nacional_fisica:.1f})</span>
                </div>
                <div style='width: 100%; background-color: #e2e8f0; border-radius: 8px; height: 14px; overflow: hidden; margin-bottom: 16px;'>
                    <div style='width: {pct_bar_fisico}%; background-color: {cor_barra_fisica}; height: 100%; border-radius: 8px; transition: width 0.4s ease;'></div>
                </div>
                """, unsafe_allow_html=True)

                # --- BARRA 2: PACTUAÇÃO FINANCEIRA ---
                if teto_nacional_orc > 0:
                    pct_orc = (orc_demandado_ufs / teto_nacional_orc) * 100.0
                    pct_bar_orc = min(100.0, max(0.0, pct_orc))
                    cor_barra_orc = "#03170a" if pct_orc <= 100 else "#b91c1c"
                    
                    st.markdown(f"""
                    <div style='margin-bottom: 6px;'>
                        <strong>💰 Demanda Orçamentária vs Teto Ceneac:</strong> 
                        <span style='background-color: #e2e8f0; color: #0f172a; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.9em;'>{pct_orc:.1f}%</span> 
                        <span style='color: #475569; font-size: 0.92em; font-weight: 500;'>({formatar_moeda_br(orc_demandado_ufs)} de {formatar_moeda_br(teto_nacional_orc)})</span>
                    </div>
                    <div style='width: 100%; background-color: #e2e8f0; border-radius: 8px; height: 14px; overflow: hidden; margin-bottom: 16px;'>
                        <div style='width: {pct_bar_orc}%; background-color: {cor_barra_orc}; height: 100%; border-radius: 8px; transition: width 0.4s ease;'></div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='margin-bottom: 16px;'>
                        <strong>💰 Demanda Orçamentária Total Acumulada das UFs:</strong> 
                        <span style='background-color: #e2e8f0; color: #0f172a; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.9em;'>{formatar_moeda_br(orc_demandado_ufs)}</span> 
                        <em style='color: #64748b; font-size: 0.9em;'>(Teto Ceneac não fixado no catálogo)</em>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                t_pact_ufs, t_pact_pend = st.tabs(["🗺️ Propostas dos Estados (Físico & Orçamento)", "⏳ Estados Sem Proposta Registrada"])

                with t_pact_ufs:
                    if df_propostas_ufs.empty:
                        st.info("Nenhuma UF registrou proposta de planejamento para esta ação.")
                    else:
                        df_exibir_pact = df_propostas_ufs[[
                            "UF_Acao_PNAPA", "Papel_Institucional", "Servidor", 
                            "Meta_Indicador", "Rec_Plan_Diarias", "Rec_Plan_Passagens", 
                            "Rec_Plan_Outras_Despesas", "Rec_Plan_Num", "Andamento"
                        ]].copy()
                        
                        df_exibir_pact.columns = [
                            "UF", "Papel", "Ponto Focal Estadual", 
                            "Meta Proposta", "Diárias (R$)", "Passagens (R$)", 
                            "Outras Desp. (R$)", "Total Previsto (R$)", "Situação"
                        ]
                        
                        for col_moeda in ["Diárias (R$)", "Passagens (R$)", "Outras Desp. (R$)", "Total Previsto (R$)"]:
                            df_exibir_pact[col_moeda] = df_exibir_pact[col_moeda].apply(formatar_moeda_br)
                        
                        st.dataframe(df_exibir_pact.reset_index(drop=True), use_container_width=True, hide_index=True)

                with t_pact_pend:
                    ufs_aderiram = df_propostas_ufs["UF_Acao_PNAPA"].dropna().unique().tolist() if not df_propostas_ufs.empty else []
                    ufs_faltantes = sorted([u for u in todas_ufs_brasil if u not in ufs_aderiram])
                    
                    if not ufs_faltantes:
                        st.success("🎉 Todas as 26 UFs já enviaram propostas para esta Ação!")
                    else:
                        st.warning(f"⚠️ **{len(ufs_faltantes)} estado(s)** ainda não cadastraram proposta:")
                        tags_estados = " ".join([f"<span style='background-color: #e2e8f0; color: #0f172a; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.85em; margin-right: 4px;'>{u}</span>" for u in ufs_faltantes])
                        st.markdown(tags_estados, unsafe_allow_html=True)

# --- TELA 7: MEUS FEEDBACKS (360º) ---
elif modo == "⭐ Meus Feedbacks (360º)":
    st.markdown("<h3 style='color: #03170a;'>⭐ Meus Feedbacks e Avaliações de Pares (360º)</h3>", unsafe_allow_html=True)
    st.markdown("Nesta área, você avalia colegas de missões concluídas (com 3 ou mais membros) e consulta os feedbacks anônimos que recebeu para o seu desenvolvimento profissional.")
    
    import json
    
    # 🚀 DATA DE CORTE RETROATIVA (01 de Agosto) para garantir que seus testes apareçam
    DATA_CORTE_360 = pd.Timestamp(date(2026, 8, 1))
    
    def limpar_e_converter_data(valor):
        if pd.isna(valor): return pd.NaT
        val_str = str(valor).strip()
        if val_str == "" or val_str.lower() in ["none", "nat", "nan"]: return pd.NaT
        if val_str.replace('.', '', 1).isdigit():
            try: return pd.to_datetime(int(float(val_str)), unit='D', origin='1899-12-30')
            except: pass
        return pd.to_datetime(val_str, errors='coerce', dayfirst=True)

    df_atvs = df_atual[df_atual["Nível"].astype(str).str.strip() == "Atividade"].copy()
    df_atvs["Data_Termino_DT"] = df_atvs["Data de Término"].apply(limpar_e_converter_data)
    
    df_concluidas = df_atvs[
        (df_atvs["Andamento"].astype(str).str.strip() == "Concluída") &
        (df_atvs["Data_Termino_DT"].notna()) &
        (df_atvs["Data_Termino_DT"] >= DATA_CORTE_360)
    ].copy()
    
    contagem_membros = df_concluidas.groupby("Codigo_Atividade")["Servidor"].nunique().reset_index()
    codigos_elegiveis = contagem_membros[contagem_membros["Servidor"] >= 3]["Codigo_Atividade"].tolist()
    
    df_elegiveis = df_concluidas[df_concluidas["Codigo_Atividade"].isin(codigos_elegiveis)]
    
    # 🚀 CORREÇÃO DE IDENTIDADE: Mapeia TODOS os nomes que estão com o seu e-mail
    meus_nomes_cadastrados = df_servidores[df_servidores["E_mail"] == email_logado]["Servidor"].unique().tolist()
    if not meus_nomes_cadastrados:
        meus_nomes_cadastrados = [nome_usuario_logado]
        
    minhas_missoes_elegiveis = df_elegiveis[df_elegiveis["Servidor"].isin(meus_nomes_cadastrados)]["Codigo_Atividade"].unique().tolist()
    
    tab_pendentes, tab_recebidos = st.tabs(["⏳ Avaliações Pendentes (Avaliar Colegas)", "📊 Meu Desempenho (Feedbacks Recebidos)"])
    
    with tab_pendentes:
        st.markdown("#### 🎯 Colegas aguardando sua avaliação")
        
        # Filtra os colegas da missão, ignorando você (A trava está desabilitada para o teste)
        df_colegas = df_elegiveis[
            (df_elegiveis["Codigo_Atividade"].isin(minhas_missoes_elegiveis)) 
            # & (~df_elegiveis["Servidor"].isin(meus_nomes_cadastrados))  <-- COMENTADO PARA O SEU TESTE
        ].copy()
        
        def ja_avaliei(json_str):
            try:
                avals = json.loads(str(json_str))
                return any(a.get("avaliador") == email_logado for a in avals)
            except:
                return False
                
        df_colegas["Ja_Avaliei"] = df_colegas["Avaliacao_Feedback"].apply(ja_avaliei)
        df_pendentes = df_colegas[~df_colegas["Ja_Avaliei"]]
        
        if df_pendentes.empty:
            st.success("🎉 Excelente! Você não tem nenhuma avaliação pendente. Todos os seus colegas de missão já foram avaliados.")
        else:
            st.info(f"Você tem **{len(df_pendentes)}** avaliação(ões) pendente(s).")
            
            opcoes_pendentes = []
            mapa_linhas_pendentes = {}
            for _, row in df_pendentes.iterrows():
                label = f"[{row['Codigo_Atividade']}] Missão: {row['Nome da Atividade']} | Colega: {row['Servidor']}"
                opcoes_pendentes.append(label)
                mapa_linhas_pendentes[label] = row
                
            alvo_sel = st.selectbox("Selecione o Colega para Avaliar:", opcoes_pendentes)
            linha_alvo = mapa_linhas_pendentes[alvo_sel]
            
            st.markdown(f"**Avaliando:** {linha_alvo['Servidor']}")
            
            nota_360 = st.radio("Como você avalia a participação e entrega deste colega nesta missão?", ["1 - Satisfatória / Positiva 👍", "0 - Insatisfatória / Precisa Melhorar 👎"])
            feedback_360 = st.text_area("Deixe um comentário construtivo (O colega verá o texto, mas não saberá quem escreveu):")
            
            if st.button("💾 Enviar Avaliação", type="primary"):
                json_antigo = str(linha_alvo["Avaliacao_Feedback"]).strip()
                try:
                    lista_avals = json.loads(json_antigo)
                    if not isinstance(lista_avals, list): lista_avals = []
                except:
                    lista_avals = []
                    
                nova_aval = {
                    "avaliador": email_logado,
                    "nota": 1 if "1" in nota_360 else 0,
                    "feedback": feedback_360.strip()
                }
                lista_avals.append(nova_aval)
                json_novo = json.dumps(lista_avals, ensure_ascii=False)
                
                p_item = {col: linha_alvo[col] for col in df_atual.columns if col in linha_alvo}
                p_item["Acao"] = "Editar"
                p_item["Id"] = str(linha_alvo["Id"])
                p_item["Avaliacao_Feedback"] = json_novo
                
                payload_sanit = {k: (0.0 if pd.isna(v) and ("Rec_" in k or "Dias_" in k) else ("" if pd.isna(v) else v)) for k, v in p_item.items()}
                
                with st.spinner("Enviando avaliação..."):
                    executar_envio_sharepoint([payload_sanit])
                    time.sleep(1.5)
                    st.cache_data.clear()
                    if "df" in st.session_state: del st.session_state.df
                st.success("Avaliação enviada com sucesso! Obrigado pelo feedback.")
                time.sleep(1.5)
                st.rerun()

    with tab_recebidos:
        st.markdown("#### 📊 Meu Computo Geral e Feedbacks")
        
        minhas_linhas = df_elegiveis[df_elegiveis["Servidor"].isin(meus_nomes_cadastrados)]
        
        todas_avals_recebidas = []
        for _, row in minhas_linhas.iterrows():
            try:
                avals = json.loads(str(row["Avaliacao_Feedback"]))
                for a in avals:
                    a["Atividade"] = row["Nome da Atividade"]
                    a["Codigo"] = row["Codigo_Atividade"]
                todas_avals_recebidas.extend(avals)
            except:
                continue
                
        if not todas_avals_recebidas:
            st.info("Você ainda não recebeu avaliações dos seus colegas nas missões elegíveis.")
        else:
            total_recebido = len(todas_avals_recebidas)
            total_positivos = sum(1 for a in todas_avals_recebidas if a.get("nota") == 1)
            taxa_satisfacao = (total_positivos / total_recebido) * 100
            
            c_dash1, c_dash2, c_dash3 = st.columns(3)
            c_dash1.metric("Total de Avaliações Recebidas", total_recebido)
            c_dash2.metric("Avaliações Positivas (Satisfatório)", total_positivos)
            c_dash3.metric("Taxa de Aprovação", f"{taxa_satisfacao:.1f}%")
            
            st.markdown("---")
            st.markdown("##### 💬 Mural de Feedbacks Anônimos")
            for av in todas_avals_recebidas:
                cor_borda = "#22c55e" if av.get("nota") == 1 else "#ef4444"
                icone = "👍" if av.get("nota") == 1 else "👎"
                texto = av.get("feedback", "Sem comentário.")
                if texto == "": 
                    texto = "*Avaliador não deixou comentário.*"
                
                st.markdown(f"""
                <div style="border-left: 5px solid {cor_borda}; padding: 10px; margin-bottom: 10px; background-color: #f8fafc; border-radius: 5px;">
                    <p style="margin:0; font-size:12px; color:#64748b;">Missão: {av['Codigo']} - {av['Atividade']}</p>
                    <p style="margin:5px 0 0 0; color:#0f172a;"><b>{icone}</b> "{texto}"</p>
                </div>
                """, unsafe_allow_html=True)


# --- TELA 8: CENTRAL DE SUGESTÕES E MELHORIAS ---
elif modo == "💡 Sugestões & Melhorias":
    st.markdown("<h2 style='color: #03170a;'>💡 Central de Feedback & Sugestões de Melhoria</h2>", unsafe_allow_html=True)
    st.caption("Espaço colaborativo para que testadores e usuários enviem inconsistências, ideias e solicitações.")
    
    # 1. Cartões de Métricas no Topo
    total_feedbacks = len(df_sugestoes) if not df_sugestoes.empty else 0
    abertos = len(df_sugestoes[df_sugestoes["Status"].astype(str).str.strip().isin(["Aberto", "Em Desenvolvimento"])]) if not df_sugestoes.empty and "Status" in df_sugestoes.columns else 0
    concluidos = len(df_sugestoes[df_sugestoes["Status"].astype(str).str.strip() == "Concluído"]) if not df_sugestoes.empty and "Status" in df_sugestoes.columns else 0
    
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
                    "🤝 Pactuação Pré-PNAPA",
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
                id_nova_sug = int(pd.to_numeric(df_sugestoes["Id"], errors='coerce').max() + 1) if not df_sugestoes.empty and "Id" in df_sugestoes.columns else 1
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
                        # 🚀 Timeout estendido para 35s
                        r = requests.post(URL_FLOW_SUGESTOES, json=payload_sugestao, timeout=35)
                        if r.status_code in [200, 202]:
                            time.sleep(2.5)
                            st.cache_data.clear()
                            st.success("🎉 Sugestão registrada com sucesso! Ela já consta no quadro de acompanhamento.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ O Power Automate rejeitou a solicitação (Status {r.status_code}).")
                    except requests.exceptions.Timeout:
                        st.error("⏳ A gravação demorou mais de 35 segundos. Verifique o quadro antes de reenviar para evitar duplicidade.")
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
            c_f_st, c_f_pr = st.columns(2)
            with c_f_st:
                filtro_status = st.selectbox("Filtrar por Status:", ["Todos", "Aberto", "Em Desenvolvimento", "Concluído", "Descartado"], key="f_sug_status")
            with c_f_pr:
                filtro_prio = st.selectbox("Filtrar por Prioridade:", ["Todas", "Alta", "Média", "Baixa"], key="f_sug_prio")
                
            df_sug_exib = df_sugestoes.copy()
            if filtro_status != "Todos" and "Status" in df_sug_exib.columns:
                df_sug_exib = df_sug_exib[df_sug_exib["Status"].astype(str).str.strip() == filtro_status]
            if filtro_prio != "Todas" and "Prioridade" in df_sug_exib.columns:
                df_sug_exib = df_sug_exib[df_sug_exib["Prioridade"].astype(str).str.strip() == filtro_prio]
                
            cols_exib = [c for c in ["Id", "Data_Registro", "Prioridade", "Status", "Modulo", "Titulo", "Descricao", "Autor", "Resposta_Admin"] if c in df_sug_exib.columns]
            st.dataframe(df_sug_exib[cols_exib], use_container_width=True, hide_index=True)
            
            # --- PAINEL EXCLUSIVO DO ADMINISTRADOR ---
            if perfil_usuario == "Administrador" and not df_sugestoes.empty and "Id" in df_sugestoes.columns:
                st.markdown("---")
                with st.expander("⚙️ **Painel de Governança (Exclusivo Administrador)**", expanded=True):
                    st.caption("Altere a prioridade real, atualize o status da demanda e dê um parecer técnico ao autor.")
                    
                    lista_ids_sug = df_sugestoes["Id"].dropna().astype(str).tolist()
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
                                    r = requests.post(URL_FLOW_SUGESTOES, json=payload_edt_sug, timeout=35)
                                    if r.status_code in [200, 202]:
                                        time.sleep(2)
                                        st.cache_data.clear()
                                        st.success(f"✅ Sugestão ID {id_gestao_sel} atualizada com sucesso!")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Erro ao atualizar (Status {r.status_code}): {r.text}")
                                except requests.exceptions.Timeout:
                                    st.error("⏳ A atualização demorou mais de 35s. Atualize a lista para verificar se foi concluída.")
                                except Exception as e:
                                    st.error(f"❌ Erro de conexão: {e}")

                    with c_btn_excluir:
                        with st.popover("🗑️ Excluir"):
                            st.caption(f"Excluir sugestão ID {id_gestao_sel}?")
                            if st.button("Confirmar exclusão", type="primary", key="btn_del_sug_conf"):
                                try:
                                    r = requests.post(URL_FLOW_SUGESTOES, json={"Acao": "Excluir", "Id": str(id_gestao_sel)}, timeout=35)
                                    if r.status_code in [200, 202]:
                                        time.sleep(2)
                                        st.cache_data.clear()
                                        st.success("Sugestão excluída.")
                                        time.sleep(1)
                                        st.rerun()
                                except requests.exceptions.Timeout:
                                    st.error("⏳ Tempo limite excedido ao tentar excluir.")
                                except Exception as e:
                                    st.error(f"Erro: {e}")


# --- TELA 9: BASE DE CONHECIMENTO (FAQ) ---
elif modo == "📖 Base de Conhecimento (FAQ)":
    # CSS com escopo seguro para o FAQ (alto contraste em caixas de código, listas e textos)
    st.markdown("""
    <style>
    div[data-testid="stMarkdownContainer"] code {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        font-weight: 600 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        border: 1px solid #cbd5e1 !important;
        font-size: 0.9em !important;
    }
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] li {
        color: #0f172a !important;
        line-height: 1.6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='color: #03170a;'>📖 Base de Conhecimento & Regras de Negócio</h2>", unsafe_allow_html=True)
    st.caption("Manual oficial de governança, diretrizes operacionais, fórmulas de metas e regras do SisPNAPA.")
    
    try:
        with open("conhecimento_faq.md", "r", encoding="utf-8") as f_faq:
            conteudo_faq = f_faq.read()
        st.markdown(conteudo_faq)
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo 'conhecimento_faq.md': {e}")
        st.info("Certifique-se de que o arquivo 'conhecimento_faq.md' está na raiz do seu repositório no GitHub.")

# --- TELA 9: ASSISTENTE VIRTUAL (GEMINI API) ---
elif modo == "🤖 Assistente Virtual":
    # CSS para garantir fundo claro no container inferior e no campo de digitação
    st.markdown("""
    <style>
    /* 1. Barra inferior e caixa de digitação (Mantidos) */
    div[data-testid="stBottomBlockContainer"] {
        background-color: #f8fafc !important;
    }
    div[data-testid="stChatInput"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-size: 14px !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #94a3b8 !important;
    }
    div[data-testid="stChatInput"] button {
        color: #15803d !important;
    }

    /* 2. Correção de contraste para caixas de texto/código no chat */
    div[data-testid="stChatMessage"] code {
        background-color: #e2e8f0 !important;
        color: #0f172a !important;
        font-weight: 600 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        border: 1px solid #cbd5e1 !important;
        font-size: 0.88em !important;
    }

    /* 3. Textos e listas do chat com alta legibilidade */
    div[data-testid="stChatMessage"] p, 
    div[data-testid="stChatMessage"] li {
        color: #0f172a !important;
        line-height: 1.6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h3 style='color: #03170a;'>🤖 Assistente Virtual SisPNAPA</h3>", unsafe_allow_html=True)
    st.caption("Tire dúvidas interativas sobre preenchimentos, regras de metas, cálculo de dashboards e operações do sistema.")

    # Configuração de Autenticação da API Gemini
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("Chave GEMINI_API_KEY não encontrada nas configurações do sistema.")
        st.stop()

    genai.configure(api_key=api_key)

    # Leitura Dinâmica do FAQ e do Código-Fonte para Injeção de Contexto
    try:
        with open("conhecimento_faq.md", "r", encoding="utf-8") as f_faq:
            conteudo_faq = f_faq.read()
    except Exception:
        conteudo_faq = "Base de conhecimento (FAQ) não localizada."

    try:
        with open("sispnapa.py", "r", encoding="utf-8") as f_code:
            conteudo_codigo = f_code.read()
    except Exception:
        conteudo_codigo = "Código-fonte não localizado."

    contexto_completo = f"""
    Você é o Assistente Virtual Oficial do SisPNAPA (Sistema de Planejamento de Ações de Emergências Ambientais do Ibama).
    Dados do usuário conectado:
    - Nome: {nome_usuario_logado}
    - Perfil de Acesso: {perfil_usuario}
    - UF de Atuação: {uf_usuario}

    --- BASE DE CONHECIMENTO & REGRAS DE NEGÓCIO (FAQ) ---
    {conteudo_faq}

    --- CÓDIGO-FONTE DO SISTEMA (ESTRUTURA TÉCNICA E NOMES DE BOTÕES) ---
    {conteudo_codigo}

    DIRETRIZES DE ATENDIMENTO:
    1. Responda em português claro, empático, didático e objetivo, utilizando tópicos e formatação limpa.
    2. Priorize os conceitos e tabelas explicativas do FAQ para esclarecer dúvidas sobre metas (regra de 80%), cálculos de dashboards, SEI, orçamentos e equipes.
    3. Consulte o código-fonte para confirmar a localização exata de abas, nomes de botões, filtros e fluxos de tela.
    4. NUNCA exiba código Python bruto, variáveis internas ou URLs confidenciais nos diálogos.
    5. Oriente o usuário a relatar falhas técnicas no menu '💡 Sugestões & Melhorias'.
    """

    # 4. Inicialização com Fallback
    nomes_para_testar = [
        "gemini-3.6-flash",
        "gemini-2.5-flash",
        "gemini-1.5-flash"
    ]

    modelo = None
    for nome_m in nomes_para_testar:
        try:
            modelo = genai.GenerativeModel(
                model_name=nome_m,
                system_instruction=contexto_completo
            )
            break
        except Exception:
            continue

    if modelo is None:
        modelo = genai.GenerativeModel("gemini-3.6-flash", system_instruction=contexto_completo)

    # Histórico da Conversa
    if "mensagens_chat" not in st.session_state:
        st.session_state.mensagens_chat = [
            {
                "role": "assistant",
                "content": f"Olá, **{nome_usuario_logado}**! Sou o assistente virtual do SisPNAPA. Como posso auxiliar suas atividades operacionais hoje?"
            }
        ]

    for msg in st.session_state.mensagens_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Entrada do Usuário, Gravação Silenciosa e Resposta
    if prompt := st.chat_input("Digite sua dúvida sobre o SisPNAPA aqui..."):
        threading.Thread(
            target=registrar_log_pergunta,
            args=(email_logado, uf_usuario, prompt)
        ).start()

        st.session_state.mensagens_chat.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        historico_chat = [
            {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
            for m in st.session_state.mensagens_chat[:-1]
        ]

        chat_session = modelo.start_chat(history=historico_chat)

        with st.chat_message("assistant"):
            with st.spinner("Consultando regras do SisPNAPA..."):
                try:
                    resposta = chat_session.send_message(prompt)
                    st.markdown(resposta.text)
                    st.session_state.mensagens_chat.append({"role": "assistant", "content": resposta.text})
                except Exception as e:
                    st.error(f"Erro ao processar consulta: {e}")
