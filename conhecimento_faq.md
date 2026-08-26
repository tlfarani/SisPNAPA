# Base de Conhecimento & FAQ Oficial — SisPNAPA

---

## 1. Acesso, Perfis, Segurança e Arquitetura Federativa

### 1.1 Como realizar o primeiro acesso ao sistema?

O acesso ao SisPNAPA é individual e restrito aos servidores autorizados:

* **Login:** Insira seu e-mail institucional completo (ex: `nome.sobrenome@ibama.gov.br`).
* **Senha Provisória Padrão:** Digite **`pnapa123`**.
* **Troca Obrigatória:** Logo após o primeiro login, acesse o rodapé da barra lateral esquerda e clique em **🔑 Trocar Minha Senha**. Defina uma senha pessoal exclusiva.

### 1.2 Como funciona a segurança das senhas?

As senhas nunca são salvas em texto puro: elas passam por um algoritmo criptográfico de dispersão unidirecional (**SHA-256**) antes de serem gravadas no repositório do SharePoint. Nem mesmo os administradores do sistema têm acesso à visualização da sua senha.

### 1.3 Quais são os perfis de acesso (RBAC) e suas permissões?

* **👑 Administrador (Nacional / Suporte):** Acesso irrestrito a todas as 27 Unidades Federativas (UFs), permissão para alterar o Catálogo Nacional de Ações do Ceneac, calibrar tetos orçamentários da DIPRO, gerenciar usuários/equipes de qualquer regional, despachar sugestões e auditar logs do sistema.
* **✏️ Editor Regional (Liderança / Ponto Focal da UF):** Autonomia para cadastrar, editar e excluir Ações e Atividades vinculadas exclusivamente à sua própria UF. Pode gerenciar a lista de servidores da sua equipe local. Não possui permissão para modificar dados de outras regionais.
* **👁️ Visualização (Consulta / Auditoria):** Acesso de somente leitura. Pode explorar os Dashboards Executivos, o Painel Pré-PNAPA e a Central de Visualização, com formulários de inserção e edição desabilitados.

### 1.4 Arquitetura Federativa Oficial (27 UFs)

O SisPNAPA adota a divisão federativa estrita da República:

* **Unidade Federativa (UF):** Entidade geográfica com **27 opções oficiais** (26 Estados + Distrito Federal - `DF`). A designação "Ceneac" não é tratada como UF.
* **Lotação / Unidade:** Reflete o setor de atuação administrativa do servidor (`Ceneac`, `CPrev`, `Coate`, `Seplog`, `Nupaem-SP`, `SUPES-RJ`, etc.). Servidores da Sede Nacional têm `UF = DF` e sua respectiva divisão no campo `Lotação`.

---

## 2. Hierarquia de Dados: Estrutura em 3 Níveis

O SisPNAPA organiza o planejamento e a execução das emergências ambientais em uma estrutura piramidal de 3 níveis relacionais:

```
┌─────────────────────────────────────────────────────────┐
│              1. AÇÃO NACIONAL (Ceneac)                  │
│       Catálogo Estratégico Padronizado (ex: CEN001)     │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              2. AÇÃO ESTADUAL (Regional)                │
│   Planejamento Anual da UF (Meta, Prazo e Orçamento)   │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│            3. ATIVIDADES DE CAMPO (Missões)             │
│  Execução Tática, Servidores, Diárias, SEI e Esforço   │
└─────────────────────────────────────────────────────────┘

```

### 2.1 O que é a Ação Nacional (Nível 1 - Estratégico)?

* É a diretriz mestre definida pela Coordenação-Geral de Emergências Ambientais (Ceneac/Sede).
* Fica cadastrada no Catálogo Oficial (`Acoes_PNAPA`) e define o **Código Nacional** (ex: `CEN001`), o Especialista Responsável na Sede (**Dono da Ação**), o **Teto Orçamentário Ceneac**, a meta física global e a unidade de medida do indicador padrão.

### 2.2 O que é a Ação Estadual (Nível 2 - Tático / Macro)?

* É o compromisso formal de planejamento assumido por uma UF dentro do ciclo anual (ex: 2026 ou 2027).
* É nela que o Ponto Focal Estadual define:
* A **Meta Quantitativa da UF** para o indicador.
* O **Papel Institucional do Estado** (`Coordenação` ou `Apoio`).
* O **Ponto Focal Estadual** (Coordenador responsável na regional).
* A **Previsão Orçamentária Macro** da UF (Diárias, Passagens e Outras Despesas).


