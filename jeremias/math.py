#!/usr/bin/env python3
"""Avaliador matemático do Jeremias — aritmética, trig, log, fatorial, equação linear."""
from __future__ import annotations

import json
import math
import re
import sys


def sen(x):
    return math.sin(math.radians(float(x)))


def cosseno(x):
    return math.cos(math.radians(float(x)))


def tangente(x):
    return math.tan(math.radians(float(x)))


def raiz(x):
    return math.sqrt(float(x))


def ln(x):
    return math.log(float(x))


def log10(x):
    return math.log10(float(x))


def fat(n):
    n = int(n)
    if n < 0 or n > 200:
        raise ValueError("fatorial fora do intervalo")
    return math.factorial(n)


ENV = {
    "sen": sen,
    "sin": sen,
    "seno": sen,
    "cos": cosseno,
    "cosseno": cosseno,
    "tan": tangente,
    "tg": tangente,
    "tangente": tangente,
    "raiz": raiz,
    "sqrt": raiz,
    "ln": ln,
    "log": log10,
    "log10": log10,
    "fat": fat,
    "fatorial": fat,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "pow": pow,
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def normalize(raw: str) -> str:
    t = raw.strip().lower()
    t = t.replace("quanto é", " ").replace("quanto e", " ")
    t = t.replace("calcula", " ").replace("calcule", " ")
    t = t.replace("resolva", " ").replace("calcular", " ")
    t = t.replace(",", ".")
    t = t.replace("^", "**")
    t = t.replace("×", "*").replace("÷", "/")
    t = re.sub(r"\bseno\s+de\s+", "sen(", t)
    t = re.sub(r"\bcosseno\s+de\s+", "cos(", t)
    t = re.sub(r"\btangente\s+de\s+", "tan(", t)
    t = re.sub(r"\braiz(?:\s+quadrada)?\s+de\s+", "raiz(", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s+elevado\s+a(?:o)?\s+(\d+(?:\.\d+)?)", r"(\1)**(\2)", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*fatorial", r"fat(\1)", t)
    t = t.replace("π", "pi")
    # close functions like sen(30
    for fn in ("sen", "cos", "tan", "raiz", "ln", "log", "fat"):
        t = re.sub(rf"\b{fn}\(([^()]+)(?!\))", rf"{fn}(\1)", t)
        t = re.sub(rf"\b{fn}\s+(\d+(?:\.\d+)?)", rf"{fn}(\1)", t)
    t = re.sub(r"\s+", " ", t).strip()
    if t.count("(") == t.count(")") + 1:
        t += ")"
    return t


def solve_linear(expr: str) -> str | None:
    m = re.search(r"([+-]?\s*\d*\.?\d*)\s*\*?\s*x\s*([+-]\s*\d+\.?\d*)?\s*=\s*([+-]?\s*\d+\.?\d*)", expr.replace(" ", ""))
    if not m:
        m = re.search(r"([+-]?\d+\.?\d*)x([+-]\d+\.?\d*)?=([+-]?\d+\.?\d*)", expr.replace(" ", ""))
    if not m:
        return None
    a = m.group(1).replace("+", "")
    a = float(a) if a not in ("", "+", "-") else (1.0 if a != "-" else -1.0)
    b = m.group(2)
    b = float(b.replace("+", "")) if b else 0.0
    c = float(m.group(3).replace("+", ""))
    if a == 0:
        return "não é equação do 1º grau em x"
    x = (c - b) / a
    return f"x = {x:g}"


def sympy_try(expr: str) -> str | None:
    try:
        import sympy as sp
    except ImportError:
        return None
    try:
        if "=" in expr and "x" in expr:
            left, right = expr.split("=", 1)
            x = sp.symbols("x")
            sol = sp.solve(sp.Eq(sp.sympify(left), sp.sympify(right)), x)
            return "x = " + ", ".join(str(s) for s in sol)
        val = sp.N(sp.sympify(expr))
        return str(val)
    except Exception:
        return None


def evaluate(raw: str) -> dict:
    original = raw.strip()
    expr = normalize(original)
    linear = solve_linear(expr.replace("**", "^"))
    if linear and "x" in expr and "=" in expr:
        return {"ok": True, "expr": expr, "result": linear, "engine": "linear"}
    try:
        val = eval(expr, {"__builtins__": {}}, ENV)  # noqa: S307
        if isinstance(val, float):
            if abs(val - round(val)) < 1e-10:
                val = int(round(val))
            else:
                val = round(val, 10)
        return {"ok": True, "expr": expr, "result": str(val), "engine": "math"}
    except Exception:
        alt = sympy_try(expr)
        if alt:
            return {"ok": True, "expr": expr, "result": alt, "engine": "sympy"}
        return {"ok": False, "expr": expr, "result": "não consegui calcular isso", "engine": "none"}


# script
if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or sys.stdin.read()
    print(json.dumps(evaluate(q), ensure_ascii=False))
