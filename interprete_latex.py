"""
interprete_latex.py
===================
Convierte lo que escribe el teclado (LaTeX) en objetos de SymPy, SIN eval ni
sympify (no ejecuta código del usuario), y explica en español qué entendió.

Piezas públicas
---------------
latex_a_sympy(latex)        LaTeX -> expresión / operación de SymPy.
ascii_a_sympy(texto)        Texto plano seguro ("pi/2", "-oo", "sqrt(2)") -> SymPy.
ascii_lista(texto)          "(1, 2, pi)" -> [1, 2, pi]
leer_en_espanol(obj)        Frase en español con lo que entendió el intérprete.
clasificar_entrada(obj)     ¿Es una función, un límite, una serie, una ecuación…?
diagnosticar(obj, latex)    Comprobaciones de sentido: errores, avisos e información.

Operaciones que reconoce (quedan SIN evaluar; las evalúa calculo_motor.py)
-------------------------------------------------------------------------
  \\lim_{x\\to a}        sp.Limit            (a^{+}, a^{-} para laterales)
  \\lim_{(x,y)\\to(a,b)}  LimiteMulti
  \\int, \\int_a^b        sp.Integral         (también integrales iteradas)
  \\sum, \\prod           sp.Sum, sp.Product
  \\frac{d}{dx}, \\frac{\\partial}{\\partial x}   sp.Derivative (órdenes y mixtas)
  \\nabla f              Gradiente
"""
from __future__ import annotations

import ast
import math
import re
from typing import Any

import sympy as sp

__all__ = [
    "latex_a_sympy", "ascii_a_sympy", "ascii_lista", "leer_en_espanol",
    "clasificar_entrada", "diagnosticar", "ErrorLatex", "ErrorNoSoportado",
    "LimiteMulti", "Gradiente",
]


# ==============================================================================
# Excepciones y contenedores de operaciones que SymPy no trae
# ==============================================================================
class ErrorLatex(ValueError):
    """La expresión no se pudo interpretar. El mensaje (en español) se muestra tal cual."""


class ErrorNoSoportado(ErrorLatex):
    """La expresión es válida pero usa algo que el intérprete aún no evalúa."""


class LimiteMulti(sp.Function):
    """Límite de varias variables: LimiteMulti(f, (x, y), (a, b)). No se evalúa solo."""
    nargs = 3

    def _latex(self, printer):
        f, xs, as_ = self.args
        return (r"\lim_{(" + r",\,".join(printer._print(v) for v in xs) + r")\to("
                + r",\,".join(printer._print(v) for v in as_) + r")} " + printer._print(f))


class Gradiente(sp.Function):
    """Gradiente de una expresión escalar: Gradiente(f). No se evalúa solo."""
    nargs = 1

    def _latex(self, printer):
        return r"\nabla\left(" + printer._print(self.args[0]) + r"\right)"


# ==============================================================================
# 1. TOKENIZADOR Y PARSER DE LaTeX
# ==============================================================================
_MAX_LONGITUD = 2000
_MAX_BITS = 200_000        # tope para potencias numéricas (evita 9^(9^9) y similares)
_MAX_FACTORIAL = 5000

_IGNORAR = {r"\,", r"\;", r"\:", r"\!", r"\ ", r"\quad", r"\qquad", r"\displaystyle", r"\limits", "~"}
_UNICODE = {
    "×": r"\times", "·": r"\cdot", "÷": r"\div", "−": "-", "≤": r"\leq", "≥": r"\geq",
    "≠": r"\neq", "π": r"\pi", "∞": r"\infty",
}
_TOKEN = re.compile(
    r"""\s+
      | (?P<num>\d+(?:\.\d+)?|\.\d+)
      | (?P<cmd>\\(?:[A-Za-z]+|.))
      | (?P<let>[A-Za-z])
      | (?P<sym>.)""",
    re.X | re.S,
)

_FUNCIONES = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "cot": sp.cot, "sec": sp.sec, "csc": sp.csc,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh, "coth": sp.coth, "sech": sp.sech, "csch": sp.csch,
    "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan,
    "arccot": sp.acot, "arcsec": sp.asec, "arccsc": sp.acsc,
    "ln": sp.log, "exp": sp.exp, "sgn": sp.sign, "sign": sp.sign,
}
_INVERSAS = {
    "sin": sp.asin, "cos": sp.acos, "tan": sp.atan, "cot": sp.acot, "sec": sp.asec, "csc": sp.acsc,
    "sinh": sp.asinh, "cosh": sp.acosh, "tanh": sp.atanh, "coth": sp.acoth,
    "sech": sp.asech, "csch": sp.acsch,
}
_MULTI = {"max": sp.Max, "min": sp.Min}
_GRIEGAS = {
    "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta", "eta", "theta", "vartheta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "rho", "sigma", "tau", "upsilon", "phi", "varphi",
    "chi", "psi", "omega", "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon",
    "Phi", "Psi", "Omega",
}
_RELACIONES = {
    "=": sp.Eq, "<": sp.Lt, ">": sp.Gt, r"\leq": sp.Le, r"\le": sp.Le,
    r"\geq": sp.Ge, r"\ge": sp.Ge, r"\neq": sp.Ne, r"\ne": sp.Ne,
}
_NO_ATOMO = set(_RELACIONES) | {
    r"\cdot", r"\times", r"\div", r"\right", r"\end", r"\to", r"\pm", r"\\", r"\mapsto", r"\mid",
}
_MSG_CONJUNTOS = (
    "Los conjuntos y la notación «tal que» (∣) aún no se evalúan. Para analizar una región o una "
    "curva escribe directamente la condición, por ejemplo x²+y² ≤ 1."
)
_NO_SOPORTADO = {
    r"\mathbb": "los conjuntos numéricos (ℝ, ℕ…)",
    r"\in": "la pertenencia a conjuntos", r"\notin": "la pertenencia a conjuntos",
    r"\subset": "los conjuntos", r"\subseteq": "los conjuntos", r"\supset": "los conjuntos",
    r"\supseteq": "los conjuntos", r"\cup": "los conjuntos", r"\cap": "los conjuntos",
    r"\emptyset": "los conjuntos", r"\setminus": "los conjuntos",
    r"\land": "los signos lógicos", r"\lor": "los signos lógicos", r"\lnot": "los signos lógicos",
    r"\Rightarrow": "los signos lógicos", r"\Leftrightarrow": "los signos lógicos",
    r"\forall": "los cuantificadores", r"\exists": "los cuantificadores", r"\nexists": "los cuantificadores",
    r"\therefore": "los signos lógicos", r"\langle": "los vectores con ⟨ ⟩", r"\rangle": "los vectores con ⟨ ⟩",
    r"\ldots": "las listas", r"\vec": "los vectores con flecha", r"\overline": "la barra superior",
    r"\circ": "la composición de funciones", r"\approx": "las aproximaciones (≈)", r"\equiv": "las congruencias (≡)",
    r"\prime": "la notación de prima (f′)",
}
_DEG = object()  # marcador: el exponente era un grado (^{\circ})


def _tokenizar(s: str) -> list[str]:
    if len(s) > _MAX_LONGITUD:
        raise ErrorLatex("La expresión es demasiado larga.")
    toks: list[str] = []
    for m in _TOKEN.finditer(s):
        t = m.group(0)
        if t.isspace():
            continue
        t = _UNICODE.get(t, t)
        if t in _IGNORAR:
            continue
        # \frac12 == \frac{1}{2}: un solo dígito por argumento sin llaves
        if toks and toks[-1] == r"\frac" and t.isdigit() and len(t) > 1:
            toks.extend([t[0], t[1:]])
            continue
        toks.append(t)
    return toks


def _buscar(toks: list[str], objetivo: str):
    """Índice de `objetivo` a profundidad 0 de llaves/paréntesis, o None."""
    prof = 0
    for i, t in enumerate(toks):
        if t in ("{", "(", "["):
            prof += 1
        elif t in ("}", ")", "]"):
            prof -= 1
        elif prof == 0 and t == objetivo:
            return i
    return None


def _partir_comas(toks: list[str]) -> list[list[str]]:
    """Separa por comas de profundidad 0."""
    partes, actual, prof = [], [], 0
    for t in toks:
        if t in ("{", "(", "["):
            prof += 1
        elif t in ("}", ")", "]"):
            prof -= 1
        if prof == 0 and t == ",":
            partes.append(actual)
            actual = []
        else:
            actual.append(t)
    partes.append(actual)
    return partes


def _es_letra_o_griega(t: str) -> bool:
    return (len(t) == 1 and t.isalpha()) or (t.startswith("\\") and t[1:] in _GRIEGAS)