* Uma Ação Estadual funciona como a "Ação Pai" que agrupa todas as missões operacionais realizadas naquele estado.

### 2.3 O que são as Atividades de Campo (Nível 3 - Operacional / Micro)?

* São as missões reais realizadas no terreno ou nos núcleos (vistorias técnicas, fiscalizações, reuniões interinstitucionais, treinamentos, simulados).
* Cada atividade é vinculada obrigatoriamente a uma Ação Estadual pai.
* Registra os servidores escalados, esforço em dias, diárias pagas, custos de passagens e o número do processo SEI comprobatório.

### 2.4 Como funciona o Código Inteligente da Atividade?

As atividades recebem um código padronizado gerado automaticamente via expressões regulares:


$$\text{Formato: } \mathbf{[Código\_Ação]-[Ano]-[UF]-ATV[Sequencial]}$$

* *Exemplo:* A terceira missão da ação `CEN001` no estado de São Paulo em 2027 recebe automaticamente o identificador **`CEN001-2027-SP-ATV03`**.

---

## 3. Gestão de Equipes, Lotações da Sede e Liderança

### 3.1 Obrigatoriedade do Cadastro Prévio

Nenhum servidor pode ser escalado em uma atividade de campo se não constar previamente cadastrado na base de Equipes. Isso previne duplicações de nomes, erros de grafia e inconsistências na prestação de contas.

* Para cadastrar um colega, acesse **👥 Gerenciar Equipes** > **➕ Cadastrar Servidor**, preencha os dados e grave no banco.

### 3.2 Regra de Liderança Única por Missão

Toda Atividade de Campo que envolve equipe possui validação estrita de liderança:

* Cada missão deve ter **exatamente 1 Coordenador de Campo**.
* Os demais servidores vinculados à mesma missão são cadastrados na função de **Apoio de Campo**.
* ⚠️ **Bloqueio de Conflito:** O sistema impede a gravação caso dois servidores sejam apontados simultaneamente como "Coordenador de Campo" na mesma missão.

### 3.3 PROCV Automático de Atributos do Servidor

Na Central de Visualização e nos relatórios, o sistema cruza em tempo real o cadastro dos servidores para enriquecer os registros operacionais com os campos:

* **É Fiscal?** (`Sim` / `Não`)
* **Possui AEAC?** (`Sim` / `Não`)
* **Função Institucional:** (`Responsável Nupaem`, `Responsável Substituto(a)`, `Coordenador(a) Geral Ceneac`, `Coordenador(a) CPrev`, `Coordenador(a) Coate`).

### 3.4 Sincronização em Cascata

Se o nome, UF ou setor de lotação de um servidor ou unidade forem editados, o sistema executa uma sincronização paralela em segundo plano, atualizando o histórico de todas as ações e atividades vinculadas.

---

## 4. Motor de Governança Operacional e Capacidade (Regras 2027+)

O SisPNAPA conta com um motor analítico de governança que calcula o termômetro de carga de trabalho dos servidores e os limites de liderança.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 REGIME DE TRAVAS DE CAPACIDADE OPERACIONAL                  │
├─────────────────────────┬───────────────────────────────────────────────────┤
│ Ciclos Anteriores (2026)│ Modo Orientativo: Alertas visuais sem bloqueio.  │
├─────────────────────────┼───────────────────────────────────────────────────┤
│ Ciclos Futuros (2027+)  │ Modo Rígido: Bloqueio impeditivo de gravação.     │
└─────────────────────────┴───────────────────────────────────────────────────┘

