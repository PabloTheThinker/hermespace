# Pattern confirmation matrix

| Component | Source | Property | Impl | OK |
|-----------|--------|----------|------|----|
| `desk.capacity` | Cowan FOA ~4; Baddeley activated WM; Miller 7±2 | Limited workspace capacity | `FOCUS_CAP=4 + ACTIVATED_CAP=12` | yes |
| `wm.phonological` | Baddeley phonological loop | Verbal/acoustic working store | `Modality.VERBAL buffer + soft cap 6` | yes |
| `wm.visuospatial` | Baddeley visuospatial sketchpad | Structural/spatial schematic store | `Modality.STRUCT for paths/architecture` | yes |
| `wm.episodic_buffer` | Baddeley 2000 episodic buffer | Bind multimodal chunks | `bind_episode → [bind] concept` | yes |
| `wm.central_executive` | Baddeley central executive | Control: update/select/protect (inhibit, shift) | `executive_mode + do_not_say inhibit` | yes |
| `gwt.competition` | Baars/Dehaene GWT ignition/competition | Salience competition for broadcast | `compete_for_focus by salience` | yes |
| `gwt.broadcast` | GWT global broadcast + Conductor inject | Winning contents available to speech/control | `build_inject_block focus-first` | yes |
| `load.sweller` | Sweller cognitive load theory | Intrinsic / extraneous / germane | `classify_message_load` | yes |
| `load.protect` | Monotropism + high load / EF tax (ops layer) | Under high load shrink options and menus | `executive=protect + inject compression` | yes |
| `desk.verbalizable` | Anthropic J-space reportability | Contents poised for report/speech | `required say field; cli say` | yes |
| `desk.modulable` | J-space modulation + attention set | Task shifts workspace contents | `enter CLEAR + recompute_cognition(user_message)` | yes |
| `desk.pre_output` | J-space silent deliberation | Workspace before user-visible speech | `save_desk + pre_llm inject` | yes |
| `gate.selectivity` | J-space selective mediation | Not all cognition uses workspace | `gate.should_inject` | yes |
| `episodic.ring` | Conductor EpisodicStore | Capped event log | `EpisodicLog max 500` | yes |
| `semantic.consolidate` | Conductor consolidate + semantic memory | Episodes → durable notes | `semantic.consolidate()` | yes |
| `meta.tribe_encode` | Meta TRIBE v2 multi-stream encoding | Stimulus streams → neural prediction (reversed: → desk slots) | `streams.encode_stimulus text/audio/visual/production` | yes |
| `meta.b2q_decode` | Meta Brain2Qwerty brain→text decode | Internal state → linguistic report | `streams.decode_to_report → Say draft` | yes |
| `meta.production_hierarchy` | Meta thought-to-action language production | Intention → semantics → report | `production_stages in desk.meta` | yes |
| `neural.field` | GWT ignition + continuous attractor field | Vector competition for FOA / broadcast | `NeuralField + NeuralSpace.sync_from_desk` | yes |
| `neural.dual_workspace` | Symbolic desk + continuous field | Two-layer workspace (discrete + geometric) | `desk.meta['neural'] + ACTIVE concepts` | yes |
| `local.ollama_embed` | Local embedding model (nomic-embed-text) | Real vectors for FOA competition | `OllamaEmbedBackend via /api/embeddings` | yes |
| `local.verbalizer` | Local chat model reportable concepts | Behavioral verbalizable workspace | `verbalize_workspace → desk concepts` | yes |
| `neural.jlens` | Anthropic Jacobian lens | Read true activation workspace | `NOT implemented (honest gap)` | gap |

Confirmed: 22 / 23