class _Parser:
    def __init__(self, toks, reales: bool, i_imaginaria: bool, ent=None):
        self.t = toks
        self.p = 0
        self.reales = reales
        self.i_imag = i_imaginaria
        self.abs_plano = 0
        self.ent = ent if ent is not None else {}   # símbolos "especiales" (índices enteros de sumas)

    # -- utilidades ---------------------------------------------------------
    def peek(self, k: int = 0):
        j = self.p + k
        return self.t[j] if j < len(self.t) else None

    def next(self):
        tok = self.peek()
        self.p += 1
        return tok

    def eat(self, tok: str) -> bool:
        if self.peek() == tok:
            self.p += 1
            return True
        return False

    def expect(self, tok: str):
        if not self.eat(tok):
            visto = self.peek()
            raise ErrorLatex(
                f"Falta «{tok}»" + (f" (se encontró «{visto}»)." if visto else " (la expresión termina antes).")
            )

    def _sub(self, tokens: list[str]):
        return _Parser(tokens, self.reales, self.i_imag, self.ent).completo()

    def inicia_atomo(self, tok) -> bool:
        if tok is None:
            return False
        if tok[0].isdigit() or (tok[0] == "." and len(tok) > 1):
            return True
        if tok in ("(", "["):
            return True
        if tok == "|":
            return self.abs_plano == 0
        if len(tok) == 1 and tok.isalpha():
            return True
        if tok.startswith("\\"):
            return tok not in _NO_ATOMO
        return False

    # -- gramática ----------------------------------------------------------
    def completo(self):
        if not self.t:
            raise ErrorLatex("No hay nada que interpretar.")
        val = self.relacion()
        if self.peek() is not None:
            if self.peek() == ",":
                raise ErrorNoSoportado("Las listas y los puntos (a, b) aún no están soportados aquí.")
            raise ErrorLatex(f"Hay símbolos que no se pudieron interpretar cerca de «{self.peek()}».")
        return val

    def relacion(self):
        izq = self.suma()
        rels = []
        while self.peek() in _RELACIONES:
            op = self.next()
            der = self.suma()
            rels.append(_RELACIONES[op](izq, der))
            izq = der
        if self.peek() == r"\mid":
            raise ErrorNoSoportado(_MSG_CONJUNTOS)
        if not rels:
            return izq
        return rels[0] if len(rels) == 1 else sp.And(*rels)

    def suma(self):
        val = self.termino()
        while self.peek() in ("+", "-"):
            op = self.next()
            rhs = self.termino()
            val = val + rhs if op == "+" else val - rhs
        return val

    def termino(self):
        val = self.unario()
        while True:
            tok = self.peek()
            if tok in ("*", r"\cdot", r"\times"):
                self.next()
                val = val * self.unario()
            elif tok in ("/", r"\div"):
                self.next()
                val = val / self.unario()
            elif self.inicia_atomo(tok):           # multiplicación implícita: 2x, (a)(b), x\sin x
                val = val * self.potencia()
            else:
                return val

    def unario(self):
        if self.eat("-"):
            return -self.unario()
        if self.eat("+"):
            return self.unario()
        return self.potencia()

    def potencia(self):
        base = self.postfijo()
        if self.peek() == "^":
            self.next()
            exp = self.exponente()
            if exp is _DEG:
                return base * sp.pi / 180
            return _pot(base, exp)
        return base

    def postfijo(self):
        val = self.atomo()
        while self.peek() == "!":
            self.next()
            if val.is_Integer and val > _MAX_FACTORIAL:
                raise ErrorLatex("Ese factorial es demasiado grande para calcularlo aquí.")
            if val.is_Integer and val < 0:
                raise ErrorLatex(f"El factorial no está definido para enteros negativos (se escribió ({val})!).")
            val = sp.factorial(val)
        return val

    def exponente(self):
        if self.peek() == "{":
            if self.peek(1) == r"\circ" and self.peek(2) == "}":
                self.p += 3
                return _DEG
            return self.grupo()
        if self.eat(r"\circ"):
            return _DEG
        if self.eat("-"):
            return -self.atomo()
        if self.eat("+"):
            return self.atomo()
        return self.atomo()

    def grupo(self):
        self.expect("{")
        val = self.relacion()
        self.expect("}")
        return val

    def grupo_tokens(self) -> list[str]:
        """Contenido crudo de {...} como lista de tokens."""
        self.expect("{")
        out, prof = [], 1
        while True:
            tok = self.next()
            if tok is None:
                raise ErrorLatex("Falta «}».")
            if tok == "{":
                prof += 1
            elif tok == "}":
                prof -= 1
                if prof == 0:
                    break
            out.append(tok)
        return out

    def grupo_texto(self) -> str:
        return "".join(self.grupo_tokens())

    def grupo_o_atomo(self):
        return self.grupo() if self.peek() == "{" else self.atomo()

    def _tokens_arg(self) -> list[str]:
        return self.grupo_tokens() if self.peek() == "{" else [self.next() or ""]

    # -- átomos -------------------------------------------------------------
    def simbolo(self, nombre: str):
        if self.peek() == "_":
            self.next()
            sub = self.grupo_texto() if self.peek() == "{" else (self.next() or "")
            sub = re.sub(r"[^A-Za-z0-9]", "", sub)
            if not sub:
                raise ErrorLatex("Hay un subíndice vacío.")
            nombre = f"{nombre}_{sub}"
        if nombre in self.ent:
            return self.ent[nombre]
        return sp.Symbol(nombre, real=self.reales)

    def atomo(self):
        tok = self.next()
        if tok is None:
            raise ErrorLatex("La expresión está incompleta (falta un número o variable al final).")
        if tok[0].isdigit() or (tok[0] == "." and len(tok) > 1):
            return sp.Rational(tok) if "." in tok else sp.Integer(tok)
        if len(tok) == 1 and tok.isalpha():
            if tok == "e" and self.peek() != "_" and "e" not in self.ent:
                return sp.E
            if tok == "i" and self.i_imag and self.peek() != "_" and "i" not in self.ent:
                return sp.I
            return self.simbolo(tok)
        if tok == "(":
            val = self.relacion()
            if self.peek() == ",":
                raise ErrorNoSoportado("Las listas y los puntos (a, b) aún no están soportados aquí.")
            self.expect(")")
            return val
        if tok == "[":
            val = self.relacion()
            self.expect("]")
            return val
        if tok == "{":
            val = self.relacion()
            self.expect("}")
            return val
        if tok == "|":
            self.abs_plano += 1
            val = self.relacion()
            self.expect("|")
            self.abs_plano -= 1
            return sp.Abs(val)
        if tok.startswith("\\"):
            return self.comando(tok)
        raise ErrorLatex(f"No se reconoce el símbolo «{tok}».")

    def operando(self, de_quien: str):
        sig = self.peek()
        if sig is None or not (self.inicia_atomo(sig) or sig in ("-", "+")):
            raise ErrorLatex(f"{de_quien} le falta la expresión sobre la que actúa.")
        return self.termino()

    def comando(self, tok: str):
        nombre = tok[1:]
        if tok == r"\pi":
            return sp.pi
        if tok == r"\infty":
            return sp.oo
        if tok == r"\exponentialE":
            return sp.E
        if tok in (r"\imaginaryI", r"\imaginaryJ"):
            return sp.I
        if nombre in _GRIEGAS:
            return self.simbolo(nombre)
        if tok == r"\placeholder":
            raise ErrorLatex("Hay casillas vacías (□) por llenar.")
        if tok == r"\frac":
            return self.fraccion()
        if tok == r"\sqrt":
            return self.raiz()
        if tok == r"\binom":
            n, k = self.grupo(), self.grupo()
            if n.is_Integer and n > _MAX_FACTORIAL:
                raise ErrorLatex("Ese coeficiente binomial es demasiado grande.")
            return sp.binomial(n, k)
        if tok == r"\left":
            return self.delimitado()
        if tok == r"\begin":
            return self.entorno()
        if tok == r"\lim":
            return self.limite()
        if tok in (r"\sum", r"\prod"):
            return self.suma_prod(tok)
        if tok == r"\int":
            return self.integral()
        if tok == r"\nabla":
            return Gradiente(self.operando("Al gradiente (∇)"))
        if tok == r"\partial":
            raise ErrorLatex("El símbolo ∂ va dentro de una fracción de derivada: usa la tecla ∂/∂x.")
        if tok in (r"\mathrm", r"\mathit", r"\text") and self.peek() == "{":
            txt = self.grupo_texto()
            if txt == "e":
                return sp.E
            if txt == "i":
                return sp.I
            if txt in _FUNCIONES or txt in _MULTI or txt == "log":
                return self.funcion(txt)
            raise ErrorLatex(f"No se reconoce «{txt}».")
        if tok == r"\operatorname":
            return self.funcion(self.grupo_texto())
        if nombre in _FUNCIONES or nombre in _MULTI or nombre == "log":
            return self.funcion(nombre)
        if tok == r"\mid":
            raise ErrorNoSoportado(_MSG_CONJUNTOS)
        if tok in _NO_SOPORTADO:
            raise ErrorNoSoportado(f"El intérprete aún no evalúa {_NO_SOPORTADO[tok]}; la tecla escribe, pero el cálculo no existe todavía.")
        if tok == r"\{":
            val = self.relacion()
            self.expect(r"\}")
            return val
        if tok == r"\}":
            raise ErrorLatex("Hay una llave que cierra sin haber abierto.")
        if tok == r"\right":
            raise ErrorLatex("Hay un paréntesis que cierra sin haber abierto.")
        raise ErrorLatex(f"No se reconoce el comando «{tok}».")

    # -- fracciones, derivadas y raíces -------------------------------------
    def fraccion(self):
        if self.peek() == "{":
            inicio = self.p
            num_t = self.grupo_tokens()
            if self.peek() == "{":
                den_t = self.grupo_tokens()
                d = self._derivada(num_t, den_t)
                if d is not None:
                    return d
                return self._sub(num_t) / self._sub(den_t)
            self.p = inicio
        num = self.grupo() if self.peek() == "{" else self.atomo()
        den = self.grupo() if self.peek() == "{" else self.atomo()
        return num / den

    @staticmethod
    def _orden_exp(t: list[str]):
        """['^','{','2','}'] -> (2, resto)  |  [] -> (1, [])  |  otra cosa -> None"""
        if not t:
            return 1, []
        if t[0] != "^":
            return None
        ex = t[1:]
        if ex[:1] == ["{"] and "}" in ex:
            cierre = ex.index("}")
            cuerpo, resto = ex[1:cierre], ex[cierre + 1:]
        elif ex:
            cuerpo, resto = ex[:1], ex[1:]
        else:
            return None
        try:
            return int("".join(cuerpo)), resto
        except ValueError:
            return None

    def _derivada(self, num_t: list[str], den_t: list[str]):
        """Si la fracción es d/dx, d²/dx², ∂/∂x, ∂²/∂x∂y…, devuelve sp.Derivative; si no, None."""
        t = list(num_t)
        if t[:4] == [r"\mathrm", "{", "d", "}"]:
            tipo, t = "d", t[4:]
        elif t[:1] == ["d"]:
            tipo, t = "d", t[1:]
        elif t[:1] == [r"\partial"]:
            tipo, t = "p", t[1:]
        else:
            return None
        o = self._orden_exp(t)
        if o is None or o[1]:
            return None
        orden = o[0]

        d = list(den_t)
        variables: list[tuple[list[str], int]] = []
        while d:
            if tipo == "d" and d[:4] == [r"\mathrm", "{", "d", "}"]:
                d = d[4:]
            elif tipo == "d" and d[:1] == ["d"]:
                d = d[1:]
            elif tipo == "p" and d[:1] == [r"\partial"]:
                d = d[1:]
            else:
                return None
            if not d or not _es_letra_o_griega(d[0]):
                return None
            var = [d[0]]
            d = d[1:]
            if d[:1] == ["_"]:
                if d[1:2] == ["{"] and "}" in d:
                    cierre = d.index("}")
                    var += d[: cierre + 1]
                    d = d[cierre + 1:]
                else:
                    var += d[:2]
                    d = d[2:]
            pot = 1
            if d[:1] == ["^"]:
                oo = self._orden_exp(d)
                if oo is None:
                    return None
                pot, d = oo
            variables.append((var, pot))
        if not variables:
            return None
        if sum(p for _, p in variables) != orden:
            raise ErrorLatex("El orden de la derivada no coincide: el exponente de arriba (d²) debe sumar lo de abajo (dx²).")
        simbolos = []
        for var, pot in variables:
            s = self._sub(var)
            if not isinstance(s, sp.Symbol):
                return None
            simbolos.append((s, pot))
        try:
            f = self.operando("A la derivada")
        except ErrorLatex:
            raise ErrorLatex("A la derivada le falta la función que se va a derivar (escríbela después de d/dx).") from None
        return sp.Derivative(f, *simbolos)

    def raiz(self):
        indice = None
        if self.peek() == "[":
            self.next()
            indice = self.relacion()
            self.expect("]")
        rad = self.grupo() if self.peek() == "{" else self.atomo()
        return sp.sqrt(rad) if indice is None else sp.root(rad, indice)

    # -- límites, sumas, integrales -----------------------------------------
    def limite(self):
        if self.peek() != "_":
            raise ErrorLatex("A «lím» le falta la condición de abajo (por ejemplo x → 0).")
        self.next()
        cond = self._tokens_arg()
        i = _buscar(cond, r"\to")
        if i is None:
            raise ErrorLatex("La condición del límite debe tener la forma «x → a».")
        izq, der = cond[:i], cond[i + 1:]
        if not izq or not der:
            raise ErrorLatex("A la condición del límite le falta algo a un lado de la flecha (x → a).")

        direccion = "+-"
        if der[-4:] in (["^", "{", "+", "}"], ["^", "{", "-", "}"]):
            direccion, der = der[-2], der[:-4]
        elif der[-2:] in (["^", "+"], ["^", "-"]):
            direccion, der = der[-1], der[:-2]

        multi = izq[:1] == ["("] and izq[-1:] == [")"]
        if multi:
            vars_t = _partir_comas(izq[1:-1])
            vals_t = _partir_comas(der[1:-1]) if der[:1] == ["("] and der[-1:] == [")"] else [der]
            variables = [self._sub(v) for v in vars_t]
            valores = [self._sub(v) for v in vals_t]
            if not all(isinstance(v, sp.Symbol) for v in variables):
                raise ErrorLatex("Las variables del límite deben ser letras: (x, y) → (a, b).")
            if len(variables) != len(valores):
                raise ErrorLatex(f"El límite tiene {len(variables)} variable(s) pero {len(valores)} valor(es) a donde tienden.")
            cuerpo = self.operando("Al límite")
            return LimiteMulti(cuerpo, sp.Tuple(*variables), sp.Tuple(*valores))
        var = self._sub(izq)
        if not isinstance(var, sp.Symbol):
            raise ErrorLatex("La variable del límite debe ser una letra (x, t, n…).")
        valor = self._sub(der)
        if valor.has(var):
            raise ErrorLatex(f"El valor al que tiende {var} no puede depender de {var} misma.")
        cuerpo = self.operando("Al límite")
        return sp.Limit(cuerpo, var, valor, direccion)

    def _limites_opcionales(self):
        inf = sup = None
        for _ in range(2):
            if self.peek() == "_" and inf is None:
                self.next()
                inf = self._tokens_arg()
            elif self.peek() == "^" and sup is None:
                self.next()
                sup = self._tokens_arg()
        return inf, sup

    def suma_prod(self, tok: str):
        nombre = "la sumatoria (Σ)" if tok == r"\sum" else "la productoria (Π)"
        inf, sup = self._limites_opcionales()
        if inf is None or sup is None:
            raise ErrorLatex(f"A {nombre} le faltan los límites: abajo «k = 1» y arriba el último valor.")
        i = _buscar(inf, "=")
        if i is None:
            raise ErrorLatex("El límite de abajo debe tener la forma «k = 1».")
        idx = self._sub(inf[:i])
        if not isinstance(idx, sp.Symbol):
            raise ErrorLatex("El índice debe ser una letra (k, n, j…). Si activaste «i es √−1», usa otra letra.")
        k = sp.Symbol(idx.name, integer=True)
        previo = self.ent.get(idx.name)
        self.ent[idx.name] = k
        try:
            ini = self._sub(inf[i + 1:])
            fin = self._sub(sup)
            cuerpo = self.operando(nombre[0].upper() + nombre[1:])
        finally:
            if previo is None:
                self.ent.pop(idx.name, None)
            else:
                self.ent[idx.name] = previo
        clase = sp.Sum if tok == r"\sum" else sp.Product
        return clase(cuerpo, (k, ini, fin))

    def _es_diferencial(self, i: int):
        """¿En t[i:] empieza «dx» o «\\mathrm{d}x»? -> (largo del prefijo, largo de la variable) o None."""
        t = self.t
        if t[i:i + 4] == [r"\mathrm", "{", "d", "}"]:
            j = i + 4
        elif t[i:i + 1] == ["d"]:
            j = i + 1
        else:
            return None
        if j >= len(t) or not _es_letra_o_griega(t[j]):
            return None
        k = j + 1
        if k < len(t) and t[k] == "_":
            if k + 1 < len(t) and t[k + 1] == "{":
                prof, m = 0, k + 1
                while m < len(t):
                    if t[m] == "{":
                        prof += 1
                    elif t[m] == "}":
                        prof -= 1
                        if prof == 0:
                            break
                    m += 1
                k = m + 1
            else:
                k += 2
        return j - i, k - j

    def _hallar_diferencial(self):
        t, i, prof, pend = self.t, self.p, 0, 1
        while i < len(t):
            tok = t[i]
            if tok in ("{", "(", "[", r"\left"):
                prof += 1
            elif tok in ("}", ")", "]", r"\right"):
                prof -= 1
            elif prof == 0:
                if tok == r"\int":
                    pend += 1
                else:
                    d = self._es_diferencial(i)
                    if d:
                        pend -= 1
                        if pend == 0:
                            return i, d
                        i += d[0] + d[1]
                        continue
            i += 1
        raise ErrorLatex("A la integral le falta el diferencial (dx, dy…) que indica la variable de integración.")

    def integral(self):
        inf, sup = self._limites_opcionales()
        i, (lp, lv) = self._hallar_diferencial()
        cuerpo_t = self.t[self.p:i]
        var = self._sub(self.t[i + lp:i + lp + lv])
        if not isinstance(var, sp.Symbol):
            raise ErrorLatex("La variable de integración debe ser una letra (dx, dy, dt…).")
        f = self._sub(cuerpo_t) if cuerpo_t else sp.Integer(1)
        self.p = i + lp + lv
        if (inf is None) != (sup is None):
            raise ErrorLatex("La integral definida necesita límite inferior y superior (o ninguno).")
        if inf is None:
            return sp.Integral(f, var)
        return sp.Integral(f, (var, self._sub(inf), self._sub(sup)))

    # -- delimitadores, funciones y entornos --------------------------------
    def delimitado(self):
        d = self.next()
        interior = self.relacion()
        if self.peek() == ",":
            raise ErrorNoSoportado("Las listas y los puntos (a, b) aún no están soportados aquí.")
        self.expect(r"\right")
        self.next()  # delimitador de cierre (no se valida: se acepta con tolerancia)
        if d in ("(", "[", r"\{", ".", r"\lbrace"):
            return interior
        if d in ("|", r"\vert", r"\lvert"):
            return sp.Abs(interior)
        if d == r"\lfloor":
            return sp.floor(interior)
        if d == r"\lceil":
            return sp.ceiling(interior)
        if d in (r"\Vert", r"\|", r"\lVert"):
            raise ErrorNoSoportado("La norma ‖·‖ de vectores aún no está soportada (para un número usa |x|).")
        raise ErrorLatex(f"Delimitador no reconocido: «{d}».")

    def argumentos(self) -> list:
        tok = self.peek()
        if tok == r"\left":
            self.next()
            self.next()  # delimitador de apertura
            args = self._lista()
            self.expect(r"\right")
            self.next()
            return args
        if tok == "(":
            self.next()
            args = self._lista()
            self.expect(")")
            return args
        return [self.unario()]                      # \sin x

    def _lista(self) -> list:
        args = [self.relacion()]
        while self.eat(","):
            args.append(self.relacion())
        return args

    def funcion(self, nombre: str):
        base_log = None
        if nombre == "log" and self.peek() == "_":
            self.next()
            base_log = self.grupo_o_atomo()
        potencia, inversa = None, False
        if self.peek() == "^":
            self.next()
            e = self.exponente()
            if e is _DEG:
                raise ErrorLatex("Un exponente en grados solo tiene sentido sobre un número.")
            if e == -1 and nombre in _INVERSAS:
                inversa = True
            else:
                potencia = e
        args = self.argumentos()

        if nombre in _MULTI:
            res = _MULTI[nombre](*args)
        else:
            if len(args) != 1:
                raise ErrorLatex(f"«{nombre}» recibe un solo argumento.")
            a = args[0]
            if nombre == "log":
                res = sp.log(a, base_log if base_log is not None else 10)
            elif inversa:
                res = _INVERSAS[nombre](a)
            elif nombre in _FUNCIONES:
                res = _FUNCIONES[nombre](a)
            else:
                raise ErrorLatex(f"No se reconoce la función «{nombre}».")
        return res if potencia is None else _pot(res, potencia)

    def entorno(self):
        nombre = self.grupo_texto()
        if nombre != "cases":
            raise ErrorNoSoportado(f"El entorno «{nombre}» (matrices, sistemas…) aún no está soportado.")
        interior, prof = [], 0
        while True:
            tok = self.next()
            if tok is None:
                raise ErrorLatex(r"Falta \end{cases}.")
            if tok == r"\end" and prof == 0:
                self.grupo_texto()
                break
            if tok == "{":
                prof += 1
            elif tok == "}":
                prof -= 1
            interior.append(tok)
        filas, fila, celda, prof = [], [], [], 0
        for tok in interior:
            if tok == "{":
                prof += 1
            elif tok == "}":
                prof -= 1
            if prof == 0 and tok == "&":
                fila.append(celda)
                celda = []
            elif prof == 0 and tok == r"\\":
                fila.append(celda)
                filas.append(fila)
                fila, celda = [], []
            else:
                celda.append(tok)
        fila.append(celda)
        if fila != [[]]:
            filas.append(fila)

        pares = []
        for fila in filas:
            if not fila[0]:
                raise ErrorLatex("Hay casillas vacías (□) en la función por trozos.")
            expr = self._sub(fila[0])
            cond_tokens = fila[1] if len(fila) > 1 else []
            if not cond_tokens or cond_tokens[0] in (r"\text", r"\mathrm"):
                cond = sp.true                       # «en otro caso»
            else:
                cond = self._sub(cond_tokens)
            pares.append((expr, cond))
        if not pares:
            raise ErrorLatex("La función por trozos está vacía.")
        return sp.Piecewise(*pares)


