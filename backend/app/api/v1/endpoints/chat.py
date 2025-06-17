from fastapi import APIRouter, Body
from ..schemas import ChatRequest, ChatResponse, Citation
from app.services.bm25 import bm25_engine      # later: transformer_engine, LLM

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, summary="Ask the legal assistant")
def chat(req: ChatRequest = Body(...)):
    """
    Dummy implementation:
    1. Retrieve top-1 snippet with BM25 (just to show a citation)
    2. Return a placeholder answer.
    """
    hits = bm25_engine.search(req.question, top_k=1, space=req.space)
    citation_objs = []
    if hits:
        h = hits[0]
        citation_objs.append(
            Citation(doc_id=h["id"], snippet=h["snippet"])
        )

    # TODO ▸ replace with real prompt + LLM call
    # dummy_answer = (
    #     "La Sala Penal exige que el escrito de casación reúna cinco condiciones acumulativas:\n\n"
    #     "1. Acto recurrible – Debe impugnar una sentencia definitiva o una resolución que ponga fin al procedimiento (art. 477 CPP).\n"
    #     "2. Legitimación activa – Solo puede interponerlo quien sufrió gravamen directo (arts. 449 y 450 CPP).\n"
    #     "3. Plazo y vía – Presentarse por escrito ante la Sala Penal dentro de los diez (10) días de la notificación, adjuntando copias de los fallos impugnados (arts. 468 y 480 CPP).\n"
    #     "4. Motivación concreta – Expresar separadamente cada agravio, indicando la norma violada y la solución pretendida; el tribunal queda limitado a esos agravios (art. 468 CPP).\n"
    #     "5. Motivos tasados – Invocar uno de los motivos del art. 478 CPP (p. ej., sentencia manifiestamente infundada, contradicción con fallo anterior, inobservancia constitucional).\n\n"
    #     "Si falta cualquiera de estos requisitos, la Corte declara inadmisible el recurso, como ocurrió en el caso citado."
    # )

    if req.question.startswith("Qué dice el artículo 12"):
        dummy_answer = (
            "Según el artículo 12 del documento, los contribuyentes en San Lorenzo "
            "que tengan más de tres árboles frutales en su terreno están exentos "
            "del impuesto inmobiliario durante 2025."
        )
    elif req.question.startswith("Redactame la demanda"):
        dummy_answer = (
            """JUZGADO DE PAZ DE SAN LORENZO
Proceso ejecutivo de menor cuantía

JUAN PÉREZ s/ EJECUCIÓN Exp. 22-345/2024

AL JUZGADO DIGO:

1. Comparece AQUASUR S.A., RUC 80012345-7, por derecho representada
   por la Abg. María López, Matr. 45.678, constituyendo domicilio en
   … (Art. 41 CPC).

2. Objeto: promover DEMANDA EJECUTIVA contra el Sr. Juan Pérez
   (CI 2.345.678) a fin de que pague:
   a) Capital: Gs. 380.000
   b) Intereses moratorios al 2 % mensual desde el 06/04/2024
   c) Costas.

3. Hechos … *[resume los puntos 1-4 del expediente]* …

4. Derecho … *art. 421 y ss. CPC; art. 7 Ley 1614/00; art. 1129 CC* …

5. Prueba:
   1) Factura original N.º 0001-0004567  
   2) Carta documento de intimación (15/04/2024)  
   3) Certificación de deuda de fecha 30/04/2024  

PETITORIO  
I. Tenga por promovida demanda ejecutiva …  
II. Se libre mandamiento de embargo …  
III. Se condene en costas al demandado.  

Proveer de conformidad,  
SERÁ JUSTICIA.

[Firma y sello]

Adjunto: Instrumental detallada supra.""")
    else:
        dummy_answer = "Lo siento, no encontré información sobre eso en la base de conocimiento."

    return ChatResponse(answer=dummy_answer, citations=citation_objs)
