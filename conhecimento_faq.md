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

### 2.5 Como funciona a Gestão do Código Inteligente da Atividade (`Codigo_Atividade`)?
As atividades de campo são unificadas por um identificador padronizado que agrupa toda a equipe:
> **Formato Padrão:** `[Código_Ação]-[Ano]-[UF]-ATV[Sequencial]`
* *Exemplo:* A terceira missão vinculada à ação `CEN02.01-2027` no estado de São Paulo recebe o identificador **`CEN02.01-2027-SP-ATV03`**.
* **Gestão Dinâmica (Inserção e Edição):** Tanto no cadastro quanto na edição (individual ou em lote), o usuário pode escolher entre duas formas de definição do código:
  1. **➕ Gerar Novo Código Sequencial:** O sistema varre o banco em tempo real, identifica o maior número `ATV` já existente para a respectiva Ação e UF, e sugere automaticamente o próximo número sequencial vago (`maior + 1`).
  2. **🔗 Vincular a Código Pré-Existente:** Permite selecionar em um menu suspenso uma atividade já iniciada por outro colega da equipe, herdando o código inteligente e garantindo que todos os servidores fiquem agrupados sob a mesma operação.

---

## 3. Gestão de Equipes, Liderança de Campo e Trava Anti-Duplicidade

### 3.1 Obrigatoriedade do Cadastro Prévio
Nenhum servidor pode ser escalado em uma atividade de campo ou indicado como ponto focal se não constar previamente cadastrado na base de Equipes (`df_servidores`). Isso previne duplicidades de nomes, variações de grafia e inconsistências contábeis.
* Para cadastrar um colaborador, acesse **👥 Gerenciar Equipes** > **➕ Cadastrar Servidor**, preencha os dados funcionais e salve.

### 3.2 Regra de Liderança Única de Campo e Exclusividade do Indicador
Toda operação de campo envolvendo um ou mais agentes obedece a uma regra estrita de liderança:
* **Exatamente 1 Coordenador de Campo:** Cada atividade (`Codigo_Atividade`) deve possuir uma única linha com a função **`Coordenador de Campo`**.
* **Membros em Apoio de Campo:** Todos os demais servidores participantes daquela mesma missão são cadastrados compulsoriamente como **`Apoio de Campo`**.
* **Exclusividade do Resultado Físico:** **Apenas a linha do Coordenador de Campo registra o resultado quantitativo do indicador.** As linhas de Apoio de Campo registram compulsoriamente valor `"0"` (exibido como `—` nas tabelas analíticas). Isso impede que a contagem física (ex: veículos abordados, terminais inspecionados) seja multiplicada pelo número de agentes em campo.

### 3.3 A Trava Anti-Duplicidade em 5 Camadas
O SisPNAPA implementa cinco camadas automáticas e integradas de proteção que impedem a sobrecontagem de indicadores:

[ Camada 1: Inserção Individual ] ──> Trava o indicador em "0" se a atividade já tiver Coordenador.
[ Camada 2: Edição Individual ]   ──> Campo só abre para edição se a linha for o Coordenador ativo.
[ Camada 3: Carga em Lote ]       ──> Só o Coordenador leva o indicador; apoios são forçados para "0".
[ Camada 4: Backend / Payload ]   ──> O gerador de envio força "0" se a função != "Coordenador de Campo".
[ Camada 5: Motor dos Dashboards ]──> Ignora linhas de apoio na soma de produtos físicos.

