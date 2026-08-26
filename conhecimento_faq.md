# Base de Conhecimento & FAQ Oficial — SisPNAPA

---

## 1. Acesso, Perfis e Segurança da Informação

### 1.1 Como realizar o primeiro acesso ao sistema?
O acesso ao SisPNAPA é individual e restrito aos servidores autorizados:
* **Login:** Insira seu e-mail institucional completo (ex: `nome.sobrenome@ibama.gov.br`).
* **Senha Provisória Padrão:** Digite **`pnapa123`**.
* **Troca Obrigatória:** Logo após o primeiro login, desça até o rodapé da barra lateral esquerda e clique em **🔑 Trocar Minha Senha**. Defina uma senha pessoal de sua preferência.

### 1.2 Como funciona a segurança das senhas?
O sistema adota padrões criptográficos de segurança. As senhas nunca são salvas em texto puro: elas passam por um algoritmo de dispersão unidirecional (**SHA-256**) antes de serem armazenadas no banco de dados. Nem os administradores do sistema têm acesso à visualização da sua senha.

### 1.3 Quais são os perfis de acesso (RBAC) e suas permissões?
O SisPNAPA utiliza controle de acesso baseado em funções (Role-Based Access Control):
* **👑 Administrador (Nacional / Suporte):** Acesso irrestrito a todas as Unidades Federativas (UFs), permissão para alterar o Catálogo Nacional de Ações do Ceneac, gerenciar todos os usuários, auditar logs e redefinir senhas.
* **✏️ Editor Regional (Liderança / Equipe da UF):** Autonomia total para cadastrar, editar e excluir Ações e Atividades vinculadas exclusivamente à sua própria UF. Pode gerenciar a lista de servidores da sua equipe local. Não visualiza opções de edição de outros estados.
* **👁️ Visualização (Consulta / Auditoria):** Acesso de somente leitura. Pode explorar os Dashboards Executivos e a Central de Visualização, mas os formulários de inserção e edição ficam bloqueados.

### 1.4 Regra de Isolamento por UF
Para garantir a governança e integridade das informações, os Editores Regionais operam em um ambiente isolado: os formulários de inserção e as opções de edição em lote filtram automaticamente a base, garantindo que nenhum estado sobrescreva dados de outra regional acidentalmente.

---

## 2. Hierarquia de Dados: Ação Nacional x Ação Estadual x Atividades de Campo

O SisPNAPA organiza o planejamento e a execução das emergências ambientais em uma estrutura piramidal de 3 níveis relacionais:

┌─────────────────────────────────────────────────────────┐
│ 1. AÇÃO NACIONAL (Ceneac) │
│ Catálogo Estratégico Padronizado (ex: CEN001) │
└────────────────────────────┬────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────┐
│ 2. AÇÃO ESTADUAL (Regional) │
│ Planejamento Anual da UF (Meta, Prazo e Orçamento) │
└────────────────────────────┬────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────┐
│ 3. ATIVIDADES DE CAMPO (Missões) │
│ Execução Tática, Servidores, Diárias, SEI e Esforço │
└─────────────────────────────────────────────────────────┘



### 2.1 O que é a Ação Nacional (Nível 1 - Estratégico)?
* É a diretriz mestre definida pela Coordenação Central (Ceneac/Sede).
* Fica cadastrada no Catálogo Nacional (`Acoes_PNAPA`) e define o **Código Nacional** (ex: `CEN001`, `CEN002`), a nomenclatura oficial, o objetivo estratégico e a unidade de medida do indicador padrão em âmbito federal.

### 2.2 O que é a Ação Estadual (Nível 2 - Tático / Macro)?
* É a adaptação da Ação Nacional para a realidade da sua Unidade Federativa dentro do ciclo anual (ex: 2026).
* É nela que o Coordenador Regional define:
  * A **Meta Quantitativa Estadual** do indicador planejado para o ano.
  * O **Orçamento Previsto Macro** alocado para o estado.
  * O **Cronograma Global** (Data de Início e Término do Planejamento).
* Uma Ação Estadual funciona como a "Ação Pai" que agrupará todas as missões operacionais realizadas naquele estado para atingir o objetivo proposto.

### 2.3 O que são as Atividades de Campo (Nível 3 - Operacional / Micro)?
* São as missões reais realizadas no terreno ou nos núcleos (vistorias técnicas, fiscalizações, reuniões interinstitucionais, treinamentos, simulados).
* Cada atividade é vinculada obrigatoriamente a uma Ação Estadual pai.
* Registra o detalhe fino da operação: servidores escalados, dias de campo, diárias pagas, custos de passagens e número do processo SEI comprobatório.

