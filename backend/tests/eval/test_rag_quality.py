from tests.eval.run_rag_eval import evaluate_all


def test_pharmatrace_rag_quality():
    results = evaluate_all()
    failures = [r for r in results if not r["passed"]]
    assert not failures, f"Başarısız RAG eval senaryoları: {failures}"