# PROJECT.md: RegDelta

## 1. Problem Statement

Foreign investors and MNC compliance teams need reliable, fast interpretation of Vietnamese regulatory updates. Manual tracking is slow and language-constrained, while direct LLM summarization can hallucinate or omit legally material changes.

RegDelta addresses this by building a self-hosted, auditable pipeline that:
- Ingests Vietnamese regulatory updates continuously
- Extracts compliance-relevant deltas
- Produces structured English compliance packs
- Verifies each claim against source text and abstains when evidence is insufficient

## 2. Target Users

- Foreign investors entering or operating in Vietnam
- MNC legal/compliance teams with regional governance mandates
- Counsel and policy teams requiring traceable evidence-backed updates

## 3. Data Sources

Primary sources (planned):
- Official Vietnamese government legal publication portals
- Ministry and regulator circular/decree releases
- Gazette-style publication feeds and official PDF/HTML releases

Collected artifacts:
- Full document text (Vietnamese)
- Metadata (issuer, date, document type, legal domain, reference IDs)
- Version history for amendment tracking

## 4. Planned End-to-End Pipeline

### Stage A: Ingestion

- Scheduled crawlers/API fetchers for official sources
- Deduplication and canonical document ID assignment
- Document versioning with change detection at article/clause level

### Stage B: Extraction and Normalization

- OCR fallback for scanned PDFs
- Legal text segmentation into chapters/articles/clauses/points
- Citation and reference normalization
- Delta detection between versions (new, amended, repealed provisions)

### Stage C: Retrieval/Grounding

- Vietnamese-first indexing of normalized clauses
- Hybrid retrieval (lexical + embedding-based)
- Evidence chunk ranking for downstream generation

### Stage D: Translation and Compliance Pack Generation

- Evidence-conditioned English generation
- Strict schema output:
  - Regulatory change summary
  - Scope/applicability
  - Effective dates
  - Required actions and deadlines
  - Risk notes
  - Evidence citations with source anchors

### Stage E: Verification and Abstention

- Claim decomposition from generated pack
- Claim-to-evidence matching and contradiction detection
- Unsupported claims marked as abstained, not asserted
- Final confidence score and verifier trace

### Stage F: Packaging and Delivery

- JSON + Markdown/PDF compliance packs
- Audit bundle including source snippets and verifier outputs
- Optional API endpoint for integration with internal compliance systems

## 5. Experimentation Plan (Week 6 Requirement)

At least two approaches will be implemented and compared:

1. Prompt-only baseline
   - Direct generation from segmented inputs without retrieval
2. RAG pipeline
   - Retrieval-grounded generation with explicit evidence citations

Candidate additional comparisons:
- RAG vs RAG + LoRA-finetuned generator
- Single model vs two-model architecture (generator + verifier)

Controlled factors:
- Shared dataset splits
- Fixed seeds and prompt templates
- Same output schema and verifier criteria

## 6. Evaluation Plan

### Metrics

- Translation fidelity:
  - COMET/BLEU
  - Legal term consistency checks
- Extraction quality:
  - Precision/Recall/F1 on annotated deltas
- Hallucination bounding:
  - Unsupported claim rate
  - Verifier precision/recall
  - Abstention calibration
- Retrieval utility:
  - Recall@k, MRR for gold evidence spans
- End-to-end usefulness:
  - Human rubric on actionability and legal traceability

### Evaluation Artifacts

- Reproducible run logs
- Ablation tables
- Error taxonomy and qualitative failure cases

## 7. Reproducible Product Plan (Week 13 Requirement)

By Week 13, repository will include:

- Complete end-to-end pipeline code and run scripts
- README with setup and execution instructions
- Saved local checkpoint runnable on SUTD cluster
- Reproducible training/evaluation logs (for example W&B)
- Evaluation harness + test set + ablation scripts

Final graded outputs also include:
- PDF report (experiments, hardware, GPU hours, final design/results)
- Oral presentation
- Optional live demo

## 8. System and Infrastructure Assumptions

- Self-hosted deployment with local model runtime
- GPU training/evaluation on SUTD cluster
- Config-driven pipeline orchestration for repeatable runs
- Artifact storage for datasets, checkpoints, and reports

## 9. Risks and Mitigations

- Source variability (HTML/PDF structure drift):
  - Mitigation: modular parsers and regression fixtures
- OCR quality for scanned legal texts:
  - Mitigation: OCR confidence thresholds + manual spot checks
- Hallucination risk in generation:
  - Mitigation: strict grounding + verifier gate + abstention policy
- Evaluation subjectivity:
  - Mitigation: predefined rubric and dual-review annotation protocol

## 10. Success Criteria

- End-to-end pipeline runs reproducibly from ingestion to verified pack output
- RAG-based approach improves evidence-grounded accuracy over prompt-only baseline
- Unsupported claims are reliably detected and abstained
- Deliverables meet Week 6 and Week 13 rubric requirements
