# Dataset Card: openwebtext_streaming

## Source

- Dataset: `OpenWebText streaming sample`
- Source: `openwebtext`
- Version: `huggingface-openwebtext-streaming`
- License / terms: Use as a real HuggingFace streaming sample; verify upstream terms before release.
- Download or streaming method: `huggingface datasets streaming`

## Status

- dataset_status: `real_nonfallback`
- dataset_scope: `streaming_sample`
- streaming sample: `True`
- complete upstream corpus: `False`
- failure reason: none

## Sample Size

- sample_seed: `31`
- max_documents: `600`
- max_tokens: `160000`
- actual_documents: `117`
- actual_train_tokens: `128294`
- actual_validation_tokens: `9257`
- actual_test_tokens: `16433`

## Hashes

- content_hash: `690ed5bdf15b6a48e3cdbc26ef82ced373a7bc770525187c4c16ba8fdb34ac77`
- split_hash_train: `3b5a248fce49cd802ad0e51fd0cbfb2d0b7f4d5e5f2b398bae7770ef7d7dac96`
- split_hash_dev: `896ad7489e783460577a119d9b3a4e09c82bd9c1f75e2032b443b49f876a449e`
- split_hash_test: `2d4b1c4b23bbd1df42dfd80bcb9714d3e1c1674d29a9f9c74565e5d19fbed75d`

## Known Limitations

- This card describes the prepared sample or failure state recorded by the repository.
- Streaming samples are bounded samples and must not be described as complete upstream corpora.
- Failed or insufficient samples remain part of the audit trail instead of being replaced by fallback fixtures.
