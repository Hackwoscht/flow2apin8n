"""Model name resolver - converts simplified model names + generationConfig params to internal MODEL_CONFIG keys.

When upstream services (e.g. New API) send requests with a generic model name
along with generationConfig containing aspectRatio / imageSize, this module
resolves them to the specific internal model name used by flow2api.

Example:
    model = "gemini-3.0-pro-image"
    generationConfig.imageConfig.aspectRatio = "16:9"
    generationConfig.imageConfig.imageSize = "2k"
    → resolved to "gemini-3.0-pro-image-landscape-2k"
"""

from typing import Optional, Dict, Any, Tuple
from ..core.logger import debug_logger

# ──────────────────────────────────────────────
# VereinfachtModellname → BasisGrundlageModellnamevorSuffix ZuordnungZuordnung
# ──────────────────────────────────────────────
IMAGE_BASE_MODELS = {
    # Gemini 2.5 Flash (GEM_PIX)
    "gemini-2.5-flash-image": "gemini-2.5-flash-image",
    # Gemini 3.0 Pro (GEM_PIX_2)
    "gemini-3.0-pro-image": "gemini-3.0-pro-image",
    # Gemini 3.1 Flash (NARWHAL)
    "gemini-3.1-flash-image": "gemini-3.1-flash-image",
    # Imagen 4.0 (IMAGEN_3_5)
    "imagen-4.0-generate-preview": "imagen-4.0-generate-preview",
}

# ──────────────────────────────────────────────
# aspectRatio KonvertierenZuordnungZuordnung
# Unterstuetzt Gemini OriginalGenerierenFormat ("16:9") UndinnerhalbTeilFormat ("landscape")
# ──────────────────────────────────────────────
ASPECT_RATIO_MAP = {
    # Gemini Standard ratio Format
    "16:9": "landscape",
    "9:16": "portrait",
    "1:1": "square",
    "4:3": "four-three",
    "3:4": "three-four",
    # EnglischTextNameDirektZuordnungZuordnung
    "landscape": "landscape",
    "portrait": "portrait",
    "square": "square",
    "four-three": "four-three",
    "three-four": "three-four",
    "four_three": "four-three",
    "three_four": "three-four",
    # grossschreibenFormFormat
    "LANDSCAPE": "landscape",
    "PORTRAIT": "portrait",
    "SQUARE": "square",
}

# jedeStueckBasisGrundlageModellUnterstuetzt aspectRatio Liste
# wieErgebnisAnfrage ratio nichtinUnterstuetztListein, HerabstufenLevelaufStandardWert
MODEL_SUPPORTED_ASPECTS = {
    "gemini-2.5-flash-image": ["landscape", "portrait"],
    "gemini-3.0-pro-image": [
        "landscape",
        "portrait",
        "square",
        "four-three",
        "three-four",
    ],
    "gemini-3.1-flash-image": [
        "landscape",
        "portrait",
        "square",
        "four-three",
        "three-four",
    ],
    "imagen-4.0-generate-preview": ["landscape", "portrait"],
}

# jedeStueckBasisGrundlageModellUnterstuetzt imageSize(UnterscheidenRate)Liste
MODEL_SUPPORTED_SIZES = {
    "gemini-2.5-flash-image": [],  # nichtUnterstuetztUpscale
    "gemini-3.0-pro-image": ["2k", "4k"],
    "gemini-3.1-flash-image": ["2k", "4k"],
    "imagen-4.0-generate-preview": [],  # nichtUnterstuetztUpscale
}

# imageSize NormalisiereneinisierenZuordnungZuordnung
IMAGE_SIZE_MAP = {
    "1k": "1k",
    "1K": "1k",
    "2k": "2k",
    "2K": "2k",
    "4k": "4k",
    "4K": "4k",
    "": "",
}

# Standard aspectRatio
DEFAULT_ASPECT = "landscape"