```

### 4.1 Tetos Anuais de Dias: Pré-PNAPA vs. Pós-PNAPA

A capacidade anual de dias de campo é escalonada conforme o papel institucional do servidor:

| Perfil do Servidor | Teto Pré-PNAPA (Planejamento) | Teto Pós-PNAPA (Execução: +50%) |
| --- | --- | --- |
| **Responsável / Coordenador Titular** | 90 dias / ano | 135 dias / ano |
| **Coordenador / Responsável Substituto** | 60 dias / ano | 90 dias / ano |
| **Membro de Equipe Regional** | 40 dias / ano | 60 dias / ano |

### 4.2 Equiparação Automática da Sede (Ceneac / Brasília)

Servidores lotados no **DF** pertencentes às divisões centrais (`Ceneac`, `CPrev`, `Coate`, `Seplog`, `Seprev`, `Secoate`) são automaticamente equiparados a **Titular/Responsável**, recebendo o teto ampliado de **90 dias (Pré) / 135 dias (Pós)** para absorver a coordenação de operações de abrangência nacional.

### 4.3 Trava Anti-Rotina (Cota de 50% Ordinárias)

Para evitar que o plano anual seja consumido apenas por manutenções rotineiras, **no máximo 50% do teto de dias do servidor pode ser alocado em atividades com Importância "Ordinária"**. O restante da capacidade deve ser direcionado a iniciativas "Prioritárias" ou "Estratégicas".

### 4.4 Limites de Liderança e Coordenação

* **Teto Global de Liderança:** Máximo de **10 Ações PNAPA** sob a coordenação do mesmo servidor no ano.
* **Regra de Ouro (Ações Nível 3):** Um mesmo coordenador pode assumir no máximo **3 Ações de Grande Porte / Nível 3** ($\ge 20$ dias de planejamento acumulado).

---

## 5. Painel de Pactuação Pré-PNAPA (Físico & Orçamentário)

O módulo **`🤝 Pactuação Pré-PNAPA`** promove a conciliação federativa entre as diretrizes da Direção/Sede (*Top-Down*) e as propostas inseridas pelas 27 UFs (*Bottom-Up*).

### 5.1 Governança Orçamentária em 3 Níveis

O painel monitora o equilíbrio orçamentário em três camadas hierárquicas:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. TETO GLOBAL DIPRO                                        │
│ Envelope orçamentário macro autorizado pela Diretoria.      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. TETO ALOCADO CENEAC                                      │
│ Soma dos tetos pré-fixados pela Sede nas Ações Nacionais.   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. DEMANDA DAS UFS (BOTTOM-UP)                              │
│ Soma dos recursos solicitados nas propostas estaduais.      │
└─────────────────────────────────────────────────────────────┘

```

* **Persistência do Teto DIPRO (`DIPRO_GLOBAL`):** O valor aprovado pela Diretoria de Proteção Ambiental é calibrado pelo Administrador e gravado no SharePoint sob a chave técnica `DIPRO_GLOBAL-[Ano]`. Esse registro permanece isolado dos formulários operacionais.
* **Saldo Restante DIPRO:** Apura em tempo real se as demandas dos 27 estados cabem no orçamento global:

$$\text{Saldo Restante} = \text{Teto Global DIPRO} - \sum \text{Recursos Demandados pelas UFs}$$



### 5.2 Semáforo de Alinhamento das Metas Físicas

Cada Ação Nacional confronta a **Meta Nacional (Top-Down)** com o **Somatório das Metas Propostas pelas UFs (Bottom-Up)**:

| Status do Alinhamento | Marcador | Condição Técnica e Significado |
| --- | --- | --- |
| **Sem Adesão (0%)** | ⚪ | Nenhuma das 27 UFs cadastrou proposta para a ação no exercício. |
| **Déficit Físico (< 100%)** | 🟡 | A soma das metas estaduais ficou abaixo da meta global do Ceneac. Demanda pactuação adicional. |
| **Meta Pactuada (100%)** | 🟢 | As metas propostas pelas UFs igualaram com precisão a meta nacional da ação. |
| **Superávit Físico (> 100%)** | 🔵 | A demanda dos estados superou a meta prevista inicialmente pela Sede. |

### 5.3 Raio-X Federativo e Identificação de UFs Pendentes

Dentro de cada ação, a aba **`⏳ Estados Sem Proposta Registrada`** cruza a base de **27 UFs** e isola instantaneamente as siglas das Superintendências que ainda não enviaram planejamento. O indicador superior exibe a adesão real:


$$\text{Taxa de Adesão Federativa} = \left( \frac{\text{UFs com Proposta}}{\mathbf{27}} \right) \times 100$$

---

## 6. Central de Visualização & Gestão (Duas Subpáginas)

O menu **📊 Visualizar Base** é estruturado em duas subpáginas especializadas:

### 6.1 Subpágina 1: Ações Estaduais (Planejamento & Metas)

Dedicada à gestão macro do plano na regional:

