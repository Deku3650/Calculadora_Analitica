# estructuras.py
"""
estructuras.py
==============
Objetos matemáticos que SymPy no trae y que el intérprete necesita para entender lo que el teclado
puede escribir: puntos, vectores, listas, espacios ℝⁿ, regiones de ℝⁿ, bolas, funciones definidas
con «↦», cuantificadores, argumentos lógicos, congruencias…

Cada objeto lleva una `lectura`: la frase en español con la que la interfaz dice «Entiendo: …».

Todo es puro Python/SymPy (sin Streamlit) y serializable (el motor corre en otro proceso).

Convenciones
------------
* Un PUNTO (a, b, …) y un VECTOR ⟨a, b, …⟩ guardan coordenadas; no se pueden mezclar a la ligera:
  punto − punto = vector, punto + vector = punto, vector + vector = vector.
* Las operaciones cuyo resultado es un NÚMERO (norma, producto punto, distancia, ángulo) quedan como
  nodos de SymPy sin evaluar (Norma, ProdPunto, Distancia, Angulo) para conservar su estructura;
  `evaluar_nodos` los calcula.
* Un CONJUNTO es un sympy.Set (intervalos, conjuntos finitos, ℕ, ℤ…) o una Region (condición sobre
  variables de ℝⁿ). Las bolas son Regiones con propiedades exactas.
"""
from __future__ import annotations

import itertools
import math

import sympy as sp

__all__ = [
    "ErrorEstructura", "Punto", "Vector", "Lista", "Espacio", "Region", "Bola", "Funcion", "Cuantificado",
    "Argumento", "Equivalencia", "Aproximado", "Congruencia", "Divisibilidad", "RelConj", "OpTop", "Pertenencia",
    "ConjuntoImagen", "Norma", "ProdPunto", "Distancia", "Angulo", "evaluar_nodos", "variables_por_defecto",
    "a_conjunto", "a_region", "operar_conjuntos", "complemento", "producto_cartesiano", "pertenece",
    "es_conjunto", "es_vectorial", "conjunto_nb", "dimension_de", "coords_de", "completar_patron", "texto_valor", "lectura_de", "ELIPSIS",
]


class ErrorEstructura(ValueError):
    """Problema con una estructura (mensaje en español, listo para mostrar)."""


# Gancho que interprete_latex rellena con su verbalizador de expresiones de SymPy (evita un import circular).
LEER = None


def texto_valor(v) -> str:
    """Texto corto de un valor (número, expresión, punto…) para usar dentro de una frase."""
    if hasattr(v, "txt"):
        return v.txt()
    try:
        s = sp.sstr(v)
    except Exception:  # noqa: BLE001
        s = str(v)
    return s.replace("**", "^").replace("oo", "∞")


def lectura_de(v) -> str:
    """Frase en español de cualquier objeto (propio o de SymPy)."""
    if hasattr(v, "lectura"):
        return v.lectura
    if LEER is not None:
        try:
            return LEER(v)
        except Exception:  # noqa: BLE001
            pass
    return texto_valor(v)


ELIPSIS = object()      # marcador de «…» dentro de una lista que se está leyendo


# ==============================================================================
# Puntos y vectores
# ==============================================================================
def _coords(it):
    out = tuple(sp.sympify(c) for c in it)
    if not out:
        raise ErrorEstructura("Hace falta al menos una coordenada.")
    for c in out:
        if not isinstance(c, sp.Expr):
            raise ErrorEstructura("Las coordenadas deben ser números o expresiones, no conjuntos ni condiciones.")
    return out


def _mismo_n(a, b, que="los objetos"):
    if a.n != b.n:
        raise ErrorEstructura(f"No se pueden combinar {que} de dimensión {a.n} y de dimensión {b.n}.")


def _escalar(o):
    if isinstance(o, sp.Expr):
        return o
    raise ErrorEstructura("Eso solo se puede multiplicar por un número. Para multiplicar dos vectores usa «·» "
                          "(producto punto) o «×» (producto cruz en ℝ³).")


