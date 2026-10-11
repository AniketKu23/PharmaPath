# PharmaPath Data Provenance and Lineage

This document tracks all external datasets ingested into the PharmaPath pipeline, including source URLs, version tags, retrieval timestamps, file sizes, and record/row counts. All data downloaded is non-synthetic and fetched directly from primary scientific repositories and APIs.

| Dataset Identifier | Primary Source URL / Endpoint | Version / Build | Date Retrieved | Raw Format | Records / Dimensions | Processing Details |
|---|---|---|---|---|---|---|
| `string_ppi_links` | STRING DB (`9606.protein.links.v12.0.txt.gz`) | v12.0 | Pending Phase 1 | GZ / TSV | Pending | High-confidence filtering (combined_score >= 700) |
| `string_ppi_info` | STRING DB (`9606.protein.info.v12.0.txt.gz`) | v12.0 | Pending Phase 1 | GZ / TSV | Pending | ENSP to Gene Symbol alias mapping |
| `chembl_targets` | ChEMBL REST API (`/target_prediction` & `/mechanism`) | ChEMBL v33/v34 | Pending Phase 1 | JSON / REST | Pending | Metformin (CHEMBL1431), Imatinib (CHEMBL941) |
| `dgidb_targets` | DGIdb API / Interaction search | DGIdb v5 | Pending Phase 1 | JSON / REST | Pending | Target verification & source annotation |
| `lincs_expression` | LINCS L1000 via Enrichr / gseapy API | Enrichr 2023/2024 | Pending Phase 1 | JSON / TSV | Pending | Per-gene perturbation z-scores / direction |
| `opentargets_disease` | Open Targets Platform GraphQL API | v4 (v24.x) | Pending Phase 1 | GraphQL | Pending | T2D (EFO_0001360) and CML (EFO_0000339) |
| `pathways_reactome` | Reactome 2022 via Enrichr / gseapy | 2022 | Pending Phase 1 | GMT / JSON | Pending | Functional overrepresentation analysis |
| `pathways_kegg` | KEGG 2021 Human via Enrichr / gseapy | 2021 | Pending Phase 1 | GMT / JSON | Pending | Functional overrepresentation analysis |
| `string_ppi_links` | https://stringdb-downloads.org/download/protein.links.v12.0/9606.protein.links.v12.0.txt.gz | STRING v12.0 | 2026-10-11 01:40:52 | Parquet/TSV | 13,715,404 rows | Homo sapiens taxon 9606 protein interactions, filtered min_score>=700 (79.31 MB) |
| `string_ppi_info` | https://stringdb-downloads.org/download/protein.info.v12.0/9606.protein.info.v12.0.txt.gz | STRING v12.0 | 2026-10-11 01:40:52 | Parquet/TSV | 19,566 rows | Homo sapiens protein info with preferred gene names (1.88 MB) |
| `targets_metformin` | ChEMBL REST API + DGIdb + Literature Seed | 2024 | 2026-10-11 01:41:32 | Parquet/TSV | 63 rows | Targets curated for Metformin (61 in PPI LCC) (0.00 MB) |
| `targets_imatinib` | ChEMBL REST API + DGIdb + Literature Seed | 2024 | 2026-10-11 01:42:21 | Parquet/TSV | 11 rows | Targets curated for Imatinib (10 in PPI LCC) (0.00 MB) |
| `disease_t2d` | https://api.platform.opentargets.org/api/v4/graphql | Open Targets Platform v4 | 2026-10-11 01:42:28 | Parquet/TSV | 500 rows | Disease genes for Type 2 Diabetes (MONDO_0005148) with score >= 0.2 (0.10 MB) |
| `disease_cml` | https://api.platform.opentargets.org/api/v4/graphql | Open Targets Platform v4 | 2026-10-11 01:42:37 | Parquet/TSV | 162 rows | Disease genes for Chronic Myeloid Leukemia (MONDO_0011996) with score >= 0.2 (0.10 MB) |
| `lincs_metformin` | Enrichr / gseapy (LINCS_L1000_Chem_Pert_up/down) | LINCS L1000 2021/2022 | 2026-10-11 01:42:57 | Parquet/TSV | 50 rows | Directional perturbation signatures for Metformin (0.10 MB) |
| `lincs_imatinib` | Enrichr / gseapy (LINCS_L1000_Chem_Pert_up/down) | LINCS L1000 2021/2022 | 2026-10-11 01:43:40 | Parquet/TSV | 614 rows | Directional perturbation signatures for Imatinib (0.10 MB) |
| `string_ppi_links` | https://stringdb-downloads.org/download/protein.links.v12.0/9606.protein.links.v12.0.txt.gz | STRING v12.0 | 2026-10-11 02:22:56 | Parquet/TSV | 13,715,404 rows | Homo sapiens taxon 9606 protein interactions, filtered min_score>=700 (79.31 MB) |
| `string_ppi_info` | https://stringdb-downloads.org/download/protein.info.v12.0/9606.protein.info.v12.0.txt.gz | STRING v12.0 | 2026-10-11 02:22:56 | Parquet/TSV | 19,566 rows | Homo sapiens protein info with preferred gene names (1.88 MB) |
| `targets_metformin` | ChEMBL REST API + DGIdb + Literature Seed | 2024 | 2026-10-11 02:23:25 | Parquet/TSV | 63 rows | Targets curated for Metformin (61 in PPI LCC) (0.00 MB) |
| `targets_imatinib` | ChEMBL REST API + DGIdb + Literature Seed | 2024 | 2026-10-11 02:23:48 | Parquet/TSV | 11 rows | Targets curated for Imatinib (10 in PPI LCC) (0.00 MB) |
| `disease_t2d` | https://api.platform.opentargets.org/api/v4/graphql | Open Targets Platform v4 | 2026-10-11 02:23:48 | Parquet/TSV | 500 rows | Disease genes for Type 2 Diabetes (MONDO_0005148) with score >= 0.2 (0.10 MB) |
| `disease_cml` | https://api.platform.opentargets.org/api/v4/graphql | Open Targets Platform v4 | 2026-10-11 02:23:48 | Parquet/TSV | 162 rows | Disease genes for Chronic Myeloid Leukemia (MONDO_0011996) with score >= 0.2 (0.10 MB) |
| `lincs_metformin` | Enrichr / gseapy (LINCS_L1000_Chem_Pert_up/down) | LINCS L1000 2021/2022 | 2026-10-11 02:23:48 | Parquet/TSV | 50 rows | Directional perturbation signatures for Metformin (0.10 MB) |
| `lincs_imatinib` | Enrichr / gseapy (LINCS_L1000_Chem_Pert_up/down) | LINCS L1000 2021/2022 | 2026-10-11 02:23:48 | Parquet/TSV | 614 rows | Directional perturbation signatures for Imatinib (0.10 MB) |