def _pot(base, exp):
    """base ** exp con tope para potencias numéricas gigantescas."""
    if getattr(base, "is_Rational", False) and getattr(exp, "is_Rational", False):
        try:
            bits = abs(float(exp)) * math.log2(max(abs(float(base)), 2.0))
        except (OverflowError, ValueError):
            bits = float("inf")
        if bits > _MAX_BITS:
            raise ErrorLatex("Esa potencia numérica es demasiado grande para calcularla aquí.")
    return base ** exp


def latex_a_sympy(latex: str, *, reales: bool = True, i_imaginaria: bool = False) -> sp.Basic:
    """
    Convierte LaTeX (el que escribe el teclado) en una expresión u operación de SymPy.

    reales        True = las variables son sp.Symbol(..., real=True) (lo habitual en cálculo).
    i_imaginaria  True = la letra «i» del teclado abc vale √-1. La tecla «i» de la
                  pestaña f(x) (\\imaginaryI) siempre es la unidad imaginaria.

    Lanza ErrorLatex (o ErrorNoSoportado) con un mensaje en español si no se puede.
    """
    try:
        return _Parser(_tokenizar(latex), reales, i_imaginaria).completo()
    except ErrorLatex:
        raise
    except RecursionError:
        raise ErrorLatex("La expresión está demasiado anidada.") from None
    except (NotImplementedError, TypeError, ValueError, ArithmeticError, AttributeError) as e:
        raise ErrorLatex(f"No pude construir esa expresión ({type(e).__name__}). Revisa que esté bien escrita.") from None