### 2.4 Como funciona o Código Inteligente da Atividade?
As atividades não possuem códigos aleatórios. Ao criar uma missão, o sistema utiliza expressões regulares (*Regex*) para analisar os registros existentes da UF e gera automaticamente o código padronizado:
$$\text{Formato: } \mathbf{[Código\_Ação]-[Ano]-[UF]-ATV[Sequencial]}$$
* *Exemplo:* A terceira missão de campo da ação `CEN001` no estado de São Paulo em 2026 receberá automaticamente o identificador **`CEN001-2026-SP-ATV03`**.

---

## 3. Gestão de Equipes e Regras de Liderança Operacional

### 3.1 Por que o cadastro prévio na equipe é obrigatório?
Para evitar erros de digitação de nomes, duplicações no banco de dados e divergências na consolidação de diárias, **nenhum servidor pode ser escalado diretamente em uma atividade de campo se não constar previamente na tabela de Equipes**.
* Se você for cadastrar uma missão e o nome do colega não aparecer na lista de seleção, acesse primeiro o menu **👥 Gerenciar Equipes** > aba **Cadastrar Servidor**, preencha os dados dele e salve. Em seguida, ele estará disponível para todas as atividades da sua regional.

### 3.2 Regra de Liderança Única por Missão
Toda Atividade de Campo que envolve trabalho em equipe possui uma validação estrita de liderança:
* Cada missão deve ter **exatamente 1 Coordenador de Campo**.
* Todos os demais servidores vinculados à mesma missão devem ser registrados com a função de **Apoio de Campo**.
* ⚠️ **Atenção ao Conflito:** Caso o usuário tente salvar uma atividade atribuindo o papel de "Coordenador de Campo" a dois servidores simultaneamente, o sistema bloqueará a gravação e emitirá um alerta de conformidade para correção.

### 3.3 Papéis Funcionais Cadastrais
No momento de cadastrar o servidor na equipe estadual, é possível parametrizar sua função institucional:
* *Fiscal / Agente Ambiental Federal*
* *Analista / Técnico Ambiental (AEAC)*
* *Responsável de Núcleo / Coordenador Regional*
* *Colaborador / Apoio Administrativo*

### 3.4 Atualização em Cascata
Se o nome, a lotação ou a UF de um servidor forem editados na tabela de Equipes, o sistema dispara uma sincronização automática em cascata em segundo plano, atualizando o histórico de todas as atividades passadas e futuras onde aquele servidor atuou.

## 4. Regras de Execução Física, Metas e Comprovação Documental

### 4.1 Como o SisPNAPA calcula o cumprimento de uma Ação Estadual?
O motor de regras do sistema avalia o atingimento da meta da Ação Estadual (Nível 2) a partir do somatório dos resultados obtidos nas Atividades de Campo (Nível 3) a ela vinculadas:
* **Ações com Meta Numérica (Indicador Quantitativo):** A ação é classificada como cumprida quando o somatório das entregas físicas realizadas nas atividades vinculadas atinge **$\ge 80\%$ da Meta Planejada da UF**.
* **Ações sem Meta Numérica (Qualitativas / Continuadas):** A ação é considerada cumprida se houver esforço operacional comprovado ($\text{Dias\_Gastos\_Exec} > 0$) e ao menos uma atividade finalizada com documento probatório registrado.

### 4.2 A Obrigatoriedade do Processo SEI (`Doc_Probatorio_Exec`)
Nenhuma atividade é validada institucionalmente apenas pela alteração manual de seu status. É indispensável registrar o número do processo ou documento comprobatório no Sistema Eletrônico de Informações (SEI) — como Relatório de Viagem, Informação Técnica ou Termo de Vistoria:
* **Sem o SEI:** A atividade não pontua no cálculo de execução física da ação estadual e gera pendência de conformidade na base.

### 4.3 Semáforo de Status das Ações Estaduais (Aba 1 — Visualizar Base)
O status de execução da Ação Estadual reflete a consolidação geral do planejamento e das entregas dentro daquela UF:

