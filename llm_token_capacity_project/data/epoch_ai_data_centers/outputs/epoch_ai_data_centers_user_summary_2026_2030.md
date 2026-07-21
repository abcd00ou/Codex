# Epoch AI Data Centers User Summary, 2026-2030

- Generated: 2026-07-20
- Source: https://epoch.ai/data/data_centers/data_centers.zip
- Basis: Epoch AI AI Data Centers ZIP. Site-level users are expanded into user-site rows.
- Counting modes: `full_exposure` assigns every listed user the full site capacity; `equal_split` divides site capacity equally across listed users to avoid double-counting in user totals.
- Contracted/planned capacity: maximum site timeline capacity observed through the downloaded dataset, not necessarily a legally contracted power-purchase amount.
- Current capacity: Epoch site-level `Current power (MW)` and `Current H100 equivalents`, aggregated by listed user.

## 2030 Top Users By Equal-Split IT Power

| Rank | User | Sites | Current IT MW | 2030 IT Power MW | Contracted/Planned IT MW | 2030 H100-eq | Latest completion date |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | OpenAI | 19 | 1,852 | 10,858 | 10,858 | 24,002,783 | 2029-01-01 |
| 2 | Unknown user | 21 | 2,198 | 4,633 | 4,633 | 8,201,659 | 2030-01-01 |
| 3 | Google DeepMind | 11 | 1,655 | 4,594 | 4,594 | 11,988,378 | 2028-07-23 |
| 4 | Meta | 13 | 1,893 | 4,323 | 4,323 | 6,782,031 | 2028-01-01 |
| 5 | Anthropic | 6 | 2,127 | 4,321 | 4,321 | 4,218,096 | 2028-09-29 |
| 6 | Microsoft | 5 | 636 | 2,456 | 2,456 | 4,703,738 | 2028-05-13 |
| 7 | ByteDance | 1 | 221 | 700 | 700 | 388,075 | 2027-09-01 |
| 8 | Cursor | 1 | 315 | 315 | 315 | 370,558 | 2026-07-01 |
| 9 | SpaceXAI | 1 | 315 | 315 | 315 | 370,558 | 2026-07-01 |
| 10 | G42 | 1 | 50 | 218 | 218 | 522,991 | 2027-03-31 |
| 11 | Alibaba | 1 | 169 | 169 | 169 | 31,885 | 2026-01-03 |

## 2030 Top Users By Contracted/Planned Equal-Split IT Power

| Rank | User | Sites | Current IT MW | Contracted/Planned IT MW | 2030 IT Power MW | Contracted/Planned H100-eq | Data centers |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | OpenAI | 19 | 1,852 | 10,858 | 10,858 | 24,002,783 | CoreWeave Chester VA; CoreWeave Dalton 1 & 2; CoreWeave Denton TX; CoreWeave Ellendale ND; CoreWeave Marble NC; CoreW... |
| 2 | Unknown user | 21 | 2,198 | 4,633 | 4,633 | 8,201,659 | DayOne Nusajaya; Google Arcola; Google Kansas City East; Google Lancaster; Google Lincoln; Google Mesa; Google Midlot... |
| 3 | Google DeepMind | 11 | 1,655 | 4,594 | 4,594 | 11,988,378 | Goodnight; Google Cedar Rapids; Google Columbus; Google Council Bluffs (East); Google Fort Wayne; Google New Albany; ... |
| 4 | Meta | 13 | 1,893 | 4,323 | 4,323 | 6,782,031 | Meta Aiken; Meta Cheyenne; Meta Eagle Mountain; Meta Gallatin; Meta Hyperion; Meta Jeffersonville; Meta Kuna; Meta Lo... |
| 5 | Anthropic | 6 | 2,127 | 4,321 | 4,321 | 4,218,096 | Amazon Madison Mega Site; Amazon Ridgeland; Anthropic-Amazon New Carlisle; Colossus 1; Colossus 2; Fluidstack Lake Ma... |
| 6 | Microsoft | 5 | 636 | 2,456 | 2,456 | 4,703,738 | Crusoe Abilene Expansion; Microsoft Fairwater Atlanta; Microsoft Fairwater Wisconsin; Microsoft Goodyear; Start Campu... |
| 7 | ByteDance | 1 | 221 | 700 | 700 | 388,075 | VNET Bayin Ulanqab |
| 8 | Cursor | 1 | 315 | 315 | 315 | 370,558 | Colossus 2 |
| 9 | SpaceXAI | 1 | 315 | 315 | 315 | 370,558 | Colossus 2 |
| 10 | G42 | 1 | 50 | 218 | 218 | 522,991 | Fluidstack Lake Mariner |
| 11 | Alibaba | 1 | 169 | 169 | 169 | 31,885 | Alibaba Zhangbei |

## Output Files

- `normalized/epoch_ai_data_center_sites.csv`: one row per data center.
- `normalized/epoch_ai_data_center_user_sites.csv`: one row per user-data-center relationship.
- `normalized/epoch_ai_data_center_user_year_summary_2026_2030.csv`: user-year summary table.
- `outputs/epoch_ai_data_centers_user_summary_2026_2030.xlsx`: workbook with the same tables.

## Method Notes

- Epoch states that the dataset covers construction timelines from satellite imagery, permits and public documents, and includes timeline estimates for IT power, compute and cost.
- Epoch says 80% of IT power estimates are expected within a factor of 1.4x; compute within 1.5x; timeline estimates within 6 months.
- User tags from Epoch are preserved as `#confident`, `#likely`, `#speculative`, or `unlabeled`.
- Multi-user sites can be analyzed with full exposure for relationship mapping or equal split for non-double-counted aggregates.
