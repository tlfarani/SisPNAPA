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
* **👑 Administrador (Nacional / Suporte):** Acesso irrestrito a todas as 27 Unidades Federativas (UFs), permissão para alterar o Catálogo Nacional de Ações do Ceneac, calibrar tetos orçamentários da DIPRO, gerenciar usuários/equipes de qualquer regional, gerenciar Unidades e instâncias superiores, despachar sugestões e auditar logs do sistema.
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

### 2.4 O que são as Atividades de Campo (Nível 3 - Operacional / Micro)?
* São as missões reais realizadas no terreno ou nos núcleos (vistorias técnicas, fiscalizações, reuniões interinstitucionais, treinamentos, simulados).
* Cada atividade é vinculada obrigatoriamente a uma Ação Setorial pai da respectiva UF.
* Registra servidores escalados, esforço em dias, diárias pagas, custos de passagens, **número do processo SEI** e **autorização de viagem para o SCDP**.

---

## 3. Gestão de Equipes, Liderança de Campo e Trava Anti-Duplicidade

### 3.1 Obrigatoriedade do Cadastro Prévio e Dedicação Máxima Customizada
Nenhum servidor pode ser escalado em uma atividade de campo se não constar previamente cadastrado na base de Equipes (`df_servidores`):
* **Campo `Dedicacao_Maxima`:** Cada servidor possui agora um teto anual de dedicação individualizado em dias (**40, 60 ou 90 dias**), cadastrado e ajustado na tela **👥 Gerenciar Equipes**.
* **Sugestão Inteligente no Cadastro:** O sistema sugere automaticamente o teto padrão (Ceneac/Titulares Nupaem: 90d; Substitutos: 60d; Membros: 40d), permitindo ao gestor ajustar conforme a realidade operacional do servidor.

### 3.2 Regra de Liderança Única de Campo e Exclusividade do Indicador
Toda operação de campo envolvendo um ou mais agentes obedece a uma regra estrita de liderança:
* **Exatamente 1 Coordenador de Campo:** Cada atividade (`Codigo_Atividade`) deve possuir uma única linha com a função **`Coordenador de Campo`**.
* **Membros em Apoio de Campo:** Todos os demais servidores participantes daquela mesma missão são cadastrados compulsoriamente como **`Apoio de Campo`**.
* **Exclusividade do Resultado Físico:** **Apenas a linha do Coordenador de Campo registra o resultado quantitativo do indicador.** As linhas de Apoio de Campo registram compulsoriamente valor `"0"` (exibido como `—` nas tabelas analíticas), evitando a multiplicação artificial de entregas.

### 3.3 A Trava Anti-Duplicidade em 5 Camadas
1. **Camada 1 — Inserção Individual:** Se a atividade for vinculada a um código pré-existente com coordenador, o sistema trava a função em `Apoio de Campo (Travado)` e zera o indicador.
2. **Camada 2 — Edição Individual:** O campo do indicador reage em tempo real à função selecionada. Se for Apoio, o campo fica desabilitado em `0`.
3. **Camada 3 — Carga em Lote:** Apenas a linha designada como Coordenador de Campo recebe o resultado preenchido; todas as demais linhas são gravadas com `"0"`.
4. **Camada 4 — Sanitização no Backend (`payload_gerador`):** Qualquer registro que não seja `Coordenador de Campo` tem o campo `Resultado_Indicador` compulsoriamente forçado para `0.0`.
5. **Camada 5 — Motor dos Dashboards:** A apuração de metas nos relatórios executivos contabiliza exclusivamente os resultados de linhas de Coordenadores.

---

## 4. Estrutura Padrão dos Formulários em 6 Abas & Botão Global de Rodapé

Para garantir padronização e evitar erros de carregamento assíncrono, **100% dos formulários de atividades** (Tela 1 — Edição e Tela 2 — Inserção) compartilham a mesma arquitetura em **6 abas funcionais**, finalizadas por um **botão primário de gravação fixo no rodapé**:

[📋 Identificação da Atividade] ➔ [👥 Recursos Humanos, Liderança & Local] ➔ [🎯 Detalhes & Indicadores] ➔ [💰 Cronograma & Custos] ➔ [📝 Observações & Justificativas] ➔ [✈️ Autorização SCDP]
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
[ 💾 Gravar Atividade / Alterações (Fixo no Rodapé) ]