class Punto:
    """Un punto (a, b, …) de ℝⁿ."""
    __slots__ = ("c", "lectura", "ambiguo")

    def __init__(self, coords, lectura=None, ambiguo=False):
        self.c = _coords(coords)
        self.ambiguo = bool(ambiguo)       # (a, b) también podría ser el intervalo abierto de a a b
        self.lectura = lectura or f"el punto {self.txt()}"

    @property
    def n(self):
        return len(self.c)

    def txt(self):
        return "(" + ", ".join(texto_valor(c) for c in self.c) + ")"

    def __repr__(self):
        return f"Punto({self.c!r}, ambiguo={self.ambiguo})"

    def __eq__(self, o):
        return isinstance(o, Punto) and self.c == o.c

    def __hash__(self):
        return hash(("Punto", self.c))

    def __sub__(self, o):
        if isinstance(o, Punto):
            _mismo_n(self, o, "puntos")
            v = [a - b for a, b in zip(self.c, o.c)]
            return Vector(v, f"el vector {Vector(v).txt()}, que va del punto {o.txt()} al punto {self.txt()}")
        if isinstance(o, Vector):
            _mismo_n(self, o, "un punto y un vector")
            p = [a - b for a, b in zip(self.c, o.c)]
            return Punto(p, f"el punto {Punto(p).txt()}, que es {self.txt()} desplazado por −{o.txt()}")
        raise ErrorEstructura("A un punto solo se le puede restar otro punto (da un vector) o un vector (da un punto).")

    def __add__(self, o):
        if isinstance(o, Vector):
            _mismo_n(self, o, "un punto y un vector")
            p = [a + b for a, b in zip(self.c, o.c)]
            return Punto(p, f"el punto {Punto(p).txt()}, que es {self.txt()} desplazado por el vector {o.txt()}")
        raise ErrorEstructura("Dos puntos no se pueden sumar. Resta uno del otro (da un vector) o suma un vector a un punto.")

    __radd__ = __add__

    def __rsub__(self, o):
        raise ErrorEstructura("No se puede restar un punto a un número o a otro tipo de objeto.")

    def __neg__(self):
        raise ErrorEstructura("Un punto no tiene signo. Si quieres el opuesto, usa un vector ⟨ ⟩.")

    def __mul__(self, o):
        raise ErrorEstructura("Un punto no se multiplica por un número. Para escalar usa un vector ⟨ ⟩.")

    __rmul__ = __truediv__ = __rtruediv__ = __mul__


class Vector:
    """Un vector ⟨a, b, …⟩ de ℝⁿ."""
    __slots__ = ("c", "lectura")

    def __init__(self, coords, lectura=None):
        self.c = _coords(coords)
        self.lectura = lectura or f"el vector {self.txt()}"

    @property
    def n(self):
        return len(self.c)

    def txt(self):
        return "⟨" + ", ".join(texto_valor(c) for c in self.c) + "⟩"

    def __repr__(self):
        return f"Vector({self.c!r})"

    def __eq__(self, o):
        return isinstance(o, Vector) and self.c == o.c

    def __hash__(self):
        return hash(("Vector", self.c))

    def __add__(self, o):
        if isinstance(o, Vector):
            _mismo_n(self, o, "vectores")
            v = [a + b for a, b in zip(self.c, o.c)]
            return Vector(v, f"el vector {Vector(v).txt()}, que es la suma de {self.txt()} y {o.txt()}")
        if isinstance(o, Punto):
            return o + self
        raise ErrorEstructura("Un vector solo se suma con otro vector (da un vector) o con un punto (da un punto), no con un número.")

    __radd__ = __add__

    def __sub__(self, o):
        if isinstance(o, Vector):
            _mismo_n(self, o, "vectores")
            v = [a - b for a, b in zip(self.c, o.c)]
            return Vector(v, f"el vector {Vector(v).txt()}, que es la resta {self.txt()} − {o.txt()}")
        raise ErrorEstructura("A un vector solo se le resta otro vector.")

    def __rsub__(self, o):
        if isinstance(o, Punto):
            return o - self
        raise ErrorEstructura("A un número no se le puede restar un vector.")

    def __neg__(self):
        v = [-a for a in self.c]
        return Vector(v, f"el vector {Vector(v).txt()}, que es el opuesto de {self.txt()}")

    def __mul__(self, o):
        k = _escalar(o)
        v = [k * a for a in self.c]
        return Vector(v, f"el vector {Vector(v).txt()}, que es {texto_valor(k)} por {self.txt()}")

    __rmul__ = __mul__

    def __truediv__(self, o):
        k = _escalar(o)
        if k == 0:
            raise ErrorEstructura("No se puede dividir un vector entre 0.")
        v = [a / k for a in self.c]
        return Vector(v, f"el vector {Vector(v).txt()}, que es {self.txt()} entre {texto_valor(k)}")

    def __rtruediv__(self, o):
        raise ErrorEstructura("No se puede dividir un número entre un vector.")

    def cruz(self, o):
        if not isinstance(o, Vector) or self.n != 3 or o.n != 3:
            raise ErrorEstructura("El producto cruz (×) solo existe entre dos vectores de ℝ³. En ℝ² usa el producto punto (·).")
        a, b = self.c, o.c
        v = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
        v = [sp.simplify(t) for t in v]
        return Vector(v, f"el vector {Vector(v).txt()}, que es el producto cruz {self.txt()} × {o.txt()} "
                         "(perpendicular a los dos)")


def es_vectorial(v) -> bool:
    return isinstance(v, (Punto, Vector))


def coords_de(v):
    """Coordenadas de un Punto/Vector (o de un escalar, como punto de ℝ¹) como tupla de sympy."""
    if isinstance(v, (Punto, Vector)):
        return v.c
    if isinstance(v, sp.Expr):
        return (v,)
    raise ErrorEstructura("Hace falta un punto, un vector o un número.")