* Apresenta o indicador, a meta quantitativa da UF, o resultado físico consolidado e a barra de `% de Execução`.
* **Painel de Edição da Ação:** Permite alterar o Papel (`Coordenação` / `Apoio`), a UF da Ação e o Ponto Focal Estadual com recarga dinâmica de equipe na **Aba 1 (Governança Estadual)**.

### 6.2 Subpágina 2: Atividades de Campo (Operações & Execução)

Dedicada à gestão micro das missões:

* Exibe código inteligente (`ATV`), servidor escalado, município, processo SEI, diárias, passagens e status documental.
* **Edição Individual e em Lote:** Permite selecionar múltiplas atividades para alterar status, homologar documentos SEI ou prorrogar prazos simultaneamente.

---

## 7. Regras de Execução Física, Metas e Comprovação SEI

### 7.1 Como o SisPNAPA calcula o cumprimento de uma Ação Estadual?

O sistema avalia o atingimento da meta da Ação Estadual (Nível 2) a partir do somatório das entregas registradas nas Atividades de Campo (Nível 3) concluídas:

* **Ações com Indicador Numérico:** Ação cumprida quando o somatório das atividades com documento atinge **$\ge 80\%$ da Meta Planejada da UF**.
* **Ações Qualitativas / Continuadas (Meta = 0):** Ação cumprida se houver esforço comprovado ($\text{Dias\_Gastos\_Exec} > 0$) e ao menos uma atividade finalizada com processo SEI.

### 7.2 A Obrigatoriedade do Processo SEI (`Doc_Probatorio_Exec`)

Nenhuma atividade é homologada sem a inserção do número de processo ou documento probatório no SEI (Relatório de Viagem, Informação Técnica, Termo de Vistoria):

* **Sem SEI:** A atividade permanece como *🟡 Sem Documento de Conclusão*, não pontua para o cumprimento da meta da Ação e gera pendência de auditoria.

### 7.3 Semáforo de Status das Ações Estaduais

| Status de Execução | Marcador | Regra de Enquadramento Operacional |
| --- | --- | --- |
| **Planejada** | ⚪ | Ação ativa dentro do cronograma vigente, aguardando execução ou lançamento das missões. |
| **Executada** | 🟢 | Meta física atingida ($\ge 80\%$ da meta da UF ou esforço comprovado em ações qualitativas), com atividades concluídas e SEI registrado. |
| **Não Executada - Sem Justificativa** | 🔴 | Prazo cronológico encerrado sem alcance da meta mínima de 80% e sem justificativa técnica. |
| **Cancelada - Sem Justificativa** | 🔴 | Ação assinalada como cancelada, porém com o campo de justificativa em branco. |
| **Cancelada (Justificada)** | 🟡 | Ação cancelada pela gestão regional contendo fundamentação técnica registrada. |

### 7.4 Semáforo de Status das Atividades de Campo

| Status da Atividade | Marcador | Descrição e Validação |
| --- | --- | --- |
| **Concluída** | 🟢 | Atividade executada e com o processo SEI preenchido no campo `Doc_Probatorio_Exec`. |
| **Sem Documento de Conclusão** | 🟡 | Atividade marcada como concluída, mas com o campo SEI vazio (pendência documental). |
| **Prevista** | 🔵 | Missão programada dentro da janela temporal de execução. |
| **Atrasada** | 🔴 | Data de término expirada sem conclusão ou justificativa registrada no sistema. |

---

## 8. Gestão de Prazos, Mural de Pendências e Justificativas

### 8.1 Identificação Automática de Atrasos

O sistema compara diariamente a data de término com a data corrente: se o prazo expirou e a atividade permanece no status *Prevista*, ela é enquadrada automaticamente como **🔴 Atrasada**.

### 8.2 Regularização de Não Execução

Caso uma missão não ocorra (fatores climáticos, contingenciamento orçamentário ou cancelamento de operação):

1. Acesse **📊 Visualizar Base** > **📌 Atividades de Campo**.
2. Selecione a linha da atividade e abra o painel de edição.
3. Altere o andamento e preencha a lista oficial de **Justificativa da Ação**.
4. O sistema regulariza o registro para **🟡 Não Executada (Justificada)**.

---

## 9. Orçamento, Diárias, Passagens e PCDP

### 9.1 Estrutura Orçamentária: Planejado vs. Executado