# ──────────────────────────────────────────────
# VideoModellVereinfachtNameZuordnungZuordnung
# ──────────────────────────────────────────────
VIDEO_BASE_MODELS = {
    # T2V models
    "veo_3_1_t2v_fast": {
        "landscape": "veo_3_1_t2v_fast_landscape",
        "portrait": "veo_3_1_t2v_fast_portrait",
    },
    "veo_2_1_fast_d_15_t2v": {
        "landscape": "veo_2_1_fast_d_15_t2v_landscape",
        "portrait": "veo_2_1_fast_d_15_t2v_portrait",
    },
    "veo_2_0_t2v": {
        "landscape": "veo_2_0_t2v_landscape",
        "portrait": "veo_2_0_t2v_portrait",
    },
    "veo_3_1_t2v_fast_ultra": {
        "landscape": "veo_3_1_t2v_fast_ultra",
        "portrait": "veo_3_1_t2v_fast_portrait_ultra",
    },
    "veo_3_1_t2v_fast_ultra_relaxed": {
        "landscape": "veo_3_1_t2v_fast_ultra_relaxed",
        "portrait": "veo_3_1_t2v_fast_portrait_ultra_relaxed",
    },
    "veo_3_1_t2v": {
        "landscape": "veo_3_1_t2v_landscape",
        "portrait": "veo_3_1_t2v_portrait",
    },
    # I2V models
    "veo_3_1_i2v_s_fast_fl": {
        "landscape": "veo_3_1_i2v_s_fast_fl",
        "portrait": "veo_3_1_i2v_s_fast_portrait_fl",
    },
    "veo_2_1_fast_d_15_i2v": {
        "landscape": "veo_2_1_fast_d_15_i2v_landscape",
        "portrait": "veo_2_1_fast_d_15_i2v_portrait",
    },
    "veo_2_0_i2v": {
        "landscape": "veo_2_0_i2v_landscape",
        "portrait": "veo_2_0_i2v_portrait",
    },
    "veo_3_1_i2v_s_fast_ultra_fl": {
        "landscape": "veo_3_1_i2v_s_fast_ultra_fl",
        "portrait": "veo_3_1_i2v_s_fast_portrait_ultra_fl",
    },
    "veo_3_1_i2v_s_fast_ultra_relaxed": {
        "landscape": "veo_3_1_i2v_s_fast_ultra_relaxed",
        "portrait": "veo_3_1_i2v_s_fast_portrait_ultra_relaxed",
    },
    "veo_3_1_i2v_s": {
        "landscape": "veo_3_1_i2v_s_landscape",
        "portrait": "veo_3_1_i2v_s_portrait",
    },
    # R2V models
    "veo_3_1_r2v_fast": {
        "landscape": "veo_3_1_r2v_fast",
        "portrait": "veo_3_1_r2v_fast_portrait",
    },
    "veo_3_1_r2v_fast_ultra": {
        "landscape": "veo_3_1_r2v_fast_ultra",
        "portrait": "veo_3_1_r2v_fast_portrait_ultra",
    },
    "veo_3_1_r2v_fast_ultra_relaxed": {
        "landscape": "veo_3_1_r2v_fast_ultra_relaxed",
        "portrait": "veo_3_1_r2v_fast_portrait_ultra_relaxed",
    },
}


def _extract_generation_params(request) -> Tuple[Optional[str], Optional[str]]:
    """vonAnfrageinExtrahieren aspectRatio Und imageSize Parameter。

    BevorzugtLevel: 
    1. request.generationConfig.imageConfig (ObersteEbene Gemini Parameter)
    2. extra fields in generationConfig (extra_body DurchleitenUebertragen)

    Returns:
        (aspect_ratio, image_size) NormalisiereneinisierennachWert
    """
    aspect_ratio = None
    image_size = None

    # Versuchenversuchenvon generationConfig Extrahieren
    gen_config = getattr(request, "generationConfig", None)

    # wieErgebnisObersteEbeneKeinhat, Versuchenversuchenvon extra fields (Pydantic extra="allow")
    if gen_config is None and hasattr(request, "__pydantic_extra__"):
        extra = request.__pydantic_extra__ or {}
        gen_config_raw = extra.get("generationConfig")
        if not isinstance(gen_config_raw, dict):
            extra_body = extra.get("extra_body") or extra.get("extraBody")
            if isinstance(extra_body, dict):
                gen_config_raw = extra_body.get("generationConfig")
        if isinstance(gen_config_raw, dict):
            image_config_raw = gen_config_raw.get("imageConfig", {})
            if isinstance(image_config_raw, dict):
                aspect_ratio = image_config_raw.get("aspectRatio")
                image_size = image_config_raw.get("imageSize")
            return (
                ASPECT_RATIO_MAP.get(aspect_ratio, aspect_ratio)
                if aspect_ratio
                else None,
                IMAGE_SIZE_MAP.get(image_size, image_size) if image_size else None,
            )

    if gen_config is not None:
        image_config = getattr(gen_config, "imageConfig", None)
        if image_config is not None:
            aspect_ratio = getattr(image_config, "aspectRatio", None)
            image_size = getattr(image_config, "imageSize", None)

    # Normalisiereneinisieren
    if aspect_ratio:
        aspect_ratio = ASPECT_RATIO_MAP.get(aspect_ratio, aspect_ratio)
    if image_size:
        image_size = IMAGE_SIZE_MAP.get(image_size, image_size)

    return aspect_ratio, image_size