| Aba | Nome da Aba | O que é informado | Comportamento e Regras de Negócio |
| :---: | :--- | :--- | :--- |
| **1** | **Identificação da Atividade** | Ação vinculada, Papel da UF, Código da Missão (`ATVxx`), Nome e Andamento. | Define o agrupador e checa se já existe coordenador ativo na base. |
| **2** | **Recursos Humanos, Liderança & Local** | Servidor integrante, Função de Campo (`Coordenador` vs `Apoio`), PCDP e Localidade. | Avalia o termômetro de carga em tempo real. A função escolhida comanda o destravamento da Aba 3. |
| **3** | **Detalhes & Indicadores** | Indicador oficial, **Resultado Físico**, Processo SEI, Tipo de Atividade e Periculosidade. | Se a Aba 2 for Coordenador, abre para preenchimento; se for Apoio, trava compulsoriamente em `0`. |
| **4** | **Cronograma & Custos** | Datas de início/fim, dias planejados/executados, diárias, passagens e outras despesas. | Apura o esforço em dias e o custeio financeiro total planejado da missão. |
| **5** | **Observações & Justificativas** | Campo de anotações contextuais e justificativa institucional obrigatória para pendências. | **Crítica para o SCDP:** O texto aqui digitado alimenta a justificativa enviada no card da chefia. |
| **6** | **Autorização SCDP** | Painel de controle de viagem: instâncias deliberadoras, destinatários e botão de disparo. | Configura o envio imediato da solicitação para o Teams e E-mail da chefia imediata/superior. |

### 4.1 Por que a Aba de Observações e Justificativas (5) vem antes da Autorização SCDP (6)?
A execução procedural do Streamlit ocorre de cima para baixo. Posicionando as Observações na Aba 5, o texto da justificativa já se encontra instanciado na memória no momento em que o usuário acessa a Aba 6, permitindo que o webhook do Power Automate consuma a justificativa da viagem em tempo real, sem inconsistências de variáveis (`NameError`).

### 4.2 Por que o botão "Gravar" fica fora das abas, no rodapé?
Abas servem para categorização temática e não para fluxos lineares obrigatórios (*wizards*). Manter o botão **`💾 Gravar Atividade`** fixo no rodapé permite que edições pontuais (como atualizar um valor na Aba 4 ou corrigir um número SEI na Aba 3) sejam salvas imediatamente de qualquer tela, mantendo a consistência com a governança central do sistema.

---

## 5. Fluxo de Autorização Prévia de Viagens (SCDP) via Teams & Outlook

O SisPNAPA integra um mecanismo de **anuência prévia digital de viagens** diretamente conectado ao ecossistema Microsoft (Teams e Outlook) por meio de gatilhos HTTP do Power Automate.

### 5.1 O Ciclo de Vida da Autorização SCDP
A coluna **`Status_Aprovacao_SCDP`** governa o estado regulamentar da viagem:
* **⚪ Não Solicitada:** Atividade cadastrada no planejamento, mas que ainda não foi submetida à deliberação da chefia.
* **⏳ Pendente:** Notificação disparada com sucesso. O card interativo aguarda manifestação formal da chefia no Teams ou Outlook.
* **✅ Aprovada:** Chefia clicou em "Aprovar" no card. A atividade está autorizada para abertura de PCDP no sistema SCDP do Governo Federal.
* **❌ Rejeitada:** Chefia recusou a autorização justificando o motivo no card. A atividade pode ser ajustada e reenviada.

### 5.2 Roteamento Hierárquico Inteligente & `Unidade_Superior`
Para refletir o organograma do Ibama e impedir conflitos de interesse, a função unificada `obter_chefia_lotacao` avalia o perfil do servidor que vai viajar:

[ Servidor Solicitante ]
│
├── É o Chefe Titular da Unidade?
│        └── ⛔ Bloqueia própria unidade (anti-autoaprovação).
│        └── 🏛️ Roteia OBRIGATORIAMENTE para a 'Unidade_Superior' (ex: SUPES ou Presidência/DF).
│
├── É o Chefe Substituto da Unidade?
│        └── 🏢 Opção 1: Enviar ao Chefe Titular da Própria Unidade.
│        └── 🏛️ Opção 2: Enviar à Unidade Superior (caso o titular esteja ausente/férias).
│
└── É Servidor Geral / Analista de Campo?
└── 🏢 Opção Padrão: Própria Unidade (Apenas Titular, Titular + Substituto ou Apenas Substituto).
└── 🏛️ Opção de Exceção: Unidade Superior (caso a chefia local esteja impedida).

### 5.3 O que compõe o Card Interativo enviado à Chefia?
Ao clicar no botão de solicitação, o Power Automate gera um *Adaptive Card* no Microsoft Teams e uma mensagem acionável no Outlook contendo:
* **Identificação:** Código e Nome da Atividade, Nome do Servidor viajante, e-mail institucional e Lotação.
* **Logística da Missão:** Município polo e UF de destino, período exato da missão (`Data Início` a `Data Término`) e dias de esforço estimados.
* **Detalhamento Financeiro:** Valor planejado de Diárias (R$), Passagens (R$) e Outras Despesas (R$), com o **Custo Total Estimado**.
* **Justificativa Operacional:** Resgate automático do texto lançado na Aba 5 (Observações).
* **Botões de Ação:** Botões nativos de "Aprovar" e "Rejeitar" com campo obrigatório para comentários.