# ==============================================================================
# 2. TEXTO PLANO SEGURO (para puntos, límites de integración, parámetros…)
# ==============================================================================
_ASCII_FUNCS = {
    "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "cot": sp.cot, "sec": sp.sec, "csc": sp.csc,
    "asin": sp.asin, "acos": sp.acos, "atan": sp.atan, "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan,
    "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh, "coth": sp.coth, "sech": sp.sech, "csch": sp.csch,
    "asinh": sp.asinh, "acosh": sp.acosh, "atanh": sp.atanh,
    "exp": sp.exp, "ln": sp.log, "sqrt": sp.sqrt, "abs": sp.Abs, "sign": sp.sign, "sgn": sp.sign,
    "floor": sp.floor, "ceil": sp.ceiling, "ceiling": sp.ceiling,
}
_ASCII_CONST = {"pi": sp.pi, "e": sp.E, "E": sp.E, "oo": sp.oo, "inf": sp.oo, "infinito": sp.oo, "infty": sp.oo}
_SUP = {"²": "**2", "³": "**3", "⁴": "**4"}


def _ascii_preparar(texto: str) -> str:
    t = texto.strip()
    if len(t) > 300:
        raise ErrorLatex("El texto es demasiado largo.")
    for a, b in {"^": "**", "×": "*", "·": "*", "÷": "/", "−": "-", "π": "pi", "∞": "oo", "√": "sqrt"}.items():
        t = t.replace(a, b)
    for a, b in _SUP.items():
        t = t.replace(a, b)
    t = re.sub(r"(\d)\s*([A-Za-z_(])", r"\1*\2", t)                 # 2x, 3(x+1), 2pi
    t = re.sub(r"\)\s*([A-Za-z0-9_(])", r")*\1", t)                 # (a)(b), (a)x
    t = re.sub(r"\bpi\s+([A-Za-z0-9(])", r"pi*\1", t)
    return t


