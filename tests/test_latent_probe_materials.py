from __future__ import annotations

from practice_theory_implementation import registry
from practice_theory_implementation.material_surfaces import MATERIAL_SURFACES
from practice_theory_implementation.materials import latent_probe
from practice_theory_implementation.substrate_loader import load_substrate


def test_latent_probe_protocol_selects_free_mech_interp_surfaces() -> None:
    result = latent_probe.latent_probe_design_protocol(
        target_model="meta-llama/Meta-Llama-3.1-8B",
        mechanistic_surfaces=["neuronpedia", "ndif_nnsight"],
        question_family="factual recall",
    )

    assert [s["id"] for s in result["selected_free_surfaces"]] == [
        "neuronpedia",
        "ndif_nnsight",
    ]
    assert "pip install nnsight" in result["nnsight_ndif_plan"]["install"]


def test_latent_probe_record_trial_enriches_with_neuronpedia(
    monkeypatch,
) -> None:
    def fake_fetch(**kwargs):
        return {
            "surface": "neuronpedia",
            "feature_id": kwargs["feature_id"],
            "summary": {"explanations": [{"description": "test feature"}]},
        }

    monkeypatch.setattr(latent_probe, "fetch_neuronpedia_feature", fake_fetch)

    result = latent_probe.latent_probe_record_trial(
        as_of="2026-06-22T00:00:00Z",
        target_model="gpt2-small",
        prompt="The Eiffel Tower is in",
        model_response="Paris",
        neuronpedia_features=["gpt2-small@6-res_scefr-ajt:650"],
    )

    assert result["mechanistic_observations"][0]["surface"] == "neuronpedia"
    assert result["mechanistic_observations"][0]["feature_id"] == (
        "gpt2-small@6-res_scefr-ajt:650"
    )


def test_neuronpedia_activation_probe_posts_custom_text(monkeypatch) -> None:
    captured = {}

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "tokens": ["Hello"],
                "values": [1.5],
                "maxValue": 1.5,
                "maxValueTokenIndex": 0,
            }

    class _Client:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, endpoint, json, headers):
            captured["endpoint"] = endpoint
            captured["json"] = json
            captured["headers"] = headers
            return _Response()

    monkeypatch.setattr(latent_probe.httpx, "Client", _Client)

    result = latent_probe.run_neuronpedia_activation_probe(
        feature_id="gpt2-small@9-res-jb:200",
        custom_text="Hello",
        api_key="secret",
    )

    assert result["surface"] == "neuronpedia"
    assert result["values"] == [1.5]
    assert captured["endpoint"].endswith("/api/activation/new")
    assert captured["json"]["feature"] == {
        "modelId": "gpt2-small",
        "source": "9-res-jb",
        "index": "200",
    }
    assert captured["headers"]["x-api-key"] == "secret"


def test_neuronpedia_topk_probe_posts_search_request(monkeypatch) -> None:
    captured = {}

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "source": "6-res_scefr-ajt",
                "results": [
                    {
                        "position": 0,
                        "token": " long",
                        "topFeatures": [
                            {
                                "activationValue": 2.5,
                                "featureIndex": 650,
                                "feature": {
                                    "modelId": "gpt2-small",
                                    "layer": "6-res_scefr-ajt",
                                    "index": "650",
                                    "explanations": [
                                        {"description": "measurement feature"}
                                    ],
                                    "pos_str": [" meters"],
                                    "neg_str": ["apple"],
                                },
                            }
                        ],
                    }
                ],
            }

    class _Client:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, endpoint, json, headers):
            captured["endpoint"] = endpoint
            captured["json"] = json
            captured["headers"] = headers
            return _Response()

    monkeypatch.setattr(latent_probe.httpx, "Client", _Client)

    result = latent_probe.run_neuronpedia_topk_by_token_probe(
        text="The bridge was long.",
        model_id="gpt2-small",
        source="6-res_scefr-ajt",
        num_results=3,
    )

    assert result["surface"] == "neuronpedia"
    assert result["positions"][0]["top_features"][0]["activation_value"] == 2.5
    assert result["positions"][0]["top_features"][0]["feature"]["explanations"] == [
        "measurement feature"
    ]
    assert captured["endpoint"].endswith("/api/search-topk-by-token")
    assert captured["json"]["numResults"] == 3


