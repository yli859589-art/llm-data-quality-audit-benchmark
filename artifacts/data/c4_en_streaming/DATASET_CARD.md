# Dataset Card: c4_en_streaming

## Source

- Dataset: `C4 English streaming sample`
- Source: `allenai/c4`
- Version: `huggingface-allenai-c4-en-streaming`
- License / terms: Use as a real HuggingFace streaming sample; verify upstream terms before release.
- Download or streaming method: `huggingface datasets streaming`

## Status

- dataset_status: `real_nonfallback`
- dataset_scope: `streaming_sample`
- streaming sample: `True`
- complete upstream corpus: `False`
- failure reason: none

## Sample Size

- sample_seed: `37`
- max_documents: `600`
- max_tokens: `160000`
- actual_documents: `399`
- actual_train_tokens: `127236`
- actual_validation_tokens: `14830`
- actual_test_tokens: `16206`

## Hashes

- content_hash: `e13ceb6cc1b5eac9aeb555831cae3cc6b914f5f955f946e3c1964fb9d2ef342e`
- split_hash_train: `9aae86de310e90726069f9d0f45bd7103d57205c9f36f843c88260cd5bbe20cc`
- split_hash_dev: `51702d51d6b4fc91930b7f36a73a51546a630c4361e66575f4b6281cf3374a01`
- split_hash_test: `e719b096d8fa6509f52a9725402a27162c631b5548e0f7a676a36c1eb5a3f186`

## Known Limitations

- This card describes the prepared sample or failure state recorded by the repository.
- Streaming samples are bounded samples and must not be described as complete upstream corpora.
- Failed or insufficient samples remain part of the audit trail instead of being replaced by fallback fixtures.