1. **Camada 1 — Inserção Individual:** Se o usuário vincular a atividade a um código pré-existente que já possua coordenador, o sistema trava automaticamente a função em `Apoio de Campo (Travado)` e bloqueia o campo de resultado em `0`.
2. **Camada 2 — Edição Individual:** O campo do indicador reage em tempo real à função selecionada. Se a linha for Apoio, o campo fica cinza e desabilitado em `0`. Se o usuário mudar a função para Coordenador (desde que não haja outro), o campo destrava na hora.
3. **Camada 3 — Carga em Lote:** Ao lançar missões com múltiplos agentes, apenas a linha designada como Coordenador de Campo recebe o resultado preenchido; todas as demais linhas são gravadas com `"0"`.
4. **Camada 4 — Sanitização no Backend (`payload_gerador`):** Antes de enviar a requisição HTTP ao SharePoint, o sistema verifica a função: qualquer registro que não seja `Coordenador de Campo` (ou que atue sob Apoio institucional) tem o campo `Resultado_Indicador` compulsoriamente redefinido para `"0"`.
5. **Camada 5 — Motor de Agregação dos Dashboards:** Nos relatórios executivos e no painel tático, o cálculo de cumprimento de metas considera apenas o resultado apurado das linhas de Coordenadores de Campo, expurgando duplicidades mesmo se houver dados legados não saneados.

### 3.4 Saneamento de Registros Legados (Resíduos Históricos)
Para atividades antigas gravadas antes da implementação da trava (onde membros de apoio ficaram com valores fracionados, como `1,67`):
* Basta selecionar as linhas dos apoios na tela `📊 Visualizar Base` ➔ `Atividades de Campo`, abrir a **Edição em Lote**, marcar *"Alterar Função de Campo?"* escolhendo `Apoio de Campo` e confirmar.
* O sistema converte os registros e **zera compulsoriamente todos os valores residuais antigos para `0`**, consolidando a meta integralmente na linha do Coordenador.

---

## 4. Ordem Harmonizada das Abas nos Formulários (UX/UI Padronizada)

Para garantir uma navegação fluida, sem retrabalho e com perfeita resposta do sistema, **100% dos formulários de atividades** (Inserção Individual, Inserção em Lote, Edição Individual e Edição em Lote) seguem rigorosamente a mesma sequência em 5 abas:

| Aba | Nome da Aba | O que é informado | Comportamento Reativo |
| :---: | :--- | :--- | :--- |
| **1** | **Identificação & Agrupador** | Ação vinculada, Papel da UF, Código da Missão (`ATVxx`), Nome e Andamento. | Define o agrupador e checa se já existe coordenador na base. |
| **2** | **Recursos Humanos & Liderança** | UF da equipe, Servidor, Função de Campo (`Coordenador` vs `Apoio`), PCDP e Localidade. | **Decisiva:** A escolha da função aqui dita o comportamento da Aba 3. |
| **3** | **Detalhes & Indicadores** | Indicador oficial, **Resultado Físico**, Número do Processo SEI, Tipo e Periculosidade. | **Responsiva:** Se a Aba 2 for Coordenador, abre para digitação; se for Apoio, trava em `0`. |
| **4** | **Cronograma & Custos** | Datas de início e término, dias planejados/executados, diárias, passagens e outras despesas. | Apura o esforço em dias e o custeio financeiro real da missão. |
| **5** | **Justificativas / Observações** | Campo livre de notas e justificativa obrigatória caso haja pendência documental ou atraso. | Protege a auditoria da atividade no SEI. |

### 4.1 Por que a Aba de Recursos Humanos (2) vem antes da Aba de Indicadores (3)?
Essa inversão resolve o atrito operacional: o Streamlit processa a interface de cima para baixo. Ao escolher primeiro quem é o servidor e qual a sua função de campo (Aba 2), quando o usuário clica na Aba 3 o sistema já sabe exatamente se deve manter o campo de indicador aberto ou bloqueá-lo com a trava anti-duplicidade, sem que o servidor precise alternar abas para destravar o formulário.

---

## 5. Motor de Governança Operacional, Limites e Apoio Interestadual

O SisPNAPA incorpora um motor analítico de governança com algoritmos preditivos de sobrecarga e regras rígidas de liderança.

### 5.1 Tetos Anuais de Dedicação: Pré-PNAPA vs. Pós-PNAPA
A capacidade anual de dias de campo é calibrada conforme a responsabilidade institucional:

| Perfil do Servidor | Teto Pré-PNAPA (Planejamento) | Teto Pós-PNAPA (Execução: +50%) |
| :--- | :---: | :---: |
| **Responsável / Coordenador Titular** | 90 dias / ano | 135 dias / ano |
| **Coordenador / Responsável Substituto** | 60 dias / ano | 90 dias / ano |
| **Membro de Equipe Regional** | 40 dias / ano | 60 dias / ano |