def ascii_a_sympy(texto: str, *, reales: bool = True, i_imaginaria: bool = False) -> sp.Basic:
    """
    Texto plano -> SymPy, sin eval. Acepta: + - * / ^ **, paréntesis, números, pi, e, oo,
    variables (x, y, x1, x_1), y funciones (sin, cos, tan, sqrt, exp, ln, log, abs, …).
    Ejemplos: "pi/2", "-oo", "2*sqrt(2)", "3x^2+1".
    """
    if not texto or not texto.strip():
        raise ErrorLatex("El campo está vacío.")
    prep = _ascii_preparar(texto)
    try:
        arbol = ast.parse(prep, mode="eval")
    except SyntaxError:
        raise ErrorLatex(f"No pude entender «{texto}». Usa * para multiplicar (2*x), ^ para potencias y paréntesis.") from None
    except (RecursionError, MemoryError):
        raise ErrorLatex("El texto está demasiado anidado.") from None
    try:
        return _ev_ast(arbol.body, reales, i_imaginaria)
    except RecursionError:
        raise ErrorLatex("El texto está demasiado anidado.") from None


def _ev_ast(n: ast.AST, reales: bool, i_imag: bool):
    if isinstance(n, ast.Constant):
        v = n.value
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ErrorLatex("Solo se admiten números.")
        return sp.Integer(v) if isinstance(v, int) else sp.Rational(repr(v))
    if isinstance(n, ast.Name):
        nombre = n.id
        if nombre in _ASCII_CONST:
            return _ASCII_CONST[nombre]
        if nombre == "I" or (nombre == "i" and i_imag):
            return sp.I
        if len(nombre) > 12 or "__" in nombre:
            raise ErrorLatex(f"Nombre no válido: «{nombre}».")
        return sp.Symbol(nombre, real=reales)
    if isinstance(n, ast.UnaryOp):
        v = _ev_ast(n.operand, reales, i_imag)
        if isinstance(n.op, ast.USub):
            return -v
        if isinstance(n.op, ast.UAdd):
            return v
        raise ErrorLatex("Operador no permitido.")
    if isinstance(n, ast.BinOp):
        a, b = _ev_ast(n.left, reales, i_imag), _ev_ast(n.right, reales, i_imag)
        if isinstance(n.op, ast.Add):
            return a + b
        if isinstance(n.op, ast.Sub):
            return a - b
        if isinstance(n.op, ast.Mult):
            return a * b
        if isinstance(n.op, ast.Div):
            return a / b
        if isinstance(n.op, ast.Pow):
            return _pot(a, b)
        raise ErrorLatex("Operador no permitido.")
    if isinstance(n, ast.Call):
        if not isinstance(n.func, ast.Name) or n.keywords:
            raise ErrorLatex("Llamada no permitida.")
        f = n.func.id
        args = [_ev_ast(a, reales, i_imag) for a in n.args]
        if f in _ASCII_FUNCS and len(args) == 1:
            return _ASCII_FUNCS[f](args[0])
        if f == "log":
            if len(args) == 1:
                return sp.log(args[0], 10)
            if len(args) == 2:
                return sp.log(args[0], args[1])
        if f == "root" and len(args) == 2:
            return sp.root(args[0], args[1])
        if f in ("max", "min") and args:
            return (sp.Max if f == "max" else sp.Min)(*args)
        if f == "factorial" and len(args) == 1:
            if args[0].is_Integer and args[0] > _MAX_FACTORIAL:
                raise ErrorLatex("Ese factorial es demasiado grande.")
            return sp.factorial(args[0])
        if f not in _ASCII_FUNCS and len(args) == 1 and 1 <= len(f) <= 3:   # x(x+1) = x·(x+1)
            return sp.Symbol(f, real=reales) * args[0]
        raise ErrorLatex(f"Función no reconocida: «{f}».")
    raise ErrorLatex("Hay algo que no es una expresión matemática.")


def ascii_lista(texto: str, **kw) -> list[sp.Basic]:
    """'(1, pi, -oo)' o '1, 2' -> [1, pi, -oo]  (separa por comas de nivel 0)."""
    t = texto.strip()
    if t.startswith("(") and t.endswith(")"):
        prof, ok = 0, True
        for i, c in enumerate(t):
            prof += c == "("
            prof -= c == ")"
            if prof == 0 and i < len(t) - 1:
                ok = False
                break
        if ok:
            t = t[1:-1]
    partes, actual, prof = [], "", 0
    for c in t:
        prof += c == "("
        prof -= c == ")"
        if c == "," and prof == 0:
            partes.append(actual)
            actual = ""
        else:
            actual += c
    partes.append(actual)
    return [ascii_a_sympy(p, **kw) for p in partes]


# ==============================================================================
# 3. LECTURA EN ESPAÑOL
# ==============================================================================
_GRIEGO_TXT = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "varepsilon": "ε", "zeta": "ζ",
    "eta": "η", "theta": "θ", "vartheta": "θ", "iota": "ι", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν",
    "xi": "ξ", "rho": "ρ", "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ", "varphi": "φ", "chi": "χ",
    "psi": "ψ", "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π",
    "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}
_NOMBRE_FUNC = {
    sp.sin: "seno", sp.cos: "coseno", sp.tan: "tangente", sp.cot: "cotangente", sp.sec: "secante", sp.csc: "cosecante",
    sp.asin: "arcoseno", sp.acos: "arcocoseno", sp.atan: "arcotangente", sp.acot: "arcocotangente",
    sp.asec: "arcosecante", sp.acsc: "arcocosecante",
    sp.sinh: "seno hiperbólico", sp.cosh: "coseno hiperbólico", sp.tanh: "tangente hiperbólica",
    sp.coth: "cotangente hiperbólica", sp.sech: "secante hiperbólica", sp.csch: "cosecante hiperbólica",
    sp.asinh: "seno hiperbólico inverso", sp.acosh: "coseno hiperbólico inverso", sp.atanh: "tangente hiperbólica inversa",
    sp.acoth: "cotangente hiperbólica inversa", sp.asech: "secante hiperbólica inversa", sp.acsch: "cosecante hiperbólica inversa",
    sp.Abs: "valor absoluto", sp.floor: "parte entera (piso)", sp.ceiling: "techo", sp.sign: "signo",
}
_ORDINAL = {4: "cuarta", 5: "quinta", 6: "sexta", 7: "séptima", 8: "octava", 9: "novena", 10: "décima"}
_REL_TXT = {sp.Eq: "es igual a", sp.Ne: "es distinto de", sp.Lt: "es menor que", sp.Le: "es menor o igual que",
            sp.Gt: "es mayor que", sp.Ge: "es mayor o igual que"}

# niveles: 0 átomo · 1 potencia · 2 función · 3 producto/cociente · 4 suma · 5 operación/relación


def _env(txt: str, nivel: int, minimo: int = 1) -> str:
    return f"({txt})" if nivel >= minimo else txt


def _nombre_simbolo(s: sp.Symbol) -> str:
    base, _, sub = s.name.partition("_")
    base = _GRIEGO_TXT.get(base, base)
    return f"{base} sub {sub}" if sub else base


def _grado_total(t) -> float:
    vs = list(t.free_symbols)
    if not vs:
        return 0
    try:
        return sp.Poly(t, *vs).total_degree()
    except Exception:  # noqa: BLE001
        return 0.5


def _ordenar_terminos(e) -> list:
    """Términos de una suma por grado descendente (SymPy pone el 1 de 1 - x² antes que x²)."""
    base = list(e.as_ordered_terms())
    return sorted(base, key=lambda t: -_grado_total(t))


def _v(e) -> tuple[str, int]:
    """(frase, nivel). Nunca lanza: lo que no conoce lo imprime con SymPy."""
    try:
        return _v_inner(e)
    except Exception:  # noqa: BLE001
        return str(e), 0