# ---- operaciones con resultado numérico: nodos de SymPy sin evaluar --------------------------
class Norma(sp.Function):
    """‖v‖: Norma(Tuple(coordenadas))."""
    nargs = 1

    def _latex(self, printer):
        return r"\left\lVert " + ", ".join(printer._print(c) for c in self.args[0]).join(["\\langle ", "\\rangle"]) + r"\right\rVert"


class ProdPunto(sp.Function):
    """u · v."""
    nargs = 2

    def _latex(self, printer):
        f = lambda t: r"\langle " + ", ".join(printer._print(c) for c in t) + r"\rangle"  # noqa: E731
        return f(self.args[0]) + r" \cdot " + f(self.args[1])


class Distancia(sp.Function):
    """d(p, q)."""
    nargs = 2

    def _latex(self, printer):
        f = lambda t: "(" + ", ".join(printer._print(c) for c in t) + ")"  # noqa: E731
        return r"d\left(" + f(self.args[0]) + ", " + f(self.args[1]) + r"\right)"


class Angulo(sp.Function):
    """Ángulo entre dos vectores."""
    nargs = 2

    def _latex(self, printer):
        f = lambda t: r"\langle " + ", ".join(printer._print(c) for c in t) + r"\rangle"  # noqa: E731
        return r"\angle\left(" + f(self.args[0]) + ", " + f(self.args[1]) + r"\right)"


def _eval_nodo(n):
    a = tuple(n.args[0])
    if isinstance(n, Norma):
        return sp.sqrt(sum(c ** 2 for c in a))
    b = tuple(n.args[1])
    if len(a) != len(b):
        raise ErrorEstructura(f"Las dimensiones no coinciden: {len(a)} y {len(b)}.")
    if isinstance(n, ProdPunto):
        return sum(x * y for x, y in zip(a, b))
    if isinstance(n, Distancia):
        return sp.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    if isinstance(n, Angulo):
        na, nb = sp.sqrt(sum(c ** 2 for c in a)), sp.sqrt(sum(c ** 2 for c in b))
        if na == 0 or nb == 0:
            raise ErrorEstructura("El ángulo con el vector cero no está definido.")
        return sp.acos(sp.simplify(sum(x * y for x, y in zip(a, b)) / (na * nb)))
    return n


def evaluar_nodos(e):
    """Reemplaza Norma/ProdPunto/Distancia/Angulo por su valor."""
    if not isinstance(e, sp.Basic):
        return e
    return e.replace(lambda x: isinstance(x, (Norma, ProdPunto, Distancia, Angulo)), _eval_nodo)


# ==============================================================================
# Listas y patrones («1, 3, 5, …, 21»)
# ==============================================================================
class Lista:
    """Lista ordenada (con repeticiones). `patron` = ('aritmetica', d) | ('geometrica', r) | None."""
    __slots__ = ("items", "patron", "abierta", "simbolica", "lectura")

    def __init__(self, items, patron=None, abierta=False, simbolica=False, lectura=None):
        self.items = tuple(items)
        self.patron = patron
        self.abierta = abierta            # termina en «…»: sigue indefinidamente
        self.simbolica = simbolica        # tiene «…» entre símbolos (x₁, x₂, …, xₙ): no se puede expandir
        self.lectura = lectura or self._lectura()

    @property
    def n(self):
        return len(self.items)

    def txt(self):
        cuerpo = ", ".join(texto_valor(i) for i in self.items)
        if self.abierta:
            cuerpo += ", …"
        return "[" + cuerpo + "]"

    def _lectura(self):
        base = f"la lista {self.txt()}"
        if self.patron:
            tipo, p = self.patron
            base += (f" (una progresión aritmética de diferencia {texto_valor(p)})" if tipo == "aritmetica"
                     else f" (una progresión geométrica de razón {texto_valor(p)})")
        return base

    def __repr__(self):
        return f"Lista({self.items!r}, patron={self.patron!r}, abierta={self.abierta}, simbolica={self.simbolica})"

    def __eq__(self, o):
        return isinstance(o, Lista) and self.items == o.items and self.abierta == o.abierta

    def __hash__(self):
        return hash(("Lista", self.items, self.abierta))