### 5.2 Equiparação Automática da Sede (Ceneac / Brasília)
Servidores lotados no **DF** vinculados às divisões centrais (`Ceneac`, `CPrev`, `Coate`, `Seplog`, `Seprev`, `Secoate`) são automaticamente equiparados a **Titular/Responsável**, recebendo o teto ampliado de **90 dias (Pré) / 135 dias (Pós)** para absorver a coordenação de operações nacionais.

### 5.3 Trava Anti-Rotina (Cota Máxima de 50% Ordinárias)
Para resguardar o foco estratégico do Ibama, **no máximo 50% do teto de dias do servidor pode ser consumido por atividades com Importância "Ordinária" / "Rotina"**. A capacidade restante deve ser destinada a iniciativas "Prioritárias" ou "Finalísticas".

### 5.4 Limites de Liderança e Coordenação
* **Teto de Coordenações por Servidor:** Máximo de **10 Ações PNAPA** sob a liderança do mesmo servidor no exercício.
* **Regra de Ouro (Ações Nível 3):** Um mesmo coordenador pode assumir no máximo **3 Ações de Grande Porte / Nível 3** ($\ge 20$ dias de dedicação planejada acumulada da equipe).

### 5.5 Regras Rígidas para o Regime de Apoio Interestadual
A governança para operações conjuntas interestaduais obedece às seguintes diretrizes:
* **Meta Física Zerada no Apoio:** A UF que cadastra proposta como `Apoio` assume compromisso exclusivamente de **esforço (dias)** e **custeio (diárias/passagens)**. O campo `Meta_Indicador` é automaticamente travado em `0.0` (exibido como `—`), impedindo a duplicação ou contagem dupla da meta nacional.
* **Titularidade do Produto:** A responsabilidade técnica pela meta física, consolidação dos relatórios e instrução do processo SEI compete exclusivamente à **UF Coordenadora**.
* **Trava Federativa de Duplicidade:** O sistema impede que uma mesma UF registre dois apoios para a mesma Ação com destino à mesma UF Coordenadora. Também impede que um estado registre Coordenação duplicada para uma mesma Ação e Tema.
* **Alerta Prévio de Coordenação Estruturada:** Ao selecionar uma ação setorial na Tela 2, caso o estado já possua linha de Coordenação cadastrada, o sistema emite um alerta visual orientativo informando o nome do Ponto Focal já designado e instruindo o cadastro de Apoio caso se trate de reforço interestadual.

---

## 6. Painel de Pactuação Pré-PNAPA em Cascata (Módulo 6)

O módulo **`🤝 Pactuação Pré-PNAPA`** promove a conciliação federativa em tempo real entre as diretrizes orçamentárias da Direção/Sede (*Top-Down*) e as demandas dos estados (*Bottom-Up*).

### 6.1 Balanço Orçamentário Triplo (DIPRO $\rightarrow$ Ceneac $\rightarrow$ Estados)
O topo da página sintetiza a saúde orçamentária do ciclo em 4 cartões executivos:
1. **🏛️ Teto Global DIPRO:** Envelope orçamentário total autorizado pela Diretoria para a Emergência Ambiental (calibrado pelo Administrador e persistido sob o identificador técnico `DIPRO_GLOBAL`).
2. **📋 Teto Alocado Ceneac:** Soma dos tetos pré-distribuídos pela Sede nas Ações do Catálogo.
3. **💰 Demandado pelas UFs:** Somatório real de diárias, passagens e custeio solicitados pelas 27 UFs nas propostas estaduais.
4. **⚖️ Saldo Restante DIPRO:** Indicador de folga ou sobrealocação orçamentária:
$$\text{Saldo Restante} = \text{Teto Global DIPRO} - \sum \text{Recursos Demandados pelas UFs}$$

---

