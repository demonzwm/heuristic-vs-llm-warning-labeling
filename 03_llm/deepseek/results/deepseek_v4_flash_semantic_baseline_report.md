# DeepSeek V4-Flash Semantic Baseline Report

## Run Summary
- Input: `03_llm/deepseek/results/deepseek_v4_flash_semantic_baseline_1027.json`
- Total rows: 1027
- Successful rows: 1027
- Failed rows: 0
- Retry total: 7
- JSON repair total: 1

## Overall Metrics
- TP: 26
- FP: 177
- TN: 799
- FN: 25
- Precision: 0.128079
- Recall: 0.509804
- F1-score: 0.204724
- Accuracy: 0.803311

## Prediction Distribution
- Predicted TP: 203
- Predicted FP: 824
- Ground-truth TP: 51
- Ground-truth FP: 976

## SCA-Level Snapshot
- cppcheck: Count=379, TP=1, FP=54, TN=321, FN=3, F1=0.033898, Accuracy=0.849604
- codeql: Count=362, TP=19, FP=105, TN=225, FN=13, F1=0.243590, Accuracy=0.674033
- csa: Count=286, TP=6, FP=18, TN=253, FN=9, F1=0.307692, Accuracy=0.905594