| Status de Execução | Marcador | Regra de Enquadramento e Condição Operacional |
| :--- | :---: | :--- |
| **Planejada** | ⚪ | Ação cadastrada no planejamento anual, dentro do cronograma vigente, aguardando início ou registro das atividades de campo. |
| **Executada** | 🟢 | Meta física atingida ($\ge 80\%$ da meta planejada da UF ou esforço comprovado em ações qualitativas), com atividades concluídas e documentação SEI inserida. |
| **Não Executada - Sem Justificativa** | 🔴 | Prazo cronológico da ação encerrado sem alcance da meta física mínima e sem registro de justificativa técnica na base. |
| **Cancelada - Sem Justificativa** | 🔴 | Ação assinalada como cancelada, porém com o campo de justificativa técnica em branco (inconsistência cadastral). |
| **Cancelada (Justificada)** | 🟡 | Ação formalmente cancelada pela gestão regional, contendo fundamentação técnica registrada no campo de justificativa. |

### 4.4 Semáforo de Status das Atividades de Campo (Aba 2 — Visualizar Base)
Cada atividade operacional realizada pela equipe possui seu próprio indicador de situação:

| Status da Atividade | Marcador | Descrição e Regra de Validação |
| :--- | :---: | :--- |
| **Concluída** | 🟢 | Atividade de campo executada e com o número SEI preenchido no campo `Doc_Probatorio_Exec`. |
| **Sem Documento de Conclusão** | 🟡 | Atividade marcada como realizada, mas com o campo de processo SEI em branco. Fica pendente de regularização documental. |
| **Em Andamento / Planejada** | 🔵 | Atividade programada dentro da janela temporal de execução prevista. |
| **Atrasada** | 🔴 | A data final prevista expirou sem que a atividade tenha sido concluída ou justificada no sistema. |
| **Não Executada (Justificada)** | 🟡 | Missão que não pôde ser realizada, com justificativa formal registrada pela equipe. |

---

## 5. Gestão de Prazos, Mural de Pendências e Justificativas

### 5.1 O que define uma Atividade em Atraso?
O sistema realiza uma verificação contínua comparando a **Data de Fim Prevista** (`Data_Fim_Prev`) com a data atual:
* Se a data final foi ultrapassada e a atividade permanece no status *Planejada* ou sem dados de execução preenchidos, o sistema atribui automaticamente a situação de **🔴 Atrasada**.

### 5.2 Como regularizar uma Atividade Não Executada?
Caso uma missão programada não ocorra devido a contingenciamento orçamentário, fatores climáticos, cancelamento de operação ou remanejamento de prioridades:
1. Acesse o menu **📊 Visualizar Base** (Aba 2 — Atividades de Campo) ou selecione a atividade para edição.
2. Altere o status para **Não Executada**.
3. Preencha obrigatoriamente o campo **Justificativa da Não Execução**, detalhando o motivo técnico do cancelamento.
4. O sistema atualizará o registro para **🟡 Não Executada (Justificada)**, regularizando a conformidade da UF no relatório de gestão anual.

### 5.3 Mural de Pendências e Auditoria Regional
Na rotina de governança, os Editores Regionais devem acompanhar o mural de pendências para sanar inconsistências ativas, tais como:
* Atividades finalizadas que ainda constam como *Sem Documento de Conclusão* (falta de SEI).
* Ações ou atividades expiradas sem justificativa registrada.
* Conflitos de alocação de equipe (ex: atividades sem *Coordenador de Campo* ou com múltiplos coordenadores atribuídos).

---

## 6. Orçamento, Diárias, Passagens e PCDP

### 6.1 Estrutura Orçamentária: Planejado vs. Executado
O SisPNAPA mantém a segregação entre os valores previstos no planejamento e os custos efetivamente liquidados na execução:
* **Recursos Planejados:** Estimativa orçamentária lançada durante a elaboração da Ação Estadual (previsão de Diárias, Passagens e Outras Despesas).
* **Recursos Executados:** Totalização real dos custos a partir do lançamento individualizado das diárias e passagens de cada servidor participante das missões.

### 6.2 Registro Individualizado por Servidor (PCDP e Diárias)
Como o cadastro em lote gera uma linha de registro para cada servidor escalado na atividade, as variáveis orçamentárias são lançadas de forma personalizada:
* **Qtd. de Diárias e Valor de Diárias:** Número de diárias concedidas e valor financeiro total pago ao servidor.
* **Valor de Passagens:** Custo dos bilhetes aéreos ou passagens terrestres emitidas para o deslocamento.
* **Número da PCDP:** Registro do identificador da Proposta de Concessão de Diárias e Passagens gerada no SCDP.
* **Dias de Campo:** Esforço operacional em dias dedicados pelo servidor àquela missão específica.