def completar_patron(antes, despues, max_terminos=500):
    """
    Completa «a, b, c, …, z»: detecta si es una progresión aritmética o geométrica y la expande.
    Devuelve una Lista. Si los elementos son simbólicos (x₁, x₂, …, xₙ) no se expande.
    """
    antes, despues = list(antes), list(despues)
    todos = antes + despues
    if not all(isinstance(t, sp.Expr) for t in todos) or any(t.free_symbols for t in todos):
        return Lista(antes + despues, simbolica=True, abierta=not despues,
                     lectura="la lista " + ", ".join(texto_valor(t) for t in antes) + ", …"
                             + ((", " + ", ".join(texto_valor(t) for t in despues)) if despues else ""))
    if len(antes) < 2:
        raise ErrorEstructura("Para completar «…» hacen falta al menos dos elementos antes de los puntos suspensivos "
                              "(por ejemplo 1, 3, …, 21).")
    d = sp.simplify(antes[1] - antes[0])
    es_arit = all(sp.simplify(antes[i + 1] - antes[i] - d) == 0 for i in range(len(antes) - 1))
    r = None
    es_geo = False
    if antes[0] != 0:
        try:
            r = sp.simplify(antes[1] / antes[0])
            es_geo = r != 1 and all(antes[i] != 0 and sp.simplify(antes[i + 1] / antes[i] - r) == 0 for i in range(len(antes) - 1))
        except Exception:  # noqa: BLE001
            es_geo = False
    # con solo dos elementos, la aritmética es la lectura natural; con tres o más, manda el patrón que se cumple
    if es_arit and not (len(antes) >= 3 and es_geo and not es_arit):
        patron = ("aritmetica", d)
    elif es_geo:
        patron = ("geometrica", r)
    else:
        raise ErrorEstructura("No reconozco el patrón de los primeros elementos: no es una progresión aritmética (diferencia "
                              "constante) ni geométrica (razón constante).")
    if not despues:
        return Lista(antes, patron=patron, abierta=True)
    ultimo = despues[-1]
    if patron[0] == "aritmetica":
        if d == 0:
            raise ErrorEstructura("Los primeros elementos son iguales: no se puede deducir cuántos términos hay.")
        k = sp.simplify((ultimo - antes[0]) / d)
        sigue = lambda i: antes[0] + i * d  # noqa: E731
    else:
        if ultimo == 0 or antes[0] == 0:
            raise ErrorEstructura("Con razón geométrica el último término no puede ser 0.")
        q = sp.simplify(ultimo / antes[0])
        if r <= 0:
            raise ErrorEstructura("Una progresión geométrica con razón negativa o cero no se completa de forma automática.")
        k = sp.simplify(sp.log(q) / sp.log(r))
        sigue = lambda i: antes[0] * r ** i  # noqa: E731
    if not (k.is_Integer and k >= len(antes) - 1):
        raise ErrorEstructura(f"El último término ({texto_valor(ultimo)}) no encaja con el patrón: la progresión nunca lo alcanza "
                              "exactamente (o ya lo pasó).")
    if int(k) + 1 > max_terminos:
        raise ErrorEstructura(f"La lista tendría {int(k) + 1} términos; el máximo es {max_terminos}.")
    items = [sp.simplify(sigue(i)) for i in range(int(k) + 1)]
    return Lista(items, patron=patron)


# ==============================================================================
# Espacios, regiones y bolas
# ==============================================================================
def variables_por_defecto(n: int):
    """Variables de un punto de ℝⁿ: x, y, z para n ≤ 3; x₁, …, xₙ después."""
    nombres = ["x", "y", "z"] if n <= 3 else [f"x_{i}" for i in range(1, n + 1)]
    return tuple(sp.Symbol(nm, real=True) for nm in nombres[:n])


class Espacio:
    """ℝⁿ (n entero, o un símbolo como n)."""
    __slots__ = ("n", "lectura")

    def __init__(self, n):
        self.n = sp.sympify(n)
        self.lectura = f"el espacio ℝ^{texto_valor(self.n)} (todos los puntos con {texto_valor(self.n)} coordenadas reales)"

    @property
    def dim(self):
        return int(self.n) if self.n.is_Integer else None

    def txt(self):
        return f"ℝ^{texto_valor(self.n)}"

    def __eq__(self, o):
        return isinstance(o, Espacio) and self.n == o.n

    def __hash__(self):
        return hash(("Espacio", self.n))

    def __repr__(self):
        return f"Espacio({self.n!r})"


class Region:
    """Conjunto de puntos de ℝⁿ descrito por una condición booleana sobre `vars`."""
    __slots__ = ("vars", "cond", "lectura", "puntos", "dominio")

    def __init__(self, vars_, cond, lectura="", puntos=None, dominio=None):
        self.vars = tuple(vars_)
        self.cond = cond
        self.puntos = tuple(puntos) if puntos else None     # si es un conjunto finito de puntos
        self.dominio = dominio                              # sympy Set base (ℕ, ℤ…) en dimensión 1, o None
        self.lectura = lectura or f"el conjunto de puntos {texto_valor(tuple(self.vars))} que cumplen {texto_valor(cond)}"

    @property
    def n(self):
        return len(self.vars)

    def txt(self):
        return "{" + ", ".join(texto_valor(v) for v in self.vars) + " : " + texto_valor(self.cond) + "}"

    def renombrar(self, nuevas):
        if len(nuevas) != self.n:
            raise ErrorEstructura("Dimensiones distintas.")
        sub = dict(zip(self.vars, nuevas))
        return Region(nuevas, self.cond.subs(sub, simultaneous=True), self.lectura, self.puntos, self.dominio)

    def __repr__(self):
        return f"Region({self.vars!r}, {sp.srepr(self.cond)}, puntos={self.puntos!r}, dominio={self.dominio!r})"

    def __eq__(self, o):
        return isinstance(o, Region) and self.vars == o.vars and self.cond == o.cond and self.puntos == o.puntos and self.dominio == o.dominio


