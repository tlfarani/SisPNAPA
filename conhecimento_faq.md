# Base de Conhecimento & FAQ Oficial — SisPNAPA

---

## 1. Acesso, Perfis, Segurança e Arquitetura Federativa

### 1.1 Como realizar o primeiro acesso ao sistema?
O acesso ao SisPNAPA é individual e restrito aos servidores autorizados:
* **Login:** Insira seu e-mail institucional completo (ex: `nome.sobrenome@ibama.gov.br`).
* **Senha Provisória Padrão:** Digite **`pnapa123`**.
* **Troca Obrigatória:** Logo após o primeiro login, acesse o rodapé da barra lateral esquerda e clique em **🔑 Trocar Minha Senha**. Defina uma senha pessoal exclusiva.

### 1.2 Como funciona a segurança das senhas?
As senhas nunca são salvas em texto puro: passam por um algoritmo criptográfico de dispersão unidirecional (**SHA-256**) antes de serem gravadas no repositório do SharePoint. Nem mesmo os administradores do sistema têm acesso à visualização da senha dos usuários.

### 1.3 Quais são os perfis de acesso (RBAC) e suas permissões?
* **👑 Administrador (Nacional / Suporte):** Acesso irrestrito a todas as 27 Unidades Federativas (UFs), permissão para alterar o Catálogo Nacional de Ações do Ceneac, calibrar tetos orçamentários da DIPRO, gerenciar usuários/equipes de qualquer regional, despachar sugestões e auditar logs do sistema.
* **✏️ Editor Regional (Liderança / Ponto Focal da UF):** Autonomia para cadastrar, editar e excluir Ações e Atividades vinculadas exclusivamente à sua própria UF. Pode gerenciar a lista de servidores da sua equipe local e propor linhas de Coordenação Estadual ou Apoio Interestadual. Não possui permissão para modificar dados de outras regionais.
* **👁️ Visualização (Consulta / Auditoria):** Acesso de somente leitura. Pode explorar os Dashboards Executivos, o Painel Pré-PNAPA, a Matriz de Alocação e a Central de Visualização, com formulários de inserção e edição desabilitados.

### 1.4 Arquitetura Federativa Oficial (27 UFs)
O SisPNAPA adota a divisão federativa estrita da República:
* **Unidade Federativa (UF):** Entidade geográfica com **27 opções oficiais** (26 Estados + Distrito Federal - `DF`). A designação "Ceneac" não é tratada como UF.
* **Lotação / Unidade:** Reflete o setor de atuação administrativa do servidor (`Ceneac`, `CPrev`, `Coate`, `Seplog`, `Nupaem-SP`, `SUPES-RJ`, etc.). Servidores da Sede Nacional têm `UF = DF` e sua respectiva divisão no campo `Lotação`.

---

## 2. Hierarquia de Dados: Estrutura em 3 Níveis e Governança Interanual

O SisPNAPA organiza o planejamento e a execução das emergências ambientais em uma estrutura piramidal de 3 níveis relacionais com interoperabilidade histórica entre os ciclos:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    1. MACROAÇÃO ESTRATÉGICA (Nível 1)                     │
│         Eixos Nacionais Ceneac / DIPRO (11 Macroações CEN01 a CEN11)      │
└─────────────────────────────────────┬─────────────────────────────────────┘
│
▼
┌───────────────────────────────────────────────────────────────────────────┐
│                    2. AÇÃO SETORIAL TÁTICA (Nível 2)                      │
│   2026: CEN001 a CEN055 (Ação Mãe) │ 2027+: CEN01.01, CEN02.01 (Por Modal)│
│       Pactuação: Coordenação Estadual Titular vs. Apoio Interestadual     │
└─────────────────────────────────────┬─────────────────────────────────────┘
│
▼
┌───────────────────────────────────────────────────────────────────────────┐
│                 3. ATIVIDADES DE CAMPO & MISSÕES (Nível 3)                │
│    Execução Operacional, Servidores, Diárias, Passagens, SEI e Esforço    │
└───────────────────────────────────────────────────────────────────────────┘

