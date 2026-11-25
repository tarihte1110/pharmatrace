from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "pharmatrace_prospectus"
DENSE_MODEL_NAME = "intfloat/multilingual-e5-large"
SPARSE_MODEL_NAME = "Qdrant/bm25"


def check_collection_health(client: QdrantClient) -> None:
    info = client.get_collection(COLLECTION_NAME)
    table = Table(title="Qdrant Koleksiyon Sağlık Raporu", show_header=True)
    table.add_column("Metrik", style="cyan")
    table.add_column("Değer", style="green")

    table.add_row("Koleksiyon Adı", COLLECTION_NAME)
    table.add_row("Durum", str(info.status))
    table.add_row("Toplam Nokta (Chunk)", str(info.points_count))
    table.add_row("Payload İndeksleri", ", ".join(info.payload_schema.keys()))
    console.print(table)


def hybrid_search(
    client: QdrantClient,
    dense_model: TextEmbedding,
    sparse_model: SparseTextEmbedding,
    query: str,
    ilac_filtresi: str | None = None,
    limit: int = 3,
) -> None:
    console.rule(f"[bold yellow]Sorgu:[/bold yellow] {query}" + (f" [Filtre: {ilac_filtresi}]" if ilac_filtresi else ""))

    # E5 mimarisi sorgular için 'query: ' ön eki bekler
    dense_vec = next(dense_model.embed([f"query: {query}"])).tolist()
    sparse_raw = next(sparse_model.embed([query]))
    sparse_vec = models.SparseVector(
        indices=sparse_raw.indices.tolist(),
        values=sparse_raw.values.tolist(),
    )

    query_filter = None
    if ilac_filtresi:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="ilac_adi",
                    match=models.MatchValue(value=ilac_filtresi),
                )
            ]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(query=dense_vec, using="dense", limit=15, filter=query_filter),
            models.Prefetch(query=sparse_vec, using="sparse", limit=15, filter=query_filter),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit,
        with_payload=True,
    ).points

    if not results:
        console.print("[red]Sonuç bulunamadı! Filtre adını veya veri içeriğini kontrol edin.[/red]")
        return

    for idx, point in enumerate(results, start=1):
        payload = point.payload or {}
        header = (
            f"#{idx} | RRF Skor: {point.score:.4f} | İlaç: {payload.get('ilac_adi', 'Bilinmiyor')} "
            f"| Etken: {payload.get('etken_maddeler', '-')} | Tip: {payload.get('dokuman_tipi', '-')}"
        )
        snippet = payload.get("raw_text") or payload.get("text", "")
        console.print(Panel(snippet[:650] + ("..." if len(snippet) > 650 else ""), title=header, border_style="cyan"))


def main() -> None:
    client = QdrantClient(url=QDRANT_URL, timeout=30)
    check_collection_health(client)

    console.print("[cyan]Embedding modelleri yükleniyor...[/cyan]")
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME, threads=6)
    sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME, threads=4)

    # 1. Test: Doğrudan etken madde / klinik yan etki sorgusu
    hybrid_search(
        client,
        dense_model,
        sparse_model,
        query="Parasetamol yüksek dozda karaciğer toksisitesi ve antidot tedavisi nedir?",
    )

    # 2. Test: Gebelik ve emzirme döneminde kullanım (anlamsal + anahtar kelime)
    hybrid_search(
        client,
        dense_model,
        sparse_model,
        query="Gebeliğin üçüncü trimesterinde kullanımı kontrendike olan ağrı kesiciler hangileridir?",
    )

    # 3. Test: Spesifik dozaj ve uygulama şekli
    hybrid_search(
        client,
        dense_model,
        sparse_model,
        query="Böbrek yetmezliği olan hastalarda doz ayarlaması nasıl yapılır?",
    )


if __name__ == "__main__":
    main()