class Bola:
    """Bola abierta B_r(c) = {p : ‖p − c‖ < r}; cerrada con ≤; esfera con =. Siempre ℝⁿ con n ≥ 2."""
    __slots__ = ("centro", "radio", "cerrada", "esfera", "lectura")

    def __init__(self, centro, radio, cerrada=False, esfera=False):
        if not isinstance(centro, Punto):
            raise ErrorEstructura("El centro de una bola debe ser un punto (a, b, …).")
        if not isinstance(radio, sp.Expr):
            raise ErrorEstructura("El radio de una bola debe ser un número.")
        self.centro, self.radio, self.cerrada, self.esfera = centro, radio, bool(cerrada), bool(esfera)
        nombre = "la esfera" if esfera else ("la bola cerrada" if cerrada else "la bola abierta")
        self.lectura = (f"{nombre} de centro {centro.txt()} y radio {texto_valor(radio)} "
                        f"(los puntos {'a distancia exactamente' if esfera else 'a distancia ' + ('menor o igual' if cerrada else 'menor')} "
                        f"que {texto_valor(radio)} del centro)")

    @property
    def n(self):
        return self.centro.n

    def region(self, vars_=None) -> Region:
        vars_ = vars_ or variables_por_defecto(self.n)
        d2 = sum((v - c) ** 2 for v, c in zip(vars_, self.centro.c))
        r2 = self.radio ** 2
        cond = sp.Eq(d2, r2) if self.esfera else (sp.Le(d2, r2) if self.cerrada else sp.Lt(d2, r2))
        return Region(vars_, cond, self.lectura)

    def txt(self):
        s = "S" if self.esfera else ("B̄" if self.cerrada else "B")
        return f"{s}_{texto_valor(self.radio)}{self.centro.txt()}"

    def __repr__(self):
        return f"Bola({self.centro!r}, {sp.srepr(self.radio)}, cerrada={self.cerrada}, esfera={self.esfera})"

    def __eq__(self, o):
        return (isinstance(o, Bola) and self.centro == o.centro and self.radio == o.radio
                and self.cerrada == o.cerrada and self.esfera == o.esfera)


# ==============================================================================
# Funciones y lógica
# ==============================================================================
class Funcion:
    """Función con variables explícitas: f(x, y) = expr  ó  (x, y) ↦ expr."""
    __slots__ = ("nombre", "vars", "expr", "lectura")

    def __init__(self, nombre, vars_, expr, lectura=None):
        self.nombre = nombre
        self.vars = tuple(vars_)
        self.expr = expr
        pre = f"la función {nombre}" if nombre else "la función"
        self.lectura = lectura or (f"{pre} que a ({', '.join(texto_valor(v) for v in self.vars)}) le asigna {lectura_de(expr)}")

    @property
    def n(self):
        return len(self.vars)

    def componer(self, interna):
        """self ∘ interna  =  self(interna(·))."""
        if not isinstance(interna, Funcion):
            raise ErrorEstructura("La composición «∘» necesita dos funciones: por ejemplo (x ↦ x²) ∘ (x ↦ x + 1).")
        if self.n != 1:
            raise ErrorEstructura("Solo se pueden componer funciones cuya función exterior tiene una sola variable.")
        nueva = sp.simplify(self.expr.subs(self.vars[0], interna.expr))
        nom = f"{self.nombre}∘{interna.nombre}" if self.nombre and interna.nombre else None
        return Funcion(nom, interna.vars, nueva,
                       f"la composición: primero se aplica {lectura_de(interna)}; al resultado se le aplica "
                       f"{lectura_de(self)}. Queda {texto_valor(nueva)}")

    def __repr__(self):
        return f"Funcion({self.nombre!r}, {self.vars!r}, {sp.srepr(self.expr)})"

    def __eq__(self, o):
        return isinstance(o, Funcion) and self.nombre == o.nombre and self.vars == o.vars and self.expr == o.expr


