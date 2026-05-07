# AI Supply Chain Global Dynamics Model

**Report date:** 2026-05-04  
**Model as-of date:** 2026-04-28  
**Status:** Research model, evidence-linked, not affiliated with Oxford Economics.

## Executive View

This report applies a macro-scenario style framework to the AI infrastructure supply chain. It is inspired by the public description of globally integrated scenario models, where shocks propagate through linked demand, supply, price, capacity, and investment channels. It does **not** reproduce Oxford Economics' proprietary Global Economic Model.

The base case shows a near-balanced 2026 HBM market: base HBM gap is **0.99x**, with full modeled fulfillment because no layer exceeds 1.0x. The bull case crosses into shortage: 2026 HBM gap rises to **1.27x**, fulfillment falls to **79%**, and unserved accelerator demand reaches **1,038,363 H100-equivalent units**.

## 1. Declared Model Structure

The model is a linked system:

```text
AI workload demand
  -> token volume
  -> accelerator utilization demand
  -> hyperscaler CapEx procurement demand
  -> effective accelerator demand
  -> HBM, CoWoS, power, networking, and storage demand
  -> supply gap ratios
  -> fulfillment, backlog, and price-pressure indexes
```

All variables below are annual unless stated otherwise.

## 1A. Chain Graph


<figure id="chain-graph" class="chain-graph">
<svg viewBox="0 0 1160 560" role="img" aria-label="AI supply chain formula graph with companies">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#486581"/>
    </marker>
  </defs>
  <rect x="18" y="12" width="1124" height="532" rx="10" fill="#F8FAFC" stroke="#BCCCDC"/>
  <text x="42" y="46" class="graph-title">Formula Chain: AI Demand to Supply Bottlenecks</text>
  
  <g class="edge">
    <line x1="265" y1="125" x2="320" y2="125" marker-end="url(#arrow)"/>
    <text x="292.5" y="117.0" text-anchor="middle">tokens / throughput</text>
  </g>
  <g class="edge">
    <line x1="265" y1="265" x2="590" y2="195" marker-end="url(#arrow)"/>
    <text x="427.5" y="222.0" text-anchor="middle">CapEx * shares / ASP</text>
  </g>
  <g class="edge">
    <line x1="525" y1="125" x2="590" y2="195" marker-end="url(#arrow)"/>
    <text x="557.5" y="152.0" text-anchor="middle">max(util, procurement)</text>
  </g>
  <g class="edge">
    <line x1="810" y1="195" x2="900" y2="63" marker-end="url(#arrow)"/>
    <text x="855.0" y="121.0" text-anchor="middle">* HBM GB</text>
  </g>
  <g class="edge">
    <line x1="810" y1="195" x2="900" y2="161" marker-end="url(#arrow)"/>
    <text x="855.0" y="170.0" text-anchor="middle">* CoWoS coef</text>
  </g>
  <g class="edge">
    <line x1="810" y1="195" x2="900" y2="259" marker-end="url(#arrow)"/>
    <text x="855.0" y="219.0" text-anchor="middle">* TDP * overhead * PUE</text>
  </g>
  <g class="edge">
    <line x1="810" y1="195" x2="900" y2="357" marker-end="url(#arrow)"/>
    <text x="855.0" y="268.0" text-anchor="middle">* fabric coef</text>
  </g>
  <g class="edge">
    <line x1="265" y1="125" x2="900" y2="455" marker-end="url(#arrow)"/>
    <text x="582.5" y="282.0" text-anchor="middle">* RAG ratio</text>
  </g>
  <g class="edge">
    <line x1="900" y1="63" x2="810" y2="420" marker-end="url(#arrow)"/>
    <text x="855.0" y="233.5" text-anchor="middle">demand / supply</text>
  </g>
  <g class="edge">
    <line x1="900" y1="161" x2="810" y2="420" marker-end="url(#arrow)"/>
    <text x="855.0" y="282.5" text-anchor="middle">demand / supply</text>
  </g>
  <g class="edge">
    <line x1="900" y1="259" x2="810" y2="420" marker-end="url(#arrow)"/>
    <text x="855.0" y="331.5" text-anchor="middle">demand / supply</text>
  </g>
  <g class="edge">
    <line x1="900" y1="357" x2="810" y2="420" marker-end="url(#arrow)"/>
    <text x="855.0" y="380.5" text-anchor="middle">demand / supply</text>
  </g>
  <g class="edge">
    <line x1="900" y1="455" x2="810" y2="420" marker-end="url(#arrow)"/>
    <text x="855.0" y="429.5" text-anchor="middle">demand / supply</text>
  </g>
  
  <g class="node">
    <rect x="60" y="82" width="205" height="86" rx="8" fill="#1C7ED6" opacity="0.94"/>
    <text x="162.5" y="107" text-anchor="middle" class="node-title">Token Demand</text>
    <text x="162.5" y="130" text-anchor="middle" class="node-subtitle">tokens/day</text>
    <text x="162.5" y="151" text-anchor="middle" class="node-company">OpenAI, Anthropic, Meta, xAI</text>
  </g>
  <g class="node">
    <rect x="60" y="222" width="205" height="86" rx="8" fill="#5F3DC4" opacity="0.94"/>
    <text x="162.5" y="247" text-anchor="middle" class="node-title">CapEx Procurement</text>
    <text x="162.5" y="270" text-anchor="middle" class="node-subtitle">prebuild demand</text>
    <text x="162.5" y="291" text-anchor="middle" class="node-company">MSFT, AWS, Google, Oracle</text>
  </g>
  <g class="node">
    <rect x="320" y="82" width="205" height="86" rx="8" fill="#1971C2" opacity="0.94"/>
    <text x="422.5" y="107" text-anchor="middle" class="node-title">Utilization Demand</text>
    <text x="422.5" y="130" text-anchor="middle" class="node-subtitle">tokens -&gt; GPUs</text>
    <text x="422.5" y="151" text-anchor="middle" class="node-company">AI services + cloud GPUs</text>
  </g>
  <g class="node">
    <rect x="590" y="148" width="220" height="94" rx="8" fill="#2B8A3E" opacity="0.94"/>
    <text x="700.0" y="173" text-anchor="middle" class="node-title">Accelerator Demand</text>
    <text x="700.0" y="196" text-anchor="middle" class="node-subtitle">gap 0.85x</text>
    <text x="700.0" y="217" text-anchor="middle" class="node-company">NVIDIA, AMD, ASICs</text>
  </g>
  <g class="node">
    <rect x="900" y="24" width="190" height="78" rx="8" fill="#F08C00" opacity="0.94"/>
    <text x="995.0" y="49" text-anchor="middle" class="node-title">HBM</text>
    <text x="995.0" y="72" text-anchor="middle" class="node-subtitle">gap 0.99x</text>
    <text x="995.0" y="93" text-anchor="middle" class="node-company">SK Hynix, Samsung, Micron</text>
  </g>
  <g class="node">
    <rect x="900" y="122" width="190" height="78" rx="8" fill="#2B8A3E" opacity="0.94"/>
    <text x="995.0" y="147" text-anchor="middle" class="node-title">CoWoS / Foundry</text>
    <text x="995.0" y="170" text-anchor="middle" class="node-subtitle">gap 0.66x</text>
    <text x="995.0" y="191" text-anchor="middle" class="node-company">TSMC, ASE, Amkor</text>
  </g>
  <g class="node">
    <rect x="900" y="220" width="190" height="78" rx="8" fill="#2B8A3E" opacity="0.94"/>
    <text x="995.0" y="245" text-anchor="middle" class="node-title">Power</text>
    <text x="995.0" y="268" text-anchor="middle" class="node-subtitle">gap 0.87x</text>
    <text x="995.0" y="289" text-anchor="middle" class="node-company">Vertiv, Eaton, Schneider</text>
  </g>
  <g class="node">
    <rect x="900" y="318" width="190" height="78" rx="8" fill="#2B8A3E" opacity="0.94"/>
    <text x="995.0" y="343" text-anchor="middle" class="node-title">Networking</text>
    <text x="995.0" y="366" text-anchor="middle" class="node-subtitle">gap 0.80x</text>
    <text x="995.0" y="387" text-anchor="middle" class="node-company">Broadcom, Marvell, Arista</text>
  </g>
  <g class="node">
    <rect x="900" y="416" width="190" height="78" rx="8" fill="#2B8A3E" opacity="0.94"/>
    <text x="995.0" y="441" text-anchor="middle" class="node-title">Storage Flow</text>
    <text x="995.0" y="464" text-anchor="middle" class="node-subtitle">gap 0.00x</text>
    <text x="995.0" y="485" text-anchor="middle" class="node-company">Solidigm, Samsung SSD</text>
  </g>
  <g class="node">
    <rect x="590" y="372" width="220" height="96" rx="8" fill="#364FC7" opacity="0.94"/>
    <text x="700.0" y="397" text-anchor="middle" class="node-title">Fulfillment / Backlog</text>
    <text x="700.0" y="420" text-anchor="middle" class="node-subtitle">100% fulfilled; 0 unserved</text>
    <text x="700.0" y="441" text-anchor="middle" class="node-company">Customer allocation risk</text>
  </g>
  <text x="42" y="526" class="graph-note">Color key: green = surplus, orange = near/tight, red = shortage. Company labels are representative exposure points, not exhaustive coverage.</text>