def _v_inner(e) -> tuple[str, int]:
    if e == sp.true:
        return "una condición siempre verdadera", 5
    if e == sp.false:
        return "una condición siempre falsa", 5
    if e.is_Integer:
        return (str(int(e)), 0) if e >= 0 else (f"menos {abs(int(e))}", 3)
    if e.is_Rational:
        return (f"{e.p}/{e.q}", 0) if e > 0 else (f"menos {abs(e.p)}/{e.q}", 3)
    if e.is_Float:
        return (str(e), 0)
    if e == sp.pi:
        return "π", 0
    if e == sp.E:
        return "e", 0
    if e == sp.I:
        return "i (la unidad imaginaria)", 0
    if e == sp.oo:
        return "infinito", 0
    if e == -sp.oo:
        return "menos infinito", 0
    if e == sp.zoo:
        return "infinito complejo", 0
    if e == sp.nan:
        return "un valor indefinido", 0
    if isinstance(e, sp.Symbol):
        return _nombre_simbolo(e), 0
    if isinstance(e, sp.Tuple):
        return "(" + ", ".join(_v(a)[0] for a in e) + ")", 0

    # ---- operaciones de cálculo ----
    if isinstance(e, sp.Limit):
        f, x, a = e.args[0], e.args[1], e.args[2]
        d = str(e.args[3]) if len(e.args) > 3 else "+-"
        lado = {"+": " por la derecha", "-": " por la izquierda"}.get(d, "")
        return (f"el límite de {_env(*_v(f), minimo=3)} cuando {_v(x)[0]} tiende a {_v(a)[0]}{lado}", 5)
    if isinstance(e, LimiteMulti):
        f, xs, as_ = e.args
        return (f"el límite de {_env(*_v(f), minimo=3)} cuando ({', '.join(_v(x)[0] for x in xs)}) "
                f"tiende a ({', '.join(_v(a)[0] for a in as_)})", 5)
    if isinstance(e, Gradiente):
        return f"el gradiente de {_env(*_v(e.args[0]), minimo=3)}", 5
    if isinstance(e, sp.Integral):
        lim = list(e.limits)
        f = _env(*_v(e.function), minimo=3)
        if len(lim) == 1 and len(lim[0]) == 1:
            return f"la integral indefinida de {f} respecto de {_v(lim[0][0])[0]}", 5
        if len(lim) == 1:
            v, a, b = lim[0]
            return (f"la integral definida de {f} respecto de {_v(v)[0]}, desde {_v(a)[0]} hasta {_v(b)[0]}", 5)
        partes = []
        for l in lim:
            if len(l) == 3:
                partes.append(f"{_v(l[0])[0]} de {_v(l[1])[0]} a {_v(l[2])[0]}")
            else:
                partes.append(_v(l[0])[0])
        return (f"la integral múltiple de {f}, integrando en este orden (de adentro hacia afuera): " + "; ".join(partes), 5)
    if isinstance(e, (sp.Sum, sp.Product)):
        k, a, b = e.limits[0]
        que = "la suma" if isinstance(e, sp.Sum) else "el producto"
        infinito = b in (sp.oo, -sp.oo)
        extra = " (una serie infinita)" if (infinito and isinstance(e, sp.Sum)) else ""
        return (f"{que}, para {_v(k)[0]} desde {_v(a)[0]} hasta {_v(b)[0]}{extra}, de {_env(*_v(e.function), minimo=3)}", 5)
    if isinstance(e, sp.Derivative):
        vc = list(e.variable_count)
        f = _env(*_v(e.expr), minimo=3)
        if len(vc) == 1:
            v, n = vc[0]
            multi = len(e.expr.free_symbols) > 1
            que = "la derivada parcial" if multi else "la derivada"
            if n == 1:
                return f"{que} de {f} respecto de {_v(v)[0]}", 5
            return f"{que} de orden {n} de {f} respecto de {_v(v)[0]}", 5
        orden = ", luego ".join(f"{_v(v)[0]}" + (f" (dos veces)" if n == 2 else f" ({n} veces)" if n > 2 else "") for v, n in vc)
        return f"la derivada parcial mixta de {f}, respecto de {orden}", 5

    # ---- relaciones y lógica ----
    for cls, txt in _REL_TXT.items():
        if isinstance(e, cls):
            return f"{_v(e.lhs)[0]} {txt} {_v(e.rhs)[0]}", 5
    if isinstance(e, sp.And):
        return " y además ".join(_v(a)[0] for a in e.args), 5
    if isinstance(e, sp.Or):
        return " o bien ".join(_v(a)[0] for a in e.args), 5
    if isinstance(e, sp.Piecewise):
        trozos = []
        for expr, cond in e.args:
            if cond == sp.true:
                trozos.append(f"vale {_v(expr)[0]} en cualquier otro caso")
            else:
                trozos.append(f"vale {_v(expr)[0]} cuando {_v(cond)[0]}")
        return "una función por trozos que " + "; ".join(trozos), 5

    # ---- funciones elementales ----
    if isinstance(e, sp.exp):
        return f"e elevado a {_env(*_v(e.args[0]))}", 1
    if isinstance(e, sp.log):
        return f"logaritmo natural de {_env(*_v(e.args[0]))}", 2
    if isinstance(e, sp.factorial):
        return f"{_env(*_v(e.args[0]))} factorial", 2
    if isinstance(e, sp.binomial):
        return f"el coeficiente binomial de {_v(e.args[0])[0]} sobre {_v(e.args[1])[0]}", 2
    if isinstance(e, (sp.Max, sp.Min)):
        pal = "máximo" if isinstance(e, sp.Max) else "mínimo"
        return f"el {pal} entre " + ", ".join(_v(a)[0] for a in e.args), 2
    nombre = _NOMBRE_FUNC.get(e.func) if hasattr(e, "func") else None
    if nombre and len(e.args) == 1:
        return f"{nombre} de {_env(*_v(e.args[0]))}", 2

    # ---- suma ----
    if e.is_Add:
        terms = _ordenar_terminos(e)
        hay_op = False
        out = ""
        for i, t in enumerate(terms):
            neg = t.could_extract_minus_sign()
            mag = -t if neg else t
            txt, niv = _v(mag)
            hay_op = hay_op or niv == 5
            if i == 0:
                out = ("menos " if neg else "") + txt
            else:
                sep = ", " if hay_op else " "
                out += f"{sep}{'menos' if neg else 'más'} {txt}"
        return out, 4

    # ---- producto, cociente, potencia ----
    if e.is_Mul or e.is_Pow:
        num, den = sp.fraction(e)
        if den != 1:
            # logaritmo en otra base: log(a)/log(b)
            if isinstance(num, sp.log) and isinstance(den, sp.log) and not den.args[0].free_symbols:
                return f"logaritmo en base {_v(den.args[0])[0]} de {_env(*_v(num.args[0]))}", 2
            nt, nn = _v(num)
            dt, dn = _v(den)
            if nn == 0 and dn == 0:
                return f"{nt} entre {dt}", 3
            return f"la fracción con numerador {nt} y denominador {dt}", 3
        if e.is_Pow:
            b, ex = e.as_base_exp()
            if ex == sp.Rational(1, 2):
                return f"raíz cuadrada de {_env(*_v(b))}", 2
            if ex == sp.Rational(1, 3):
                return f"raíz cúbica de {_env(*_v(b))}", 2
            if ex.is_Rational and ex.q > 1:
                inner = _v(sp.Pow(b, ex.p))[0] if ex.p != 1 else _v(b)[0]
                return f"raíz {ex.q}-ésima de ({inner})", 2
            bt, bn = _v(b)
            if ex == 2:
                return f"{_env(bt, bn)} al cuadrado", 1
            if ex == 3:
                return f"{_env(bt, bn)} al cubo", 1
            if ex.is_Integer and int(ex) in _ORDINAL:
                return f"{_env(bt, bn)} a la {_ORDINAL[int(ex)]}", 1
            et, en = _v(ex)
            return f"{_env(bt, bn)} elevado a {_env(et, en)}", 1
        factores = e.as_ordered_factors()
        if factores and factores[0] == -1:
            resto = sp.Mul(*factores[1:])
            return "menos " + _v(resto)[0], 3
        partes = []
        for f in factores:
            ft, fn = _v(f)
            partes.append(_env(ft, fn, 2) if fn in (2, 4, 5) else ft)
        return " por ".join(partes), 3

    return str(e), 0


def leer_en_espanol(obj) -> str:
    """Frase en español con lo que entendió el intérprete. Sin mayúscula inicial: la interfaz
    la antepone a «Entiendo: …» (así no se convierte una variable «x» o «α» en «X» o «Α»)."""
    txt, _ = _v(obj)
    return txt + "."


# ==============================================================================
# 4. CLASIFICACIÓN DE LA ENTRADA
# ==============================================================================
_OPERACIONES = (sp.Limit, LimiteMulti, sp.Integral, sp.Sum, sp.Product, sp.Derivative, Gradiente)


def _variables(e) -> list[sp.Symbol]:
    return sorted((s for s in e.free_symbols if isinstance(s, sp.Symbol)), key=lambda s: s.name)


def _describir_funcion(expr, vars_) -> str:
    if expr.has(sp.Piecewise):
        return "definida por trozos"
    try:
        if vars_ and expr.is_polynomial(*vars_):
            if not vars_:
                return "constante"
            g = sp.Poly(expr, *vars_).total_degree()
            return {0: "constante", 1: "lineal (polinomio de grado 1)", 2: "cuadrática (polinomio de grado 2)",
                    3: "cúbica (polinomio de grado 3)"}.get(g, f"polinomial de grado {g}")
        if vars_ and expr.is_rational_function(*vars_):
            return "racional (cociente de polinomios)"
    except Exception:  # noqa: BLE001
        pass
    comp = []
    if expr.has(sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc):
        comp.append("trigonométrica")
    if expr.has(sp.asin, sp.acos, sp.atan, sp.acot, sp.asec, sp.acsc):
        comp.append("trigonométrica inversa")
    if expr.has(sp.sinh, sp.cosh, sp.tanh, sp.coth, sp.sech, sp.csch):
        comp.append("hiperbólica")
    if expr.has(sp.exp):
        comp.append("exponencial")
    if expr.has(sp.log):
        comp.append("logarítmica")
    if any(p.is_Pow and p.exp.is_Rational and not p.exp.is_Integer for p in sp.preorder_traversal(expr)):
        comp.append("con raíces")
    if expr.has(sp.Abs):
        comp.append("con valor absoluto")
    if expr.has(sp.floor, sp.ceiling):
        comp.append("con parte entera")
    if expr.has(sp.factorial, sp.binomial):
        comp.append("con factoriales")
    if comp:
        return "combinación " + ("de tipo " if len(comp) == 1 else "de tipos ") + ", ".join(comp)
    return "algebraica"


