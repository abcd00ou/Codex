# AI Supply Chain Study Agent System (prompt.md)

---

# Objective

Build a structured, data-driven AI supply chain intelligence system to:

* Quantify how **token demand translates into hardware demand**
* Identify **real bottlenecks (HBM, packaging, power, network)**
* Track **hyperscaler investment dynamics**
* Analyze **supply-demand imbalance across the value chain**
* Support **forward-looking investment strategy**

---

# Core Reference: Value Chain + Dynamics Mapping

## AI Supply Chain Framework (Anchor Table)

| Layer        | Component                    | KPI                  | Token Increase Impact | Bottleneck   | Investment Signal | Key Players         |
| ------------ | ---------------------------- | -------------------- | --------------------- | ------------ | ----------------- | ------------------- |
| End Customer | ChatGPT, Agents, Physical AI | Tokens/day, Users    | Demand explosion      | -            | ARPU growth       | OpenAI              |
| AI Service   | API, SaaS                    | Tokens/sec, cost     | Inference load UP     | Cost         | Efficiency        | Anthropic           |
| Cloud / DC   | GPU cluster                  | Utilization, latency | Capex UP              | Power        | DC expansion      | Microsoft Azure     |
| System       | GPU servers                  | Throughput           | Scale-up              | Interconnect | Rack design       | NVIDIA              |
| GPU          | H100, B200                   | TFLOPS               | Demand UP             | Supply       | Core compute      | NVIDIA, AMD         |
| HBM          | HBM3e                        | BW, capacity         | **Explosive UP**      | Packaging    | Critical          | SK Hynix            |
| DRAM         | DDR5                         | Capacity             | Moderate UP           | Cycle        | Stable            | Samsung Electronics |
| SSD          | NVMe                         | IOPS                 | RAG UP                | NAND price   | AI storage        | Solidigm            |
| CPU          | Xeon, EPYC                   | I/O                  | Linear UP             | -            | Infra             | Intel               |
| Network      | IB / Ethernet                | Bandwidth            | Cluster UP            | Switch       | Critical          | Broadcom            |
| Packaging    | CoWoS                        | Yield                | **Bottleneck**        | Capacity     | Key constraint    | TSMC                |
| Power        | Grid                         | MW                   | DC limit              | Grid         | Infra             | Schneider           |
| ASIC         | TPU, Trainium, Maia          | TFLOPS/W             | Custom silicon UP     | Design cycle | Efficiency        | Google, AWS, MSFT   |
| Edge AI      | NPU, Mobile AI               | TOPS/W               | Inference at edge     | Power budget | Diversification   | Qualcomm, Apple     |
| Sovereign AI | National GPU clusters        | National compute     | Policy-driven demand  | Access       | Government spend  | UAE, Saudi, EU      |

---

## Core Dynamics Equation

```text
Token UP -> Inference UP -> GPU UP
-> HBM UP-UP -> Packaging bottleneck
-> Data Center Capex UP -> Power bottleneck
-> Cloud structure shift (Multi-cloud / Sovereign AI)
-> Edge AI / Physical AI (next wave)
```

---

## Supplementary Layers (2025-2026 additions)

### Sovereign AI Trend
- UAE: $100B AI investment plan (G42 + Microsoft)
- Saudi Arabia: NEOM + ARAMCO AI clusters, NVIDIA deal $600M+
- EU: AI Gigafactory initiative (EUR 20B+)
- Japan: RAPIDUS + domestic AI cluster push
- India: IndiaAI Mission ($1.25B)
- Impact: Additional 15-20% GPU demand beyond hyperscaler baseline

### Edge AI / Physical AI Layer
- Robotics: Figure, Boston Dynamics, 1X - each robot ~10 TOPS local
- Automotive: NVIDIA DRIVE Thor, Qualcomm Snapdragon Ride
- Industrial: Predictive maintenance + vision inference at edge
- Consumer: On-device LLM (Apple Intelligence, Gemini Nano)
- Scale: 1B+ edge AI devices by 2027 (IDC estimate)

### Power Infrastructure Supply Chain Detail
- Transformers: ABB, Siemens Energy, Hitachi (2-3 year lead time)
- Cooling: Vertiv liquid cooling, Eaton, Schneider Electric
- UPS: Eaton 9900, APC by Schneider
- Generators: Cummins, Caterpillar (diesel backup)
- Grid interconnection: 3-5 year permitting timeline in US
- Key constraint: Transformer shortage persists through 2026

### ASIC Layer (Custom Silicon)
- Google TPU v5e/v5p: 100+ ExaFLOPS deployed, 2x efficiency vs H100
- AWS Trainium2: 2x perf/cost vs H100 for training
- Microsoft Maia 100: Azure-specific LLM training chip
- Meta MTIA v2: Recommendation + inference ASIC
- Apple Neural Engine: 38 TOPS in M4, on-device AI
- Impact: 20-30% of hyperscaler AI workloads shifting to custom ASICs by 2027