</svg>
<svg viewBox="0 0 1240 520" role="img" aria-label="Representative company relationship graph">
  <defs>
    <marker id="arrow2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#486581"/>
    </marker>
  </defs>
  <rect x="18" y="12" width="1204" height="488" rx="10" fill="#F8FAFC" stroke="#BCCCDC"/>
  <text x="42" y="46" class="graph-title">Representative Company Links: Demand, Cloud, Accelerators, and Bottlenecks</text>
  <text x="155" y="74" text-anchor="middle" class="company-column">AI demand</text>
  <text x="395" y="54" text-anchor="middle" class="company-column">Cloud / GPU procurement</text>
  <text x="640" y="82" text-anchor="middle" class="company-column">Accelerators</text>
  <text x="890" y="40" text-anchor="middle" class="company-column">HBM / Foundry / Packaging</text>
  <text x="1130" y="90" text-anchor="middle" class="company-column">Infrastructure</text>
  
  <g class="company-edge">
    <line x1="155" y1="120" x2="395" y2="100" marker-end="url(#arrow2)" stroke="#6741D9"/>
    <text x="275.0" y="106.0" text-anchor="middle">strategic cloud</text>
  </g>
  <g class="company-edge">
    <line x1="155" y1="120" x2="395" y2="340" marker-end="url(#arrow2)" stroke="#6741D9"/>
    <text x="275.0" y="226.0" text-anchor="middle">$30B cloud</text>
  </g>
  <g class="company-edge">
    <line x1="155" y1="120" x2="395" y2="420" marker-end="url(#arrow2)" stroke="#6741D9"/>
    <text x="275.0" y="266.0" text-anchor="middle">GPU cloud</text>
  </g>
  <g class="company-edge">
    <line x1="155" y1="200" x2="395" y2="180" marker-end="url(#arrow2)" stroke="#6741D9"/>
    <text x="275.0" y="186.0" text-anchor="middle">strategic compute</text>
  </g>
  <g class="company-edge">
    <line x1="155" y1="200" x2="395" y2="260" marker-end="url(#arrow2)" stroke="#6741D9"/>
    <text x="275.0" y="226.0" text-anchor="middle">cloud compute</text>
  </g>
  <g class="company-edge">
    <line x1="155" y1="280" x2="640" y2="140" marker-end="url(#arrow2)" stroke="#C92A2A"/>
    <text x="397.5" y="206.0" text-anchor="middle">GPU purchase</text>
  </g>
  <g class="company-edge">
    <line x1="155" y1="360" x2="640" y2="140" marker-end="url(#arrow2)" stroke="#C92A2A"/>
    <text x="397.5" y="246.0" text-anchor="middle">Colossus GPUs</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="100" x2="640" y2="140" marker-end="url(#arrow2)" stroke="#C92A2A"/>
    <text x="517.5" y="116.0" text-anchor="middle">GPU supply</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="180" x2="640" y2="140" marker-end="url(#arrow2)" stroke="#C92A2A"/>
    <text x="517.5" y="156.0" text-anchor="middle">GPU supply</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="260" x2="640" y2="140" marker-end="url(#arrow2)" stroke="#C92A2A"/>
    <text x="517.5" y="196.0" text-anchor="middle">GPU supply</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="340" x2="640" y2="140" marker-end="url(#arrow2)" stroke="#C92A2A"/>
    <text x="517.5" y="236.0" text-anchor="middle">GPU supply</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="420" x2="640" y2="140" marker-end="url(#arrow2)" stroke="#C92A2A"/>
    <text x="517.5" y="276.0" text-anchor="middle">GPU supply</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="100" x2="640" y2="250" marker-end="url(#arrow2)" stroke="#E8590C"/>
    <text x="517.5" y="171.0" text-anchor="middle">MI300/MI325</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="180" x2="640" y2="250" marker-end="url(#arrow2)" stroke="#E8590C"/>
    <text x="517.5" y="211.0" text-anchor="middle">GPU/ASIC mix</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="260" x2="640" y2="360" marker-end="url(#arrow2)" stroke="#E8590C"/>
    <text x="517.5" y="306.0" text-anchor="middle">TPU demand</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="180" x2="640" y2="360" marker-end="url(#arrow2)" stroke="#E8590C"/>
    <text x="517.5" y="266.0" text-anchor="middle">Trainium</text>
  </g>
  <g class="company-edge">
    <line x1="640" y1="140" x2="890" y2="80" marker-end="url(#arrow2)" stroke="#F08C00"/>
    <text x="765.0" y="106.0" text-anchor="middle">HBM3e/HBM4</text>
  </g>
  <g class="company-edge">
    <line x1="640" y1="140" x2="890" y2="220" marker-end="url(#arrow2)" stroke="#F08C00"/>
    <text x="765.0" y="176.0" text-anchor="middle">HBM3e</text>
  </g>
  <g class="company-edge">
    <line x1="640" y1="140" x2="890" y2="150" marker-end="url(#arrow2)" stroke="#F08C00"/>
    <text x="765.0" y="141.0" text-anchor="middle">qualification</text>
  </g>
  <g class="company-edge">
    <line x1="640" y1="250" x2="890" y2="80" marker-end="url(#arrow2)" stroke="#F08C00"/>
    <text x="765.0" y="161.0" text-anchor="middle">HBM supply</text>
  </g>
  <g class="company-edge">
    <line x1="640" y1="250" x2="890" y2="150" marker-end="url(#arrow2)" stroke="#F08C00"/>
    <text x="765.0" y="196.0" text-anchor="middle">HBM supply</text>
  </g>
  <g class="company-edge">
    <line x1="640" y1="140" x2="890" y2="320" marker-end="url(#arrow2)" stroke="#2B8A3E"/>
    <text x="765.0" y="226.0" text-anchor="middle">foundry</text>
  </g>
  <g class="company-edge">
    <line x1="640" y1="250" x2="890" y2="320" marker-end="url(#arrow2)" stroke="#2B8A3E"/>
    <text x="765.0" y="281.0" text-anchor="middle">foundry</text>
  </g>
  <g class="company-edge">
    <line x1="640" y1="140" x2="890" y2="390" marker-end="url(#arrow2)" stroke="#2B8A3E"/>
    <text x="765.0" y="261.0" text-anchor="middle">advanced package</text>
  </g>
  <g class="company-edge">
    <line x1="640" y1="250" x2="890" y2="390" marker-end="url(#arrow2)" stroke="#2B8A3E"/>
    <text x="765.0" y="316.0" text-anchor="middle">advanced package</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="100" x2="1130" y2="160" marker-end="url(#arrow2)" stroke="#0B7285"/>
    <text x="762.5" y="126.0" text-anchor="middle">fabric</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="180" x2="1130" y2="160" marker-end="url(#arrow2)" stroke="#0B7285"/>
    <text x="762.5" y="166.0" text-anchor="middle">fabric</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="260" x2="1130" y2="160" marker-end="url(#arrow2)" stroke="#0B7285"/>
    <text x="762.5" y="206.0" text-anchor="middle">fabric</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="100" x2="1130" y2="310" marker-end="url(#arrow2)" stroke="#495057"/>
    <text x="762.5" y="201.0" text-anchor="middle">power chain</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="180" x2="1130" y2="310" marker-end="url(#arrow2)" stroke="#495057"/>
    <text x="762.5" y="241.0" text-anchor="middle">power chain</text>
  </g>
  <g class="company-edge">
    <line x1="395" y1="260" x2="1130" y2="310" marker-end="url(#arrow2)" stroke="#495057"/>
    <text x="762.5" y="281.0" text-anchor="middle">power chain</text>
  </g>
  <g class="company-edge">
    <line x1="155" y1="120" x2="1130" y2="440" marker-end="url(#arrow2)" stroke="#1971C2"/>
    <text x="642.5" y="276.0" text-anchor="middle">RAG/storage pull</text>
  </g>
  
  <g class="company-node">
    <rect x="70" y="92" width="170" height="56" rx="8" fill="#1C7ED6"/>
    <text x="155" y="126" text-anchor="middle">OpenAI</text>
  </g>
  <g class="company-node">
    <rect x="70" y="172" width="170" height="56" rx="8" fill="#1C7ED6"/>
    <text x="155" y="206" text-anchor="middle">Anthropic</text>
  </g>
  <g class="company-node">
    <rect x="70" y="252" width="170" height="56" rx="8" fill="#1C7ED6"/>
    <text x="155" y="286" text-anchor="middle">Meta AI</text>
  </g>
  <g class="company-node">
    <rect x="70" y="332" width="170" height="56" rx="8" fill="#1C7ED6"/>
    <text x="155" y="366" text-anchor="middle">xAI</text>
  </g>
  <g class="company-node">
    <rect x="310" y="72" width="170" height="56" rx="8" fill="#5F3DC4"/>
    <text x="395" y="106" text-anchor="middle">Microsoft Azure</text>
  </g>
  <g class="company-node">
    <rect x="310" y="152" width="170" height="56" rx="8" fill="#5F3DC4"/>
    <text x="395" y="186" text-anchor="middle">AWS</text>
  </g>
  <g class="company-node">
    <rect x="310" y="232" width="170" height="56" rx="8" fill="#5F3DC4"/>
    <text x="395" y="266" text-anchor="middle">Google Cloud</text>
  </g>
  <g class="company-node">
    <rect x="310" y="312" width="170" height="56" rx="8" fill="#5F3DC4"/>
    <text x="395" y="346" text-anchor="middle">Oracle Cloud</text>
  </g>
  <g class="company-node">
    <rect x="310" y="392" width="170" height="56" rx="8" fill="#5F3DC4"/>
    <text x="395" y="426" text-anchor="middle">CoreWeave</text>
  </g>
  <g class="company-node">
    <rect x="555" y="112" width="170" height="56" rx="8" fill="#C92A2A"/>
    <text x="640" y="146" text-anchor="middle">NVIDIA</text>
  </g>
  <g class="company-node">
    <rect x="555" y="222" width="170" height="56" rx="8" fill="#C92A2A"/>
    <text x="640" y="256" text-anchor="middle">AMD</text>
  </g>
  <g class="company-node">
    <rect x="555" y="332" width="170" height="56" rx="8" fill="#C92A2A"/>
    <text x="640" y="366" text-anchor="middle">ASICs</text>
  </g>
  <g class="company-node">
    <rect x="805" y="52" width="170" height="56" rx="8" fill="#F08C00"/>
    <text x="890" y="86" text-anchor="middle">SK Hynix</text>
  </g>
  <g class="company-node">
    <rect x="805" y="122" width="170" height="56" rx="8" fill="#F08C00"/>
    <text x="890" y="156" text-anchor="middle">Samsung</text>
  </g>
  <g class="company-node">
    <rect x="805" y="192" width="170" height="56" rx="8" fill="#F08C00"/>
    <text x="890" y="226" text-anchor="middle">Micron</text>
  </g>
  <g class="company-node">
    <rect x="805" y="292" width="170" height="56" rx="8" fill="#2B8A3E"/>
    <text x="890" y="326" text-anchor="middle">TSMC</text>
  </g>
  <g class="company-node">
    <rect x="805" y="362" width="170" height="56" rx="8" fill="#2B8A3E"/>
    <text x="890" y="396" text-anchor="middle">TSMC CoWoS</text>
  </g>
  <g class="company-node">
    <rect x="1045" y="132" width="170" height="56" rx="8" fill="#0B7285"/>
    <text x="1130" y="166" text-anchor="middle">Broadcom / Marvell / Arista</text>
  </g>
  <g class="company-node">
    <rect x="1045" y="282" width="170" height="56" rx="8" fill="#495057"/>
    <text x="1130" y="316" text-anchor="middle">Vertiv / Eaton / Schneider</text>
  </g>
  <g class="company-node">
    <rect x="1045" y="412" width="170" height="56" rx="8" fill="#1971C2"/>
    <text x="1130" y="446" text-anchor="middle">Solidigm / Samsung SSD</text>
  </g>
  <text x="42" y="484" class="graph-note">Edges are representative links from the project relationship map; labels are simplified for readability and should be read with the evidence table.</text>