def resolve_model_name(
    model: str, request=None, model_config: Dict[str, Any] = None
) -> str:
    """wirdVereinfachtModellname + generationConfig ParameterParsenfuerinnerhalbTeil MODEL_CONFIG key。

    wieErgebnis model bereitsBereitsistGueltig MODEL_CONFIG key, DirektZurueckgeben。
    wieErgebnis model istVereinfachtName(BasisGrundlageModellname), dannBasisBasierend auf generationConfig in
    aspectRatio / imageSize ZusammensetzenVerbindenAbgeschlossenGesamtinnerhalbTeilModellname。

    Args:
        model: AnfrageinModellname
        request: ChatCompletionRequest Instanz(verwendenFuerExtrahieren generationConfig)
        model_config: MODEL_CONFIG Woerterbuch(verwendenFuerValidierenParsennachModellname)

    Returns:
        ParsennachinnerhalbTeilModellname
    """
    # ────── BildModell-Aufloesung ──────
    if model in IMAGE_BASE_MODELS:
        base = IMAGE_BASE_MODELS[model]
        aspect_ratio, image_size = (
            _extract_generation_params(request) if request else (None, None)
        )

        # Standard aspect ratio
        if not aspect_ratio:
            aspect_ratio = DEFAULT_ASPECT

        # PruefenUnterstuetzt aspect ratio
        supported_aspects = MODEL_SUPPORTED_ASPECTS.get(base, [])
        if aspect_ratio not in supported_aspects and supported_aspects:
            debug_logger.log_warning(
                f"[MODEL_RESOLVER] Modell {base} nichtUnterstuetzt aspectRatio={aspect_ratio}, "
                f"HerabstufenLevelauf {DEFAULT_ASPECT}"
            )
            aspect_ratio = DEFAULT_ASPECT

        # ZusammensetzenVerbindenModellname
        resolved = f"{base}-{aspect_ratio}"

        # PruefenUnterstuetzt imageSize
        if image_size and image_size != "1k":
            supported_sizes = MODEL_SUPPORTED_SIZES.get(base, [])
            if image_size in supported_sizes:
                resolved = f"{resolved}-{image_size}"
            else:
                debug_logger.log_warning(
                    f"[MODEL_RESOLVER] Modell {base} nichtUnterstuetzt imageSize={image_size}, IgnorierenIgnorieren"
                )

        # Am meistenEndgueltigValidieren
        if model_config and resolved not in model_config:
            debug_logger.log_warning(
                f"[MODEL_RESOLVER] ParsennachModellname {resolved} nichtin MODEL_CONFIG in, "
                f"FallbackaufOriginalAnfangModellname {model}"
            )
            return model

        debug_logger.log_info(
            f"[MODEL_RESOLVER] ModellnameKonvertieren: {model} → {resolved} "
            f"(aspectRatio={aspect_ratio}, imageSize={image_size or 'default'})"
        )
        return resolved

    # ────── VideoModell-Aufloesung ──────
    if model in VIDEO_BASE_MODELS:
        aspect_ratio, _ = (
            _extract_generation_params(request) if request else (None, None)
        )

        # VideoStandardQuerformat
        if not aspect_ratio or aspect_ratio not in ("landscape", "portrait"):
            aspect_ratio = "landscape"

        orientation_map = VIDEO_BASE_MODELS[model]
        resolved = orientation_map.get(aspect_ratio)

        if resolved and model_config and resolved in model_config:
            debug_logger.log_info(
                f"[MODEL_RESOLVER] VideoModellnameKonvertieren: {model} → {resolved} "
                f"(aspectRatio={aspect_ratio})"
            )
            return resolved

        debug_logger.log_warning(
            f"[MODEL_RESOLVER] VideoModell {model} ParsenFehlgeschlagen (aspect={aspect_ratio}), "
            f"VerwendenOriginalAnfangModellname"
        )
        return model

    # wieErgebnisbereitsBereitsistGueltig MODEL_CONFIG key, DirektZurueckgeben
    if model_config and model in model_config:
        return model

    # nichtWissenModellname, OriginalGleichZurueckgeben(DurchunterDownstream MODEL_CONFIG ValidierungMelden)
    return model


def get_base_model_aliases() -> Dict[str, str]:
    """ZurueckgebenallehatVereinfachtModellname(UnterscheidenName)UndderenBeschreibenBeschreiben, verwendenFuer /v1/models SchnittstelleAnzeigen。"""
    aliases = {}

    for alias, base in IMAGE_BASE_MODELS.items():
        aspects = MODEL_SUPPORTED_ASPECTS.get(base, [])
        sizes = MODEL_SUPPORTED_SIZES.get(base, [])
        desc_parts = [f"aspects: {', '.join(aspects)}"]
        if sizes:
            desc_parts.append(f"sizes: {', '.join(sizes)}")
        aliases[alias] = f"Image generation (alias) - {'; '.join(desc_parts)}"

    for alias in VIDEO_BASE_MODELS:
        aliases[alias] = (
            "Video generation (alias) - supports landscape/portrait via generationConfig"
        )

    return aliases