```

### 2.1 O que é a Macroação Estratégica (Nível 1 - Estratégico)?
* É a diretriz mestre definida pela Coordenação-Geral de Emergências Ambientais (Ceneac/Sede) alinhada às metas ministeriais e da Diretoria de Proteção Ambiental (DIPRO).
* É fixada em **11 Macroações Estratégicas (`CEN01` a `CEN11`)**, que agregam metas físicas nacionais, tetos orçamentários do Ceneac e os Especialistas Sede responsáveis (**Dono da Ação**).

### 2.2 O que é a Ação Setorial (Nível 2 - Tático / Proposta Estadual)?
* É o compromisso formal de planejamento assumido por uma UF dentro do ciclo anual:
  * **Papel Institucional:** Define se o estado atua como **`Coordenação`** (titular formal da ação e responsável pela meta física) ou como **`Apoio`** (fornecimento de servidores e custeio em socorro a outro estado).
  * **UF Coordenadora (`UF_Coordenadora`):** Campo obrigatório que indica a qual unidade federativa o esforço se destina. Em linhas de *Coordenação*, a `UF_Coordenadora` é o próprio estado proponente; em linhas de *Apoio*, registra o estado destinatário da operação conjunta.
  * **Ponto Focal Estadual:** Coordenador formal da ação na regional (obrigatório em Coordenações; preenchido automaticamente como *Equipe em Apoio* nas linhas de colaboração).
  * **Tema / Modal Predominante:** Segmentação técnica da operação (`Rodovias`, `Ferrovias`, `Portos`, `Dutos`, etc.).
  * **Orçamento Planejado:** Detalhamento discriminado em *Diárias*, *Passagens* e *Outras Despesas*.

### 2.3 Como funciona a correlação histórica e agregação dinâmica entre 2026 e 2027?
O SisPNAPA resolve a disparidade histórica de nomenclaturas por meio da função **`construir_mapa_macro_dinamico`**, que consome o catálogo `Acoes_PNAPA.xlsx`:
* **Ciclo 2026 (Ações CEN001 a CEN055):** Como os códigos foram publicados normativamente como `CEN001-2026` a `CEN055-2026`, o sistema consulta dinamicamente a coluna `Acao_Mae` do catálogo e vincula cada uma das 55 iniciativas às 11 Macroações (`CEN01` a `CEN11`).
* **Ciclos 2027+ (Ações Fracionadas por Modal):** Adotam a notação hierárquica por ponto (`CEN01.01`, `CEN02.01`, `CEN02.02`, etc.), onde o prefixo antes do ponto já referencia diretamente a Macroação mãe.
* **Benefício Gerencial:** Permite comparar o desempenho físico, financeiro e operacional de 2026 com o ciclo de 2027 sob a mesma régua executiva, sem quebrar os registros legados.

### 2.4 O que são as Atividades de Campo (Nível 3 - Operacional / Micro)?
* São as missões reais realizadas no terreno ou nos núcleos (vistorias técnicas, fiscalizações, reuniões interinstitucionais, treinamentos, simulados).
* Cada atividade é vinculada obrigatoriamente a uma Ação Setorial pai da respectiva UF.
* Registra servidores escalados, esforço em dias, diárias pagas, custos de passagens e o **número do processo SEI comprobatório**.

### 2.5 Como funciona o Código Inteligente da Atividade?
As atividades recebem um identificador unívoco gerado automaticamente:
> **Formato:** `[Código_Ação]-[Ano]-[UF]-ATV[Sequencial]`
* *Exemplo:* A terceira missão vinculada à ação `CEN02.01-2027` no estado de São Paulo recebe o identificador **`CEN02.01-2027-SP-ATV03`**.

---

## 3. Gestão de Equipes, Lotações da Sede e Liderança

### 3.1 Obrigatoriedade do Cadastro Prévio
Nenhum servidor pode ser escalado em uma atividade de campo ou indicado como ponto focal se não constar previamente cadastrado na base de Equipes (`df_servidores`). Isso previne duplicidades de nomes, variações de grafia e inconsistências contábeis.
* Para cadastrar um colaborador, acesse **👥 Gerenciar Equipes** > **➕ Cadastrar Servidor**, preencha os dados funcionais e salve.

### 3.2 Regra de Liderança Única por Missão
Toda Atividade de Campo envolvendo múltiplos servidores possui validação estrita:
* Cada missão deve conter **exatamente 1 Coordenador de Campo**.
* Os demais integrantes são cadastrados na função de **Apoio de Campo**.
* ⚠️ **Bloqueio de Conflito:** O sistema impede a gravação caso dois servidores sejam apontados simultaneamente como "Coordenador de Campo" na mesma missão.

### 3.3 Atributos Funcionais Automáticos
A plataforma cruza em tempo real o cadastro de servidores para enriquecer os registros operacionais com os seguintes atributos:
* **É Fiscal?** (`Sim` / `Não`)
* **Possui AEAC?** (`Sim` / `Não`)
* **Função Institucional:** (`Responsável Nupaem`, `Responsável Substituto(a)`, `Coordenador(a) Geral Ceneac`, `Coordenador(a) CPrev`, `Coordenador(a) Coate`, `Membro de Equipe`).

### 3.4 Sincronização em Cascata
Se a identificação funcional, UF ou divisão de lotação de um servidor forem alteradas no módulo de equipes, o sistema executa uma atualização síncrona em cascata em todas as ações e atividades do banco de dados.

---

## 4. Motor de Governança Operacional, Limites e Apoio Interestadual

O SisPNAPA incorpora um motor analítico de governança com algoritmos preditivos de sobrecarga e regras rígidas de liderança.

### 4.1 Tetos Anuais de Dedicação: Pré-PNAPA vs. Pós-PNAPA
A capacidade anual de dias de campo é calibrada conforme a responsabilidade institucional:

| Perfil do Servidor | Teto Pré-PNAPA (Planejamento) | Teto Pós-PNAPA (Execução: +50%) |
| :--- | :---: | :---: |
| **Responsável / Coordenador Titular** | 90 dias / ano | 135 dias / ano |
| **Coordenador / Responsável Substituto** | 60 dias / ano | 90 dias / ano |
| **Membro de Equipe Regional** | 40 dias / ano | 60 dias / ano |

### 4.2 Equiparação Automática da Sede (Ceneac / Brasília)
Servidores lotados no **DF** vinculados às divisões centrais (`Ceneac`, `CPrev`, `Coate`, `Seplog`, `Seprev`, `Secoate`) são automaticamente equiparados a **Titular/Responsável**, recebendo o teto ampliado de **90 dias (Pré) / 135 dias (Pós)** para absorver a coordenação de operações nacionais.

### 4.3 Trava Anti-Rotina (Cota Máxima de 50% Ordinárias)
Para resguardar o foco estratégico do Ibama, **no máximo 50% do teto de dias do servidor pode ser consumido por atividades com Importância "Ordinária"**. A capacidade restante deve ser destinada a iniciativas "Prioritárias" ou "Estratégicas".

### 4.4 Limites de Liderança e Coordenação
* **Teto de Coordenações por Servidor:** Máximo de **10 Ações PNAPA** sob a liderança do mesmo servidor no exercício.
* **Regra de Ouro (Ações Nível 3):** Um mesmo coordenador pode assumir no máximo **3 Ações de Grande Porte / Nível 3** ($\ge 20$ dias de dedicação planejada acumulada).

### 4.5 Regras Rígidas para o Regime de Apoio Interestadual
A governança para operações conjuntas interestaduais obedece às seguintes diretrizes:
* **Meta Física Zerada no Apoio:** A UF que cadastra proposta como `Apoio` assume compromisso exclusivamente de **esforço (dias)** e **custeio (diárias/passagens)**. O campo `Meta_Indicador` é automaticamente travado em `0.0` (exibido como `—`), impedindo a duplicação ou contagem dupla da meta nacional.
* **Titularidade do Produto:** A responsabilidade técnica pela meta física, consolidação dos relatórios e instrução do processo SEI compete exclusivamente à **UF Coordenadora**.
* **Trava Federativa de Duplicidade:** O sistema impede que uma mesma UF registre dois apoios para a mesma Ação com destino à mesma UF Coordenadora. Também impede que um estado registre Coordenação duplicada para uma mesma Ação e Tema.
* **Alerta Prévio de Coordenação Estruturada:** Ao selecionar uma ação setorial na Tela 2, caso o estado já possua linha de Coordenação cadastrada, o sistema emite um alerta visual orientativo informando o nome do Ponto Focal já designado e instruindo o cadastro de Apoio caso se trate de reforço interestadual.

---

## 5. Painel de Pactuação Pré-PNAPA em Cascata (Módulo 6)

O módulo **`🤝 Pactuação Pré-PNAPA`** promove a conciliação federativa em tempo real entre as diretrizes orçamentárias da Direção/Sede (*Top-Down*) e as demandas dos estados (*Bottom-Up*).

### 5.1 Balanço Orçamentário Triplo (DIPRO $\rightarrow$ Ceneac $\rightarrow$ Estados)
O topo da página sintetiza a saúde orçamentária do ciclo em 4 cartões executivos:
1. **🏛️ Teto Global DIPRO:** Envelope orçamentário total autorizado pela Diretoria para a Emergência Ambiental (calibrado pelo Administrador e persistido sob o identificador técnico `DIPRO_GLOBAL`).
2. **📋 Teto Alocado Ceneac:** Soma dos tetos pré-distribuídos pela Sede nas Ações do Catálogo.
3. **💰 Demandado pelas UFs:** Somatório real de diárias, passagens e custeio solicitados pelas 27 UFs nas propostas estaduais.
4. **⚖️ Saldo Restante DIPRO:** Indicador de folga ou sobrealocação orçamentária:
$$\text{Saldo Restante} = \text{Teto Global DIPRO} - \sum \text{Recursos Demandados pelas UFs}$$

---

### 5.2 Estrutura Modular da Tela de Pactuação (Seções 4.1 a 4.4)

A visualização é organizada em quatro painéis analíticos sequenciais, intercalados por espaçamento suave:

#### Seção 4.1 — Capacidade da Força de Trabalho por Equipe (Nupaem & Sede Ceneac)
Painel retrátil com indicadores de carga horária:
* Tabela completa com quantitativo de agentes por equipe, capacidade total em dias, dias comprometidos no plano, saldo disponível de dias e taxa de ocupação percentual.
* Semáforo de saturação (`Normal`, `Alerta` ou `Sobrecarga`).

#### Seção 4.2 — Status da Rede Federativa & Adesão das UFs ao Ciclo
Diagnóstico de prontidão institucional:
* Relação de UFs com propostas salvas no exercício (crachás verdes).
* Alerta de UFs pendentes de lançamento (crachás vermelhos), com contador de cobertura nacional ($X/27\text{ UFs}$).

#### Seção 4.3 — Matriz de Alocação de Esforço (Dias) e Recursos (R$) por Ação
Painel analítico expandido por padrão, estruturado em três abas complementares com **barras de progresso nativas** (`ProgressColumn`):
* **🎯 Consolidado por Macroação (N1):** Exibe código PNAPA, nome da macroação, liderança da Sede, quantidade de setoriais e propostas vinculadas, total de dias, percentual visual de esforço consumido, orçamento total demandado e percentual visual de orçamento consumido.
* **📈 Consolidado por Ação Setorial (N2):** Visão sintética por modal/tema. Oculta colunas intermediárias de diárias e passagens para focar em *Total Dias*, *% Esforço*, *Total Demandado (R$)* e *% Orçamento*, facilitando a tomada de decisão pelos coordenadores.
* **📋 Detalhamento Analítico (Propostas):** Visão itemizada para auditoria contábil. Discrimina explicitamente *UF Proponente*, *Papel Institucional*, *UF Coordenadora (Destino)*, *Ponto Focal*, *Meta Física*, *Dias de Campo*, *Diárias (R$)*, *Passagens (R$)*, *Outras Despesas (R$)* e *Total Previsto (R$)*.
* **Blindagem Numérica e KPIs de Rodapé:** As colunas financeiras são tratadas estritamente como números de ponto flutuante (`float`), impedindo falhas de concatenação textual. O rodapé consolida cinco métricas em cards dedicados: *Esforço de Campo*, *Total Diárias*, *Total Passagens*, *Total Outras Despesas* e *Orçamento Total*.
* **Filtro Responsivo por UF:** Permite isolar a análise para um estado específico (ex: `SP` ou `DF`). As barras de progresso recalculam automaticamente sua escala de 100% com base nos totais daquele estado.

#### Seção 4.4 — Exportações Oficiais: Minuta de Portaria em Excel e PDF
Barra de ferramentas dedicada para download imediato de documentos padronizados:
* **📊 Baixar Matriz (Excel):** Gera planilha `.xlsx` com formatação visual completa, largura de colunas otimizada, máscaras monetárias nativas e abas divididas em *Anexo I - Macro (Portaria)* e *Anexo II - Ações Setoriais*.
* **📜 Minuta Portaria (PDF):** Compilação direta via biblioteca `ReportLab` em arquivo binário `.pdf` (formato A4 Paisagem / Landscape), aplicando a paleta oficial verde do Ibama (`#293D09` e `#506B23`), mesclagem vertical (*SPAN*) das ações-mãe, quebra de texto em apoios cruzados (`SP (➔ RN, PR)`), numeração de páginas automatizada (*Página X de Y*) e a Nota Oficial de Governança Federativa.

