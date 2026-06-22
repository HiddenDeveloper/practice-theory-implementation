"""Materials for the Latent Knowledge Probe practice."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

NEURONPEDIA_BASE_URL = "https://www.neuronpedia.org"

FREE_MECH_INTERP_SURFACES = [
    {
        "id": "neuronpedia",
        "name": "Neuronpedia",
        "kind": "public_api_and_website",
        "cost": "free_public_api",
        "best_for": [
            "SAE feature dashboards",
            "feature explanations",
            "top activations",
            "custom-text feature activation tests",
        ],
        "source": "https://docs.neuronpedia.org/",
        "notes": (
            "Use as the default public feature-evidence surface when a Neuronpedia "
            "feature id is available."
        ),
    },
    {
        "id": "ndif_nnsight",
        "name": "NDIF with NNsight",
        "kind": "remote_model_internals_api",
        "cost": "free_for_research_access_account",
        "best_for": [
            "remote open-model activation reads",
            "activation interventions",
            "causal tracing",
            "large models without local GPU",
        ],
        "source": "https://ndif.us/",
        "notes": (
            "Requires NNsight and NDIF access. This material returns a runnable "
            "experiment plan rather than silently pretending remote credentials exist."
        ),
    },
    {
        "id": "transformerlens",
        "name": "TransformerLens",
        "kind": "local_python_library",
        "cost": "open_source_local_runtime",
        "best_for": [
            "activation cache",
            "activation patching",
            "hook-based interventions",
            "small and mid-size local open models",
        ],
        "source": "https://transformerlensorg.github.io/TransformerLens/",
        "notes": "Use when the target model can be loaded locally.",
    },
    {
        "id": "saelens",
        "name": "SAELens",
        "kind": "local_python_library",
        "cost": "open_source_local_runtime",
        "best_for": [
            "SAE loading",
            "SAE feature analysis",
            "training or evaluating sparse autoencoders",
        ],
        "source": "https://github.com/decoderesearch/SAELens",
        "notes": "Use with local model activations or published SAE releases.",
    },
]

CONFIDENCE_LABELS = {
    "retrieval-supported",
    "constructed-plausible",
    "activation-present-response-blocked",
    "confabulation-likely",
    "unknown",
}


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _as_list(value: object) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _parse_neuronpedia_feature_id(feature_id: str) -> dict[str, str] | None:
    """Parse MODEL@SAE:INDEX into Neuronpedia URL components."""
    if "@" not in feature_id or ":" not in feature_id:
        return None
    model_id, rest = feature_id.split("@", 1)
    sae_id, index = rest.rsplit(":", 1)
    if not model_id or not sae_id or not index:
        return None
    return {"model_id": model_id, "sae_id": sae_id, "feature_index": index}


def _feature_api_url(base_url: str, model_id: str, sae_id: str, feature_index: str) -> str:
    return (
        f"{base_url.rstrip('/')}/api/feature/"
        f"{model_id}/{sae_id}/{feature_index}"
    )


def _feature_page_url(base_url: str, model_id: str, sae_id: str, feature_index: str) -> str:
    return f"{base_url.rstrip('/')}/{model_id}/{sae_id}/{feature_index}"


def _summarize_neuronpedia_feature(payload: dict[str, Any]) -> dict[str, Any]:
    explanations = payload.get("explanations")
    if not isinstance(explanations, list):
        explanations = []
    top_explanations: list[dict[str, Any]] = []
    for item in explanations[:5]:
        if isinstance(item, dict):
            top_explanations.append(
                {
                    "description": item.get("description") or item.get("explanation"),
                    "score": item.get("score"),
                    "author": item.get("authorName") or item.get("author"),
                }
            )

    activations = payload.get("activations") or payload.get("topActivations")
    activation_count = len(activations) if isinstance(activations, list) else None
    return {
        "feature": {
            "model_id": payload.get("modelId") or payload.get("model_id"),
            "sae_id": payload.get("layer") or payload.get("saeId") or payload.get("sae_id"),
            "feature_index": payload.get("index") or payload.get("featureIndex"),
        },
        "explanations": top_explanations,
        "activation_count": activation_count,
        "has_logits": bool(
            payload.get("logits") or payload.get("pos_str") or payload.get("neg_str")
        ),
    }


def fetch_neuronpedia_feature(
    *,
    feature_id: str | None = None,
    model_id: str | None = None,
    sae_id: str | None = None,
    feature_index: str | int | None = None,
    timeout_seconds: float = 10.0,
    base_url: str = NEURONPEDIA_BASE_URL,
) -> dict[str, Any]:
    """Fetch one public Neuronpedia feature dashboard as JSON."""
    parsed = _parse_neuronpedia_feature_id(feature_id) if feature_id else None
    if parsed:
        model_id = parsed["model_id"]
        sae_id = parsed["sae_id"]
        feature_index = parsed["feature_index"]
    if not model_id or not sae_id or feature_index is None:
        return {
            "error": (
                "provide feature_id as MODEL@SAE:INDEX or provide model_id, "
                "sae_id, and feature_index"
            )
        }
    feature_index_str = str(feature_index)
    api_url = _feature_api_url(base_url, model_id, sae_id, feature_index_str)
    page_url = _feature_page_url(base_url, model_id, sae_id, feature_index_str)
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.get(api_url)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {
            "surface": "neuronpedia",
            "feature_id": f"{model_id}@{sae_id}:{feature_index_str}",
            "api_url": api_url,
            "page_url": page_url,
            "access_gap": f"Neuronpedia feature fetch failed: {type(exc).__name__}: {exc}",
        }
    if not isinstance(payload, dict):
        return {
            "surface": "neuronpedia",
            "feature_id": f"{model_id}@{sae_id}:{feature_index_str}",
            "api_url": api_url,
            "page_url": page_url,
            "access_gap": "Neuronpedia returned non-object JSON",
        }
    return {
        "surface": "neuronpedia",
        "observed_at": _now(),
        "feature_id": f"{model_id}@{sae_id}:{feature_index_str}",
        "api_url": api_url,
        "page_url": page_url,
        "summary": _summarize_neuronpedia_feature(payload),
        "raw": payload,
    }


def run_neuronpedia_activation_probe(
    custom_text: str | list[str],
    feature_id: str | None = None,
    model_id: str | None = None,
    source: str | None = None,
    feature_index: str | int | None = None,
    timeout_seconds: float = 20.0,
    base_url: str = NEURONPEDIA_BASE_URL,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run Neuronpedia-hosted custom-text activation testing for one feature."""
    parsed = _parse_neuronpedia_feature_id(feature_id) if feature_id else None
    if parsed:
        model_id = parsed["model_id"]
        source = parsed["sae_id"]
        feature_index = parsed["feature_index"]
    if not model_id or not source or feature_index is None:
        return {
            "surface": "neuronpedia",
            "error": (
                "provide feature_id as MODEL@SOURCE:INDEX or provide model_id, "
                "source, and feature_index"
            ),
        }
    feature_index_str = str(feature_index)
    endpoint = f"{base_url.rstrip('/')}/api/activation/new"
    headers = {"content-type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    payload = {
        "feature": {
            "modelId": model_id,
            "source": source,
            "index": feature_index_str,
        },
        "customText": custom_text,
    }
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as exc:
        return {
            "surface": "neuronpedia",
            "endpoint": endpoint,
            "feature_id": f"{model_id}@{source}:{feature_index_str}",
            "access_gap": (
                f"Neuronpedia activation probe returned HTTP "
                f"{exc.response.status_code}: {exc.response.text[:240]}"
            ),
            "api_key_hint": "Set NEURONPEDIA_API_KEY if this resource requires auth.",
        }
    except Exception as exc:
        return {
            "surface": "neuronpedia",
            "endpoint": endpoint,
            "feature_id": f"{model_id}@{source}:{feature_index_str}",
            "access_gap": (
                f"Neuronpedia activation probe failed: {type(exc).__name__}: {exc}"
            ),
        }
    if not isinstance(result, dict):
        return {
            "surface": "neuronpedia",
            "endpoint": endpoint,
            "feature_id": f"{model_id}@{source}:{feature_index_str}",
            "access_gap": "Neuronpedia activation probe returned non-object JSON",
        }
    tokens = result.get("tokens")
    values = result.get("values") or result.get("activations", {}).get("values")
    return {
        "surface": "neuronpedia",
        "observed_at": _now(),
        "endpoint": endpoint,
        "feature_id": f"{model_id}@{source}:{feature_index_str}",
        "custom_text": custom_text,
        "tokens": tokens if isinstance(tokens, list) else [],
        "values": values if isinstance(values, list) else [],
        "max_value": result.get("maxValue"),
        "max_value_token_index": result.get("maxValueTokenIndex")
        or result.get("activations", {}).get("maxValueIndex"),
        "raw": result,
    }