</svg>
</figure>


## 1B. Company Exposure Map

The model treats companies as exposure points along the transmission chain. Demand-side companies create token and CapEx pull; upstream suppliers determine whether that demand can become deployed compute.

| Layer / Role | Representative Companies | Model Variables | Transmission Logic |
|---|---|---|---|
| AI demand owners | OpenAI, Anthropic, Google DeepMind, Meta AI, xAI | `tokens_per_day` | End-user and model-training demand expands token volume and raises accelerator utilization demand. |
| Cloud procurement | Microsoft Azure, AWS, Google Cloud, Oracle Cloud, CoreWeave | `total_capex_usd, accelerators_procured` | Cloud CapEx converts expected AI demand into forward accelerator procurement before utilization fully materializes. |
| Accelerators | NVIDIA, AMD, Intel Gaudi; internal ASICs: Google TPU, AWS Trainium, Microsoft Maia, Meta MTIA | `accelerator_demand, accelerator_supply` | Accelerator availability sets the starting point for HBM, CoWoS, power, and networking demand. |
| HBM | SK Hynix, Samsung, Micron | `hbm_demand_pb, hbm_supply_pb, hbm_gap` | HBM content per accelerator converts GPU demand into memory bit and stack allocation pressure. |
| Advanced packaging / foundry | TSMC CoWoS, TSMC, ASE, Amkor, Samsung Foundry | `cowos_demand_wpm, cowos_supply_wpm, cowos_gap` | Advanced package slots and foundry flow determine how many high-end AI accelerators can ship. |
| Power infrastructure | Vertiv, Eaton, Schneider Electric, GE Vernova, ABB | `power_demand_gw, power_supply_gw, power_gap` | Power and cooling determine whether purchased accelerators can be energized and deployed. |
| Networking | Broadcom, Marvell, Arista, Cisco, Mellanox/NVIDIA | `network_demand_tbps, network_supply_tbps, network_gap` | Scale-up and scale-out cluster fabric demand rises with accelerator count and cluster complexity. |
| Storage | Solidigm, Samsung SSD, Kioxia, WD/SanDisk, Seagate | `storage_demand_pb_per_day` | Agentic and RAG workloads create retrieval, context, and storage-flow pressure. |