---

### 5.3 Árvore de Pactuação e Responsividade por Estado
A Seção 5 desdobra cada Macroação (N1) em suas Setoriais filhas (N2) e propostas de estados (N3):
* **Comportamento Responsivo:** Quando uma UF específica é selecionada no topo, a árvore filtra os cards para evidenciar o compromisso daquele estado, detalhando as ações em que ele atua como Coordenador e destacando apoios prestados a terceiros ou recebidos de outros estados.
* **Monitoramento de Diretrizes Ceneac:** Identifica ações de adesão obrigatória nacional (27 UFs) ou estadual dirigida, apontando nominalmente os estados que ainda não lançaram proposta como Coordenadores.

---

## 6. Central de Visualização & Gestão Operacional

O menu **📊 Visualizar Base** oferece ferramentas para acompanhamento e edição das operações:

### 6.1 Subpágina 1: Ações Estaduais (Planejamento & Metas Segmentadas por Tema)
* **Segmentação por Modal / Tema:** Cada linha de planejamento agrega e afere seu percentual de execução cruzando `[Número da Ação PNAPA, UF_Acao_PNAPA, Tema da Atividade]`. Uma linha de Rodovias computa exclusivamente vistorias rodoviárias, isolando-se de Ferrovias ou Portos.
* **Trava Documental SEI:** Atividades concluídas sem número de processo SEI cadastrado pontuam **zero** no resultado físico da ação estadual.
* **Painel de Edição da Ação:** Permite atualizar o Papel institucional, a UF Coordenadora, o Coordenador responsável e as metas físicas.

