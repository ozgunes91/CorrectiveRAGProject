# CorrectiveRAGProject — Kanıt Odaklı RAG + Guardrails (LangGraph)
![LangGraph workflow diyagramı](./graph.png)

Soru yönlendirme (routing), local vektör store’dan kanıt çekme (retrieval), gerektiğinde web aramasıyla destekleme ve **grader** kontrolleri (relevance + grounding + answer-quality) ile halüsinasyonu azaltmayı hedefleyen bir **Corrective RAG** pipeline’ı.

**Ana prensip:** cevap **kanıtla desteklenemiyorsa** sistem **arama / yeniden deneme / reddetme** yoluna gitmeli.

---

## Workflow ne yapıyor?

Bir soru geldiğinde LangGraph state machine şu akışı izler:

1. **Route**: Soru “VectorStore/RAG mı, Web Search mü?” → LLM router karar verir.
2. **Retrieve**: Local Chroma vektör veritabanından doküman çekilir.
3. **Doc grading**: Gelen dokümanlar “soruyla alakalı mı?” diye puanlanır.
4. Kanıt zayıfsa: **Web Search (Tavily)** yapılır, sonuçlar evidence listesine `Document` olarak eklenir.
5. **Generate**: Mevcut kanıtlara dayanarak cevap üretilir.
6. **Generation grading**
   - Cevap **dokümanlara dayanıyor mu** (grounded)?
   - Cevap **soruyu karşılıyor mu**?

Konsolda adım adım logları görürsün (örn. `---ROUTE QUESTION---`, `---RETRIEVE---`, `---WEB SEARCH---`, `---CHECK HALLUCINATIONS---`).

---

## Repo yapısı

> Repo listesinde görünen mevcut yapıya göre.

- `main.py`  
  Demo giriş noktası (env yükler + `app.invoke({"question": ...})` çağırır).

- `ingestion.py`  
  Ingestion + vectorstore kurulumunu tanımlar ve graph’ın kullandığı `retriever` nesnesini sağlar.  
  Chroma local persist dizini: `./.chroma/` (gitignored).

- `graph/graph.py`  
  LangGraph uygulamasını kurar ve compile eder.  
  ⚠️ Not: Mevcut implementasyonda graph ayrıca PNG export eder:
  `app.get_graph().draw_mermaid_png(output_file_path="graph.png")`

- `graph/state.py`  
  Graph state şeması.

- `graph/node_constants.py`  
  Node isim sabitleri (`RETRIEVE`, `GRADE_DOCUMENTS`, `WEBSEARCH`, `GENERATE`, …).

- `graph/nodes/`  
  Node fonksiyonları (`retrieve`, `grade_documents`, `web_search`, `generate`).

- `graph/chains/`  
  Prompt/LLM chain’leri ve grader’lar (router, relevance grader, hallucination/grounding grader, answer grader).

- `graph.png`  
  Graph diyagramı (graph builder tarafından üretilir).

---

## Gereksinimler

- Python **3.11+**
- Ortam değişkenleri:
  - `OPENAI_API_KEY` (LLM + embeddings)
  - `TAVILY_API_KEY` (web arama)
  - `USER_AGENT` (opsiyonel ama önerilir; HTTP warning’lerini susturur)
- Opsiyonel (observability / LangSmith):
  - `LANGCHAIN_TRACING_V2`
  - `LANGCHAIN_PROJECT`
  - `LANGCHAIN_API_KEY`

---

## Hızlı kurulum

### 1) Virtual env

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Bağımlılıklar

`requirements.txt` varsa:

```bash
pip install -r requirements.txt
```

Yoksa (mevcut import’larla uyumlu minimal liste):

```bash
pip install -U   python-dotenv   langgraph   langchain-openai   langchain-chroma   langchain-tavily   langchain-community   langchain-text-splitters   chromadb
```

### 3) `.env` ayarla (commit etme)

Repo root’a `.env` oluştur:

```env
OPENAI_API_KEY=sk-xxxxxxxx
TAVILY_API_KEY=tvly-xxxxxxxx
USER_AGENT=ozgunes-corrective-rag/1.0

# Opsiyonel: LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=CorrectiveRAGProject
LANGCHAIN_API_KEY=lsv2_xxxxx
```

`.env.example` şablon olarak var.

### 4) Local Chroma’yı oluştur / güncelle (gerekirse)

`ingestion.py` içinde ingestion pipeline tanımlı (URL/loader → chunk → embeddings → Chroma persist `./.chroma/`).

Senin mevcut implementasyona bağlı olarak vectorstore:
- `ingestion.py` içinde bir `__main__` bloğu varsa `python ingestion.py` ile, veya
- `retriever` initialize edilirken import sırasında

oluşuyor olabilir.

### 5) Çalıştır

```bash
python main.py
```

---

## Kanıt kaynakları

Bu projede iki evidence yolu var:

1. **Curated corpus (Chroma)**  
   `ingestion.py`’de indekslediğin kaynaklar.

2. **Live web fallback (Tavily)**  
   Kanıt zayıfsa devreye girer. Tavily sonuçları `langchain_core.documents.Document`’a çevrilip evidence listesine eklenir.

---

## Sık görülen uyarılar

### Structured output uyarısı (`json_schema` → `function_calling`)
Bazı modeller (özellikle `gpt-3.5-turbo`) `json_schema` Structured Outputs desteklemez.
LangChain otomatik olarak `function_calling`’e düşer. İstersen grader kurarken `method="function_calling"` açıkça set edebilirsin.

### Deprecation uyarıları (Chroma / Tavily)
Split paketleri kullanmak önerilir (senin güncel kod zaten buna geçti):

```python
from langchain_chroma import Chroma
from langchain_tavily import TavilySearch
```

### `USER_AGENT environment variable not set`
`.env` içine `USER_AGENT` koyarak susturabilirsin.

---

## Bilinen implementasyon “gotcha” (düzeltmen önerilir)

Grader’lar `binary_score` olarak `"yes"` / `"no"` gibi string döndürüyorsa şu şekilde kontrol et:

```python
if score.binary_score == "yes":
    ...
```

Çünkü Python’da **boş olmayan her string** ( `"no"` dahil ) truthy sayılır.

---

## Ürünleştirme için net sonraki adımlar

- `streamlit_app.py` ekle:
  - chat
  - route rozeti (RAG vs Web)
  - evidence panel (source + snippet)
  - grounded / not grounded göstergesi
- Output şemasını standardize et:
  `answer`, `route`, `web_search_used`, `grounded`, `answers_question`, `sources[]`
- `eval/` klasörü:
  küçük test set + grounding/answer pass rate raporu
- Lisans ekle