## 2. Formula Book

### 2.1 Token Demand to Accelerator Utilization

```text
accelerators_required =
  tokens_per_day
  / 86,400
  / (tokens_per_second_per_accelerator * utilization)
```

**Interpretation:** actual AI workload volume becomes required accelerator service capacity.

### 2.2 CapEx to Accelerator Procurement

```text
accelerators_procured =
  total_capex_usd
  * ai_infra_share
  * accelerator_share
  / avg_accelerator_asp_usd
```

**Interpretation:** hyperscalers buy ahead of realized token demand for training runs, reserve capacity, future inference demand, redundancy, and scarce-component allocation.

### 2.3 Effective Accelerator Demand

```text
accelerator_demand =
  max(accelerators_required, accelerators_procured)
  + prior_period_backlog
```

**Interpretation:** procurement demand dominates when cloud providers prebuild capacity ahead of utilization.

### 2.4 Accelerator to HBM

```text
hbm_demand_pb =
  accelerator_demand
  * hbm_gb_per_accelerator
  / 1,000,000
```

**Unit:** PB/year.

### 2.5 Accelerator to CoWoS

```text
cowos_demand_wpm =
  accelerator_demand
  * cowos_wpm_per_accelerator
```

**Unit:** wafer starts per month.  
**Caveat:** this is currently a low-confidence normalized coefficient. The replacement model should use die area, interposer area, package yield, HBM stack count, and wafer throughput.