### 6.3 Origem do Recurso Financeiro
Para garantir a correta prestação de contas entre a Sede e as Superintendências, cada lançamento orçamentário deve especificar a fonte pagadora:
* **Recurso Regional (UF):** Custeio realizado com a dotação orçamentária própria descentralizada para a Superintendência/Núcleo.
* **Recurso Central (Ceneac/Sede):** Custeio direto pela Coordenação-Geral de Emergências Ambientais (passagens ou diárias emitidas diretamente por Brasília).


## 7. Funcionalidades de Produtividade em Lote e Filtros Avançados

### 7.1 Inserção em Lote de Atividades (Menu: Inserir > Atividades)
A funcionalidade de inserção em lote foi concebida para eliminar o trabalho repetitivo no registo de missões operacionais conjuntas:

* **Mecânica de Funcionamento:**
  1. No formulário de inserção de Atividade, preencha os dados comuns da missão (Ação Pai, Tipo de Atividade, Descrição, Datas de Início e Término, Município/Localidade).
  2. Na aba **Recursos Humanos**, utilize o campo de seleção múltipla (*multiselect*) para marcar todos os servidores que participaram ou participarão da missão.
  3. O sistema gerará automaticamente **uma linha de registo individual para cada servidor selecionado** na base de dados.
* **Preservação do Identificador Único:**
  * Todas as linhas geradas pelo mesmo formulário partilham exatamente o mesmo `Codigo_Atividade` (ex.: `CEN001-2026-SP-ATV02`).
  * Isto permite que o sistema trate a missão como uma única entidade nos agrupamentos e relatórios, mantendo simultaneamente a individualização de diárias, passagens e PCDP por agente.
* **Validação de Papéis na Inserção em Lote:**
  * Ao selecionar múltiplos elementos, defina o servidor que atuará como **Coordenador de Campo**; os restantes serão automaticamente tipificados como **Apoio de Campo**, prevenindo inconsistências de liderança.

---

### 7.2 Edição em Lote na Base de Dados (Menu: Visualizar Base)
A edição em lote permite atualizar dezenas de registos em poucos segundos, sendo essencial para fecho de meses, prestação de contas e regularização de pendências:

* **Passo a Passo Operacional:**
  1. Aceda à **Aba 1 (Ações)** ou à **Aba 2 (Atividades de Campo)**.
  2. Na primeira coluna da tabela, marque a caixa de seleção (`Selecionar`) nas linhas que pretende modificar em conjunto.
  3. Ao marcar duas ou mais linhas, o painel inferior **"Edição em Lote"** é ativado automaticamente.
  4. Escolha o campo que deseja alterar (ex.: *Status de Execução*, *Documento SEI Comprobatório*, *Data de Término Real* ou *Justificativa*).
  5. Insira o novo valor pretendido e clique no botão **Salvar Alterações em Lote**.
* **Principais Aplicações Práticas:**
  * **Homologação Documental em Massa:** Selecionar todas as linhas dos servidores que participaram da mesma missão e colar o número do Processo/Documento SEI de uma só vez.
  * **Atualização de Status de Missão:** Marcar múltiplos registos com status *Prevista* e convertê-los para *Concluída* ou *Cancelada*.
  * **Regularização de Prazos:** Ajustar datas de término de várias atividades que sofreram prorrogação de cronograma.
* **Salvaguarda de Integridade:**
  * Campos individuais sensíveis (como valores específicos de passagens ou nomes de servidores) não são sobrescritos de forma destrutiva; apenas as variáveis comuns selecionadas sofrem atualização em massa.

---

### 7.3 Exploração Rápida e Filtros Avançados
Para gerir grandes volumes de dados sem perda de desempenho, o SisPNAPA disponibiliza um ecossistema de filtragem multinível na **Central de Visualização**:

* **Filtros por Popover (Menus Suspensos Superiores):**
  * **Filtro por UF:** Isola instantaneamente os dados da regional selecionada (para Administradores) ou fixa a UF local (para Editores Regionais).
  * **Filtro por Ação Macro (Ceneac):** Permite visualizar apenas as atividades vinculadas a um código específico (ex.: todas as vistorias de `CEN001`).
  * **Filtro por Status de Execução:** Segmenta ações e atividades por situação operacional (*Concluída*, *Atrasada*, *Planejada*, *Sem Documento de Conclusão*).
