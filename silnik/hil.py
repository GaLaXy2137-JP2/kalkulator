import os


NORMALIZED_NAMES = {
    "cholesterol całkowity": "cholesterol",
    "trójglicerydy": "triglycerides",
    "albuminy": "albumin",
    "fosfor nieorganiczny": "phosphate",
    "magnez": "magnesium",
    "żelazo": "iron",
    "lipaza (dggr)": "lipase",
    "bilirubina całkowita": "total bilirubin",
    "bilirubina bezpośrednia": "direct bilirubin",
    "białko całkowite": "total protein",
    "γ-gt": "ggt",
}

HEMOLYSIS_BASE = {
    "ast": 1.3,
    "ldh": 1.3,
    "ck": 1.3,
    "alt": 1.2,
    "gldh": 1.2,
    "iron": 1.2,
    "magnesium": 1.2,
    "phosphate": 1.2,
    "lipase": 1.1,
}

LIPEMIA_BASE = {
    "triglycerides": 1.3,
    "cholesterol": 1.3,
    "total protein": 1.2,
    "albumin": 1.2,
    "crp": 1.2,
    "phosphate": 1.1,
    "magnesium": 1.1,
}

ICTERUS_BASE = {
    "total bilirubin": 1.3,
    "direct bilirubin": 1.3,
    "alt": 1.15,
    "ast": 1.15,
    "alp": 1.15,
    "ggt": 1.15,
}

EXCLUDED_PARAMS = {
    "sodium",
    "sód",
    "potassium",
    "potas",
    "chloride",
    "chlorki",
    "glucose",
    "glukoza",
    "creatinine",
    "kreatynina",
    "urea",
    "mocznik",
    "t4 całkowita",
    "t4 wolna",
    "tsh",
    "tli (pies)",
    "acth",
    "kortyzol",
    "progesteron",
}

HEMOLYSIS_SEVERITY = {
    "none": 0.0,
    "mild": 0.5,
    "high": 1.0,
}

LIPEMIA_SEVERITY = {
    "none": 0.0,
    "mild": 0.5,
    "high": 1.0,
}

ICTERUS_SEVERITY = {
    "absent": 0.0,
    "present": 1.0,
}

MAX_HIL_MULTIPLIER = 1.35
DEBUG_HIL = os.getenv("HIL_DEBUG", "1") == "1"
FORCE_HIL_MULTIPLIER = os.getenv("HIL_FORCE_MULTIPLIER")


def _normalize_param(name):
    normalized = str(name).strip().lower()
    return NORMALIZED_NAMES.get(normalized, normalized)


def _normalize_choice(value, default):
    if not value:
        return default

    return str(value).strip().lower()


def _condition_multiplier(param_name, severity_value, mapping):
    base = mapping.get(param_name, 1.0)
    return 1 + (base - 1) * severity_value


def _evaluate_condition(param_name, severity_value, mapping, condition_name, dictionary_name):
    base = mapping.get(param_name, 1.0)
    matched = param_name in mapping
    multiplier = 1 + (base - 1) * severity_value

    return {
        "condition": condition_name,
        "matched": matched,
        "dictionary": dictionary_name,
        "base": base,
        "multiplier": multiplier,
        "severity": severity_value,
    }


def _resolve_hil_details(param_name, hemolysis=None, lipemia=None, icterus=None):
    original_name = param_name
    normalized_name = _normalize_param(param_name)

    if normalized_name in EXCLUDED_PARAMS:
        return {
            "original_name": original_name,
            "normalized_name": normalized_name,
            "multiplier": 1.0,
            "matched_conditions": [],
            "excluded": True,
        }

    hemolysis_value = HEMOLYSIS_SEVERITY.get(_normalize_choice(hemolysis, "none"), 0.0)
    lipemia_value = LIPEMIA_SEVERITY.get(_normalize_choice(lipemia, "none"), 0.0)
    icterus_value = ICTERUS_SEVERITY.get(_normalize_choice(icterus, "absent"), 0.0)

    condition_results = [
        _evaluate_condition(normalized_name, hemolysis_value, HEMOLYSIS_BASE, "hemolysis", "HEMOLYSIS_BASE"),
        _evaluate_condition(normalized_name, lipemia_value, LIPEMIA_BASE, "lipemia", "LIPEMIA_BASE"),
        _evaluate_condition(normalized_name, icterus_value, ICTERUS_BASE, "icterus", "ICTERUS_BASE"),
    ]

    matched_conditions = [result for result in condition_results if result["matched"]]

    if not matched_conditions and DEBUG_HIL:
        print("NO HIL MATCH:", normalized_name)

    multiplier = max(result["multiplier"] for result in condition_results)

    if FORCE_HIL_MULTIPLIER is not None:
        try:
            multiplier = float(FORCE_HIL_MULTIPLIER)
            if DEBUG_HIL:
                print(f"HIL FORCE MULTIPLIER active: {multiplier}")
            return {
                "original_name": original_name,
                "normalized_name": normalized_name,
                "multiplier": multiplier,
                "matched_conditions": matched_conditions,
                "excluded": False,
            }
        except ValueError:
            if DEBUG_HIL:
                print(f"Invalid HIL_FORCE_MULTIPLIER: {FORCE_HIL_MULTIPLIER}")

    multiplier = min(multiplier, MAX_HIL_MULTIPLIER)

    return {
        "original_name": original_name,
        "normalized_name": normalized_name,
        "multiplier": multiplier,
        "matched_conditions": matched_conditions,
        "excluded": False,
    }


def get_hil_multiplier(param_name, hemolysis=None, lipemia=None, icterus=None):
    details = _resolve_hil_details(param_name, hemolysis, lipemia, icterus)
    return details["multiplier"]


def get_adjusted_volume(base_volume, param_name, hemolysis=None, lipemia=None, icterus=None):
    details = _resolve_hil_details(param_name, hemolysis, lipemia, icterus)
    final_volume = base_volume * details["multiplier"]

    if DEBUG_HIL:
        print({
            "param": details["original_name"],
            "normalized": details["normalized_name"],
            "base_volume": base_volume,
            "multiplier": details["multiplier"],
            "final_volume": final_volume,
            "matched_hil": [
                {
                    "condition": item["condition"],
                    "dictionary": item["dictionary"],
                    "base": item["base"],
                    "severity": item["severity"],
                    "multiplier": item["multiplier"],
                }
                for item in details["matched_conditions"]
            ],
            "excluded": details["excluded"],
        })

    return final_volume