### 2.6 Accelerator to Power

```text
power_demand_gw =
  accelerator_demand
  * accelerator_tdp_w
  * server_overhead
  * pue
  / 1,000,000,000
```

### 2.7 Accelerator to Networking

```text
network_demand_tbps =
  accelerator_demand
  * network_tbps_per_accelerator
  * (1 + network_complexity_growth * years_after_2026)
```

### 2.8 Tokens to Storage Flow

```text
storage_demand_pb_per_day =
  tokens_per_day
  * rag_storage_ratio
  * bytes_per_token
  / 1,000
  / 1,000,000,000
```

### 2.9 Gap, Fulfillment, Backlog

```text
gap_ratio[layer] = demand[layer] / supply[layer]

limiting_gap = max(gap_ratio[accelerator],
                   gap_ratio[hbm],
                   gap_ratio[cowos],
                   gap_ratio[power],
                   gap_ratio[networking])

fulfillment_rate = min(1, 1 / limiting_gap)

unserved_accelerators =
  accelerator_demand * (1 - fulfillment_rate)

next_period_backlog =
  unserved_accelerators * backlog_carryover
```

### 2.10 Price Pressure Index

```text
shortage = max(gap_ratio - 1, 0)
surplus = max(1 - gap_ratio, 0)

price_pressure_index =
  max(80,
      100 * (1
             + price_beta * (exp(shortage) - 1)
             - 0.25 * surplus))
```