### 6.2 Estrutura Modular da Tela de Pactuação

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
* **📈 Consolidado por Ação Setorial (N2):** Visão sintética por modal/tema. Foca em *Total Dias*, *% Esforço*, *Total Demandado (R$)* e *% Orçamento*, facilitando a tomada de decisão pelos coordenadores.
* **📋 Detalhamento Analítico (Propostas):** Visão itemizada para auditoria contábil. Discrimina explicitamente *UF Proponente*, *Papel Institucional*, *UF Coordenadora (Destino)*, *Ponto Focal*, *Meta Física*, *Dias de Campo*, *Diárias (R$)*, *Passagens (R$)*, *Outras Despesas (R$)* e *Total Previsto (R$)*.
* **Blindagem Numérica e KPIs de Rodapé:** As colunas financeiras são tratadas estritamente como números de ponto flutuante (`float`), impedindo falhas de concatenação textual. O rodapé consolida cinco métricas em cards dedicados: *Esforço de Campo*, *Total Diárias*, *Total Passagens*, *Total Outras Despesas* e *Orçamento Total*.

#### Seção 4.4 — Exportações Oficiais: Minuta de Portaria em Excel e PDF
Barra de ferramentas dedicada para download imediato de documentos padronizados:
* **📊 Baixar Matriz (Excel):** Gera planilha `.xlsx` com formatação visual completa, largura de colunas otimizada, máscaras monetárias nativas e abas divididas em *Anexo I - Macro (Portaria)* e *Anexo II - Ações Setoriais*.
* **📜 Minuta Portaria (PDF):** Compilação direta via biblioteca `ReportLab` em arquivo binário `.pdf` (formato A4 Paisagem / Landscape), aplicando a paleta oficial verde do Ibama (`#293D09` e `#506B23`), mesclagem vertical (*SPAN*) das ações-mãe, quebra de texto em apoios cruzados (`SP (➔ RN, PR)`), numeração de páginas automatizada (*Página X de Y*) e a Nota Oficial de Governança Federativa.

---

## 7. Central de Visualização, Gestão de Registros e Correção de Datas

O menu **📊 Visualizar Base** oferece ferramentas completas para acompanhamento, filtragem e edição das operações:

### 7.1 Exibição Real de Datas e Ordenação Cronológica Estrita
* **Fim do Erro `01/01/1970`:** As colunas `Data de Início` e `Data de Término` são processadas na interface como objetos de data nativos do Python (`datetime.date`). Isso impede que o componente `st.column_config.DateColumn` interprete strings textuais incorretamente e caia no marco zero da era Unix.
* **Ordenação Cronológica Real:** Ao clicar nos cabeçalhos das tabelas, os registros são ordenados de forma cronológica natural (janeiro a dezembro), eliminando ordenações alfabéticas distorcidas (onde maio aparecia antes de fevereiro).
* **Independência dos Filtros:** Essa formatação visual afeta apenas o espelho de tela; a barra superior de filtros por período continua operando em paralelo com total precisão sobre a coluna `Data_Inicio_Datetime`.

### 7.2 Subpágina 1: Ações Setoriais (Planejamento & Metas por Modal)
* **Segmentação por Modal / Tema:** Cada linha de planejamento agrega e afere seu percentual de execução cruzando `[Número da Ação PNAPA, UF_Acao_PNAPA, UF_Coordenadora]`. Uma linha de Rodovias computa exclusivamente vistorias rodoviárias, isolando-se de Ferrovias ou Portos.
* **Trava Documental SEI:** Atividades concluídas sem número de processo SEI cadastrado pontuam **zero** no resultado físico da ação estadual.
* **Painel de Edição da Ação:** Permite atualizar o Papel institucional, a UF Coordenadora, o Coordenador responsável e as metas físicas.

### 7.3 Subpágina 2: Atividades de Campo (Operações & Execução)
* Central de auditoria micro: exibe código inteligente (`ATV`), servidor escalado, município polo, processo SEI, diárias pagas, passagens e situação documental.
* **Edição Individual Responsiva:** Permite alterar o `Codigo_Atividade` (para um novo sequencial sugerido ou pré-existente) e garante que o campo do indicador abra imediatamente se a linha for definida como Coordenador de Campo.
* **Edição em Lote:** Permite selecionar múltiplas atividades para alterar andamento, código agregador ou função de campo. Se as atividades forem convertidas em Apoio de Campo, os indicadores legados são automaticamente saneados para `"0"`.

