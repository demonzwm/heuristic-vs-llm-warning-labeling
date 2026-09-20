# Fusion Preflight Validation

- Repository layout validated.
- Model scope: `gpt`

| Check | Result | Detail |
| --- | --- | --- |
| Required input files | PASS | All required paths exist. |
| Inference input has no evaluation label fields | PASS | No evaluation label fields found. |
| Stage 2 prompt isolation | PASS | No heuristic label or evaluation label leakage detected. |

## Input Hashes

- `02_heuristic\results\heuristic_labels_1027.json`: `e41a83084232542cab7f4d2aeae44c4367ab0f8cf0c60988a122e4ec0e1179bc`
- `02_heuristic\results\heuristic_evolution_evidence_1027.json`: `e2eda384f3807562bffdaf1f203b509eea4cf3b1d8e9de8cf3971ba32a7273a7`
- `05_fusion\method\data\fusion_inference_input_1027.json`: `c5dc0bd628c59c12e2de5211ff523c3a55d0757be02af0544f5445543d95c7be`
- `05_fusion\method\stage1\stage1_results_1027.json`: `03de83231faaca6584b94deeda602ded53169983d20fa90579ad9ac85f8df5b5`
- `05_fusion\method\stage1\stage1_provenance.json`: `bbb880c82e509d8821268f63492cde6bb90cfa1b797a27d12d7b02dcd67a5793`
- `05_fusion\method\prompts\stage1_semantic_analysis_prompt.txt`: `14c774f4593b8174bcfe83a7a81dc39cc65f9217583300e24ee94420341b2b67`
- `05_fusion\method\prompts\stage2_disagreement_verification_prompt.txt`: `0959abdf86d7291bd4cd00502a9c45430e3306df6ed4dc3f53e7bebd91324a0b`
- `05_fusion\method\demonstrations\few_shot\selected_6shots.json`: `e18f0f61be2c309c611481af4f988299dd3ab6a911e69a47591de0cb18b3d535`
- `05_fusion\method\schemas\cwe_476_schema.md`: `a4e3753cd8581a6885c90582d03e7ecb6b9f23a819ae52789c4cba739e5dd796`
- `05_fusion\method\schemas\cwe_787_schema.md`: `3b8c581e764c636e906141164a05c38a72ce8820d8d9a2f6ca21fde6919ddd79`
- `05_fusion\method\schemas\generic_schema.md`: `7870bec0710fedac7e2c3b38d8e7df2ed6464801a8ea8ab092e14cdd4a6f4a7e`
- `03_llm\gpt\results\gpt_ouol_1027.json`: `b92cc201f5d5580088221ed781e464f5a2ebe74edb844064e0af9443709d9964`
- `05_fusion\gpt\results\stage1\gpt_stage1_predictions.json`: `d30e4b77fd2501e38ec5d2d3da5582baf9da91111daadbba64326fd3447de960`