### 5.4 Auditoria e Carimbo de Data/Hora Oficial (Fuso de Brasília UTC-3)
Ao deliberar no Teams, o fluxo captura automaticamente:
1. O nome do respondente real via expressão:
   ```text
   first(body('Aguardar_uma_aprovação')?['responses'])?['responder']?['displayName']

2. O horário exato convertido para o relógio oficial de Brasília via função:
convertFromUtc(utcNow(), 'E. South America Standard Time', 'dd/MM/yyyy HH:mm')

O resultado é gravado na coluna Aprovador_SCDP (ex: Tiago Luz Farani em 30/09/2026 17:02), refletido imediatamente na tabela do SisPNAPA.

## 6. Disparo de SCDP em Bloco (Agrupamento por Unidade em Lote)

Em missões multidisciplinares ou fiscalizações integradas com servidores de várias unidades (ex: 2 agentes de SP, 1 do RJ e 1 da Sede/DF), o SisPNAPA disponibiliza o **disparo de solicitações em lote** tanto na **Tela 1 (Visualização)** quanto na **Tela 2 (Carga em Lote)**.

### 6.1 Como funciona o Agrupamento por Unidade?
Ao selecionar múltiplas atividades na tabela da Tela 1 ou marcar a opção de SCDP no cadastro multi-servidor da Tela 2:
1. O sistema faz um agrupamento em tempo real por **Lotação e UF** (`df.groupby(["Lot_Ref", "UF_Ref"])`).
2. Para cada unidade participante, o sistema abre um container visual exibindo os servidores daquele núcleo e o somatório de custos estimados daquele grupo.
3. Cada grupo possui seus próprios seletores independentes de alçada, permitindo, por exemplo, enviar as missões do Nupaem-SP para o Titular de SP e, simultaneamente, as missões do Nupaem-RJ para a chefia do RJ.

### 6.2 Disparo Paralelo Concorrente (`ThreadPoolExecutor`)
Como o SCDP do Governo Federal exige pedidos individuais de PCDP, o sistema itera sobre cada atividade de forma concorrente:
* Um pool de conexões paralelas (`ThreadPoolExecutor(max_workers=5)`) dispara as requisições HTTP para o Power Automate sem travar a interface do navegador.
* O SharePoint é atualizado em lote com `Status_Aprovacao_SCDP = "Pendente"` e o usuário recebe um alerta consolidado (*toast*) informando a quantidade exata de cards entregues no Teams da chefia.

---

## 7. Catálogo Corporativo de Unidades (`🏢 Gerenciar Unidades`)

A tela de gestão de unidades parametriza a estrutura funcional para viabilizar as rotinas do SCDP:
* **Coluna `Unidade_Superior`:** Permite indicar para qual unidade subordinam-se as deliberações de viagem da chefia daquele setor. A lista disponibiliza todas as unidades cadastradas nacionalmente no formato amigável `Nome (UF)` (ex: `DILIC (DF)`, `SUPES-SP (SP)`, `Presidência (DF)`).
* **Bloqueio Anti-Ciclo:** O formulário de edição remove automaticamente a própria unidade da lista de opções, impedindo que um setor seja cadastrado como superior de si mesmo.
* **Alerta de Dependência na Exclusão:** Se um administrador tentar excluir uma unidade que esteja configurada como superior de outros setores ativos, o sistema emite um bloqueio orientativo informando as unidades dependentes.
* **Sincronização em Cascata:** Se o nome ou a UF de uma unidade for alterado na tabela auxiliar, o SisPNAPA atualiza automaticamente a lotação de todos os servidores vinculados na base de Equipes.

---

## 8. Motor de Governança Operacional, Limites e Capacidade Anual

### 8.1 Cálculo do Termômetro de Capacidade do Servidor
O sistema avalia a capacidade do servidor priorizando os dados funcionais salvos:
1. **Prioridade Máxima:** Valor configurado na coluna `Dedicacao_Maxima` da tabela de servidores (40, 60 ou 90 dias).
2. **Regra de Fallback (Cadastros Legados):** Sede Ceneac/Titulares Nupaem: 90 dias; Substitutos Nupaem: 60 dias; Membros de Equipe: 40 dias.
3. **Expansão Pós-PNAPA (+50%):** Durante a execução ao longo do ano, o limite de capacidade expande em 1,5x (40d $\rightarrow$ 60d; 60d $\rightarrow$ 90d; 90d $\rightarrow$ 135d).
4. **Hard Limit (2027+):** Bloqueio estrito de salvamento caso a nova atividade faça o servidor ultrapassar o teto limite permitido.

### 8.2 Apuração da Capacidade das UFs (`Capacidade_Total_Dias`)
O cálculo da força de trabalho anual das UFs considera **estritamente os servidores cadastrados com `Equipe_Emergencias == "Sim"`**. Servidores de outros setores ou não integrados à resposta ambiental não entram no somatório de dias da UF, garantindo que o saldo operacional reflita a capacidade real do Nupaem.

---

## 9. Painel de Pactuação Pré-PNAPA em Cascata (Módulo 🤝)

O módulo **`🤝 Pactuação Pré-PNAPA`** promove a conciliação federativa em tempo real entre as diretrizes da Direção/Sede (*Top-Down*) e as propostas dos estados (*Bottom-Up*).

### 9.1 Balanço Orçamentário Triplo (DIPRO $\rightarrow$ Ceneac $\rightarrow$ Estados)
1. **🏛️ Teto Global DIPRO:** Envelope total autorizado pela Diretoria para a Emergência Ambiental (persistido sob `DIPRO_GLOBAL`).
2. **📋 Teto Alocado Ceneac:** Soma dos tetos pré-distribuídos pela Sede nas Ações do Catálogo.
3. **💰 Demandado pelas UFs:** Somatório real de diárias, passagens e custeio solicitados pelas 27 UFs nas propostas estaduais.
4. **⚖️ Saldo Restante DIPRO:** Indicador de folga ou sobrealocação orçamentária:
$$\text{Saldo Restante} = \text{Teto Global DIPRO} - \sum \text{Recursos Demandados pelas UFs}$$

### 9.2 Matriz de Alocação e Exportações Oficiais (Excel & PDF)
* **Matriz Analítica com Barras Nativas:** Visualização em 3 abas (*Macroações N1*, *Ações Setoriais N2* e *Detalhamento das Propostas*), equipadas com barras visuais de consumo de esforço (`% Esforço`) e orçamento (`% Orçamento`).
* **Exportação Excel (`.xlsx`):** Emissão da minuta com formatação completa em verde institucional, máscaras monetárias e abas de Anexo I e Anexo II.
* **Exportação PDF (`.pdf`):** Relatório oficial compilado via `ReportLab` em formato Paisagem (A4), com cabeçalhos institucionais do Ibama, mesclagem vertical de ações-mãe, quebra de texto em apoios interestaduais e numeração de páginas automática (*Página X de Y*).

---

## 10. Regras de Execução Física, Metas e Comprovação SEI

### 10.1 Critérios de Cumprimento de Ações Estaduais
* **Ações com Indicador Numérico:** Cumprida quando a soma das entregas de atividades homologadas com SEI alcança **$\ge 80\%$ da Meta Planejada da UF**.
* **Ações Qualitativas / Continuadas (Meta = 0):** Cumprida se houver esforço de campo registrado (`Dias_Gastos_Exec > 0`) e ao menos uma missão concluída com processo SEI.
* **Ações sob Regime de Apoio:** Cumprida quando a equipe dedica $\ge 80\%$ dos dias planejados em socorro ao estado coordenador.

### 10.2 Obrigatoriedade Estrita do Processo SEI (`Doc_Probatorio_Exec`)
Nenhuma entrega física é homologada sem o número de processo ou documento comprobatório no SEI:
* **Atividade concluída sem SEI:** Enquadra-se visualmente como *🟡 Sem Documento de Conclusão*, gera pendência de auditoria e **tem seu resultado físico desconsiderado (zero)** em todas as métricas consolidadas.

### 10.3 Semáforo de Status das Ações Estaduais

| Status de Execução | Marcador | Regra de Enquadramento Operacional | Impacto no Desempenho |
| :--- | :---: | :--- | :--- |
| **Planejada** | ⚪ | Ação ativa dentro do prazo regulamentar, aguardando execução das missões. | Conta como meta ativa no denominador. |
| **Executada** | 🟢 | Meta física atingida ($\ge 80\%$ da meta da UF) com comprovação SEI. | Pontua como meta cumprida (+1). |
| **Não Executada - Sem Justificativa** | 🔴 | Prazo expirado sem atingir 80% da meta e sem justificativa técnica registrada. | Penaliza o índice de sucesso da UF e entra no mural de atenção. |
| **Cancelada - Sem Justificativa** | 🔴 | Marcada como cancelada, mas com o campo de justificativa em branco. | Penaliza a taxa de sucesso e gera pendência formal. |
| **Cancelada (Justificada)** | 🟡 | Cancelada pela gestão regional contendo fundamentação técnica validada. | **Expurgada da base ativa:** não penaliza a nota da UF nem os índices do Brasil. |

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