---

## 8. Regras de Execução Física, Metas e Comprovação SEI

### 8.1 Critérios de Cumprimento de Ações Estaduais
* **Ações com Indicador Numérico:** Considerada cumprida quando o somatório das entregas das atividades homologadas com SEI alcança **$\ge 80\%$ da Meta Planejada da UF**.
* **Ações Qualitativas / Continuadas (Meta = 0):** Cumprida se houver esforço de campo registrado (`Dias_Gastos_Exec > 0`) e ao menos uma missão concluída com processo SEI.
* **Ações sob Regime de Apoio:** Considerada cumprida quando a equipe dedica $\ge 80\%$ dos dias planejados em socorro ao estado coordenador.

### 8.2 Obrigatoriedade Estrita do Processo SEI (`Doc_Probatorio_Exec`)
Nenhuma entrega física é homologada sem a inserção do número de processo ou documento probatório no SEI (Relatório de Viagem, Informação Técnica, Termo de Vistoria):
* **Atividade concluída com SEI em branco:** Enquadra-se visualmente como *🟡 Sem Documento de Conclusão*, gera pendência de auditoria e **tem seu resultado físico desconsiderado (zero)** em todas as métricas consolidadas.

### 8.3 Semáforo de Status das Ações Estaduais

| Status de Execução | Marcador | Regra de Enquadramento Operacional | Impacto no Desempenho |
| :--- | :---: | :--- | :--- |
| **Planejada** | ⚪ | Ação ativa dentro do prazo regulamentar, aguardando execução das missões. | Conta como meta ativa no denominador. |
| **Executada** | 🟢 | Meta física atingida ($\ge 80\%$ da meta da UF) com comprovação SEI. | Pontua como meta cumprida (+1). |
| **Não Executada - Sem Justificativa** | 🔴 | Prazo expirado sem atingir 80% da meta e sem justificativa técnica registrada. | Penaliza o índice de sucesso da UF e entra no mural de atenção. |
| **Cancelada - Sem Justificativa** | 🔴 | Marcada como cancelada, mas com o campo de justificativa em branco. | Penaliza a taxa de sucesso e gera pendência formal. |
| **Cancelada (Justificada)** | 🟡 | Cancelada pela gestão regional contendo fundamentação técnica validada. | **Expurgada da base ativa:** não penaliza a nota da UF nem os índices do Brasil. |

---

## 9. Produtividade em Lote e Operações Conjuntas

### 9.1 Inserção Multi-Servidor (Lote Operacional com Trava de Indicador)
Permite registrar missões com múltiplos agentes em um único envio garantindo a unicidade do indicador:
1. No menu `➕ Inserir Nova Linha` (Nível: Atividade), preencha os dados comuns da operação (Ação, Código, Nome, Localidade, Datas, Custos).
2. Na aba de liderança, selecione quem será o **Coordenador de Campo** e, na aba de indicadores, lance o resultado da entrega.
3. Abra o popover `👥 Deseja cadastrar esta atividade para múltiplos servidores?` e selecione os demais colegas da equipe.
4. O sistema gera registros simultâneos com o mesmo `Codigo_Atividade`: **apenas o coordenador recebe o resultado físico do indicador, enquanto todos os demais recebem automaticamente resultado `"0"`**.

### 9.2 Edição em Lote e Unificação de Código
1. Na tabela de **Atividades**, selecione as linhas desejadas com as caixas de seleção.
2. Na Aba 1 da edição em lote, marque *"Alterar Código da Atividade?"* para vincular todas as linhas a um código existente ou gerar um novo código sequencial `ATVxx`.
3. Na Aba 2, marque *"Alterar Função de Campo?"* para definir os membros como Apoio de Campo, limpando resíduos de contagem anterior.
4. Clique em **Confirmar Alterações em Massa**. As diárias e atribuições individuais são preservadas, mas o agrupador e o indicador são uniformizados.

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