---

# System Architecture

```text
[Data Agent]       <- Web scraping + seed data
    |
[Mapping Agent]    <- Value chain knowledge graph
    |
[Modeling Agent]   <- Token -> Hardware quantification
    |
[Bottleneck Agent] <- Demand/capacity ratio, cascade prediction
    |
[Strategy Agent]   <- Investment signals, phase positioning
    |
[Report Agent]     <- HTML dashboard + PPT
```

---

# Agent Definitions

---

## 1. Data Intelligence Agent

### Role

Collect:

* Token demand signals (usage, context, AI features)
* Hyperscaler CapEx
* Supply chain updates (HBM, GPU, packaging)
* Earnings / guidance

### Output

```json
{
  "events": [
    {
      "event": "capex",
      "company": "Microsoft",
      "value": 80000000000,
      "year": 2025,
      "source": "earnings"
    },
    {
      "event": "supply_constraint",
      "component": "HBM",
      "severity": "critical",
      "detail": "CoWoS capacity tight"
    }
  ],
  "last_updated": "2026-03-23"
}
```

### Skills

* Web scraping (requests + BeautifulSoup)
* Seed data loading with fallback
* NLP event classification
* Source validation

---

## 2. Supply Chain Mapping Agent

### Role

Map companies to the value chain, build dependency graph

### Output

```json
{
  "NVIDIA": {
    "layer": "gpu_server",
    "tier": 1,
    "upstream": ["TSMC", "SK Hynix", "Broadcom"],
    "downstream": ["Microsoft Azure", "AWS"]
  }
}
```

### Skills

* Knowledge graph construction
* Tier classification (1/2/3)
* Upstream/downstream dependency analysis

---

## 3. Quant Modeling Agent

### Role

Translate token demand to hardware demand quantitatively

### Core Models

#### Model 1: Token to GPU

```python
GPU_needed = Tokens_per_day / (86400 * GPU_tokens_per_sec * utilization)
```

#### Model 2: GPU to HBM

```python
HBM_demand_GB = GPU_count * HBM_per_GPU_GB
```

#### Model 3: Memory Pressure (Context Length)

```python
KV_cache_GB = (context_length * concurrent_users * bytes_per_token * 2) / 1e9
```

#### Model 4: SSD Demand (RAG + Vector DB)

```python
storage_GB = (tokens_per_day * rag_ratio / avg_doc_tokens) * avg_doc_tokens * bytes_per_token / 1e9
```

#### Model 5: Power Demand

```python
power_MW = GPU_count * TDP_W * server_overhead * PUE / 1e6
```

### Scenario Analysis
- Bear: growth_rate * 0.7
- Base: growth_rate * 1.0
- Bull: growth_rate * 1.5

---

## 4. Bottleneck Detection Agent

### Role

Identify supply constraints and predict cascade effects

### Output

```json
{
  "current_bottleneck": "HBM",
  "utilization": 0.95,
  "severity": "critical",
  "next_bottleneck": "Power",
  "resolution_timeline_months": 12,
  "cascade_risk": ["CoWoS -> HBM -> GPU supply chain"],
  "investment_window": "H2 2025 - H1 2026"
}
```

### Logic

* Demand vs capacity ratio by layer
* CURRENT_CAPACITY_UTILIZATION scoring
* Cascade prediction (current -> next -> after)
* Resolution timeline based on capacity expansion plans

---

## 5. Strategy / Investment Agent

### Role

Generate investment insights based on bottleneck analysis

### Output

```json
{
  "investment_signals": [
    {
      "company": "SK Hynix",
      "layer": "HBM",
      "signal": "Strong Buy",
      "thesis": "HBM3e critical bottleneck, 95% utilization, 2.5x demand growth",
      "catalyst": "GB200 ramp H2 2025",
      "risk": "Samsung capacity catch-up, CoWoS yield risk",
      "timeframe": "6-18 months"
    }
  ],
  "phase_position": "Phase 2 (HBM)",
  "key_themes": ["Memory upcycle", "Power infra scarcity", "Sovereign AI"]
}
```

---

## 6. Report / Visualization Agent

### Role

Generate HTML dashboard and PPT presentation

### HTML Dashboard Sections
1. AI Supply Chain Value Chain visualization (bottleneck colors)
2. Token demand to hardware demand conversion table
3. Current/next bottleneck analysis cards
4. Hyperscaler CapEx trend (ASCII bar chart)
5. Investment signal table
6. Scenario-based 2025-2027 demand forecast

### PPT Slides
1. Cover slide
2. Value Chain Overview (bottleneck highlights)
3. Token to Hardware Demand model
4. Bottleneck status and cascade prediction
5. Hyperscaler CapEx trends
6. Investment signals and positioning
7. Risk factors
8. 2025-2027 demand forecast scenarios