def test_neuronpedia_topk_probe_handles_slim_feature_response(monkeypatch) -> None:
    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "source": "0-gemmascope-res-16k",
                "results": [
                    {
                        "position": 0,
                        "token": "Hello",
                        "topFeatures": [
                            {"activationValue": 49.0, "featureIndex": 12231}
                        ],
                    }
                ],
            }

    class _Client:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, endpoint, json, headers):
            return _Response()

    monkeypatch.setattr(latent_probe.httpx, "Client", _Client)

    result = latent_probe.run_neuronpedia_topk_by_token_probe(
        text="Hello",
        model_id="gemma-2-2b-it",
        source="0-gemmascope-res-16k",
        num_results=1,
    )

    feature = result["positions"][0]["top_features"][0]["feature"]
    assert feature["model_id"] == "gemma-2-2b-it"
    assert feature["layer"] == "0-gemmascope-res-16k"
    assert feature["index"] == "12231"


def test_neuronpedia_steering_probe_posts_feature_intervention(monkeypatch) -> None:
    captured = {}

    class _Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "DEFAULT": "default text",
                "STEERED": "steered text",
                "steeredLogProbs": [{"token": " long"}],
            }

    class _Client:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def post(self, endpoint, json, headers):
            captured["endpoint"] = endpoint
            captured["json"] = json
            captured["headers"] = headers
            return _Response()

    monkeypatch.setattr(latent_probe.httpx, "Client", _Client)

    feature = {
        "modelId": "gpt2-small",
        "layer": "6-res_scefr-ajt",
        "index": 650,
        "strength": 20,
    }
    result = latent_probe.run_neuronpedia_steering_probe(
        prompt="The old bridge was",
        model_id="gpt2-small",
        features=[feature],
        seed=7,
    )

    assert result["surface"] == "neuronpedia"
    assert result["default_completion"] == "default text"
    assert result["steered_completion"] == "steered text"
    assert captured["endpoint"].endswith("/api/steer")
    assert captured["json"]["features"] == [feature]
    assert captured["json"]["seed"] == 7


def test_latent_recovery_trial_selects_scaffold_recruited_candidate(monkeypatch) -> None:
    def fake_topk(**kwargs):
        text = kwargs["text"]
        if text == "baseline":
            index = "1"
            activation = 5.0
        elif text == "control":
            index = "3"
            activation = 4.0
        else:
            index = "2"
            activation = 9.0
        return {
            "surface": "neuronpedia",
            "positions": [
                {
                    "position": 0,
                    "token": " token",
                    "top_features": [
                        {
                            "activation_value": activation,
                            "feature_index": int(index),
                            "feature": {
                                "model_id": "gpt2-small",
                                "layer": "6-res_scefr-ajt",
                                "index": index,
                                "explanations": ["candidate"],
                                "pos_str": [],
                                "neg_str": [],
                            },
                        }
                    ],
                }
            ],
        }

    def fake_steer(**kwargs):
        return {
            "surface": "neuronpedia",
            "default_completion": "default",
            "steered_completion": "steered",
            "features": kwargs["features"],
        }

    monkeypatch.setattr(latent_probe, "run_neuronpedia_topk_by_token_probe", fake_topk)
    monkeypatch.setattr(latent_probe, "run_neuronpedia_steering_probe", fake_steer)

    result = latent_probe.run_latent_recovery_trial(
        baseline_text="baseline",
        scaffold_texts=["scaffold"],
        final_probe_text="final",
        model_id="gpt2-small",
        source="6-res_scefr-ajt",
        negative_control_texts=["control"],
    )

    assert result["candidate_features"][0]["feature_id"] == (
        "gpt2-small@6-res_scefr-ajt:2"
    )
    assert result["steering_result"]["features"][0]["index"] == 2
    assert result["confidence_recommendation"] == (
        "latent-recruitment-with-intervention-candidate"
    )