* **Filtros Temporais via Sliders e Intervalos de Datas:**
  * Permitem restringir a visualização a um trimestre, mês ou período operacional específico sem necessidade de digitação manual de texto.
* **Pesquisa Livre e Localização por Servidor:**
  * Caixa de pesquisa rápida para filtrar por nome de servidor, localidade, número de PCDP ou código de processo SEI.
* **Botão de Limpeza Rápida (Reset):**
  * Restaura todas as visões para a configuração padrão com um único clique.

---

### 7.4 Boas Práticas e Prevenção de Inconsistências em Massa
* **Confirmação Visual Pós-Gravação:** Após executar uma inserção ou edição em lote, observe a mensagem de sucesso e a recarga automática da tabela para certificar-se de que todas as linhas foram sincronizadas com o repositório central.
* **Verificação Prévia de Equipa:** Antes de iniciar a inserção em lote de uma atividade, assegure-se de que todos os membros da missão já constam da aba *Gerenciar Equipes*. Caso falte algum servidor, cadastre-o previamente para evitar a necessidade de recriar o lote.
* **Atenção ao Conflito de Filtros:** Se uma atividade recém-cadastrada não surgir de imediato no ecrã, verifique se não existem filtros ativos de *Status* ou *Intervalo de Datas* que estejam a ocultar o novo registo.

## 8. Dashboards Executivos e Consolidação Nacional

O módulo **📈 Dashboards Executivos** consolida em tempo real o desempenho físico, orçamentário e operacional do SisPNAPA. A primeira aba (**Visão Executiva Geral**) apresenta o panorama estratégico do plano por meio de duas tabelas estruturantes:

---

### 8.1 Tabela 1: Status de Execução Geral do PNAPA (Por UF e Nacional)

Esta tabela apresenta o ranking e a taxa de sucesso das Unidades Federativas e do Consolidado Nacional, avaliando **quantas ações planejadas conseguiram atingir o limiar de cumprimento ($\ge 80\%$)**.

┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 🏆 Status de Execução Geral do PNAPA (Por UF e Nacional) │
├────────────┬─────────────────────────────────────────────┬──────────────────────┬──────────────────────┤
│ UF / Nível │ % de Ações Executadas (Meta Física ≥ 80%) │ No. Ações Planejadas │ Ações c/ Meta Atingida│
└────────────┴─────────────────────────────────────────────┴──────────────────────┴──────────────────────┘



#### A. Como é calculado o percentual de uma UF específica (Ex: São Paulo - SP)?
1. **No. Ações Planejadas:** Total de Ações Estaduais cadastradas e ativas no plano de trabalho daquela UF.
2. **Ações c/ Meta Atingida:** Quantidade de ações da UF cuja execução física acumulada (somatório das atividades concluídas com SEI) atingiu **$\ge 80\%$ da meta estadual planejada**.
3. **Fórmula do % de Ações Executadas da UF:**
   $$\% \text{ de Ações Executadas (UF)} = \left( \frac{\text{Ações c/ Meta Atingida na UF}}{\text{No. de Ações Planejadas pela UF}} \right) \times 100$$
   * *Exemplo da imagem:* SP planejou $26$ ações e atingiu a meta em $5$ delas. 
   $$\% \text{ Executadas (SP)} = \left( \frac{5}{26} \right) \times 100 = 19,2\%$$

---

#### B. Como é calculado o percentual do Consolidado Global (🇧🇷 NACIONAL)?
O nível nacional **não é uma média simples das porcentagens dos estados**. Uma ação nacional só é considerada cumprida no país se o somatório das entregas físicas de todos os estados atingir o limiar global de $80\%$:

1. **Condição para uma Ação Nacional ser "Executada":**
   $$\text{Percentual Físico Nacional da Ação} = \left( \frac{\sum_{\text{todas as UFs}} \text{Resultado Físico}}{\sum_{\text{todas as UFs}} \text{Meta Física Planejada}} \right) \times 100 \ge 80\%$$
2. **No. Ações Planejadas (Nacional):** Quantidade de ações distintas do catálogo nacional que foram adotadas por ao menos uma UF no país (ex: $33$ ações).
3. **Ações c/ Meta Atingida (Nacional):** Total de ações distintas do catálogo nacional que ultrapassaram a régua de $\ge 80\%$ na soma de todos os estados (ex: $6$ ações).
4. **Fórmula do % de Ações Executadas Nacional:**
   $$\% \text{ de Ações Executadas (Nacional)} = \left( \frac{\text{Ações Nacionais c/ Meta Global} \ge 80\%}{\text{Total de Ações Nacionais Planejadas}} \right) \times 100$$
   * *Exemplo da imagem:* Das $33$ ações nacionais planejadas no Brasil, $6$ atingiram $\ge 80\%$ na soma nacional:
   $$\% \text{ Executadas (Nacional)} = \left( \frac{6}{33} \right) \times 100 = 18,2\%$$