**Interpretation:** 100 is neutral; shortage pressure is convex because scarce components are rationed by allocation and price.

## 3. Evidence-Linked Coefficients

| Coefficient | Value | Unit | Confidence | Status | Sensitivity Range | Evidence IDs |
|---|---:|---|---:|---|---|---|
| `COEF_CAPEX_AI_INFRA_SHARE` | 0.58 | share_of_total_capex | 55% | partially_supported | [0.45, 0.7] | SRC_MICROSOFT_FY2026_Q1_CALL, SRC_ALPHABET_Q1_2026_SEC_8K, SRC_META_Q1_2026_RESULTS, SRC_SEC_MSFT_LATEST_PRIMARY, SRC_SEC_AMZN_LATEST_PRIMARY, SRC_SEC_GOOGL_LATEST_PRIMARY, SRC_SEC_META_LATEST_PRIMARY, SRC_SEC_ORCL_LATEST_PRIMARY, SRC_SEC_FINANCIALS_DB_20260504 |
| `COEF_CAPEX_ACCELERATOR_SHARE` | 0.46 | share_of_ai_infra_capex | 45% | derived_proxy | [0.3, 0.6] | SRC_MICROSOFT_FY2026_Q1_CALL, SRC_NVIDIA_FY2026_Q4_RESULTS, SRC_SEC_MSFT_LATEST_PRIMARY, SRC_SEC_AMZN_LATEST_PRIMARY, SRC_SEC_GOOGL_LATEST_PRIMARY, SRC_SEC_META_LATEST_PRIMARY, SRC_SEC_NVDA_LATEST_PRIMARY, SRC_SEC_AMD_LATEST_PRIMARY, SRC_SEC_FINANCIALS_DB_20260504 |
| `COEF_AVG_ACCELERATOR_ASP_USD` | 55000 | usd_per_h100_equivalent | 40% | derived_proxy | [35000, 90000] | SRC_NVIDIA_H100_SPEC, SRC_NVIDIA_H200_SPEC, SRC_NVIDIA_GB200_NVL72_SPEC, SRC_NVIDIA_FY2026_Q4_RESULTS, SRC_SEC_NVDA_LATEST_PRIMARY, SRC_SEC_AMD_LATEST_PRIMARY, SRC_SEC_FINANCIALS_DB_20260504 |
| `COEF_COWOS_WPM_PER_ACCELERATOR` | 0.018 | wafers_per_month_per_accelerator_unit | 35% | calibrated_placeholder | [0.01, 0.03] | SRC_NVIDIA_H100_SPEC, SRC_NVIDIA_H200_SPEC, SRC_NVIDIA_GB200_NVL72_SPEC, SRC_LOCAL_GAP_ENGINE_ANCHORS, SRC_SEC_NVDA_LATEST_PRIMARY, SRC_SEC_AMD_LATEST_PRIMARY, SRC_SEC_TSM_LATEST_PRIMARY, SRC_SEC_FINANCIALS_DB_20260504 |
| `COEF_NETWORK_TBPS_PER_ACCELERATOR` | 0.0035 | tbps_per_accelerator | 45% | derived_proxy | [0.002, 0.008] | SRC_NVIDIA_GB200_NVL72_SPEC, SRC_SEC_AVGO_LATEST_PRIMARY, SRC_SEC_MRVL_LATEST_PRIMARY, SRC_SEC_ANET_LATEST_PRIMARY, SRC_SEC_CSCO_LATEST_PRIMARY, SRC_SEC_FINANCIALS_DB_20260504 |
| `COEF_RAG_STORAGE_RATIO` | 0.34 | share_of_tokens_touching_retrieval_or_context_storage | 30% | assumption | [0.1, 0.6] | SRC_NVIDIA_GB200_NVL72_SPEC, SRC_SEC_MSFT_LATEST_PRIMARY, SRC_SEC_AMZN_LATEST_PRIMARY, SRC_SEC_GOOGL_LATEST_PRIMARY, SRC_SEC_META_LATEST_PRIMARY, SRC_SEC_FINANCIALS_DB_20260504 |

## 3A. Formula Reliability Matrix

Current model use label: **scenario_analysis_only**. Research-only coefficients: COEF_CAPEX_ACCELERATOR_SHARE, COEF_AVG_ACCELERATOR_ASP_USD, COEF_COWOS_WPM_PER_ACCELERATOR, COEF_NETWORK_TBPS_PER_ACCELERATOR, COEF_RAG_STORAGE_RATIO. Critical audit items: COEF_CAPEX_ACCELERATOR_SHARE, COEF_AVG_ACCELERATOR_ASP_USD, COEF_COWOS_WPM_PER_ACCELERATOR.