---

# Workflow

```text
1. Data collection (web scraping + seed data)
2. Supply chain mapping (knowledge graph)
3. Demand modeling (quantitative models)
4. Bottleneck detection (utilization scoring)
5. Strategy generation (investment signals)
6. Visualization (HTML + PPT)
```

---

# Key Metrics

## Demand
* Tokens/day
* Context length
* Concurrent sessions

## Infrastructure
* GPU utilization
* Power usage (MW)
* DC capacity (GW)

## Hardware
* HBM capacity (GB, market share)
* GPU shipments (units)
* SSD usage (EB)

---

# Critical Bottlenecks (2025-2026)

1. HBM (Memory) - 95% utilization
2. Packaging (CoWoS) - 92% utilization
3. Power / Grid - transformer shortage
4. Network - InfiniBand capacity
5. Data center capacity - permitting delays

---

# Investment Phases

| Phase | Focus              | Timeframe    | Key Players            |
| ----- | ------------------ | ------------ | ---------------------- |
| 1     | GPU                | 2023-2024    | NVIDIA, AMD            |
| 2     | HBM                | 2024-2025    | SK Hynix, Micron       |
| 3     | Power / Infra      | 2025-2026    | Vertiv, Schneider, GEV |
| 4     | Edge / Physical AI | 2026-2027    | Qualcomm, Arm, ASML    |

---

# Continuous Loop

```text
New Data -> Model Update -> Bottleneck Shift -> Strategy Update
```

---

# Final Objective

Answer:

* Where is demand moving?
* What breaks first?
* Who captures value?
* What should be invested next?

---

## Amendments from Initial prompt.md (v2 additions)

The following sections were added to enhance the original framework:

1. **Sovereign AI Trend**: UAE, Saudi Arabia, EU, Japan, India government AI investments creating 15-20% incremental GPU demand beyond hyperscaler baseline.

2. **Edge AI / Physical AI Layer**: Robotics, automotive, industrial, and consumer edge AI devices creating new inference demand layer distinct from cloud.

3. **Power Infrastructure Detail**: Transformer supply chain (2-3 year lead time), cooling systems, UPS, and grid interconnection as separate bottleneck analysis layer.

4. **ASIC Layer**: Google TPU, AWS Trainium, Microsoft Maia, Meta MTIA as efficiency-driven displacement of commodity GPU for specific workloads (20-30% shift by 2027).

---

## 투자 네트워크 분석 (보완 추가)

투자 관계, 하드웨어 공급, VC 투자를 시각화하여 자금 흐름과 의존성 구조 파악

| 관계 유형 | 색상 | 주요 사례 |
|---------|------|---------|
| Investment | 핑크 | NVIDIA→OpenAI $100B, Microsoft→OpenAI $13B+ |
| Hardware Supply | 청록 | SK Hynix→NVIDIA HBM3e 독점, TSMC→NVIDIA CoWoS |
| Service | 파랑 | OpenAI→Oracle $30B 클라우드 계약 |
| VC | 초록 | OpenAI→Figure AI $675M, OpenAI→Anysphere |

---

## 보고서 유형 (보완 추가)

| 유형 | 형식 | 대상 | 내용 |
|------|------|------|------|
| HTML 대시보드 | 인터랙티브 웹 | 실시간 모니터링 | D3.js 네트워크 그래프 포함 |
| PPT | 8슬라이드 | 임원 보고 | Value Chain → 병목 → 투자 시그널 |
| Word | 7장 학습 문서 | 심층 스터디 | 수식·데이터·참고URL 포함 |

---

## 데이터베이스 (보완 추가)

PostgreSQL `ai_scm` DB (9개 테이블):
- 시계열 병목 추적 (bottleneck_scores)
- 투자 시그널 히스토리 (investment_signals)
- 네트워크 그래프 스냅샷 (network_nodes, network_edges)
- 수요 예측 버전 관리 (model_results)

---

## Sovereign AI & Edge AI (보완 추가)

| 카테고리 | 내용 | 수혜 기업 |
|---------|------|---------|
| Sovereign AI | 각국 정부 자체 AI 인프라 구축 (UAE, 사우디, EU, 일본) | NVIDIA, HPE, Dell |
| Edge AI | 스마트폰·자동차·로봇 AI 칩 | 퀄컴, Apple, NVIDIA Orin |
| Physical AI | 로봇·자율주행 AI | Figure AI, Tesla, Boston Dynamics |

---

## 전력 인프라 세부 공급망 (보완 추가)

```
전력 수요 → 변전소(변압기) → UPS → 냉각(에어/액냉) → PDU → GPU 서버
수혜 기업: Vertiv (UPS·냉각), Eaton (PDU), Schneider (통합 인프라), GE Vernova (변압기)
변압기 리드타임: 2-3년 → 전력 병목의 구조적 원인
```
