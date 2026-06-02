# Public Learning-Theme Alignment Matrix

This matrix explains how the repository maps to public AI/ML course-project themes. It avoids claiming official course completion or hidden-grader certification.

| Project family | Public theme being studied | Implemented modules | Local verification |
|---|---|---|---|
| Focused LLM benchmark | data quality, compact LM evaluation, attention systems measurement | `llm_benchmark/dataset.py`, `char_lm.py`, `attention.py`, `experiment.py`, `reporting.py` | checksum-verified Tiny Shakespeare, ablations, held-out loss curves, sanitized error analysis, throughput and estimated-memory comparison |
| CS188-inspired AI | search, multi-agent decision making, RL, probabilistic inference, ML | `cs188/pacman_core.py`, `search.py`, `multiagent.py`, `rl.py`, `inference.py`, `ml.py` | BFS/A*/Corners, alpha-beta, value iteration, HMM forward filtering/Viterbi, held-out perceptron accuracy |
| Coursera-ML-inspired basics | supervised learning, neural networks, decision trees, unsupervised learning, recommenders, RL | `coursera_ml/supervised.py`, `advanced.py`, `unsupervised_recsys_rl.py` | held-out regression/classification metrics, K-Means, anomaly probe, held-out matrix factorization |
| CS231n-inspired vision/deep learning | classifiers, differentiable layers, CNNs, RNN/attention, contrastive and diffusion utilities | `cs231n/layers.py`, `classifiers.py`, `sequence.py`, `diffusion_contrastive.py` | numerical gradient checks, held-out classifier accuracy, attention smoke tests |
| D2L-inspired deep learning | textbook-style from-scratch neural-network components | `d2l/core.py` | linear regression, held-out softmax regression accuracy, convolution, attention |
| CS224n-inspired NLP | word vectors, parsing, GPT-style modeling, NLP task metrics | `cs224n/word_vectors.py`, `parser.py`, `gpt2.py`, `tasks.py` | PPMI, negative sampling, transition parse, GPT-style forward/generation, ROUGE-L |
| CS336-inspired language modeling systems | tokenizer, transformer LM, optimization, systems, scaling, data, alignment | `cs336/tokenizer.py`, `optim.py`, `systems.py`, `scaling.py`, `data.py`, `alignment.py` | BPE, mini LM step, AdamW, attention, scaling-law fit, data cleaning, DPO |

## Integrity boundary

The repository is an independent implementation portfolio. Tiny Shakespeare is public and checksum-verified. The repository does not include or claim access to hidden graders, restricted datasets, private notebooks, or official solution files.
