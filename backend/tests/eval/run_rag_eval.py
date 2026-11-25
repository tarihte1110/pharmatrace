"""Run RAGAS evaluation against the verified golden dataset."""
import json
import re
from pathlib import Path
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from rich.console import Console
from rich.table import Table
from app.core.config import settings
from app.rag.graph import pharma_rag_graph

console = Console()
DATASET_PATH = Path(__file__).parent / "golden_dataset.json"

JUDGE_SYSTEM_PROMPT = """You are an automated clinical RAG evaluator.
Evaluate ONLY the clinical/medical statements in the `answer` against the provided `contexts`.
Ignore the standard "Kaynaklar" reference section and the final clinical disclaimer note.
Allow minor paraphrasing or formatting in Turkish as long as the medical facts match the context.
Respond ONLY with a valid JSON object:
{"faithful": true/false, "unsupported_claims": ["..."], "score": 0.0 to 1.0}"""

judge_llm = ChatOpenAI(
    model=settings.DEEPSEEK_MODEL,
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=settings.DEEPSEEK_BASE_URL,
    temperature=0.0,
    max_tokens=200,
)


def check_citation_integrity(answer: str, contexts: list[dict]) -> tuple[bool, str]:
    """Yanıttaki [Kaynak X] etiketlerinin getirilen kaynaklarla eşleşmesini doğrular."""
    cited_ids = {int(m) for m in re.findall(r"\[Kaynak\s+(\d+)\]", answer)}
    valid_ids = {int(c["source_id"]) for c in contexts}

    if not cited_ids:
        return False, "Hiç [Kaynak X] atfı bulunamadı"

    hallucinated_ids = cited_ids - valid_ids
    if hallucinated_ids:
        return False, f"Var olmayan kaynak ID atfı: {sorted(hallucinated_ids)}"

    if "Kaynaklar" not in answer:
        return False, "Alt 'Kaynaklar' listesi eksik"

    return True, f"Geçerli atıflar: {sorted(cited_ids)}"


def judge_faithfulness(question: str, answer: str, contexts: list[dict]) -> dict:
    """Yanıtın yalnızca verilen prospektüs parçalarına sadık kalıp kalmadığını denetler."""
    ctx_blob = "\n\n".join(
        f"[Kaynak {c['source_id']} - {c['ilac_adi']}]: {c['text']}" for c in contexts
    )
    prompt = f"QUESTION: {question}\n\nCONTEXTS:\n{ctx_blob}\n\nANSWER:\n{answer}"
    resp = judge_llm.invoke(
        [SystemMessage(content=JUDGE_SYSTEM_PROMPT), HumanMessage(content=prompt)]
    )
    raw = resp.content.strip().strip("`").replace("json", "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"faithful": False, "unsupported_claims": ["Judge JSON parse error"], "score": 0.0}


def evaluate_all() -> list[dict]:
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    results = []

    for case in cases:
        state = pharma_rag_graph.invoke(
            {
                "question": case["question"],
                "ilac_filtresi": None,
                "etken_madde_filtresi": None,
                "is_pharmaceutical": True,
                "contexts": [],
                "answer": "",
            }
        )

        answer = state["answer"]
        contexts = state.get("contexts", [])
        is_pharma = state["is_pharmaceutical"]

        # 1. Guardrail & Kategori kontrolü
        guardrail_ok = is_pharma == case["expected_is_pharmaceutical"]
        keyword_ok = all(kw.lower() in answer.lower() for kw in case["expected_keywords"])

        # 2. Klinik sorularda atıf + halüsinasyon kontrolü
        if case["category"] == "in_scope_clinical":
            cite_ok, cite_note = check_citation_integrity(answer, contexts)
            faith_eval = judge_faithfulness(case["question"], answer, contexts)
            faith_score = float(faith_eval.get("score", 0.0))
            faith_ok = bool(faith_eval.get("faithful", False)) or faith_score >= 0.85
        else:
            cite_ok, cite_note = True, "N/A (Kapsam dışı / Red)"
            faith_ok, faith_score = True, 1.0

        passed = guardrail_ok and keyword_ok and cite_ok and faith_ok
        results.append(
            {
                "id": case["id"],
                "category": case["category"],
                "passed": passed,
                "guardrail_ok": guardrail_ok,
                "cite_ok": cite_ok,
                "cite_note": cite_note,
                "faith_score": faith_score,
            }
        )

    return results


def print_report(results: list[dict]) -> None:
    table = Table(title="PharmaTrace RAG Klinik Değerlendirme Raporu")
    table.add_column("Test ID", style="cyan")
    table.add_column("Kategori")
    table.add_column("Guardrail")
    table.add_column("Kaynak Doğruluğu")
    table.add_column("Sadakat Skoru")
    table.add_column("Durum")

    for r in results:
        table.add_row(
            r["id"],
            r["category"],
            "PASS" if r["guardrail_ok"] else "FAIL",
            f"{'PASS' if r['cite_ok'] else 'FAIL'} ({r['cite_note']})",
            f"{r['faith_score']:.2f}",
            "[green]PASS[/green]" if r["passed"] else "[red]FAIL[/red]",
        )

    console.print(table)
    pass_rate = sum(1 for r in results if r["passed"]) / len(results) * 100
    console.print(f"\n[bold]Genel Başarı Oranı:[/bold] %{pass_rate:.1f}")


if __name__ == "__main__":
    report = evaluate_all()
    print_report(report)