def run_neuronpedia_steering_probe(
    prompt: str,
    model_id: str,
    features: list[dict[str, Any]],
    temperature: float = 0.3,
    n_tokens: int = 32,
    freq_penalty: float = 0.0,
    seed: int = 42,
    strength_multiplier: float = 1.0,
    steer_method: str = "SIMPLE_ADDITIVE",
    timeout_seconds: float = 45.0,
    base_url: str = NEURONPEDIA_BASE_URL,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run Neuronpedia-hosted SAE feature steering for a completion prompt."""
    if not features:
        return {
            "surface": "neuronpedia",
            "error": "features must contain at least one SAE feature to steer with",
        }
    endpoint = f"{base_url.rstrip('/')}/api/steer"
    headers = {"content-type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    payload = {
        "prompt": prompt,
        "modelId": model_id,
        "features": features,
        "temperature": temperature,
        "n_tokens": n_tokens,
        "freq_penalty": freq_penalty,
        "seed": seed,
        "strength_multiplier": strength_multiplier,
        "steer_method": steer_method,
    }
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as exc:
        return {
            "surface": "neuronpedia",
            "endpoint": endpoint,
            "access_gap": (
                f"Neuronpedia steering probe returned HTTP "
                f"{exc.response.status_code}: {exc.response.text[:240]}"
            ),
            "api_key_hint": "Set NEURONPEDIA_API_KEY if this resource requires auth.",
        }
    except Exception as exc:
        return {
            "surface": "neuronpedia",
            "endpoint": endpoint,
            "access_gap": (
                f"Neuronpedia steering probe failed: {type(exc).__name__}: {exc}"
            ),
        }
    if not isinstance(result, dict):
        return {
            "surface": "neuronpedia",
            "endpoint": endpoint,
            "access_gap": "Neuronpedia steering probe returned non-object JSON",
        }
    return {
        "surface": "neuronpedia",
        "observed_at": _now(),
        "endpoint": endpoint,
        "prompt": prompt,
        "model_id": model_id,
        "features": features,
        "default_completion": result.get("DEFAULT") or result.get("default"),
        "steered_completion": result.get("STEERED") or result.get("steered"),
        "default_logprobs": result.get("defaultLogProbs"),
        "steered_logprobs": result.get("steeredLogProbs"),
        "share_url": result.get("shareUrl") or result.get("shareURL"),
        "raw": result,
    }


def _feature_brief(raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    explanations = raw.get("explanations")
    explanation_texts: list[str] = []
    if isinstance(explanations, list):
        for item in explanations[:2]:
            if isinstance(item, dict) and isinstance(item.get("description"), str):
                explanation_texts.append(item["description"])
    return {
        "model_id": raw.get("modelId"),
        "layer": raw.get("layer"),
        "index": raw.get("index"),
        "source_set_name": raw.get("sourceSetName"),
        "explanations": explanation_texts,
        "pos_str": raw.get("pos_str")[:5] if isinstance(raw.get("pos_str"), list) else [],
        "neg_str": raw.get("neg_str")[:5] if isinstance(raw.get("neg_str"), list) else [],
    }


def run_neuronpedia_topk_by_token_probe(
    text: str | list[str],
    model_id: str,
    source: str,
    num_results: int = 5,
    ignore_bos: bool = True,
    density_threshold: float = 0.01,
    timeout_seconds: float = 30.0,
    base_url: str = NEURONPEDIA_BASE_URL,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Discover top activating Neuronpedia features per token for custom text."""
    endpoint = f"{base_url.rstrip('/')}/api/search-topk-by-token"
    headers = {"content-type": "application/json"}
    if api_key:
        headers["x-api-key"] = api_key
    payload = {
        "modelId": model_id,
        "source": source,
        "text": text,
        "numResults": max(1, min(int(num_results), 20)),
        "ignoreBos": ignore_bos,
        "densityThreshold": max(0.0, min(float(density_threshold), 1.0)),
    }
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as exc:
        return {
            "surface": "neuronpedia",
            "endpoint": endpoint,
            "access_gap": (
                f"Neuronpedia top-k probe returned HTTP "
                f"{exc.response.status_code}: {exc.response.text[:240]}"
            ),
            "api_key_hint": "Set NEURONPEDIA_API_KEY if this resource requires auth.",
        }
    except Exception as exc:
        return {
            "surface": "neuronpedia",
            "endpoint": endpoint,
            "access_gap": f"Neuronpedia top-k probe failed: {type(exc).__name__}: {exc}",
        }
    if not isinstance(result, dict):
        return {
            "surface": "neuronpedia",
            "endpoint": endpoint,
            "access_gap": "Neuronpedia top-k probe returned non-object JSON",
        }

    positions: list[dict[str, Any]] = []
    for row in result.get("results") or []:
        if not isinstance(row, dict):
            continue
        features: list[dict[str, Any]] = []
        for item in row.get("topFeatures") or []:
            if not isinstance(item, dict):
                continue
            feature = item.get("feature")
            if not isinstance(feature, dict):
                feature = {
                    "modelId": model_id,
                    "layer": source,
                    "index": str(item.get("featureIndex")),
                }
            features.append(
                {
                    "activation_value": item.get("activationValue"),
                    "feature_index": item.get("featureIndex"),
                    "feature": _feature_brief(feature),
                }
            )
        positions.append(
            {
                "position": row.get("position"),
                "token": row.get("token"),
                "top_features": features,
            }
        )
    return {
        "surface": "neuronpedia",
        "observed_at": _now(),
        "endpoint": endpoint,
        "model_id": model_id,
        "source": source,
        "text": text,
        "positions": positions,
    }


def _feature_key(feature: dict[str, Any]) -> str | None:
    model_id = feature.get("model_id")
    layer = feature.get("layer")
    index = feature.get("index")
    if model_id is None or layer is None or index is None:
        return None
    return f"{model_id}@{layer}:{index}"


def _flatten_top_features(trace: dict[str, Any]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for position in trace.get("positions") or []:
        if not isinstance(position, dict):
            continue
        token = position.get("token")
        for rank, item in enumerate(position.get("top_features") or [], start=1):
            if not isinstance(item, dict):
                continue
            feature = item.get("feature")
            if not isinstance(feature, dict):
                continue
            key = _feature_key(feature)
            if key is None:
                continue
            flattened.append(
                {
                    "feature_id": key,
                    "token": token,
                    "rank": rank,
                    "activation_value": item.get("activation_value") or 0,
                    "feature": feature,
                }
            )
    return flattened


def _summarize_candidate_features(
    baseline_trace: dict[str, Any],
    comparison_traces: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    baseline_keys = {item["feature_id"] for item in _flatten_top_features(baseline_trace)}
    candidates: dict[str, dict[str, Any]] = {}
    for trace in comparison_traces:
        label = trace.get("label")
        for item in _flatten_top_features(trace):
            if item["feature_id"] in baseline_keys:
                continue
            current = candidates.setdefault(
                item["feature_id"],
                {
                    "feature_id": item["feature_id"],
                    "max_activation": 0,
                    "seen_in": [],
                    "feature": item["feature"],
                },
            )
            activation = item["activation_value"]
            if isinstance(activation, int | float):
                current["max_activation"] = max(current["max_activation"], activation)
            current["seen_in"].append(
                {
                    "label": label,
                    "token": item["token"],
                    "rank": item["rank"],
                    "activation_value": item["activation_value"],
                }
            )
    ordered = sorted(
        candidates.values(),
        key=lambda row: float(row.get("max_activation") or 0),
        reverse=True,
    )
    return ordered[: max(1, limit)]


def _steering_feature_from_candidate(
    candidate: dict[str, Any], default_strength: float
) -> dict[str, Any] | None:
    feature = candidate.get("feature")
    if not isinstance(feature, dict):
        return None
    model_id = feature.get("model_id")
    layer = feature.get("layer")
    index = feature.get("index")
    if model_id is None or layer is None or index is None:
        return None
    try:
        numeric_index = int(index)
    except (TypeError, ValueError):
        return None
    return {
        "modelId": str(model_id),
        "layer": str(layer),
        "index": numeric_index,
        "strength": default_strength,
    }


def run_latent_recovery_trial(
    baseline_text: str,
    scaffold_texts: list[str],
    final_probe_text: str,
    model_id: str,
    source: str,
    negative_control_texts: list[str] | None = None,
    num_results: int = 10,
    candidate_limit: int = 5,
    run_steering: bool = True,
    steering_strength: float = 20.0,
    steering_temperature: float = 0.3,
    steering_tokens: int = 24,
    seed: int = 42,
    timeout_seconds: float = 30.0,
    base_url: str = NEURONPEDIA_BASE_URL,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run the hosted baseline -> scaffold -> final latent-recovery pattern."""
    baseline_trace = run_neuronpedia_topk_by_token_probe(
        text=baseline_text,
        model_id=model_id,
        source=source,
        num_results=num_results,
        density_threshold=0.0,
        timeout_seconds=timeout_seconds,
        base_url=base_url,
        api_key=api_key,
    )
    baseline_trace["label"] = "baseline"

    scaffold_traces: list[dict[str, Any]] = []
    for i, text in enumerate(scaffold_texts, start=1):
        trace = run_neuronpedia_topk_by_token_probe(
            text=text,
            model_id=model_id,
            source=source,
            num_results=num_results,
            density_threshold=0.0,
            timeout_seconds=timeout_seconds,
            base_url=base_url,
            api_key=api_key,
        )
        trace["label"] = f"scaffold_{i}"
        scaffold_traces.append(trace)

    final_trace = run_neuronpedia_topk_by_token_probe(
        text=final_probe_text,
        model_id=model_id,
        source=source,
        num_results=num_results,
        density_threshold=0.0,
        timeout_seconds=timeout_seconds,
        base_url=base_url,
        api_key=api_key,
    )
    final_trace["label"] = "final_probe"

    control_traces: list[dict[str, Any]] = []
    for i, text in enumerate(negative_control_texts or [], start=1):
        trace = run_neuronpedia_topk_by_token_probe(
            text=text,
            model_id=model_id,
            source=source,
            num_results=num_results,
            density_threshold=0.0,
            timeout_seconds=timeout_seconds,
            base_url=base_url,
            api_key=api_key,
        )
        trace["label"] = f"negative_control_{i}"
        control_traces.append(trace)

    access_gaps = [
        trace.get("access_gap")
        for trace in [baseline_trace, *scaffold_traces, final_trace, *control_traces]
        if trace.get("access_gap")
    ]
    candidate_features = _summarize_candidate_features(
        baseline_trace,
        [*scaffold_traces, final_trace],
        limit=candidate_limit,
    )
    control_feature_ids = {
        item["feature_id"]
        for trace in control_traces
        for item in _flatten_top_features(trace)
    }
    for candidate in candidate_features:
        candidate["appears_in_negative_control"] = (
            candidate["feature_id"] in control_feature_ids
        )

    steering_result: dict[str, Any] | None = None
    if run_steering and candidate_features:
        feature = _steering_feature_from_candidate(candidate_features[0], steering_strength)
        if feature is not None:
            steering_result = run_neuronpedia_steering_probe(
                prompt=baseline_text,
                model_id=model_id,
                features=[feature],
                temperature=steering_temperature,
                n_tokens=steering_tokens,
                seed=seed,
                timeout_seconds=timeout_seconds,
                base_url=base_url,
                api_key=api_key,
            )
        else:
            steering_result = {
                "surface": "neuronpedia",
                "access_gap": "top candidate could not be converted to steering feature",
            }

    recommendation = "unknown"
    recommendation_basis: list[str] = []
    if access_gaps:
        recommendation_basis.append("one or more hosted Neuronpedia calls had access gaps")
    if candidate_features:
        recommendation_basis.append(
            "scaffold/final traces recruited candidate features absent from baseline top-k"
        )
        recommendation = "latent-recruitment-candidate"
    if candidate_features and all(
        not candidate.get("appears_in_negative_control")
        for candidate in candidate_features[: min(3, len(candidate_features))]
    ):
        recommendation_basis.append("top candidates were not present in negative controls")
    if steering_result and not steering_result.get("access_gap"):
        recommendation_basis.append("hosted steering returned default/steered comparison")
        recommendation = "latent-recruitment-with-intervention-candidate"

    return {
        "surface": "neuronpedia",
        "observed_at": _now(),
        "model_id": model_id,
        "source": source,
        "baseline": baseline_trace,
        "scaffolds": scaffold_traces,
        "final_probe": final_trace,
        "negative_controls": control_traces,
        "candidate_features": candidate_features,
        "steering_result": steering_result,
        "access_gaps": access_gaps,
        "confidence_recommendation": recommendation,
        "recommendation_basis": recommendation_basis,
        "interpretation_limits": [
            (
                "This material discovers and intervenes on features; it does not "
                "prove hidden factual recovery by itself."
            ),
            (
                "Use downstream judgment to compare answer quality, prompt leakage, "
                "controls, and steering effects."
            ),
        ],
    }


def _format_turns(turns: list[dict[str, Any]], upto: int | None = None) -> str:
    selected = turns if upto is None else turns[:upto]
    lines: list[str] = []
    for turn in selected:
        speaker = str(turn.get("speaker") or "unknown").strip() or "unknown"
        text = str(turn.get("text") or "").strip()
        if not text:
            continue
        lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


def run_interactive_latent_positioning_trial(
    turns: list[dict[str, Any]],
    model_id: str,
    source: str,
    target_probe_text: str | None = None,
    negative_control_turns: list[dict[str, Any]] | None = None,
    num_results: int = 10,
    candidate_limit: int = 5,
    run_steering: bool = True,
    steering_strength: float = 20.0,
    steering_temperature: float = 0.3,
    steering_tokens: int = 24,
    seed: int = 42,
    timeout_seconds: float = 30.0,
    base_url: str = NEURONPEDIA_BASE_URL,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Run a cumulative, interactive latent-positioning transcript trial."""
    if not turns:
        return {"surface": "neuronpedia", "error": "turns must not be empty"}

    turn_traces: list[dict[str, Any]] = []
    for i in range(1, len(turns) + 1):
        cumulative_text = _format_turns(turns, upto=i)
        trace = run_neuronpedia_topk_by_token_probe(
            text=cumulative_text,
            model_id=model_id,
            source=source,
            num_results=num_results,
            density_threshold=0.0,
            timeout_seconds=timeout_seconds,
            base_url=base_url,
            api_key=api_key,
        )
        trace["label"] = f"turn_{i}"
        trace["turn_index"] = i
        trace["latest_turn"] = turns[i - 1]
        trace["cumulative_text"] = cumulative_text
        turn_traces.append(trace)

    baseline_trace = turn_traces[0]
    target_trace: dict[str, Any] | None = None
    if target_probe_text:
        target_text = _format_turns(turns) + "\nprobe: " + target_probe_text
        target_trace = run_neuronpedia_topk_by_token_probe(
            text=target_text,
            model_id=model_id,
            source=source,
            num_results=num_results,
            density_threshold=0.0,
            timeout_seconds=timeout_seconds,
            base_url=base_url,
            api_key=api_key,
        )
        target_trace["label"] = "target_probe"
        target_trace["cumulative_text"] = target_text

    control_traces: list[dict[str, Any]] = []
    if negative_control_turns:
        for i in range(1, len(negative_control_turns) + 1):
            cumulative_text = _format_turns(negative_control_turns, upto=i)
            trace = run_neuronpedia_topk_by_token_probe(
                text=cumulative_text,
                model_id=model_id,
                source=source,
                num_results=num_results,
                density_threshold=0.0,
                timeout_seconds=timeout_seconds,
                base_url=base_url,
                api_key=api_key,
            )
            trace["label"] = f"negative_control_turn_{i}"
            trace["turn_index"] = i
            trace["latest_turn"] = negative_control_turns[i - 1]
            trace["cumulative_text"] = cumulative_text
            control_traces.append(trace)

    comparison_traces = [*turn_traces[1:]]
    if target_trace is not None:
        comparison_traces.append(target_trace)
    candidate_features = _summarize_candidate_features(
        baseline_trace,
        comparison_traces,
        limit=candidate_limit,
    )

    control_feature_ids = {
        item["feature_id"]
        for trace in control_traces
        for item in _flatten_top_features(trace)
    }
    first_seen_by_feature: dict[str, dict[str, Any]] = {}
    for trace in comparison_traces:
        for item in _flatten_top_features(trace):
            first_seen_by_feature.setdefault(
                item["feature_id"],
                {
                    "label": trace.get("label"),
                    "turn_index": trace.get("turn_index"),
                    "latest_turn": trace.get("latest_turn"),
                    "token": item.get("token"),
                    "activation_value": item.get("activation_value"),
                },
            )
    for candidate in candidate_features:
        candidate["appears_in_negative_control"] = (
            candidate["feature_id"] in control_feature_ids
        )
        candidate["first_seen"] = first_seen_by_feature.get(candidate["feature_id"])

    steering_result: dict[str, Any] | None = None
    if run_steering and candidate_features:
        feature = _steering_feature_from_candidate(candidate_features[0], steering_strength)
        if feature is not None:
            steering_result = run_neuronpedia_steering_probe(
                prompt=_format_turns(turns),
                model_id=model_id,
                features=[feature],
                temperature=steering_temperature,
                n_tokens=steering_tokens,
                seed=seed,
                timeout_seconds=timeout_seconds,
                base_url=base_url,
                api_key=api_key,
            )
        else:
            steering_result = {
                "surface": "neuronpedia",
                "access_gap": "top candidate could not be converted to steering feature",
            }

    traces_for_gap_check = [
        *turn_traces,
        *control_traces,
        *([target_trace] if target_trace else []),
    ]
    access_gaps = [
        trace.get("access_gap")
        for trace in traces_for_gap_check
        if trace and trace.get("access_gap")
    ]
    recommendation = "unknown"
    recommendation_basis: list[str] = []
    if candidate_features:
        recommendation = "interactive-latent-positioning-candidate"
        recommendation_basis.append(
            "later cumulative turns recruited candidate features absent from the first turn"
        )
    if candidate_features and all(
        not candidate.get("appears_in_negative_control")
        for candidate in candidate_features[: min(3, len(candidate_features))]
    ):
        recommendation_basis.append("top candidates were not present in control transcript")
    if steering_result and not steering_result.get("access_gap"):
        recommendation = "interactive-latent-positioning-with-intervention-candidate"
        recommendation_basis.append("hosted steering returned default/steered comparison")
    if access_gaps:
        recommendation_basis.append("one or more hosted Neuronpedia calls had access gaps")

    return {
        "surface": "neuronpedia",
        "observed_at": _now(),
        "model_id": model_id,
        "source": source,
        "turn_traces": turn_traces,
        "target_probe": target_trace,
        "negative_controls": control_traces,
        "candidate_features": candidate_features,
        "steering_result": steering_result,
        "access_gaps": access_gaps,
        "confidence_recommendation": recommendation,
        "recommendation_basis": recommendation_basis,
        "interpretation_limits": [
            (
                "This material analyzes a transcript path; it does not generate "
                "the responding model's missing turns by itself."
            ),
            (
                "Evidence is strongest when assistant responses are real, controls "
                "are comparable, and steering changes the target response."
            ),
        ],
    }


def latent_probe_design_protocol(
    target_model: str | None = None,
    mechanistic_surfaces: list[str] | None = None,
    question_family: str | None = None,
    model_runtime: str | None = None,
    known_targets: list[str] | None = None,
    unknown_controls: list[str] | None = None,
    planted_or_misleading_controls: list[str] | None = None,
    intervention_plan: list[str] | None = None,
    stopping_conditions: list[str] | None = None,
    gaps: list[str] | None = None,
) -> dict[str, Any]:
    """Prepare the concrete free/open interpretability route for a probe."""
    if not target_model:
        return {"error": "provide target_model"}
    if not question_family:
        return {"error": "provide question_family"}
    requested = {
        s.strip().lower() for s in (mechanistic_surfaces or []) if isinstance(s, str)
    }
    selected = [
        surface
        for surface in FREE_MECH_INTERP_SURFACES
        if surface["id"] in requested or surface["name"].lower() in requested
    ]
    if not selected:
        selected = FREE_MECH_INTERP_SURFACES[:2]
    return {
        "target_model": target_model,
        "model_runtime": model_runtime,
        "question_family": question_family,
        "selected_free_surfaces": selected,
        "controls": {
            "known_targets": known_targets or [],
            "unknown_controls": unknown_controls or [],
            "planted_or_misleading_controls": planted_or_misleading_controls or [],
        },
        "intervention_plan": intervention_plan or [
            "Use Neuronpedia feature evidence when feature ids exist.",
            "Use NNsight/NDIF or TransformerLens for activation read/intervention.",
            "Do not upgrade confidence without causal or counterfactual checks.",
        ],
        "stopping_conditions": stopping_conditions or [
            "No mechanistic surface is reachable.",
            "Behavioral and mechanistic evidence diverge without a discriminating next probe.",
            "Controls show prompt suggestibility or planted-fact uptake.",
        ],
        "gaps": gaps or [],
        "nnsight_ndif_plan": {
            "install": "pip install nnsight",
            "remote_access": "create free NDIF research account if remote=True is needed",
            "sketch": [
                "from nnsight import LanguageModel",
                "model = LanguageModel(target_model, device_map='auto', dispatch=True)",
                "with model.trace(prompt, remote=True): save hidden states or intervene",
            ],
        },
        "source_notes": [
            "Neuronpedia is the default public API surface for SAE feature dashboards.",
            (
                "NDIF/NNsight is the default remote open-model internals route "
                "when credentials are available."
            ),
            (
                "TransformerLens/SAELens are local-library routes when the model "
                "and SAE can be loaded locally."
            ),
        ],
    }


def latent_probe_record_trial(
    as_of: str,
    prompt: str,
    target_model: str | None = None,
    model_response: str | None = None,
    scaffolding_move: str | None = None,
    mechanistic_observations: list[dict[str, Any]] | None = None,
    relational_observations: list[str] | None = None,
    intervention_results: list[dict[str, Any]] | None = None,
    control_results: list[dict[str, Any]] | None = None,
    neuronpedia_features: list[dict[str, Any] | str] | None = None,
    gaps: list[str] | None = None,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """Record one probe trial, enriching it with public Neuronpedia evidence."""
    if not target_model:
        return {"error": "provide target_model"}
    if model_response is None:
        return {"error": "provide model_response"}
    fetched_features: list[dict[str, Any]] = []
    for feature in _as_list(neuronpedia_features):
        if isinstance(feature, str):
            fetched_features.append(
                fetch_neuronpedia_feature(
                    feature_id=feature, timeout_seconds=timeout_seconds
                )
            )
        elif isinstance(feature, dict):
            fetched_features.append(
                fetch_neuronpedia_feature(
                    feature_id=feature.get("feature_id"),
                    model_id=feature.get("model_id"),
                    sae_id=feature.get("sae_id"),
                    feature_index=feature.get("feature_index"),
                    timeout_seconds=timeout_seconds,
                )
            )
    combined_mechanistic = list(mechanistic_observations or [])
    combined_mechanistic.extend(fetched_features)
    access_gaps = [
        item.get("access_gap")
        for item in fetched_features
        if isinstance(item, dict) and item.get("access_gap")
    ]
    return {
        "as_of": as_of,
        "recorded_at": _now(),
        "target_model": target_model,
        "prompt": prompt,
        "scaffolding_move": scaffolding_move,
        "model_response": model_response,
        "relational_observations": relational_observations or [],
        "mechanistic_observations": combined_mechanistic,
        "intervention_results": intervention_results or [],
        "control_results": control_results or [],
        "gaps": [*(gaps or []), *access_gaps],
    }


def _optional_import_error() -> dict[str, Any] | None:
    missing: list[str] = []
    for module_name in ("torch", "transformer_lens"):
        try:
            __import__(module_name)
        except Exception as exc:
            missing.append(f"{module_name}: {type(exc).__name__}: {exc}")
    if not missing:
        return None
    return {
        "surface": "transformerlens",
        "access_gap": "TransformerLens local runtime is not installed",
        "missing": missing,
        "install": "uv add --optional mechinterp transformer-lens torch",
        "direct_install": "uv pip install transformer-lens torch",
    }


def run_transformerlens_activation_probe(
    prompt: str,
    model_name: str = "gpt2-small",
    activation_names: list[str] | None = None,
    target_token: str | None = None,
    control_prompts: list[str] | None = None,
    ablate_activation_name: str | None = None,
    ablate_position: int = -1,
    device: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Run a local TransformerLens activation-cache probe when deps are present.

    This is intentionally conservative: it records activation shapes and summary
    norms, top next-token predictions, optional control-prompt summaries, and one
    simple zero-ablation contrast. It does not claim a circuit by itself.
    """
    if gap := _optional_import_error():
        return {
            **gap,
            "planned_probe": {
                "model_name": model_name,
                "prompt": prompt,
                "activation_names": activation_names or [],
                "target_token": target_token,
                "control_prompts": control_prompts or [],
                "ablate_activation_name": ablate_activation_name,
                "ablate_position": ablate_position,
            },
        }

    import torch
    from transformer_lens import HookedTransformer

    selected_names = set(activation_names or ["blocks.0.hook_resid_pre"])

    def names_filter(name: str) -> bool:
        return name in selected_names

    model_kwargs: dict[str, Any] = {}
    if device:
        model_kwargs["device"] = device
    model = HookedTransformer.from_pretrained(model_name, **model_kwargs)
    tokens = model.to_tokens(prompt)
    logits, cache = model.run_with_cache(tokens, names_filter=names_filter)

    final_logits = logits[0, -1]
    top_k = max(1, min(int(top_k), 25))
    top = torch.topk(final_logits, k=top_k)
    top_predictions = [
        {
            "token": model.to_string(int(token_id)),
            "token_id": int(token_id),
            "logit": float(logit),
        }
        for logit, token_id in zip(top.values, top.indices, strict=False)
    ]

    target: dict[str, Any] | None = None
    if target_token:
        target_tokens = model.to_tokens(target_token, prepend_bos=False)[0]
        if len(target_tokens) == 1:
            token_id = int(target_tokens[0])
            target = {
                "token": target_token,
                "token_id": token_id,
                "clean_logit": float(final_logits[token_id]),
            }
        else:
            target = {
                "token": target_token,
                "access_gap": "target_token must tokenize to exactly one token",
                "token_ids": [int(t) for t in target_tokens],
            }

    activation_summaries: list[dict[str, Any]] = []
    for name in selected_names:
        if name not in cache:
            activation_summaries.append({"name": name, "access_gap": "not present in cache"})
            continue
        value = cache[name]
        activation_summaries.append(
            {
                "name": name,
                "shape": list(value.shape),
                "mean": float(value.float().mean()),
                "norm": float(value.float().norm()),
            }
        )

    controls: list[dict[str, Any]] = []
    for control_prompt in control_prompts or []:
        control_tokens = model.to_tokens(control_prompt)
        control_logits = model(control_tokens)[0, -1]
        control_top = torch.topk(control_logits, k=min(top_k, 5))
        controls.append(
            {
                "prompt": control_prompt,
                "top_predictions": [
                    {
                        "token": model.to_string(int(token_id)),
                        "token_id": int(token_id),
                        "logit": float(logit),
                    }
                    for logit, token_id in zip(
                        control_top.values, control_top.indices, strict=False
                    )
                ],
            }
        )

    ablation: dict[str, Any] | None = None
    if ablate_activation_name:
        if ablate_activation_name not in selected_names:
            return {
                "surface": "transformerlens",
                "access_gap": (
                    "ablate_activation_name must also be included in activation_names "
                    "so the clean cache and intervention name are explicit"
                ),
            }

        def zero_ablate(activation: Any, _hook: Any) -> Any:
            patched = activation.clone()
            patched[:, ablate_position, :] = 0
            return patched

        patched_logits = model.run_with_hooks(
            tokens, fwd_hooks=[(ablate_activation_name, zero_ablate)]
        )[0, -1]
        ablation = {
            "activation_name": ablate_activation_name,
            "position": ablate_position,
            "top_prediction_after_ablation": model.to_string(
                int(torch.argmax(patched_logits))
            ),
        }
        if target and "token_id" in target and "clean_logit" in target:
            patched_logit = float(patched_logits[int(target["token_id"])])
            ablation["target_patched_logit"] = patched_logit
            ablation["target_logit_delta"] = patched_logit - float(target["clean_logit"])

    return {
        "surface": "transformerlens",
        "observed_at": _now(),
        "model_name": model_name,
        "prompt": prompt,
        "top_predictions": top_predictions,
        "target": target,
        "activation_summaries": activation_summaries,
        "control_results": controls,
        "ablation_result": ablation,
        "interpretation_limits": [
            "Activation norms and top-token shifts are evidence, not a circuit explanation.",
            "A retrieval-supported judgment still needs controls and causal convergence.",
        ],
    }


def latent_probe_confidence_judgment(
    claim: str,
    classification: str,
    confidence: str,
    behavioral_evidence: list[str] | None = None,
    mechanistic_evidence: list[str] | None = None,
    causal_evidence: list[str] | None = None,
    control_evidence: list[str] | None = None,
    counterevidence: list[str] | None = None,
    missing_registers: list[str] | None = None,
    next_probe: str | None = None,
) -> dict[str, Any]:
    """Record a bounded confidence judgment and flag over-strong labels."""
    behavioral = behavioral_evidence or []
    mechanistic = mechanistic_evidence or []
    causal = causal_evidence or []
    controls = control_evidence or []
    missing = list(missing_registers or [])
    warnings: list[str] = []
    if classification not in CONFIDENCE_LABELS:
        warnings.append(
            f"classification {classification!r} is outside the practice label set"
        )
    if classification == "retrieval-supported":
        required = {
            "behavioral_evidence": behavioral,
            "mechanistic_evidence": mechanistic,
            "causal_evidence": causal,
            "control_evidence": controls,
        }
        absent = [name for name, values in required.items() if not values]
        if absent:
            warnings.append(
                "retrieval-supported is over-strong without: " + ", ".join(absent)
            )
            missing.extend(absent)
    return {
        "claim": claim,
        "classification": classification,
        "confidence": confidence,
        "behavioral_evidence": behavioral,
        "mechanistic_evidence": mechanistic,
        "causal_evidence": causal,
        "control_evidence": controls,
        "counterevidence": counterevidence or [],
        "missing_registers": sorted(set(missing)),
        "next_probe": next_probe,
        "warnings": warnings,
    }