def clasificar_entrada(obj) -> dict:
    """
    ¿Qué es lo que se escribió?  Devuelve un dict con:
      tipo       funcion | constante | relacion | limite | limite_multi | integral | serie |
                 suma_finita | producto | derivada | gradiente | compuesta
      etiqueta   nombre legible ("Función de 2 variables", "Serie infinita"…)
      variables  lista de símbolos libres (sin los índices/variables ligadas)
      n          cantidad de variables
      detalle    texto corto adicional (tipo de función, definida/indefinida, etc.)
    """
    vars_ = _variables(obj)
    n = len(vars_)
    info: dict[str, Any] = {"variables": vars_, "n": n, "detalle": ""}

    if obj in (sp.true, sp.false):
        info.update(tipo="relacion", etiqueta="Condición ya decidida: es " + ("siempre verdadera" if obj == sp.true else "siempre falsa"))
    elif isinstance(obj, (sp.Eq, sp.Ne, sp.Lt, sp.Le, sp.Gt, sp.Ge, sp.And, sp.Or)):
        parte = "ecuación" if isinstance(obj, sp.Eq) else "desigualdad" if not isinstance(obj, (sp.And, sp.Or)) else "sistema de condiciones"
        info.update(tipo="relacion", etiqueta=f"{parte.capitalize()} en {n} variable{'s' if n != 1 else ''}")
    elif isinstance(obj, sp.Limit):
        d = str(obj.args[3]) if len(obj.args) > 3 else "+-"
        lado = {"+": "lateral por la derecha", "-": "lateral por la izquierda"}.get(d, "bilateral")
        infinito = obj.args[2] in (sp.oo, -sp.oo)
        info.update(tipo="limite", etiqueta=f"Límite {'en el infinito' if infinito else lado} de una variable",
                    detalle="")
    elif isinstance(obj, LimiteMulti):
        info.update(tipo="limite_multi", etiqueta=f"Límite de {len(obj.args[1])} variables")
    elif isinstance(obj, sp.Integral):
        lim = list(obj.limits)
        definida = all(len(l) == 3 for l in lim)
        impropia = definida and any(b in (sp.oo, -sp.oo) or a in (sp.oo, -sp.oo) for _, a, b in lim)
        mult = {1: "", 2: " doble", 3: " triple"}.get(len(lim), " múltiple")
        etiq = f"Integral{mult} {'impropia' if impropia else 'definida' if definida else 'indefinida'}"
        info.update(tipo="integral", etiqueta=etiq)
    elif isinstance(obj, sp.Sum):
        k, a, b = obj.limits[0]
        if b in (sp.oo, -sp.oo) or a in (sp.oo, -sp.oo):
            info.update(tipo="serie", etiqueta="Serie infinita")
        else:
            info.update(tipo="suma_finita", etiqueta="Suma finita")
    elif isinstance(obj, sp.Product):
        k, a, b = obj.limits[0]
        info.update(tipo="producto", etiqueta="Producto infinito" if b in (sp.oo, -sp.oo) else "Productoria finita")
    elif isinstance(obj, sp.Derivative):
        vc = list(obj.variable_count)
        total = sum(c for _, c in vc)
        parcial = len(obj.expr.free_symbols) > 1
        etiq = ("Derivada parcial" if parcial else "Derivada") + (f" de orden {total}" if total > 1 else "")
        info.update(tipo="derivada", etiqueta=etiq + (" mixta" if len(vc) > 1 else ""))
    elif isinstance(obj, Gradiente):
        info.update(tipo="gradiente", etiqueta="Gradiente")
    elif any(obj.has(c) for c in _OPERACIONES):
        info.update(tipo="compuesta", etiqueta="Expresión que combina operaciones de cálculo")
    elif n == 0:
        info.update(tipo="constante", etiqueta="Expresión constante (un número)")
    else:
        info.update(tipo="funcion", etiqueta=f"Función de {n} variable{'s' if n != 1 else ''}"
                    + (f" ({', '.join(str(v) for v in vars_)})" if n <= 4 else ""),
                    detalle=_describir_funcion(obj, vars_))
        info["por_trozos"] = bool(obj.has(sp.Piecewise))
    return info


# ==============================================================================
# 5. COMPROBACIONES DE SENTIDO
# ==============================================================================
def _num_val(v):
    """float si v es un número real finito; si no, None."""
    try:
        if v.is_number and v.is_real and v.is_finite:
            return float(v)
    except Exception:  # noqa: BLE001
        pass
    return None


def _a(n, t):
    return {"nivel": n, "texto": t}


def diagnosticar(obj, latex: str = "") -> list[dict]:
    """
    Revisa si lo escrito TIENE SENTIDO matemático y avisa de lo dudoso.
    Devuelve una lista de {"nivel": "error"|"aviso"|"info", "texto": str}.
    "error" = no tiene sentido (la app no debería calcular); "aviso" = tiene sentido pero
    probablemente no es lo que se quería; "info" = aclaración útil.
    """
    r: list[dict] = []

    # --- a nivel de texto LaTeX ---
    if latex:
        if re.search(r"(?<![A-Za-z\\])[fgh]\\left\(|(?<![A-Za-z\\])[fgh]\(", latex):
            r.append(_a("aviso", "Escribiste algo como «f(x)». La app no define funciones con nombre: lo lee como el producto "
                        "de f por (x). Si querías definir una función, escribe directamente su fórmula (por ejemplo x²+1)."))
        if re.search(r"\\mathrm\{d\}\s*\\mathrm\{d\}", latex):
            r.append(_a("aviso", "Hay dos diferenciales seguidos; revisa que no sobre una «d»."))

    # --- recorrer la estructura ---
    for nodo in sp.preorder_traversal(obj):
        _diag_nodo(nodo, r)

    # --- comprobaciones globales de expresiones ---
    if isinstance(obj, sp.Expr) and not isinstance(obj, _OPERACIONES):
        if obj.has(sp.zoo, sp.nan):
            r.append(_a("error", "La expresión contiene una división entre cero o una operación indefinida "
                        "(por ejemplo 1/0 o 0/0): no tiene valor."))
        if obj.has(sp.oo, -sp.oo) and not obj.has(*_OPERACIONES):
            r.append(_a("aviso", "La expresión contiene infinito como un valor más; normalmente ∞ solo se usa como límite "
                        "o como extremo de una suma o integral."))
        if obj.has(sp.I):
            escribio_i = bool(re.search(r"\\imaginary[IJ]|\\mathrm\{i\}|(?<![A-Za-z\\])i(?![A-Za-z])", latex or ""))
            if latex and not escribio_i:
                r.append(_a("error", "Esta expresión no existe en los números reales: para evaluarla hubo que usar números "
                            "complejos (por ejemplo, el logaritmo, el arcoseno o una raíz de índice par de un número negativo)."))
            else:
                r.append(_a("aviso", "La expresión incluye la unidad imaginaria i. Los análisis de este módulo se hacen sobre "
                            "variables y valores REALES; los resultados pueden no ser los esperados."))
        vs = _variables(obj)
        if len(vs) > 4:
            r.append(_a("aviso", f"Hay {len(vs)} variables. Con más de 3, las gráficas y la Hessiana se limitan o se omiten."))
        if vs and obj.count_ops() < 80:
            try:
                s = sp.simplify(obj)
                if not s.free_symbols and not obj.has(*_OPERACIONES):
                    r.append(_a("info", f"Aunque aparecen variables, la expresión se simplifica a la constante ${sp.latex(s)}$."))
            except Exception:  # noqa: BLE001
                pass
        if isinstance(obj, sp.Piecewise):
            _diag_trozos(obj, r)
    if isinstance(obj, (sp.Eq, sp.Lt, sp.Le, sp.Gt, sp.Ge, sp.Ne)):
        if obj.lhs == obj.rhs and isinstance(obj, sp.Eq):
            r.append(_a("aviso", "Los dos lados son idénticos: la igualdad es siempre verdadera y no dice nada."))
        if not obj.free_symbols:
            r.append(_a("aviso", "No hay variables: la afirmación es simplemente verdadera o falsa."))
    if isinstance(obj, sp.Basic) and obj in (sp.true, sp.false):
        r.append(_a("aviso", "Esta relación se evaluó por completo, así que es " + (
            "siempre verdadera (por ejemplo, los dos lados son idénticos): no restringe nada." if obj == sp.true
            else "siempre falsa (una contradicción): no tiene solución.")))

    # --- notas informativas de convención ---
    if isinstance(obj, sp.Basic):
        nombres = {s.name for s in obj.free_symbols if isinstance(s, sp.Symbol)}
        if "n" in nombres and len(nombres) > 1 and not obj.has(sp.Sum, sp.Limit):
            r.append(_a("info", "Aparece la letra «n» junto a otras variables. Para estudiar una sucesión o una serie se "
                        "elige la variable índice en la sección «Series y sucesiones»."))
    return r


