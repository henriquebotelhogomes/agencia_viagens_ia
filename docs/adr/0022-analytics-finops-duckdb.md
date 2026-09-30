# ADR-0022 — Analytics & FinOps Colunar: DuckDB e Armazenamento Parquet

- **Status**: Aceita
- **Data**: 2026-09-29
- **Contexto do PRD**: D8, D12
- **Alinhamento do Harness**: `~/.gemini/config/resources.md` (§3) e `GEMINI.md` (§1, §2)

## Contexto e problema

O painel de controle de FinOps do Voyager AI (`/v1/finops` e interface web no Next.js) exibe métricas agregadas de consumo de tokens, custo estimado em USD e economia frente ao baseline do GPT-4o.

Atualmente, essas informações são calculadas por consultas relacionais em tempo real no PostgreSQL (`src/db/models.py`) ou computadas em memória. Conforme o histórico de execuções aumenta, esse padrão apresenta atritos:

1. **Conflito de Carga OLTP vs. OLAP:** O banco relacional PostgreSQL deve focar em operações transacionais transientes (estado da execução, rollback de versões e controle de concorrência). Executar queries de agregação analítica complexa (percentis, médias móveis de 90 dias, agrupamentos multidimensionais por modelo de IA) sobrecarrega o banco de produção.
2. **Custo e Complexidade de Data Warehouses Externos:** Subir um BigQuery ou Snowflake para um projeto de portfólio serverless é inviável financeiramente e viola a política de Scale-to-Zero ($0/mês).

## Opções consideradas

### 1. Manter agregações no PostgreSQL (status quo)

- ✅ Não introduz bibliotecas adicionais.
- ❌ Baixa performance analítica em datasets crescentes; concorrência de I/O com a escrita das tarefas do worker.

### 2. Banco analítico externo em nuvem (BigQuery / ClickHouse Cloud)

- ✅ Escalabilidade infinita.
- ❌ Custo mensal mínimo ou risco de cobrança acidental; complexidade excessiva de IAM e conectores.

### 3. DuckDB embutido lendo arquivos colunares Parquet (Padrão Harness)

- ✅ **Zero-Daemon & Custo Zero:** Motor analítico colunar executado no próprio processo Python, sem servidores em background ociosos.
- ✅ **Performance OLAP Extrema:** Leitura vetorizada de arquivos `.parquet` particionados em microssegundos.
- ✅ **Integração com Polars/Pandas:** Análise instantânea de séries temporais de consumo de tokens e benchmarking comparativo entre modelos.

## Decisão

Adotar o **DuckDB** com armazenamento particionado em **Apache Parquet (`.parquet`)** para a camada analítica de FinOps:

1. **Exportação Assíncrona de Telemetria:** Ao término de cada execução no worker SAQ, os metadados consolidados de consumo (`prompt_tokens`, `completion_tokens`, `cost_usd`, `model`, `latency_seconds`) são gravados em registros particionados por data em formato `.parquet`.
2. **Consultas Analíticas Instantâneas:** O endpoint `/v1/finops` utiliza o DuckDB em memória para computar métricas consolidadas, taxas de economia e distribuições estatísticas diretamente dos arquivos colunares.
3. **Desacoplamento Arquitetural:** O banco PostgreSQL permanece estritamente transacional (OLTP), blindado contra lentidão por consultas analíticas.

## Consequências

### Positivas

- **Consultas em Milissegundos:** Agregações sobre milhares de execuções processadas em <10ms.
- **Portabilidade de Dados:** Arquivos `.parquet` podem ser facilmente versionados, inspecionados em notebooks ou baixados diretamente para auditoria.
- **Zero Custo de Infraestrutura:** Elimina a necessidade de manter serviços analíticos externos rodando 24/7.

### Negativas / Mitigações

- **Sincronização de Arquivos em Ambientes Serverless Efêmeros:** No Cloud Run com Scale-to-Zero, o sistema de arquivos local é efêmero por container. Mitigada mantendo o PostgreSQL como fonte da verdade de longo prazo, com geração sob demanda de tabelas analíticas DuckDB em cache ou persistência em bucket de baixo custo quando necessário.