### 6.2 Subpágina 2: Atividades de Campo (Operações & Execução)
* Central de auditoria micro: exibe código inteligente (`ATV`), servidor escalado, município polo, processo SEI, diárias pagas, passagens e situação documental.
* **Edição em Lote:** Permite selecionar múltiplas atividades para alterar andamento, inserir números de processo SEI ou prorrogar cronogramas simultaneamente.

---

## 7. Regras de Execução Física, Metas e Comprovação SEI

### 7.1 Critérios de Cumprimento de Ações Estaduais
* **Ações com Indicador Numérico:** Considerada cumprida quando o somatório das entregas das atividades homologadas com SEI alcança **$\ge 80\%$ da Meta Planejada da UF**.
* **Ações Qualitativas / Continuadas (Meta = 0):** Cumprida se houver esforço de campo registrado (`Dias_Gastos_Exec > 0`) e ao menos uma missão concluída com processo SEI.
* **Ações sob Regime de Apoio:** Considerada cumprida quando a equipe dedica $\ge 80\%$ dos dias planejados em socorro ao estado coordenador.

### 7.2 Obrigatoriedade Estrita do Processo SEI (`Doc_Probatorio_Exec`)
Nenhuma entrega física é homologada sem a inserção do número de processo ou documento probatório no SEI (Relatório de Viagem, Informação Técnica, Termo de Vistoria):
* **Atividade concluída com SEI em branco:** Enquadra-se visualmente como *🟡 Sem Documento de Conclusão*, gera pendência de auditoria e **tem seu resultado físico desconsiderado (zero)** em todas as métricas consolidadas.