| Formula Block | Current Reliability | Why | Upgrade Needed |
|---|---|---|---|
| tokens_to_accelerators | High structure / medium calibration | Throughput equation is mechanically valid, but tokens/sec depends on workload mix. | Replace H100-equivalent throughput with measured model/workload benchmarks. |
| capex_to_accelerators | Medium-low | CapEx split and blended accelerator ASP are derived proxies. | Company-quarter CapEx split plus NVIDIA/AMD shipment and ASP bridge. |
| accelerators_to_hbm | High structure / medium mix | HBM per accelerator is product-spec based, but GPU mix is simplified. | Explicit H100/H200/B200/GB200/MI300 mix and HBM stack count. |
| accelerators_to_cowos | Low / placeholder | Current coefficient is calibrated, not package-physics based. | Die area, interposer area, package yield, wafer starts, and package throughput. |
| accelerators_to_power | High structure / medium facility calibration | TDP and PUE structure is sound; server overhead and energization timing need site data. | Rack-level power, cooling overhead, interconnection queue, and PUE by facility. |
| accelerators_to_networking | Medium-low | GB200 NVL72 scale-up bandwidth is direct, but external scale-out fabric is proxied. | Topology split: NVLink, InfiniBand/Ethernet, NIC count, radix, oversubscription. |
| price_pressure_index | Research-only | Convex shortage response is useful for scenario comparison, not a transaction price model. | Historical component price elasticity by utilization and lead time. |

## 4. Baseline and Scenario Results

| Scenario | Year | Limiting Layer | Fulfillment | Unserved Accels | Accelerator Gap | HBM Gap | CoWoS Gap | Power Gap | Network Gap |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| bear | 2026 | accelerator | 100% | 0 | 0.69x | 0.80x | 0.54x | 0.71x | 0.65x |
| bear | 2027 | accelerator | 100% | 0 | 0.58x | 0.63x | 0.44x | 0.54x | 0.52x |
| bear | 2028 | accelerator | 100% | 0 | 0.48x | 0.49x | 0.36x | 0.42x | 0.42x |
| base | 2026 | accelerator | 100% | 0 | 0.85x | 0.99x | 0.66x | 0.87x | 0.80x |
| base | 2027 | accelerator | 100% | 0 | 0.71x | 0.77x | 0.54x | 0.67x | 0.65x |
| base | 2028 | accelerator | 100% | 0 | 0.59x | 0.60x | 0.44x | 0.52x | 0.52x |
| bull | 2026 | hbm | 79% | 1,038,363 | 1.09x | 1.27x | 0.85x | 1.11x | 1.02x |
| bull | 2027 | hbm | 89% | 794,159 | 1.03x | 1.13x | 0.79x | 0.98x | 0.83x |
| bull | 2028 | hbm | 86% | 1,237,978 | 1.13x | 1.16x | 0.85x | 0.98x | 0.92x |

## 5. Stress Scenarios

These stress scenarios are formula-defined overlays on the base case. They are deliberately simple so the shock transmission can be audited.

| Stress Scenario | Shock | Declared Formula | Peak 2026 Gap | Implied Fulfillment | Transmission Channel |
|---|---|---|---:|---:|---|
| HBM4 qualification delay | HBM supply -15% | `hbm_gap_stress = hbm_gap / (1 - 0.15)` | 1.16x | 86% | Memory allocation tightens first; accelerator deployment is capped by HBM availability. |
| Power interconnection delay | AI-ready power supply -20% | `power_gap_stress = power_gap / (1 - 0.20)` | 1.09x | 92% | GPU delivery can continue, but energized deployment lags and backlog shifts to data-center operators. |
| CoWoS ramp slippage | CoWoS supply -20% | `cowos_gap_stress = cowos_gap / (1 - 0.20)` | 0.82x | 100% | Advanced packaging queue lengthens; second-tier accelerator and ASIC customers face allocation risk. |
| CapEx air pocket | AI infrastructure demand -22% | `gap_stress = gap * (1 - 0.22)` | 0.77x | 100% | Supplier pricing pressure eases; backlog drawdown improves near-term fulfillment but reduces order visibility. |
| AI demand boom | Demand +32%, supply ramp +6% | `gap_stress = gap * 1.32 / 1.06` | 1.23x | 81% | HBM becomes the binding constraint; power and networking become second-order constraints. |

## 6. Scenario Interpretation

### Base Case

The 2026 base case is close to balance. HBM is the tightest layer, but the modeled HBM gap remains just below shortage at **0.99x**. This means the system can fulfill modeled accelerator demand, but has limited buffer if demand or qualification timing moves adversely.

### Bull AI CapEx Cycle

The bull case is the first true shortage scenario. HBM reaches **1.27x**, making it the binding constraint. Accelerator, power, and networking also tighten, but HBM caps deployment first. The implication is that memory allocation, not only GPU supply, determines who can deploy AI clusters on time.

### HBM4 Qualification Delay

If HBM supply is delayed by 15%, the base-case 2026 HBM gap moves above 1.0x. This shifts the system from “tight but fulfillable” to “allocation-constrained,” especially for customers without long-term priority contracts.

### Power Interconnection Delay

Power is a slower-moving constraint. A power supply shock does not necessarily prevent GPU shipments, but it prevents energized deployment. The economic symptom is stranded or delayed compute capacity, higher data-center lease premiums, and longer backlog realization.

### CapEx Air Pocket

A CapEx pullback improves near-term fulfillment but weakens order visibility for upstream suppliers. Under this scenario, pricing pressure eases first in accelerators and networking, while HBM remains more resilient because memory content per accelerator continues to rise.

## 7. Strategic Implications

1. HBM is the highest-leverage variable in the current model.
2. CapEx-driven procurement demand matters more than current token utilization in near-term supply-chain stress.
3. Power and networking are second-wave bottlenecks: they bind after accelerator procurement has already happened.
4. CoWoS must be rebuilt with package-area math before the model is investment-grade.
5. The model should be refreshed whenever company CapEx guidance, NVIDIA data-center revenue, HBM bit supply, or TSMC advanced packaging capacity changes.