class Cuantificado:
    """∀ / ∃ / ∄ variables ∈ dominio : cuerpo."""
    __slots__ = ("cuantificador", "vars", "dominio", "cuerpo", "lectura")

    def __init__(self, cuantificador, vars_, dominio, cuerpo, lectura=None):
        self.cuantificador = cuantificador          # 'para_todo' | 'existe' | 'no_existe'
        self.vars = tuple(vars_)
        self.dominio = dominio                      # conjunto o None (= ℝ)
        self.cuerpo = cuerpo
        pal = {"para_todo": "para todo", "existe": "existe", "no_existe": "no existe"}[cuantificador]
        dom = f" en {lectura_de(dominio)}" if dominio is not None else " real"
        nom = ", ".join(texto_valor(v) for v in self.vars)
        if cuantificador == "para_todo":
            self.lectura = lectura or f"{pal} {nom}{dom}, se cumple que {lectura_de(cuerpo)}"
        else:
            self.lectura = lectura or f"{pal} {nom}{dom} tal que {lectura_de(cuerpo)}"

    def __repr__(self):
        return f"Cuantificado({self.cuantificador!r}, {self.vars!r}, {self.dominio!r}, {self.cuerpo!r})"

    def __eq__(self, o):
        return (isinstance(o, Cuantificado) and self.cuantificador == o.cuantificador
                and self.vars == o.vars and self.dominio == o.dominio and self.cuerpo == o.cuerpo)


class Argumento:
    """Premisas ∴ conclusión."""
    __slots__ = ("premisas", "conclusion", "lectura")

    def __init__(self, premisas, conclusion):
        self.premisas, self.conclusion = tuple(premisas), conclusion
        self.lectura = ("el argumento con premisas: " + "; ".join(lectura_de(p) for p in self.premisas)
                        + f"; y conclusión: {lectura_de(conclusion)}")

    def __repr__(self):
        return f"Argumento({self.premisas!r}, {self.conclusion!r})"

    def __eq__(self, o):
        return isinstance(o, Argumento) and self.premisas == o.premisas and self.conclusion == o.conclusion


class Equivalencia:
    """a ≡ b (identidad de expresiones o equivalencia lógica)."""
    __slots__ = ("a", "b", "lectura")

    def __init__(self, a, b):
        self.a, self.b = a, b
        self.lectura = f"la afirmación de que {lectura_de(a)} es equivalente (idéntico) a {lectura_de(b)}"

    def __repr__(self):
        return f"Equivalencia({self.a!r}, {self.b!r})"

    def __eq__(self, o):
        return isinstance(o, Equivalencia) and self.a == o.a and self.b == o.b


class Aproximado:
    """a ≈ b."""
    __slots__ = ("a", "b", "lectura")

    def __init__(self, a, b):
        self.a, self.b = a, b
        self.lectura = f"la afirmación de que {lectura_de(a)} es aproximadamente igual a {lectura_de(b)}"

    def __repr__(self):
        return f"Aproximado({self.a!r}, {self.b!r})"

    def __eq__(self, o):
        return isinstance(o, Aproximado) and self.a == o.a and self.b == o.b


class Congruencia:
    """a ≡ b (mod n)."""
    __slots__ = ("a", "b", "n", "lectura")

    def __init__(self, a, b, n):
        self.a, self.b, self.n = a, b, n
        self.lectura = f"la congruencia: {lectura_de(a)} es congruente con {lectura_de(b)} módulo {lectura_de(n)}"

    def __repr__(self):
        return f"Congruencia({self.a!r}, {self.b!r}, {self.n!r})"

    def __eq__(self, o):
        return isinstance(o, Congruencia) and self.a == o.a and self.b == o.b and self.n == o.n


class Divisibilidad:
    """a ∣ b  (a divide a b)."""
    __slots__ = ("a", "b", "lectura")

    def __init__(self, a, b):
        self.a, self.b = a, b
        self.lectura = f"la afirmación de que {lectura_de(a)} divide a {lectura_de(b)}"

    def __repr__(self):
        return f"Divisibilidad({self.a!r}, {self.b!r})"

    def __eq__(self, o):
        return isinstance(o, Divisibilidad) and self.a == o.a and self.b == o.b


_RELCONJ = {"subset": "es subconjunto propio de", "subseteq": "es subconjunto de", "supset": "es superconjunto propio de",
            "supseteq": "es superconjunto de", "eq": "es igual a", "ne": "es distinto de"}


class RelConj:
    """Relación entre conjuntos (⊂, ⊆, ⊃, ⊇, =, ≠): se evalúa después, con explicación."""
    __slots__ = ("op", "a", "b", "lectura")

    def __init__(self, op, a, b):
        self.op, self.a, self.b = op, a, b
        self.lectura = f"la afirmación de que {lectura_de(a)} {_RELCONJ[op]} {lectura_de(b)}"

    def __repr__(self):
        return f"RelConj({self.op!r}, {self.a!r}, {self.b!r})"

    def __eq__(self, o):
        return isinstance(o, RelConj) and self.op == o.op and self.a == o.a and self.b == o.b