### 7.3 Semáforo de Status das Ações Estaduais

| Status de Execução | Marcador | Regra de Enquadramento Operacional | Impacto no Desempenho |
| :--- | :---: | :--- | :--- |
| **Planejada** | ⚪ | Ação ativa dentro do prazo regulamentar, aguardando execução das missões. | Conta como meta ativa no denominador. |
| **Executada** | 🟢 | Meta física atingida ($\ge 80\%$ da meta da UF) com comprovação SEI. | Pontua como meta cumprida (+1). |
| **Não Executada - Sem Justificativa** | 🔴 | Prazo expirado sem atingir 80% da meta e sem justificativa técnica registrada. | Penaliza o índice de sucesso da UF e entra no mural de atenção. |
| **Cancelada - Sem Justificativa** | 🔴 | Marcada como cancelada, mas com o campo de justificativa em branco. | Penaliza a taxa de sucesso e gera pendência formal. |
| **Cancelada (Justificada)** | 🟡 | Cancelada pela gestão regional contendo fundamentação técnica validada. | **Expurgada da base ativa:** não penaliza a nota da UF nem os índices do Brasil. |

---

## 8. Prazos, Justificativas e Acompanhamento Financeiro

### 8.1 Identificação Automática de Atrasos
O sistema compara em tempo real a data de término da atividade com a data corrente: se o prazo expirou e a atividade permanece com andamento *Prevista*, é classificada como **🔴 Atrasada**.