## 8. Evidence Register

| Source ID | Publisher | Evidence Type | Confidence | Link |
|---|---|---|---:|---|
| `SRC_NVIDIA_H100_SPEC` | NVIDIA | direct_product_spec | 95% | [NVIDIA H100 GPU product specifications](https://www.nvidia.com/en-gb/data-center/h100/) |
| `SRC_NVIDIA_H200_SPEC` | NVIDIA | direct_product_spec | 95% | [NVIDIA H200 GPU product specifications](https://www.nvidia.com/en-in/data-center/h200/) |
| `SRC_NVIDIA_GB200_NVL72_SPEC` | NVIDIA | direct_product_spec | 95% | [NVIDIA GB200 NVL72 specifications](https://www.nvidia.com/en-us/data-center/gb200-nvl72/) |
| `SRC_NVIDIA_FY2026_Q4_RESULTS` | NVIDIA | direct_company_result | 95% | [NVIDIA Announces Financial Results for Fourth Quarter and Fiscal 2026](https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2026) |
| `SRC_MICROSOFT_FY2026_Q1_CALL` | Microsoft | direct_company_commentary | 90% | [Microsoft Fiscal Year 2026 First Quarter Earnings Conference Call](https://www.microsoft.com/en-us/investor/events/fy-2026/earnings-fy-2026-q1) |
| `SRC_ALPHABET_Q1_2026_SEC_8K` | Alphabet / SEC | direct_company_result | 95% | [Alphabet Announces First Quarter 2026 Results](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000043/googexhibit991q12026.htm) |
| `SRC_META_Q1_2026_RESULTS` | Meta | direct_company_result | 95% | [Meta Reports First Quarter 2026 Results](https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-First-Quarter-2026-Results/default.aspx) |
| `SRC_LOCAL_GAP_ENGINE_ANCHORS` | Local model | internal_synthesis | 65% | [Current capacity utilization anchors from config.py and gap_engine.py](config.py::CURRENT_CAPACITY_UTILIZATION) |
| `SRC_SEC_FILINGS_DB_20260504` | SEC EDGAR | direct_sec_metadata_database | 95% | [AI SCM company filing metadata database](data/sec_filings.json) |
| `SRC_SEC_MSFT_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Microsoft 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/789019/000119312526191507/msft-20260331.htm) |
| `SRC_SEC_AMZN_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Amazon 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000014/amzn-20260331.htm) |
| `SRC_SEC_GOOGL_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Alphabet 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm) |
| `SRC_SEC_META_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Meta Platforms 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/1326801/000162828026028526/meta-20260331.htm) |
| `SRC_SEC_ORCL_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Oracle 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/1341439/000119312526101045/orcl-20260228.htm) |
| `SRC_SEC_NVDA_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [NVIDIA 10-K filing for FY2026](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm) |
| `SRC_SEC_AMD_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [AMD 10-K filing for FY2025](https://www.sec.gov/Archives/edgar/data/2488/000000248826000018/amd-20251227.htm) |
| `SRC_SEC_MU_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Micron 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/723125/000072312526000006/mu-20260226.htm) |
| `SRC_SEC_AVGO_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Broadcom 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/1730168/000173016826000016/avgo-20260201.htm) |
| `SRC_SEC_MRVL_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Marvell 10-K filing for FY2026](https://www.sec.gov/Archives/edgar/data/1835632/000183563226000011/mrvl-20260131.htm) |
| `SRC_SEC_ANET_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Arista Networks 10-K filing for FY2025](https://www.sec.gov/Archives/edgar/data/1596532/000159653226000013/anet-20251231.htm) |
| `SRC_SEC_CSCO_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Cisco 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/858877/000085887726000021/csco-20260124.htm) |
| `SRC_SEC_VRT_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Vertiv 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/1674101/000162828026026556/vrt-20260331.htm) |
| `SRC_SEC_ETN_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [Eaton 10-K filing for FY2025](https://www.sec.gov/Archives/edgar/data/1551182/000155118226000007/etn-20251231.htm) |
| `SRC_SEC_GEV_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [GE Vernova 10-Q filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/1996810/000199681026000064/gev-20260331.htm) |
| `SRC_SEC_TSM_LATEST_PRIMARY` | SEC EDGAR | direct_company_filing_metadata | 95% | [TSMC 6-K filing for 2026 Q1](https://www.sec.gov/Archives/edgar/data/1046179/000104617926000205/tsm-monthend6kx20260424.htm) |
| `SRC_SEC_FINANCIALS_DB_20260504` | SEC XBRL companyfacts | direct_sec_xbrl_financial_statement_database | 95% | [AI SCM company financial statement facts database](data/sec_financials.json) |

## 9. Validation Notes

- Direct product specs and company filings are treated as high-confidence inputs.
- CapEx split, accelerator ASP, CoWoS coefficient, networking coefficient, and RAG storage ratio remain derived or provisional.
- Low-confidence coefficients are retained only because they are explicit, traceable, and have a replacement path in `data/model_evidence.json`.
- The companion Excel model is formula-driven: `outputs/excel/ai_scm_supply_demand_simulator.xlsx`.