class Pertenencia:
    """a ∈ S  /  a ∉ S. Guarda los operandos (para poder explicarlos); `valor()` da el booleano de SymPy."""
    __slots__ = ("a", "S", "negado", "lectura")

    def __init__(self, a, S, negado=False):
        self.a, self.S, self.negado = a, S, bool(negado)
        self.lectura = f"la afirmación de que {lectura_de(a)} {'NO ' if negado else ''}pertenece a {lectura_de(S)}"

    def valor(self):
        r = pertenece(self.a, self.S)
        return sp.Not(r) if self.negado else r

    def __repr__(self):
        return f"Pertenencia({self.a!r}, {self.S!r}, negado={self.negado})"

    def __eq__(self, o):
        return isinstance(o, Pertenencia) and self.a == o.a and self.S == o.S and self.negado == o.negado


_OPTOP = {"int": "el interior", "cl": "la cerradura (clausura)", "Fr": "la frontera", "ext": "el exterior",
          "diam": "el diámetro"}


class OpTop:
    """Operador topológico aplicado a un conjunto: int, cl, Fr, ext, diam."""
    __slots__ = ("nombre", "conjunto", "lectura")

    def __init__(self, nombre, conjunto):
        self.nombre, self.conjunto = nombre, conjunto
        self.lectura = f"{_OPTOP[nombre]} de {lectura_de(conjunto)}"

    def __repr__(self):
        return f"OpTop({self.nombre!r}, {self.conjunto!r})"

    def __eq__(self, o):
        return isinstance(o, OpTop) and self.nombre == o.nombre and self.conjunto == o.conjunto


class ConjuntoImagen:
    """{ expr(n) : n ∈ A, condición }, por ejemplo {2n : n ∈ ℤ}."""
    __slots__ = ("expr", "var", "dominio", "cond", "lectura")

    def __init__(self, expr, var, dominio, cond=None):
        self.expr, self.var, self.dominio, self.cond = expr, var, dominio, cond
        self.lectura = (f"el conjunto de los valores {lectura_de(expr)} cuando {texto_valor(var)} recorre {lectura_de(dominio)}"
                        + (f" y se cumple {lectura_de(cond)}" if cond is not None and cond != sp.true else ""))

    def __repr__(self):
        return f"ConjuntoImagen({sp.srepr(self.expr)}, {self.var!r}, {self.dominio!r}, cond={self.cond!r})"

    def __eq__(self, o):
        return (isinstance(o, ConjuntoImagen) and self.expr == o.expr and self.var == o.var
                and self.dominio == o.dominio and self.cond == o.cond)


# ==============================================================================
# Conjuntos: conversión, operaciones y pertenencia
# ==============================================================================
def es_conjunto(v) -> bool:
    return isinstance(v, (sp.Set, Region, Bola, Espacio, ConjuntoImagen, OpTop))


def _x1():
    return variables_por_defecto(1)[0]


def _set_a_cond(S, x):
    try:
        return S.as_relational(x)
    except Exception:  # noqa: BLE001
        return sp.Contains(x, S)


def a_conjunto(v):
    """Normaliza a sympy.Set | Region | Espacio (los puntos y números sueltos se vuelven conjuntos de un elemento)."""
    if isinstance(v, (sp.Set, Region, Espacio, ConjuntoImagen, OpTop)):
        return v
    if isinstance(v, Bola):
        return v.region()
    if isinstance(v, Punto) and v.ambiguo and not any(c.free_symbols for c in v.c):
        # (a, b) en un contexto de conjuntos es, ante todo, el intervalo abierto de a a b
        return sp.Interval.open(*v.c)
    if isinstance(v, Punto):
        return Region(variables_por_defecto(v.n), sp.And(*[sp.Eq(x, c) for x, c in zip(variables_por_defecto(v.n), v.c)]),
                      f"el conjunto con el único punto {v.txt()}", puntos=(v,))
    if isinstance(v, Lista):
        return sp.FiniteSet(*v.items)
    if isinstance(v, sp.Expr):
        return sp.FiniteSet(v)
    raise ErrorEstructura("Eso no es un conjunto.")


def conjunto_nb(v):
    """Como a_conjunto, pero CONSERVA las bolas (para poder dar explicaciones exactas sobre ellas)."""
    if isinstance(v, (Bola, Region, Espacio, sp.Set, ConjuntoImagen, OpTop)):
        return v
    return a_conjunto(v)


def a_region(v, dim=None) -> Region:
    """Convierte un conjunto a Region (para combinarlo con regiones de ℝⁿ)."""
    v = a_conjunto(v)
    if isinstance(v, Region):
        return v
    if isinstance(v, Espacio):
        if v.dim is None:
            raise ErrorEstructura("No se puede operar con ℝ^n si n no es un número concreto (por ejemplo ℝ²).")
        return Region(variables_por_defecto(v.dim), sp.true, v.lectura)
    if isinstance(v, sp.Set):
        x = _x1()
        reg = Region((x,), _set_a_cond(v, x), lectura_de(v), dominio=v if not isinstance(v, (sp.Interval, sp.FiniteSet, sp.Union)) else None)
        return reg
    raise ErrorEstructura("Ese conjunto no se puede combinar con regiones de ℝⁿ.")