def test_interactive_latent_positioning_uses_cumulative_turns(monkeypatch) -> None:
    seen_texts = []

    def fake_topk(**kwargs):
        text = kwargs["text"]
        seen_texts.append(text)
        index = "1" if "notebook" not in text else "2"
        return {
            "surface": "neuronpedia",
            "positions": [
                {
                    "position": 0,
                    "token": " token",
                    "top_features": [
                        {
                            "activation_value": 8.0,
                            "feature_index": int(index),
                            "feature": {
                                "model_id": "gpt2-small",
                                "layer": "6-res_scefr-ajt",
                                "index": index,
                                "explanations": ["candidate"],
                                "pos_str": [],
                                "neg_str": [],
                            },
                        }
                    ],
                }
            ],
        }

    def fake_steer(**kwargs):
        return {
            "surface": "neuronpedia",
            "default_completion": "default",
            "steered_completion": "steered",
            "features": kwargs["features"],
        }

    monkeypatch.setattr(latent_probe, "run_neuronpedia_topk_by_token_probe", fake_topk)
    monkeypatch.setattr(latent_probe, "run_neuronpedia_steering_probe", fake_steer)

    result = latent_probe.run_interactive_latent_positioning_trial(
        turns=[
            {"speaker": "user", "text": "Wow that's an old bridge."},
            {"speaker": "assistant", "text": "It sounds weathered and historic."},
            {"speaker": "user", "text": "I found an engineering notebook."},
        ],
        model_id="gpt2-small",
        source="6-res_scefr-ajt",
        negative_control_turns=[{"speaker": "user", "text": "I bought apples."}],
    )

    assert "assistant: It sounds weathered and historic." in seen_texts[1]
    assert result["candidate_features"][0]["feature_id"] == (
        "gpt2-small@6-res_scefr-ajt:2"
    )
    assert result["candidate_features"][0]["first_seen"]["turn_index"] == 3
    assert result["confidence_recommendation"] == (
        "interactive-latent-positioning-with-intervention-candidate"
    )


def test_confidence_judgment_flags_overstrong_retrieval_supported() -> None:
    result = latent_probe.latent_probe_confidence_judgment(
        claim="model knows the answer",
        classification="retrieval-supported",
        confidence="high",
        behavioral_evidence=["answered consistently"],
    )

    assert result["warnings"]
    assert "mechanistic_evidence" in result["missing_registers"]
    assert "causal_evidence" in result["missing_registers"]
    assert "control_evidence" in result["missing_registers"]


def test_transformerlens_probe_reports_install_gap_when_runtime_missing() -> None:
    result = latent_probe.run_transformerlens_activation_probe(
        prompt="The Eiffel Tower is in the city of",
        model_name="gpt2-small",
        activation_names=["blocks.0.hook_resid_pre"],
        target_token=" Paris",
        control_prompts=["The Eiffel Tower is in the city of Rome"],
        ablate_activation_name="blocks.0.hook_resid_pre",
    )

    if result.get("access_gap"):
        assert result["surface"] == "transformerlens"
        assert "install" in result
        assert result["planned_probe"]["target_token"] == " Paris"
    else:
        assert result["surface"] == "transformerlens"
        assert result["activation_summaries"]
        assert result["ablation_result"]["activation_name"] == "blocks.0.hook_resid_pre"


def test_latent_probe_bundle_loads_with_code_owned_materials() -> None:
    loaded = load_substrate(material_surfaces=MATERIAL_SURFACES)

    assert loaded.errors == []
    registry.validate_against(loaded.substrate)
    bundle = loaded.bundles["latent_knowledge_probe"]
    assert "design_latent_probe_protocol" in bundle.affordance_ids
    assert "discover_neuronpedia_topk_features" in bundle.affordance_ids
    assert "run_neuronpedia_activation_probe" in bundle.affordance_ids
    assert "run_neuronpedia_steering_probe" in bundle.affordance_ids
    assert "run_latent_recovery_trial" in bundle.affordance_ids
    assert "run_interactive_latent_positioning_trial" in bundle.affordance_ids
    assert "run_transformerlens_activation_probe" in bundle.affordance_ids
    assert "latent_probe_record_trial" in loaded.substrate.materials
    assert "run_neuronpedia_topk_by_token_probe" in loaded.substrate.materials
    assert "run_neuronpedia_activation_probe" in loaded.substrate.materials
    assert "run_neuronpedia_steering_probe" in loaded.substrate.materials
    assert "run_latent_recovery_trial" in loaded.substrate.materials
    assert "run_interactive_latent_positioning_trial" in loaded.substrate.materials
    assert "run_transformerlens_activation_probe" in loaded.substrate.materials