---

#### C. Estudo de Caso Prático (Cenário de Descentralização)
Considere a ação hipotética `CEN001` planejada em dois estados:

* **Em SP:** Meta $= 10$ vistorias | Realizado $= 8$ vistorias.
  $$\text{Execução SP} = \left( \frac{8}{10} \right) \times 100 = 80\% \implies \mathbf{Meta\ Atingida\ em\ SP\ (Soma\ +1\ para\ SP)}$$
* **No RJ:** Meta $= 10$ vistorias | Realizado $= 0$ vistorias.
  $$\text{Execução RJ} = \left( \frac{0}{10} \right) \times 100 = 0\% \implies \mathbf{N\tilde{a}o\ Atingida\ no\ RJ\ (Soma\ +0\ para\ RJ)}$$
* **No Consolidado Nacional:**
  $$\text{Resultado Global} = 8 + 0 = 8 \quad \Big| \quad \text{Meta Global} = 10 + 10 = 20$$
  $$\text{Execução Nacional} = \left( \frac{8}{20} \right) \times 100 = 40\% \implies \mathbf{N\tilde{a}o\ Atingida\ no\ Brasil\ (Soma\ +0\ para\ o\ Nacional)}$$

> **Impacto:** A ação pontua como cumprida individualmente para São Paulo, mas **não** pontua no indicador nacional de ações executadas, pois o resultado somado do país ($40\%$) ficou abaixo da linha de corte de $80\%$.

---

### 8.2 Tabela 2: Status de Execução Geral do PNAPA (Por Ação Nacional)