def dimension_de(v):
    v = a_conjunto(v)
    if isinstance(v, (OpTop, ConjuntoImagen)):
        try:
            import calculo_conjuntos as _cc
            v = _cc._canon(v)
        except Exception:  # noqa: BLE001
            pass
    if isinstance(v, Bola):
        return v.n
    if isinstance(v, Region):
        return v.n
    if isinstance(v, Espacio):
        return v.dim
    if v == sp.S.Complexes:
        return 1
    if isinstance(v, sp.Set):
        return 1
    return None


def _unificar(A: Region, B: Region):
    if A.n != B.n:
        raise ErrorEstructura(f"No se pueden combinar un conjunto de ℝ^{A.n} con uno de ℝ^{B.n}: viven en espacios distintos.")
    return A, B.renombrar(A.vars)


def operar_conjuntos(op, A, B):
    """op ∈ {'union', 'inter', 'dif'}."""
    A, B = a_conjunto(A), a_conjunto(B)
    pal = {"union": "la unión de", "inter": "la intersección de", "dif": "la diferencia entre"}[op]
    if isinstance(A, sp.Set) and isinstance(B, sp.Set):
        return {"union": sp.Union, "inter": sp.Intersection, "dif": sp.Complement}[op](A, B)
    RA, RB = a_region(A), a_region(B)
    RA, RB = _unificar(RA, RB)
    cond = {"union": sp.Or(RA.cond, RB.cond), "inter": sp.And(RA.cond, RB.cond), "dif": sp.And(RA.cond, sp.Not(RB.cond))}[op]
    conj = " y " if op != "dif" else " y "
    return Region(RA.vars, cond, f"{pal} {lectura_de(A)}{conj}{lectura_de(B)}")


def complemento(A):
    A = a_conjunto(A)
    if isinstance(A, sp.Set):
        return sp.Complement(sp.S.Reals, A)
    if isinstance(A, Espacio):
        return sp.S.EmptySet
    R = a_region(A)
    return Region(R.vars, sp.Not(R.cond), f"el complemento de {lectura_de(A)} (todo lo que no está en él)")


def producto_cartesiano(A, B):
    """A × B para conjuntos (rectángulos, cajas…)."""
    RA, RB = a_region(A), a_region(B)
    n = RA.n + RB.n
    nuevas = variables_por_defecto(n)
    ca = RA.cond.subs(dict(zip(RA.vars, nuevas[:RA.n])), simultaneous=True)
    cb = RB.cond.subs(dict(zip(RB.vars, nuevas[RA.n:])), simultaneous=True)
    return Region(nuevas, sp.And(ca, cb), f"el producto cartesiano {lectura_de(A)} × {lectura_de(B)}")


def pertenece(a, S):
    """a ∈ S como booleano de SymPy (True/False si es decidible; condición o Contains si no)."""
    if isinstance(S, (OpTop, ConjuntoImagen)):
        try:
            import calculo_conjuntos as _cc
            S = _cc._canon(S)
        except Exception as exc:  # noqa: BLE001
            raise ErrorEstructura("Para probar pertenencia a este conjunto, primero evalúalo.") from exc
    S = a_conjunto(S)
    if isinstance(a, Vector):
        a = Punto(a.c)
    if isinstance(S, Espacio):
        pa = a if isinstance(a, Punto) else Punto((a,)) if isinstance(a, sp.Expr) else None
        if pa is None:
            raise ErrorEstructura("Eso no es un punto.")
        if S.dim is None:
            raise ErrorEstructura("Para probar pertenencia a ℝ^n, n debe ser un número concreto.")
        if any(c.has(sp.I) for c in pa.c):
            return sp.false
        return sp.true if pa.n == S.dim else sp.false
    if isinstance(S, Region):
        pa = a if isinstance(a, Punto) else Punto((a,)) if isinstance(a, sp.Expr) else None
        if pa is None:
            raise ErrorEstructura("Eso no es un punto.")
        if pa.n != S.n:
            raise ErrorEstructura(f"El punto tiene {pa.n} coordenada(s) pero el conjunto vive en ℝ^{S.n}.")
        if S.puntos is not None:
            return sp.Or(*[sp.And(*[sp.Eq(x, y) for x, y in zip(pa.c, q.c)]) for q in S.puntos])
        res = S.cond.subs(dict(zip(S.vars, pa.c)), simultaneous=True)
        return sp.simplify(res) if res.free_symbols == set() else res
    # sympy Set (ℝ¹ o ℂ)
    if isinstance(a, Punto):
        if a.n != 1:
            raise ErrorEstructura(f"El punto tiene {a.n} coordenadas pero el conjunto es un subconjunto numérico de 1 entrada.")
        a = a.c[0]
    if not isinstance(a, sp.Expr):
        raise ErrorEstructura("Eso no es un número ni un punto.")
    if a.free_symbols:
        return sp.Contains(a, S)
    r = S.contains(a)
    return r if r in (sp.true, sp.false) else sp.Contains(a, S)
