"""RAG matcher: find similar client profiles from coach program database."""
import json
import os
from typing import Optional

_rag_data = None


def _load_rag_data():
    global _rag_data
    if _rag_data is not None:
        return _rag_data

    path = os.path.join(os.path.dirname(__file__), '../../data/rag_coach_programs.json')
    if not os.path.exists(path):
        _rag_data = []
        return _rag_data

    with open(path, 'r', encoding='utf-8') as f:
        _rag_data = json.load(f)
    return _rag_data


def _profile_score(entry_profile: dict, query: dict) -> float:
    """Score how similar a stored profile is to the query profile. Lower = more similar."""
    score = 0.0

    # Weight difference (most important for program design)
    ew = entry_profile.get("weight") or 70
    qw = query.get("weight") or 70
    score += abs(ew - qw) * 1.5  # 1.5 weight per kg difference

    # Height difference
    eh = entry_profile.get("height") or 170
    qh = query.get("height") or 170
    score += abs(eh - qh) * 0.3

    # Age difference
    ea = entry_profile.get("age") or 25
    qa = query.get("age") or 25
    if ea and qa:
        score += abs(ea - qa) * 0.8

    # Goal match (exact = 0, different = 30 penalty)
    if entry_profile.get("target") == query.get("target"):
        score -= 20  # bonus for same goal
    else:
        score += 30

    # Gym match
    if entry_profile.get("gym") == query.get("gym"):
        score -= 10  # bonus

    # Activity match
    if entry_profile.get("activity") == query.get("activity"):
        score -= 5  # bonus

    return score


def find_similar_programs(
    age: int = 25,
    weight: float = 70,
    height: float = 170,
    target: str = "gain_muscle",
    gym: str = "gym",
    activity: str = "moderate",
    top_n: int = 2,
    program_type: str = "training",  # "training" or "nutrition"
) -> list[dict]:
    """Find the N most similar coach programs from the RAG database."""
    data = _load_rag_data()
    if not data:
        return []

    query = {
        "age": age,
        "weight": weight,
        "height": height,
        "target": target,
        "gym": gym,
        "activity": activity,
    }

    # Score all entries
    scored = []
    for entry in data:
        # Skip entries without the requested program type
        if program_type == "nutrition" and not entry.get("nutrition"):
            continue
        if program_type == "training" and not entry.get("training"):
            continue

        score = _profile_score(entry["profile"], query)
        scored.append((score, entry))

    # Sort by score (lowest = most similar)
    scored.sort(key=lambda x: x[0])

    # Return top N
    results = []
    for score, entry in scored[:top_n]:
        results.append({
            "profile": entry["profile"],
            "program": entry.get(program_type, ""),
            "similarity_score": round(score, 1),
        })

    return results


def format_similar_programs_for_prompt(
    similar: list[dict],
    program_type: str = "training",
) -> str:
    """Format similar programs as text for AI prompt injection."""
    if not similar:
        return ""

    type_label = "ANTRENMAN" if program_type == "training" else "BESLENME"
    lines = [f"═══ BENZERİ PROFİLLERE YAZILMIŞ GERÇEK KOÇ {type_label} PROGRAMLARI ═══"]
    lines.append(f"(Profil benzerlik sırasına göre {len(similar)} program)")
    lines.append("")

    for i, item in enumerate(similar, 1):
        p = item["profile"]
        lines.append(f"── BENZER DANIŞAN {i} ──")
        lines.append(f"Profil: {p.get('age', '?')} yaş, {p.get('weight', '?')}kg, {p.get('height', '?')}cm, hedef: {p.get('target', '?')}, salon: {p.get('gym', '?')}")
        program = item.get("program", "")
        # Truncate if too long (max 2000 chars per example)
        if len(program) > 2000:
            program = program[:2000] + "\n  ... (devamı kısaltıldı)"
        lines.append(program)
        lines.append("")

    lines.append(f"BU PROGRAMLARIN YAPISINI, EGZERSİZ SIRASINI VE SET/TEKRAR MANTIĞINI REFERANS AL.")
    lines.append(f"Öğrencinin profiline göre uyarla — birebir kopyalama, AMA aynı kalitede yaz.")
    lines.append("")

    return "\n".join(lines)