### 8.2 Regularização de Não Execução
Em caso de inviabilidade de missão (condições meteorológicas severas, contingenciamento ou cancelamento de operação):
1. Acesse **📊 Visualizar Base** > **📌 Atividades de Campo**.
2. Selecione a atividade e abra o painel de edição.
3. Altere o andamento para *Não Executada* ou *Cancelada* e preencha a lista oficial de **Justificativa da Ação**.
4. O sistema regulariza o registro para **🟡 Não Executada (Justificada)** ou **Cancelada (Justificada)**, protegendo os indicadores da regional.

### 8.3 Acompanhamento PCDP (SCDP)
A inserção individualizada permite auditar custos reais por agente:
* **Quantidade de Diárias e Valor de Diárias (R$)**
* **Valor Efetivo de Passagens Aéreas/Terrestres (R$)**
* **Número da PCDP (SCDP)**
* **Dias de Campo Efetivamente Cumpridos**

---

## 9. Produtividade em Lote e Operações Conjuntas

### 9.1 Inserção Multi-Servidor (Lote Operacional)
Permite registrar missões com múltiplos agentes em um único envio:
1. No menu `➕ Inserir Nova Linha` (Nível: Atividade), preencha os dados comuns da operação (município, datas, modal, objetivo).
2. Na aba de servidores, selecione todos os participantes da missão via seletor múltiplo.
3. O sistema cria um registro individual para cada agente no SharePoint, compartilhando o mesmo `Codigo_Atividade` e permitindo a apropriação exata dos custos de diárias por matrícula.