def _diag_trozos(pw: sp.Piecewise, r: list[dict]) -> None:
    vs = _variables(pw)
    if len(vs) != 1:
        return
    x = vs[0]
    conds = [c for _, c in pw.args]
    try:
        fs = [sp.lambdify(x, c, "math") for c in conds]
    except Exception:  # noqa: BLE001
        return
    huecos = solapes = 0
    for i in range(-60, 61):
        v = i / 6
        cuantas = 0
        for f in fs:
            try:
                cuantas += bool(f(v))
            except Exception:  # noqa: BLE001
                pass
        huecos += cuantas == 0
        solapes += cuantas > 1
    if huecos:
        r.append(_a("aviso", "Hay valores de la variable en los que NINGÚN trozo aplica: la función no está definida ahí. "
                    "Si querías cubrir todos los casos, agrega un trozo final «en otro caso»."))
    if solapes and pw.args[-1][1] != sp.true:
        r.append(_a("aviso", "Algunos trozos se traslapan; SymPy aplica el primero cuyas condiciones se cumplan."))
    elif solapes:
        pass


def _diag_nodo(n, r: list[dict]) -> None:
    # ---------- Límite ----------
    if isinstance(n, sp.Limit):
        f, x, a = n.args[0], n.args[1], n.args[2]
        d = str(n.args[3]) if len(n.args) > 3 else "+-"
        if x not in f.free_symbols:
            r.append(_a("aviso", f"La variable {x} no aparece dentro del límite: el límite de una constante es la propia constante."))
        if a.has(x):
            r.append(_a("error", f"El valor al que tiende {x} no puede depender de {x} misma."))
        if a in (sp.oo, -sp.oo) and d in ("+", "-"):
            r.append(_a("aviso", "Al tender a infinito no tiene sentido «por la derecha/izquierda»: se ignora el lado."))
        if a in (sp.zoo, sp.nan):
            r.append(_a("error", "El valor al que tiende la variable no está definido."))
        extra = sorted((s.name for s in f.free_symbols if s != x), key=str)
        if extra:
            r.append(_a("aviso", f"El límite contiene otras variables ({', '.join(extra)}): se tratarán como constantes (parámetros)."))
    # ---------- Límite de varias variables ----------
    elif isinstance(n, LimiteMulti):
        f, xs, as_ = n.args
        if len(xs) != len(as_):
            r.append(_a("error", "Hay distinto número de variables que de valores a donde tienden."))
        faltan = [str(x) for x in xs if x not in f.free_symbols]
        if faltan:
            r.append(_a("aviso", f"La(s) variable(s) {', '.join(faltan)} no aparece(n) en la función."))
        if len(set(xs)) != len(xs):
            r.append(_a("error", "Hay una variable repetida en el límite."))
        if len(xs) == 1:
            r.append(_a("info", "Escribiste un límite con una sola variable entre paréntesis; se tratará como límite normal."))
    # ---------- Integral ----------
    elif isinstance(n, sp.Integral):
        for l in n.limits:
            v = l[0]
            if v not in n.function.free_symbols:
                r.append(_a("aviso", f"El integrando no depende de {v}: integrar una constante respecto de {v} da (constante)·{v}."))
            if len(l) == 3:
                a, b = l[1], l[2]
                if a.has(v) or b.has(v):
                    r.append(_a("error", f"Los límites de integración no pueden depender de la variable de integración ({v})."))
                av, bv = _num_val(a), _num_val(b)
                if av is not None and bv is not None:
                    if av == bv:
                        r.append(_a("info", "Los dos límites coinciden: una integral sobre un intervalo de longitud 0 vale 0."))
                    elif av > bv:
                        r.append(_a("aviso", "El límite inferior es mayor que el superior: el resultado cambia de signo "
                                    "respecto de integrar de menor a mayor."))
                if a in (sp.zoo, sp.nan) or b in (sp.zoo, sp.nan):
                    r.append(_a("error", "Un límite de integración no está definido."))
                if (a == sp.oo) or (b == -sp.oo):
                    r.append(_a("aviso", "Los límites van de +∞ hacia atrás o hacia −∞ al revés; revisa el orden."))
        vars_int = [l[0] for l in n.limits]
        if len(set(vars_int)) != len(vars_int):
            r.append(_a("error", "Se integra dos veces respecto de la misma variable: revisa los diferenciales."))
    # ---------- Suma / Producto ----------
    elif isinstance(n, (sp.Sum, sp.Product)):
        k, a, b = n.limits[0]
        que = "suma" if isinstance(n, sp.Sum) else "producto"
        if k not in n.function.free_symbols:
            r.append(_a("aviso", f"El índice {k} no aparece dentro de la {que}: se repite el mismo término en cada paso."))
        if a.has(k) or b.has(k):
            r.append(_a("error", f"Los límites de la {que} no pueden depender del índice ({k})."))
        for nombre, v in (("inferior", a), ("superior", b)):
            vv = _num_val(v)
            if vv is not None and vv != int(vv):
                r.append(_a("error", f"El límite {nombre} de la {que} debe ser un número entero (es {v})."))
        if a in (sp.oo, -sp.oo):
            r.append(_a("error", f"El límite inferior de la {que} no puede ser infinito."))
        av, bv = _num_val(a), _num_val(b)
        if av is not None and bv is not None and av > bv:
            r.append(_a("aviso", f"El límite inferior ({a}) es mayor que el superior ({b}): la {que} está vacía "
                        f"(vale {'0' if isinstance(n, sp.Sum) else '1'} por convención)."))
        if b == -sp.oo:
            r.append(_a("aviso", "El límite superior es −∞; normalmente es +∞ o un entero."))
    # ---------- Derivada ----------
    elif isinstance(n, sp.Derivative):
        total = sum(c for _, c in n.variable_count)
        for v, c in n.variable_count:
            if v not in n.expr.free_symbols:
                r.append(_a("aviso", f"La expresión no depende de {v}: su derivada respecto de {v} es 0."))
        if total > 6:
            r.append(_a("aviso", f"Derivada de orden {total}: puede tardar y producir expresiones enormes."))
        if n.expr.has(sp.Abs, sp.floor, sp.ceiling, sp.sign, sp.Piecewise, sp.Max, sp.Min):
            r.append(_a("info", "La expresión contiene valor absoluto, parte entera, signo o trozos: no es derivable en algunos puntos."))
    # ---------- Gradiente ----------
    elif isinstance(n, Gradiente):
        if not n.args[0].free_symbols:
            r.append(_a("aviso", "El gradiente de una constante es el vector cero."))
        elif len(n.args[0].free_symbols) == 1:
            r.append(_a("info", "Con una sola variable el gradiente es simplemente la derivada."))
    # ---------- Funciones con dominio restringido (constantes obvias) ----------
    elif isinstance(n, sp.log) and not n.args[0].free_symbols:
        v = _num_val(n.args[0])
        if v is not None and v <= 0:
            r.append(_a("error", f"El logaritmo de {n.args[0]} no existe en los reales (el argumento debe ser positivo)."))
    elif isinstance(n, (sp.asin, sp.acos)) and not n.args[0].free_symbols:
        v = _num_val(n.args[0])
        if v is not None and abs(v) > 1:
            r.append(_a("error", f"El arcoseno/arcocoseno de {n.args[0]} no existe en los reales (el argumento debe estar entre −1 y 1)."))
    elif isinstance(n, sp.Pow) and not n.free_symbols:
        b, e = n.as_base_exp()
        bv, ev = _num_val(b), _num_val(e)
        if bv is not None and ev is not None:
            if bv == 0 and ev <= 0:
                r.append(_a("error", "Hay un 0 elevado a una potencia no positiva (0⁰ o división entre cero)."))
            elif bv < 0 and e.is_Rational and e.q % 2 == 0:
                r.append(_a("error", f"Hay una raíz de índice par de un número negativo ({b}): no existe en los reales."))
    elif isinstance(n, sp.factorial) and not n.args[0].free_symbols:
        v = _num_val(n.args[0])
        if v is not None and (v < 0 or v != int(v)):
            r.append(_a("error", f"El factorial solo se define para enteros no negativos (se escribió {n.args[0]})."))