Esta tabela detalha o desempenho individualizado de cada linha de ação, exibindo o volume absoluto de metas, entregas e a taxa percentual de realização.

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 🎯 Status de Execução Geral do PNAPA (Por Ação Nacional) │
├────────────────────────────────────────┬─────────────┬──────────────┬──────────────────┤
│ Ação PNAPA │ % Execução │ Meta (Física)│ Resultado (Físico│
└────────────────────────────────────────┴─────────────┴──────────────┴──────────────────┘

#### A. Comportamento com e sem Filtros Regionais
* **Sem Filtro de UF (Visão Consolidada Brasil):**
  * `Meta (Física)` $=$ Soma das metas planejadas por todos os estados para aquela ação.
  * `Resultado (Físico)` $=$ Soma de todos os resultados homologados com SEI no país.
  * `% Execução` $=$ $(\text{Resultado Global} / \text{Meta Global}) \times 100$.
* **Com Filtro de UF Ativo (Ex: Filtrado por `SP` ou `RJ`):**
  * A tabela recalcula instantaneamente e passa a exibir exclusivamente a Meta daquela regional, o Resultado obtido por aquela equipe e o percentual de cumprimento local da ação.

---

#### B. Semáforo e Régua de Cores da Tabela 2
A coluna **`% Execução`** utiliza quatro faixas visuais padronizadas:

| Faixa Percentual | Cor de Fundo | Significado Operacional | Exemplo da Tabela |
| :--- | :---: | :--- | :--- |
| **$\ge 100\%$** | 🔵 **Azul** | **Meta Totalmente Cumprida / Superada:** A entrega física igualou ou ultrapassou o planejado. | `CEN031` ($660\%$), `CEN019` ($100\%$) |
| **$80,0\%$ a $99,9\%$** | 🟢 **Verde** | **Meta Atingida (Faixa de Conformidade):** Atingiu o patamar mínimo regulamentar do PNAPA. | `CEN014` ($83,3\%$) |
| **$50,0\%$ a $79,9\%$** | 🟡 **Amarelo** | **Execução Parcial / Atenção:** Ação em andamento, mas abaixo do índice formal de conclusão. | `CEN028` ($79,0\%$) |
| **$< 50,0\%$** | 🔴 **Vermelho** | **Execução Crítica / Insuficiente:** Baixo avanço físico ou sem entregas comprovadas. | `CEN022` ($43,8\%$), `CEN034` ($23,4\%$) |

---

### 8.3 Relação Dinâmica entre a Tabela 1 e a Tabela 2
A Tabela 1 é a **síntese executiva** do que é apurado linha a linha na Tabela 2:
* Toda linha da Tabela 2 que estiver com a cor **Azul ($\ge 100\%$)** ou **Verde ($\ge 80\%$)** somará $+1$ na coluna `Ações c/ Meta Atingida` da Tabela 1.
* Toda linha da Tabela 2 com a cor **Amarela ($50\% - 79,9\%$)** ou **Vermelha ($< 50\%$)** contará apenas no total de `No. Ações Planejadas`, reduzindo o percentual geral de execução da UF ou do país.


## 9. Módulo de Desenvolvimento Humano e Avaliação 360º

O SisPNAPA integra um módulo dedicado ao desenvolvimento de recursos humanos, clima organizacional e melhoria contínua das operações de emergência ambiental. O sistema automatiza a recolha de perceções sobre trabalho em equipa, liderança e suporte mútuo após a realização de missões conjuntas.

---

### 9.1 Gatilho Lógico e Critérios de Ativação
O formulário de Avaliação 360º não fica disponível de forma indiscriminada. Ele é ativado pelo sistema apenas quando uma missão cumpre, cumulativamente, os seguintes requisitos de negócio:

1. **Status Oficial de Conclusão:** A atividade de campo deve estar com o andamento formalmente registado como **🟢 Concluída** (incluindo a inserção válida do número do documento/processo SEI probatório).
2. **Dimensão Mínima da Equipa ($\ge 3$ Servidores):** O agrupamento do `Codigo_Atividade` (ex.: `CEN001-2026-SP-ATV02`) deve conter **3 ou mais servidores únicos e distintos** registados nas linhas da atividade. Missões individuais ou executadas em dupla não disparam o ciclo 360º para evitar a quebra involuntária do anonimato.

---

### 9.2 Notificação e Convite Automático
Assim que a atividade de campo atinge as condições de ativação:
* O sistema dispara um fluxo em segundo plano que identifica o endereço de e-mail institucional de todos os servidores que integraram a missão.
* Cada membro da equipa recebe uma notificação convidando-o a aceder ao SisPNAPA para avaliar a dinâmica da operação e o desempenho colaborativo dos seus pares.

---

### 9.3 Estrutura da Avaliação Entre Pares
Ao aceder ao módulo de avaliação na interface do sistema:
* **Filtro de Autoavaliação:** O servidor autenticado visualiza apenas os nomes dos colegas que estiveram consigo na mesma missão (o seu próprio nome não surge para avaliação).
* **Avaliação Objetiva (Nota/Conceito):** Registo de apreciação sobre a postura, cooperação e entrega técnica do colega durante os dias de campo.
* **Feedback Qualitativo (Comentário Construtivo):** Campo aberto opcional para observações qualitativas, elogios a atuações de destaque ou recomendações operacionais de melhoria.

---

### 9.4 Princípios de Anonimização e Segurança Psicológica
A arquitetura do módulo 360º foi desenhada com salvaguardas rígidas de confidencialidade:

* **Desvinculação do Avaliador:** O identificador, nome e e-mail de quem emitiu a avaliação nunca são gravados em associação direta com a mensagem de feedback nem são exibidos em nenhuma interface de consulta.
* **Mural de Feedbacks Anónimos:** Na aba pessoal (**Meus Feedbacks**), o servidor avaliado visualiza apenas:
  * O código e descrição da missão correspondente.
  * O indicador visual de avaliação positiva ou de atenção.
  * O texto descritivo do feedback recebido.
* **Sem Rastreabilidade Hierárquica:** Os colegas de equipa não conseguem identificar quem escreveu cada comentário individual, fomentando um ambiente seguro para partilha de observações honestas e construtivas.

---

### 9.5 Boas Práticas na Redação de Feedbacks Operacionais
* **Foco em Comportamentos e Processos:** Descreva situações observadas no terreno (ex.: pontualidade, comunicação durante a vistoria, gestão de equipamentos, cumprimento de protocolos de segurança).
* **Orientação para o Desenvolvimento:** Evite críticas genéricas; apresente sugestões práticas que auxiliem o colega em missões futuras.
* **Reconhecimento Positivo:** Destaque posturas proativas, capacidade de resolução de conflitos e apoio prestado em cenários de pressão ou emergência ambiental.

## 10. Governança do Piloto, Reporte de Inconsistências e Suporte

A fase piloto nacional do SisPNAPA tem como objetivo consolidar a transição digital do planeamento e execução das emergências ambientais, garantindo a validação da ferramenta em ambiente operacional real com múltiplos estados participantes.

---

### 10.1 Utilização de Dados Reais do Ciclo Operacional de 2026
* **Ambiente de Produção Oficial:** O ambiente de testes piloto **não utiliza dados fictícios**. Todos os registos de Ações Estaduais e Atividades de Campo inseridos pelas equipas regionais correspondem ao passivo executado e ao planeamento oficial de 2026.
* **Validade Institucional:** As informações registadas e homologadas com documento SEI compõem diretamente o relatório consolidado de monitorização do plano, evitando retrabalho futuro de migração de dados.

---

### 10.2 Central de Sugestões e Registo de Inconsistências (Menu: 💡 Sugestões & Melhorias)
Para assegurar a rastreabilidade e evitar a dispersão de pedidos em canais informais (como WhatsApp ou e-mails individuais), **todas as ocorrências, dúvidas técnicas e propostas de melhoria devem ser submetidas diretamente pela interface do sistema**:

* **Como Submeter um Registo:**
  1. Aceda ao menu lateral **💡 Sugestões & Melhorias**.
  2. Selecione o **Módulo Afetado** (ex.: *Autenticação/Login*, *Inserção de Atividades*, *Edição em Lote*, *Dashboards Executivos*, *Equipes*, *Módulo 360º*).
  3. Defina a **Prioridade do Pedido**:
     * 🔴 **Alta (Bloqueante/Erro Crítico):** Erros de sistema, falhas de gravação no banco de dados, divergências graves em cálculos de metas ou impossibilidade de login.
     * 🟡 **Média (Operacional/Ajuste):** Dificuldades visuais, lentidão pontual de carregamento ou necessidade de ajuste em rótulos de campos.
     * 🔵 **Baixa (Sugestão de Nova Funcionalidade):** Ideias de novos gráficos, atalhos de navegação ou filtros adicionais para ciclos futuros.
  4. Descreva a situação com clareza (indicando, se aplicável, o código da atividade ou a mensagem de erro apresentada).

---

### 10.3 Quadro de Acompanhamento e Ciclo de Vida dos Chamados
Na aba **Quadro de Acompanhamento** da Central de Sugestões, todos os utilizadores podem monitorizar o tratamento das solicitações em tempo real:

| Status do Pedido | Significado e Encaminhamento Técnico |
| :--- | :--- |
| 📥 **Recebido / Aberto** | Ocorrência registada com sucesso na base de auditoria e aguardando triagem da equipa técnica. |
| ⚙️ **Em Análise / Desenvolvimento** | Ajuste em implementação no código-fonte, correção no fluxo do Power Automate ou melhoria em validação. |
| ✅ **Concluído / Resolvido** | Correção implementada no ambiente de produção ou melhoria disponibilizada para todos os utilizadores. |
| ℹ️ **Esclarecido / Informativo** | Pedido relacionado com dúvida de regra de negócio, solucionado com orientação direta na base de conhecimento. |

---

### 10.4 Boas Práticas de Salvaguarda e Segurança (Fase Piloto)
* **Manutenção Temporária de Controlos Locais:** Durante a vigência da versão Alfa/Piloto, recomenda-se que as superintendências mantenham os seus controlos paralelos (planilhas regionais) atualizados preventivamente, assegurando contingência em caso de manutenção nos servidores centrais.
* **Verificação de Concorrência de Rede:** Em períodos de grande volume de lançamentos simultâneos entre diferentes estados, aguarde a mensagem verde de confirmação após gravações em lote antes de fechar o navegador.

---

### 10.5 Canais de Suporte e Assistência ao Utilizador
1. **Assistente Virtual Nativo (`🤖 Assistente Virtual`):** Primeiro nível de atendimento disponível 24/7 diretamente no menu do sistema para esclarecimento imediato de regras de negócio, senhas padrão, regras de $80\%$ e operações em lote.
2. **Central de Sugestões e Melhorias:** Canal formal para reporte de anomalias e acompanhamento de chamados técnicos.
3. **Ponto Focal Regional:** O Editor Regional de cada UF atua como multiplicador local para alinhamento de equipas e validação de permissões de acesso.

<img width="425" height="693" alt="image" src="https://github.com/user-attachments/assets/eb4b474a-a9ab-46b7-b5a8-175aa6f78341" />
