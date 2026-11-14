# Wild-benchmark direction-blindness audit (zero spend, no models)

Run: `python3 -I audit.py data . <fixtures.json>` (downloaded 2026-11-14). One `audit()` function is applied to every dataset; per-dataset numbers are in `results.json`.

| Dataset | n items | n audited (exchangeable roles) | Direction-blind ceiling | Mirror coverage | Mirrored pairs with different labels | Majority baseline |
|---|---|---|---|---|---|---|
| POSITIVE CONTROL: ours, reciprocal | 192 | 192 | 100.0% | 100% | 0% | 50.0% |
| POSITIVE CONTROL: ours, directed | 192 | 192 | 50.0% | 100% | 100% | 50.0% |
| OpenFGA sample-stores (check assertions) | 1603 | 1 | 100% (n=1, vacuous) | 0% | n/a | 100% |
| Cedar examples (ALLOW/DENY requests) | 72 | 0 | n/a | n/a | n/a | n/a |
| PrivacyLens main_data | 493 | 493 | 100% (vacuous, see caveat) | 0% | n/a | 100% (single label) |
| ContextualIntegritySyntheticDataset (HF) | 4024 info items (729 seeds) | 4024 | 99.9% (vacuous, 3952 groups for 4024 items) | 0% | n/a | 52.4% |

Control (all 384 action rows pooled): ceiling 75%, mirror coverage 100%, 50% of pairs differ. Swapped-role oracle (computable only for the control, from the `routes` table): correct rule 100%; applying the rule to swapped roles gives 100% on reciprocal, 0% on directed. Expected 100%/50% ceilings confirmed. Directed ceiling equals majority baseline (both 50%).

## Candidates (URL, licence, revision)
- Applicable, audited:
  - PrivacyLens https://github.com/SALT-NLP/PrivacyLens, MIT, commit 9c2ee07b. Roles: `seed.data_sender` / `seed.data_recipient` (provided fields, lower-cased text). Context: data_type, data_subject, transmission_principle. 0 unparsed. Label: README describes every seed as a negative (violating) norm, so label is constant (I did not find a per-item label field).
  - ContextualIntegritySyntheticDataset https://huggingface.co/datasets/huseyinatahaninan/ContextualIntegritySyntheticDataset, apache-2.0, sha e6fe38ea, 729 seeds. Roles: JSON `seed.sender` / `seed.recipient` (provided). Item = one information key with label allowed/disallowed from `dataset_item.annotation`; context = scenario, domain, user_intention, data_subject, transmission_principle, info key. 0 unparsed.
  - OpenFGA sample-stores https://github.com/openfga/sample-stores, Apache-2.0, commit 6802b4d8. 54 store files, 1603 check assertions (label = expected true/false). Roles: `user` and `object` only when both have the same type prefix (provided; 1 of 1603: expenses `employee:matt can_manage employee:daniel`). Context = store, test name, relation.
  - Cedar examples https://github.com/cedar-policy/cedar-examples, Apache-2.0 (LICENSE file; not re-read in full), commit 99280344. 72 request JSONs, label = ALLOW/DENY directory. Roles: principal/resource where entity types match: 0 of 72.
- Not applicable / not usable:
  - ConfAIde https://github.com/skywalker023/confAIde (MIT, commit 3174c63e): tiers are prompt text files with continuous human ratings or no gold labels; tier 2 has info/actor/use, not a same-typed role pair. Not parsed.
  - AuthorizationBench https://github.com/PEACH-Research-Lab/AuthorizationBench (MIT, commit bfe1fc27): 286 agentic sandbox tasks with free-text vignettes and violated-action criteria; no structured role pair or per-item gold label. Not audited.
  - CIMemories https://huggingface.co/datasets/facebook/CIMemories (cc-by-nc-4.0, sha 7a2bde79): attribute-vs-task prompts, no sender/recipient fields; test.csv has empty `label` column. Not applicable.
  - GoldCoin, AirGapAgent, AuthGateBench, DelegationBench, OrgAccess, Role-Conditioned Refusals: not found by my HF searches / not tried on GitHub; no claim made. HF search for GoldCoin returned only an unrelated coin dataset.

## What this does and does not show
- Roles were taken from provided structured fields; no regex or manual mapping. Unparsed items: 0 everywhere.
- 0% mirror coverage means these datasets contain no item whose role-swapped twin is also present, so no direction-blind classifier can be separated from a direction-aware one on them. This is only on the data present.
- Caveat on the ceilings: for PrivacyLens and CI-synthetic the roles are free text and nearly every item is its own group, so a ceiling near 100% is partly vacuous (a lookup table scores 100% on singletons). The informative number is mirror coverage (0%). For OpenFGA and Cedar the same-typed role pair almost never occurs (1/1603, 0/72), so those suites test user-to-object access, not direction between exchangeable roles; that is a scope mismatch, not evidence of a flaw.
- The audit does not show that a model is direction-blind, nor that these benchmarks are flawed for their own purpose. Mirrors could exist in a differently-keyed version (e.g., synonymous role phrases); exact-string matching after lower-casing would miss them. Sender/recipient swap in CI data is often semantically odd (user to hotel staff), so mirror absence is partly by design.