### 9.2 Edição em Lote na Central de Visualização
1. Na tabela de **Ações** ou **Atividades**, selecione as caixas das linhas desejadas.
2. No painel de edição em massa, selecione os atributos que deseja atualizar (ex: *Data de Término*, *Doc SEI*, *Situação*).
3. Clique em **Confirmar e Aplicar Alterações em Massa**. As atribuições individuais dos servidores são preservadas.

---

## 10. Dashboards Executivos e Consolidação Nacional

O módulo **`📈 Dashboards Executivos`** centraliza a gestão estratégica do PNAPA, apoiado em uma barra superior fixa de filtros (**Sticky Top Bar**) e navegação em 4 abas estruturadas:

### 10.1 Navegação pelas Abas Estratégicas
1. **🏛️ Ações PNAPA (Estratégico - N1):** Consolidação orientada pelas 11 Macroações. Permite alternar a análise entre três perspectivas:
   * *🎯 Metas Físicas (Atingimento de Indicadores $\ge 80\%$)*
   * *💰 Orçamento (Execução Financeira $\ge 50\%$)*
   * *⏳ Esforço Operacional (Dias Gastos $\ge 50\%$)*
2. **🎯 Ações Setoriais (Tático - N2):** Monitoramento das ações táticas por modal e regional, apresentando a Tabela 1 (Desempenho por Estado), Tabela 2 (Execução por Ação Setorial) e Tabela 3 (Mural de Pendências Críticas de Justificativa).
3. **🗓️ Operações & Calendário (Operacional - N3):** Painel interativo com:
   * **Gráfico de Gantt Interativo:** Linha do tempo dinâmica com filtros de visualização *Mensal*, *Trimestral* ou *Anual*, colorida pelo status documental e operacional das missões.
   * **Execução Orçamentária Mensal:** Gráficos comparativos entre recursos planejados e executados por categoria de despesa (Diárias, Passagens e Outras).
   * **Esforço Mensal e por Servidor:** Curva de dedicação de dias de campo e ranking de cumprimento de esforço por agente.
4. **⚖️ Governança & Carga:** Matriz de Sobrecarga cruzando servidores contra os níveis de carga das ações (Nível 1, 2 e 3) e Gráfico de Dispersão de Priorização (*Dias Planejados vs. Importância da Atividade*).

### 10.2 Regras de Negócio e Expurgo *Bottom-Up*
* **Fungibilidade da Meta Institucional:** Se uma UF dividiu sua atuação em múltiplos modais da mesma macroação (ex: Rodovias e Ferrovias), a visualização N1 unifica os resultados, permitindo que o superávit de um modal compense eventuais déficits de outro.
* **Expurgo de Cancelamentos Justificados:** Ações marcadas como `Cancelada (Justificada)` são retiradas da contagem do denominador e das metas acumuladas, garantindo que impedimentos fortuitos não penalizem a avaliação institucional da UF ou da Coordenação Nacional.

---

## 11. Central de Sugestões, Melhorias e Suporte

### 11.1 Abertura de Chamados (`💡 Sugestões & Melhorias`)
Todas as solicitações de suporte, identificação de inconsistências ou propostas de aprimoramento devem ser submetidas pela própria plataforma:
1. Acesse **💡 Sugestões & Melhorias** > aba **➕ Enviar Nova Sugestão**.
2. Preencha o módulo envolvido, a prioridade (`Alta`, `Média` ou `Baixa`), o título e o detalhamento técnico.
3. O chamado é registrado no repositório de governança e despachado pela equipe de desenvolvimento e administração no **Quadro de Acompanhamento**.

### 11.2 Canais de Apoio ao Usuário
1. **Assistente Virtual Nativo (`🤖 Assistente Virtual`):** Atendimento automatizado com inteligência artificial para consulta imediata de regras de negócio, tetos de capacidade operacional, rotinas de cálculo e navegação.
2. **Central de Sugestões & Melhorias:** Canal formal para requisição de ajustes funcionais e correções.
3. **Ponto Focal Regional:** Coordenador estadual responsável pela gestão dos planos locais e validação de acessos junto à Sede.
