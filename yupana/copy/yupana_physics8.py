"""
yupana_physics — модуль для работы с физическими законами СФВ Плотникова.

Загружает JSON из yupana/physics/ и предоставляет программный доступ:
  - 7 коциклов (receptacle) — структура клеток
  - Описания величин (wiki) — словарь операторов
  - Физические процессы (14) — операции между коциклами
  - Физические законы (87) — формулы через Eps_0*c^n

Для SPICE-симулятора: каждый закон → .subckt, каждый процесс → поведенческая модель.
"""

import json
import os
import re
from fractions import Fraction
from typing import Dict, List, Optional, Any

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PHYSICS_DIR = os.path.join(_THIS_DIR, "yupana", "physics")


def _load_json(filename: str) -> dict:
    path = os.path.join(PHYSICS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Не найден {path}. Создайте каталог yupana/physics/ и поместите туда JSON.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_receptacle() -> dict:
    return _load_json("receptacle.json")


def load_wiki() -> dict:
    return _load_json("wiki.json")


def load_processes() -> dict:
    return _load_json("physical_processes.json")


def load_laws() -> dict:
    return _load_json("physical_laws.json")


def load_all() -> dict:
    return {
        "receptacle": load_receptacle(),
        "wiki": load_wiki(),
        "processes": load_processes(),
        "laws": load_laws(),
    }


# ── Парсинг scale-фактора ──

_SCALE_RE = re.compile(r'Eps_0\*c\^([+-]?\d+)')


def parse_scale(scale_str: str) -> int:
    m = _SCALE_RE.search(scale_str)
    return int(m.group(1)) if m else 0


# ── Коциклы ──

def get_cocycle_names(receptacle: dict) -> List[str]:
    return [k for k in receptacle["cocycles"].keys() if not k.startswith("g_")]


def get_cells_by_cocycle(receptacle: dict, cocycle_key: str) -> Dict[str, dict]:
    return receptacle["cocycles"][cocycle_key]["cells"]


def get_filled_cells(receptacle: dict, cocycle_key: str) -> Dict[str, dict]:
    cells = get_cells_by_cocycle(receptacle, cocycle_key)
    return {k: v for k, v in cells.items() if v.get("symbol")}


def get_cocycle_scale(receptacle: dict, cocycle_key: str) -> int:
    cell0 = receptacle["cocycles"][cocycle_key]["cells"].get("0", {})
    return parse_scale(cell0.get("symbol", ""))


# ── Описания величин ──

def get_quantity_name(wiki: dict, symbol: str) -> str:
    op = wiki["operators"].get(symbol)
    return op["name"] if op else symbol


def get_quantity_ru(wiki: dict, symbol: str) -> str:
    op = wiki["operators"].get(symbol)
    return op.get("ru", "") if op else ""


# ── Законы ──

def get_laws_with_formula(laws: dict) -> Dict[str, dict]:
    return {k: v for k, v in laws["laws"].items() if v.get("formula")}


def get_law_parts(laws: dict, law_key: str) -> List[str]:
    return laws["laws"][law_key].get("part_order", [])


def get_laws_by_process(laws: dict, processes: dict, process_key: str) -> List[str]:
    proc = processes["processes"].get(process_key, {})
    return proc.get("physical_laws", [])


# ── SPICE-экспорт ──

def law_to_spice_subckt(law_key: str, law: dict) -> str:
    name_safe = law_key.replace("law_", "law")
    parts = law.get("part_order", [])
    formula = law.get("formula", "")
    ru_name = law.get("ru", "")
    
    if not formula:
        return f"* {law_key}: {ru_name} — нет формулы"
    
    ports = " ".join(f"n_{p}" for p in parts) + " n_out"
    
    lines = [
        f"* {law_key}: {ru_name}",
        f"* Formula: {formula}",
        f".subckt {name_safe} {ports}",
    ]
    
    if parts:
        expr_parts = " * ".join(f"V(n_{p})" for p in parts)
        lines.append(f"B1 n_out 0 V={expr_parts}")
    else:
        lines.append("B1 n_out 0 V=1")
    
    lines.append(".ends")
    return "\n".join(lines)


def cocycle_to_spice_matrix(receptacle: dict, cocycle_key: str) -> str:
    cocycle = receptacle["cocycles"][cocycle_key]
    cells = cocycle["cells"]
    name = cocycle.get("name", cocycle_key)
    
    lines = [
        f"* --- Cocycle: {name} (scale={cocycle['scale']}) ---",
        f"* Cells: {len(cells)}",
        "",
        "* Filled cells:",
    ]
    
    for cell_id, cell in sorted(cells.items()):
        sym = cell.get("symbol", "")
        if sym:
            arrows = cell.get("arrows", [])
            arr_str = " ".join(arrows) if arrows else ""
            lines.append(f"*   [{cell_id:>6}] {sym:<12} {arr_str}")
    
    lines.append("")
    lines.append(f".subckt cocycle_{cocycle_key}")
    
    for cell_id, cell in sorted(cells.items()):
        sym = cell.get("symbol", "")
        if sym and sym != "Eps_0":
            lines.append(f"R_{cell_id} n_{cell_id} 0 1")
    
    lines.append(".ends")
    return "\n".join(lines)


def export_all_spice(output_path: str = None) -> str:
    laws = load_laws()
    receptacle = load_receptacle()
    
    lines = [
        "* ==========================================================",
        "* SFV Plotnikov — full SPICE netlist",
        "* Source: https://plotnikovna.narod.ru/",
        "* ==========================================================",
        "",
    ]
    
    lines.append("* --- COCYCLES ---")
    for key in get_cocycle_names(receptacle):
        lines.append(cocycle_to_spice_matrix(receptacle, key))
        lines.append("")
    
    lines.append("* --- LAWS WITH FORMULAS ---")
    for law_key, law in get_laws_with_formula(laws).items():
        lines.append(law_to_spice_subckt(law_key, law))
        lines.append("")
    
    netlist = "\n".join(lines)
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(netlist)
    
    return netlist


# ── Проверка ──

def verify():
    r = load_receptacle()
    w = load_wiki()
    p = load_processes()
    l = load_laws()
    
    n_cocycles = len(get_cocycle_names(r))
    n_operators = len(w["operators"])
    n_processes = len(p["processes"])
    n_laws = len(l["laws"])
    n_formula_laws = len(get_laws_with_formula(l))
    
    print(f"Cocycles:     {n_cocycles}")
    print(f"Operators:    {n_operators}")
    print(f"Processes:    {n_processes}")
    print(f"Laws:         {n_laws}")
    print(f"With formula: {n_formula_laws}")
    
    missing = set()
    for key in get_cocycle_names(r):
        for cell in get_filled_cells(r, key).values():
            sym = cell["symbol"]
            if sym and sym not in w["operators"] and not sym.startswith("Eps_0") and sym not in ("R",):
                missing.add(sym)
    
    if missing:
        print(f"WARNING — symbols without wiki desc: {missing}")
    else:
        print("OK — all symbols described in wiki")
    
    return True


if __name__ == "__main__":
    verify()
