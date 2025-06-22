from fastapi import APIRouter, Body
from ..schemas import ChatRequest, ChatResponse, Citation
from app.services.bm25 import bm25_engine      # later: transformer_engine, LLM
from time import sleep  # Simulate processing time

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, summary="Ask the legal assistant")
def chat(req: ChatRequest = Body(...)):
    """
    Dummy implementation:
    1. Retrieve top-1 snippet with BM25 (just to show a citation)
    2. Return a placeholder answer.
    """
    sleep(1)  # Simulate processing time
    hits = bm25_engine.search(req.question, top_k=1, space=req.space)
    citation_objs = []
    file_url = None
    if hits:
        h = hits[0]
        citation_objs.append(
            Citation(doc_id=h["id"], snippet=h["snippet"])
        )

    if req.question.startswith("Qué dice el artículo 12"):
        dummy_answer = (
            "Según el artículo 12 del documento, los contribuyentes en San Lorenzo "
            "que tengan más de tres árboles frutales en su terreno están exentos "
            "del impuesto inmobiliario durante 2025."
        )

    elif req.question.startswith("Redáctame la demanda ejecutiva para el caso Juan Pérez s/ Ejecución (Exp. 22-345/2024)"):
        dummy_answer = (
            """### JUZGADO DE PAZ DE SAN LORENZO  
**Proceso ejecutivo de menor cuantía**  
**JUAN PÉREZ s/ EJECUCIÓN — Exp. 22-345/2024**
#### AL JUZGADO DIGO:
1. **Comparece** **AQUASUR S.A.**, RUC 80012345-7, por derecho representada por la Abg. **María López**, Matr. 45.678, constituyendo domicilio en … (art. 41 CPC).
2. **Objeto:** promover **DEMANDA EJECUTIVA** contra el Sr. **Juan Pérez** (CI 2.345.678) a fin de que pague:  
   - **Capital:** Gs. 380 000  
   - **Intereses moratorios:** 2 % mensual desde el **06/04/2024**  
   - **Costas**
3. **Hechos** … *[resume los puntos 1-4 del expediente]* …
4. **Derecho** … *arts. 421 y ss. CPC; art. 7 Ley 1614/00; art. 1129 CC* …
5. **Prueba:**  
   1. Factura original Nº 0001-0004567  
   2. Carta documento de intimación (15/04/2024)  
   3. Certificación de deuda de fecha 30/04/2024  
### PETITORIO  
I. Tenga por **promovida** la demanda ejecutiva …  
II. Se **libre mandamiento de embargo** …  
III. Se **condene en costas** al demandado.  
---
Proveer de conformidad,  
**SERÁ JUSTICIA.**

`[Firma y sello]`

*Adjunto: Instrumental detallada supra.*
""")
        
    elif req.question == "Cuántos casos resolvió Alfredo en 2025":
        citation_objs = [
            Citation(doc_id="casos_por_abogado.xlsx", snippet="Alfredo resolvió 27 casos en 2025.")
        ]
        dummy_answer = "Alfredo resolvió 27 casos en 2025. Ten en cuenta que el año no ha terminado y puede haber más casos pendientes."

    elif req.question.lower().strip().startswith(
        "cuántos casos de hurto hubo por año desde 2011"):
        file_name = "image.png"
        file_url  = f"/downloads/{file_name}"

        dummy_answer = (
            "Aquí tienes el número de casos de hurto registrados entre 2011 y 2023:\n\n"
            "| Año | Casos |\n"
            "|-----|------:|\n"
            "| 2011 | 6 |\n| 2012 | 13 |\n| 2013 | 8 |\n| 2014 | 19 |\n"
            "| 2015 | 14 |\n| 2016 | 12 |\n| 2017 | 5 |\n| 2018 | 15 |\n"
            "| 2019 | 14 |\n| 2020 | 24 |\n| 2021 | 28 |\n| 2022 | 20 |\n| 2023 | 22 |\n\n"
            f"Puedes descargar el diagrama en alta resolución aquí: {file_url}"
        )
        citation_objs = [
            Citation(doc_id="varios", snippet="")
        ]
        sleep(1)  # Simulate processing time for file retrieval
    
    elif req.question.startswith("Crea un resumen del caso con ID: 96748"):

        dummy_answer = (
            """**Identificación**
            
- Órgano / Sala: Corte Suprema de Justicia, Sala Penal
- Expediente: Flora Irene Giménez Cáceres s/ Hurto Agravado. N° 10503/2019
- Fecha de resolución: [AMBIGUO]
- Tipo de proceso: Penal

**Hechos clave**

Flora Irene Giménez Cáceres fue condenada por hurto agravado. El Tribunal Colegiado de Sentencia dictó la Sentencia Definitiva N° 523 el 15 de diciembre de 2021. El Tribunal de Apelación Penal, 3ra Sala, confirmó esta sentencia mediante el Acuerdo y Sentencia N° 29 el 4 de mayo de 2022. El defensor de Giménez interpuso un Recurso Extraordinario de Casación contra ambas resoluciones.

**Pretensiones y agravios**

El defensor de Giménez, Abg. Miguel Said Bobadilla, argumentó que la sentencia de primera instancia y la resolución del Tribunal de Apelación contienen errores procesales y sustanciales. Entre los agravios, se mencionan la falta de descripción precisa de los hechos en el auto de apertura, la incorrecta aplicación del artículo 65 del Código Penal, y la violación de principios constitucionales.

**Cuestiones sometidas**

1. Es admisible el recurso de casación?
2. En su caso, resulta procedente?

**Decisión**

- Admisibilidad: Inadmisible
- Fondo: No se analiza

**Fundamentos esenciales**

La Corte Suprema de Justicia determinó que el recurso de casación es inadmisible debido a que no cumple con los requisitos formales establecidos en el Código Procesal Penal. Los ministros señalaron que el recurso no estaba debidamente fundamentado y que no se habían invocado los motivos de casación de manera clara y específica. Además, se indicó que el recurso de casación no puede ser utilizado como una tercera instancia y que la ley exige una motivación clara y específica para su admisibilidad.

**Resultado y efectos**

La Corte Suprema de Justicia declaró inadmisible el Recurso Extraordinario de Casación interpuesto contra la Sentencia Definitiva N° 523 y el Acuerdo y Sentencia N° 29. Las costas fueron impuestas a la parte vencida, conforme a los artículos 261 y 269 del Código Procesal Penal.

**Citas relevantes**

- Art. 477 del Código Procesal Penal
- Art. 478 del Código Procesal Penal
- Art. 480 del Código Procesal Penal
- Art. 468 del Código Procesal Penal
- Art. 449 del Código Procesal Penal
"""
        )
        citation_objs = [
            Citation(doc_id="96748", snippet="")
        ]

    else:
        dummy_answer = "Lo siento, no encontré información sobre eso en la base de conocimiento."
        citation_objs = []

    return ChatResponse(answer=dummy_answer, citations=citation_objs, file_url=file_url)
