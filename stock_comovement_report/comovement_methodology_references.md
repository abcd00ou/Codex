# Comovement / Coupling Methodology References

This note records the references used to define the stock comovement report methodology.

## Core Methodology

1. Daniel J. Fenn, Mason A. Porter, Stacy Williams, Mark McDonald, Neil F. Johnson, Nick S. Jones, "Temporal Evolution of Financial Market Correlations", arXiv, 2010.
   - URL: https://arxiv.org/abs/1011.3225
   - Relevance: Uses stock/market return correlation matrices, random matrix theory, and PCA to identify evolving common components in financial markets.

2. M. Tumminello, F. Lillo, R. N. Mantegna, "Correlation, hierarchies, and networks in financial markets", arXiv, 2008.
   - URL: https://arxiv.org/abs/0809.4615
   - Relevance: Discusses correlation matrices, hierarchical trees, correlation-based networks, and filtering procedures for financial market structure.

3. Kristin J. Forbes and Roberto Rigobon, "No Contagion, Only Interdependence: Measuring Stock Market Comovements", Journal of Finance / NBER working paper.
   - URL: https://www.nber.org/papers/w7267
   - Relevance: Warns that raw correlation changes can be misleading, especially under changing volatility. The report therefore describes coupling/interdependence rather than causality.

4. Stock correlation network overview.
   - URL: https://en.wikipedia.org/wiki/Stock_correlation_network
   - Relevance: Summarizes the common workflow of computing cross-correlations from stock return series and using thresholds/networks to identify linked assets.

5. Principal component analysis overview.
   - URL: https://en.wikipedia.org/wiki/Principal_component_analysis
   - Relevance: Documents PCA as a dimensionality-reduction method where the first component captures the largest variance direction; used here as a common-factor proxy.

## AI Supply Chain Bottleneck Context

These sources are used only to motivate a bottleneck-sensitive interpretation layer. They do not identify bottlenecks from the stock-price data itself.

1. International Energy Agency, "Energy and AI" coverage as reported by The Guardian, 2025.
   - URL: https://www.theguardian.com/technology/2025/apr/10/energy-demands-from-ai-datacentres-to-quadruple-by-2030-says-report
   - Relevance: Summarizes the IEA view that AI is a major driver of data-centre electricity demand growth, supporting power/grid as a bottleneck-sensitive section.

2. Danbo Chen et al., "Concentrated siting of AI data centers drives regional power-system stress under rising global compute demand", arXiv, 2026.
   - URL: https://arxiv.org/abs/2604.06198
   - Relevance: Provides a power-system stress framing for AI data-center concentration and regional grid vulnerability.

3. Zheng Liu, "Generative Design for Direct-to-Chip Liquid Cooling for Data Centers", arXiv, 2026.
   - URL: https://arxiv.org/abs/2604.10941
   - Relevance: Documents why rising AI rack power density increases the need for direct-to-chip liquid cooling and thermal-management capacity.

4. Tom's Hardware, "Samsung and SK hynix warn AI-driven memory shortages could last until 2027 and beyond", 2026.
   - URL: https://www.tomshardware.com/tech-industry/artificial-intelligence/samsung-and-sk-hynix-warn-ai-driven-memory-shortages-could-last-until-2027-and-beyond-as-hbm-demand-explodes-customers-already-reserving-supply-years-ahead-while-the-wider-dram-market-begins-to-tighten
   - Relevance: Market reporting on AI-driven HBM/DRAM shortage narratives; useful context for why DRAM coupling may be bottleneck-sensitive.

5. Tom's Hardware, "Memory makers have no plans to increase RAM production despite crushing memory shortages", 2025.
   - URL: https://www.tomshardware.com/pc-components/dram/memory-makers-have-no-plans-to-increase-production-despite-crushing-ram-shortages-modest-2026-increase-predicted-as-dram-makers-hedge-their-ai-bets
   - Relevance: Market reporting on DRAM makers prioritizing HBM and capacity conversion, which can connect AI demand to broader memory tightness.

6. Tom's Hardware, "TSMC says advanced-node capacity falls about three times short of AI demand", 2025.
   - URL: https://www.tomshardware.com/tech-industry/semiconductors/tsmc-csays-advanced-node-capacity-falls-short-of-ai-demand
   - Relevance: Market reporting on advanced-node capacity constraints; relevant to AI chip, foundry, and semiconductor equipment sections.

## Operational Criteria Used In This Report

- Price input: adjusted close.
- Primary transformation: monthly log return.
- Pair coupling: Pearson correlation of overlapping monthly returns.
- Time-varying coupling: 12-month rolling average pair correlation.
- Frequency cross-check: daily and weekly log returns are retained only as robustness checks against the monthly baseline.
- Group common factor: first principal component explained variance on standardized returns.
- Group classification:
  - High coupling: average pair correlation >= 0.60 and PC1 explained share >= 0.60.
  - Moderate coupling: average pair correlation >= 0.35, or PC1/strong-pair evidence indicates partial coupling.
  - Weak / fragmented: below the moderate threshold.
- Member classification:
  - Coupling core: mean correlation to group >= 0.50 or at least two links >= 0.65.
  - Partial / bridge: mean correlation to group >= 0.35 or best peer correlation >= 0.55.
  - Weakly coupled: below those thresholds.
- Bottleneck lens:
  - The report does not infer the actual location of AI supply-chain bottlenecks from stock prices alone.
  - High or rising coupling in a bottleneck-sensitive section is treated as a screening signal that market participants may be pricing the section as a common shortage/capacity factor.
  - A bottleneck claim requires external operating evidence such as lead time, ASP, backlog, utilization, inventory, capex, customer prepayments, interconnection delays, power availability, or cooling capacity.

## Interpretation Guardrails

- Correlation is evidence of comovement, not causality.
- Bottleneck-sensitive coupling is not proof of a shortage; it is a hypothesis to test against operating data.
- Broader groups can show lower average coupling because of country, exchange, factor, and business-model heterogeneity.
- Short listing histories reduce common-window length and can make rolling results less stable.
- Cross-market calendars create asynchronous return observations; the report uses overlapping monthly returns as the primary comparison window.