* **Recursos Planejados:** Estimativa lançada na elaboração da Ação ou Atividade (previsão de Diárias, Passagens e Outras Despesas).
* **Recursos Executados:** Totalização financeira real a partir do lançamento das diárias e passagens pagas a cada servidor.

### 9.2 Registro Individualizado por Servidor

Como a inserção em lote gera uma linha individual para cada agente da missão, os custos são alocados com precisão:

* **Qtd. de Diárias e Valor de Diárias (R$)**
* **Valor de Passagens (R$)**
* **Número da PCDP (SCDP)**
* **Dias de Campo Efetivos**

---

## 10. Produtividade em Lote e Filtros Avançados

### 10.1 Inserção Multi-Servidor (Lote)

Permite cadastrar missões conjuntas rapidamente:

1. No formulário `➕ Inserir Nova Linha` (Nível: Atividade), preencha os dados comuns da missão.
2. Na aba de carga em lote, selecione todos os servidores participantes via *multiselect*.
3. O sistema cria uma linha individual para cada servidor no SharePoint, todas compartilhando o mesmo `Codigo_Atividade`.

### 10.2 Edição em Lote na Central de Visualização

1. Na tabela de **Ações** ou **Atividades**, marque as caixas de seleção na primeira coluna.
2. No painel inferior de edição em lote, marque os atributos que deseja sobrescrever (ex: *Data de Término*, *Doc SEI*, *Andamento*).
3. Clique em **Confirmar e Aplicar Alterações em Massa**. Os dados individuais dos servidores (`Fiscal`, `AEAC`, `Função`) são preservados.

---

## 11. Dashboards Executivos e Consolidação Nacional

O módulo **`📈 Dashboards Executivos`** consolida o desempenho físico e financeiro do PNAPA em tempo real.

### 11.1 Tabela 1: Status de Execução Geral do PNAPA (Por UF e Nacional)

Avalia a taxa de sucesso das 27 UFs e do país com base na quantidade de ações que atingiram a régua de **$\ge 80\%$ de cumprimento físico**:

$$\% \text{ de Ações Executadas da UF} = \left( \frac{\text{Ações com Meta Atingida na UF}}{\text{Total de Ações Planejadas pela UF}} \right) \times 100$$

* **Consolidado Global (🇧🇷 NACIONAL):** Não é uma média simples das UFs. Uma ação nacional só pontua como cumprida se a soma das entregas de todos os estados atingir $\ge 80\%$ da meta nacional somada:

$$\% \text{ Executadas Nacional} = \left( \frac{\text{Ações Nacionais com Meta Global } \ge 80\%}{\text{Total de Ações Nacionais no País}} \right) \times 100$$



### 11.2 Régua Semafórica da Tabela 2 (Por Ação)

| Faixa Percentual | Cor de Fundo | Significado Operacional |
| --- | --- | --- |
| **$\ge 100\%$** | 🔵 **Azul** | **Meta Totalmente Cumprida / Superada** |
| **$80,0\%$ a $99,9\%$** | 🟢 **Verde** | **Meta Atingida (Faixa de Conformidade PNAPA)** |
| **$50,0\%$ a $79,9\%$** | 🟡 **Amarelo** | **Execução Parcial / Atenção** |
| **$< 50,0\%$** | 🔴 **Vermelho** | **Execução Crítica / Insuficiente** |

---

## 12. Central de Sugestões, Melhorias e Suporte

### 12.1 Reporte Formal via Sistema (`💡 Sugestões & Melhorias`)

Todas as inconsistências, ideias e solicitações devem ser enviadas pela própria plataforma:

1. Acesse o menu **💡 Sugestões & Melhorias** > aba **➕ Enviar Nova Sugestão**.
2. Indique o módulo relacionado, a prioridade (`Alta`, `Média` ou `Baixa`), o título e o detalhamento.
3. O chamado é indexado no repositório de governança e despachado pelo Administrador no **Quadro de Acompanhamento**.

### 12.2 Canais de Apoio ao Usuário

1. **Assistente Virtual Nativo (`🤖 Assistente Virtual`):** Atendimento interativo 24/7 com inteligência artificial para consulta rápida de regras de negócio, tetos operacionais, senhas padrão e navegação.
2. **Central de Sugestões:** Canal para reporte de falhas e requisições de melhoria.
3. **Ponto Focal Regional:** Multiplicador da Superintendência para alinhamento de equipe e validação de permissões.
