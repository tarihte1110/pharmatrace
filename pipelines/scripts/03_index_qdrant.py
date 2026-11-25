import json
import uuid
from pathlib import Path
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent
CHUNKS_PATH = BASE_DIR / "data" / "processed" / "all_chunks.json"

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "pharmatrace_prospectus"
DENSE_MODEL_NAME = "intfloat/multilingual-e5-large"
SPARSE_MODEL_NAME = "Qdrant/bm25"
BATCH_SIZE = 32


def ensure_collection(client: QdrantClient, dense_dim: int) -> None:
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={
                "dense": models.VectorParams(
                    size=dense_dim,
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )
            },
        )
        for field_name in ["ilac_adi", "etken_maddeler", "dokuman_tipi", "kategori"]:
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field_name,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        console.print(f"[green]Yeni Qdrant koleksiyonu oluşturuldu:[/green] {COLLECTION_NAME}")
    else:
        info = client.get_collection(COLLECTION_NAME)
        console.print(
            f"[cyan]Mevcut '{COLLECTION_NAME}' koleksiyonu bulundu (Kayıtlı nokta: {info.points_count}). "
            "Kaldığı yerden devam ediliyor...[/cyan]"
        )


def get_existing_ids(client: QdrantClient) -> set[str]:
    existing: set[str] = set()
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=500,
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )
        for rec in records:
            existing.add(str(rec.id))
        if offset is None:
            break
    return existing


def run_indexing() -> None:
    if not CHUNKS_PATH.exists():
        console.print("[red]Hata: all_chunks.json bulunamadı! Önce 02_parse_prospectus.py çalıştırın.[/red]")
        return

    chunks: list[dict] = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    console.rule(f"[bold cyan]PharmaTrace - {len(chunks)} Parçanın Qdrant Hybrid İndekslemesi[/bold cyan]")

    console.print(f"[cyan]Dense Embedding modeli yükleniyor:[/cyan] {DENSE_MODEL_NAME}")
    dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME, threads=6)

    console.print(f"[cyan]Sparse (BM25) modeli yükleniyor:[/cyan] {SPARSE_MODEL_NAME}")
    sparse_model = SparseTextEmbedding(model_name=SPARSE_MODEL_NAME, threads=4)

    sample_vec = next(dense_model.embed(["passage: test"]))
    dense_dim = len(sample_vec)

    client = QdrantClient(url=QDRANT_URL, timeout=60)
    ensure_collection(client, dense_dim)

    existing_ids = get_existing_ids(client)
    pending_chunks = [
        item
        for item in chunks
        if str(uuid.uuid5(uuid.NAMESPACE_DNS, item["chunk_id"])) not in existing_ids
    ]

    if not pending_chunks:
        console.print("[bold green]Tüm parçalar zaten Qdrant'a indekslenmiş durumda![/bold green]")
        return

    console.print(f"[yellow]İşlenecek kalan parça sayısı:[/yellow] {len(pending_chunks)} / {len(chunks)}")

    total = len(pending_chunks)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Vektörleştiriliyor ve Qdrant'a yazılıyor...", total=total)

        for start_idx in range(0, total, BATCH_SIZE):
            batch = pending_chunks[start_idx : start_idx + BATCH_SIZE]
            dense_texts = [f"passage: {item['text']}" for item in batch]
            sparse_texts = [item["text"] for item in batch]

            dense_embeddings = list(dense_model.embed(dense_texts))
            sparse_embeddings = list(sparse_model.embed(sparse_texts))

            points: list[models.PointStruct] = []
            for item, dense_vec, sparse_vec in zip(batch, dense_embeddings, sparse_embeddings):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item["chunk_id"]))
                payload = {
                    "chunk_id": item["chunk_id"],
                    "text": item["text"],
                    "raw_text": item["raw_text"],
                    **item["metadata"],
                }
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector={
                            "dense": dense_vec.tolist(),
                            "sparse": models.SparseVector(
                                indices=sparse_vec.indices.tolist(),
                                values=sparse_vec.values.tolist(),
                            ),
                        },
                        payload=payload,
                    )
                )

            client.upsert(collection_name=COLLECTION_NAME, points=points)
            progress.update(task, advance=len(batch))

    collection_info = client.get_collection(COLLECTION_NAME)
    console.rule(
        f"[bold green]İndeksleme Tamamlandı! Qdrant Toplam Nokta Sayısı: {collection_info.points_count}[/bold green]"
    )


if __name__ == "__main__":
    run_indexing()