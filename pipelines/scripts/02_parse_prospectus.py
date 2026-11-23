"""Parse prospectus documents into structured sections and chunks."""
import json
import re
from pathlib import Path
import fitz  # PyMuPDF
from rich.console import Console
from rich.table import Table

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = BASE_DIR / "data" / "manifest.json"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MAX_CHUNK_CHARS = 1800  # Uzun klinik bölümlerin (örn. 4.5 veya 4.8) bölünme eşiği
OVERLAP_CHARS = 220     # Alt parçalar arası bağlam koruma örtüşmesi


def clean_drug_name(raw_name: str) -> str:
    """Tablo kalıntılarını temizleyerek saf ilaç adını döndürür."""
    first_col = raw_name.split("\t")[0].strip()
    return re.sub(r"\s+", " ", first_col)


def extract_active_ingredients(full_text: str, doc_type: str, fallback: str) -> list[str]:
    """
    KT belgelerinde 'Etkin madde(ler):', KÜB belgelerinde ise '2. KALİTATİF VE KANTİTATİF BİLEŞİM'
    bölümünden gerçek etken maddeleri ayıklar.
    """
    head_text = full_text[:3000]
    if doc_type == "KT":
        pattern = r"Etkin madde(?:ler)?\s*:\s*(.+?)(?=\n\s*(?:Yardımcı madde|Bu ilacı|Kullanma Talimatı|1\.))"
    else:
        pattern = r"Etkin madde(?:ler)?\s*:\s*(.+?)(?=\n\s*(?:Yardımcı madde|3\.|FARMASÖTİK))"

    match = re.search(pattern, head_text, re.IGNORECASE | re.DOTALL)
    if not match:
        return [item.strip().title() for item in fallback.split("+")]

    raw_block = re.sub(r"\s+", " ", match.group(1)).strip()
    # Dozaj birimlerini ve standart dolgu kelimelerini temizle
    cleaned = re.sub(r"\b\d+(?:[.,]\d+)?\s*(?:mg|g|ml|mcg|iu|%)\b", "", raw_block, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\b(?:her\s+bir|film\s+kaplı|enterik\s+kaplı|tablet|saşe|kapsül|içerir|eşdeğer|olarak|miktarında)\b",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    parts = [p.strip(" .,;:-()[]") for p in re.split(r",|\bve\b|\+|/", cleaned) if len(p.strip(" .,;:-()[]")) > 2]
    # Tekrar edenleri sırayı bozmadan temizle
    unique_parts = list(dict.fromkeys(p.title() for p in parts if len(p) < 45))
    return unique_parts if unique_parts else [item.strip().title() for item in fallback.split("+")]


def split_long_section(text: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    """Uzun bölümleri paragraf ve cümle sınırlarını koruyarak örtüşmeli alt parçalara böler."""
    if len(text) <= max_chars:
        return [text]

    sub_chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + max_chars, text_len)
        if end < text_len:
            # Cümle sonu veya satır sonu bularak kelime ortasından kesmeyi önle
            break_pos = max(text.rfind("\n", start + max_chars // 2, end), text.rfind(". ", start + max_chars // 2, end))
            if break_pos != -1:
                end = break_pos + 1

        piece = text[start:end].strip()
        if piece:
            sub_chunks.append(piece)

        if end >= text_len:
            break
        start = max(end - overlap, start + 1)

    return sub_chunks


def get_section_patterns(doc_type: str) -> tuple[re.Pattern, re.Pattern]:
    """Belge tipine (KT veya KÜB) özel ana ve alt başlık Regex kurallarını döndürür."""
    if doc_type == "KUB":
        main_re = re.compile(
            r"(?m)^([1-9]\.\s+(?:BEŞERİ TIBBİ ÜRÜNÜN ADI|KALİTATİF VE KANTİTATİF BİLEŞİM|FARMASÖTİK FORM|KLİNİK ÖZELLİKLER|FARMAKOLOJİK ÖZELLİKLER|FARMASÖTİK ÖZELLİKLER|RUHSAT SAHİBİ|RUHSAT NUMARASI).*)$",
            re.IGNORECASE,
        )
        sub_re = re.compile(
            r"(?m)^((?:4\.[1-9]|5\.[1-3]|6\.[1-6])\.?\s+[A-ZÇĞİÖŞÜa-zçğıöşü\s,/-]+)$",
            re.IGNORECASE,
        )
    else:
        main_re = re.compile(
            r"(?m)^([1-5]\.\s+[A-ZÇĞİÖŞÜ0-9\s,/-]+(?:nedir|dikkat edilmesi gerekenler|nasıl kullanılır|yan etkiler|saklanması).*)$",
            re.IGNORECASE,
        )
        sub_re = re.compile(
            r"(?m)^((?:.*?(?:kullanmayınız|dikkatli kullanınız|yiyecek ve içecek|hamilelik|emzirme|araç ve makine|diğer ilaçlar ile birlikte kullanımı|uygun kullanım ve doz|uygulama yolu|değişik yaş grupları|kullanmanız gerekenden fazla|kullanmayı unutursanız))[:\?]?)$",
            re.IGNORECASE,
        )
    return main_re, sub_re


def parse_single_pdf(pdf_path: Path, entry: dict) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages_text: list[tuple[int, str]] = []

    for page_idx, page in enumerate(doc, start=1):
        text = page.get_text("text")
        text = re.sub(r"(?m)^\s*\d+\s*/\s*\d+\s*$", "", text)
        pages_text.append((page_idx, text))

    full_doc_text = "\n".join(t for _, t in pages_text)
    doc_type = entry.get("doc_type", "KT").upper()
    clean_name = clean_drug_name(entry["ilac_adi"])
    kategori = entry.get("kategori", "Genel")
    active_ingredients = extract_active_ingredients(full_doc_text, doc_type, entry["etken_madde"])

    main_section_re, sub_section_re = get_section_patterns(doc_type)

    chunks: list[dict] = []
    current_main = "1. Genel Ürün Bilgisi"
    current_sub = "Özet"
    buffer: list[str] = []
    start_page = 1

    def flush_buffer(end_page: int) -> None:
        raw_content = "\n".join(buffer).strip()
        if len(raw_content) < 60:
            return

        sub_pieces = split_long_section(raw_content)
        total_parts = len(sub_pieces)

        for part_idx, piece in enumerate(sub_pieces, start=1):
            part_suffix = f" (Bölüm {part_idx}/{total_parts})" if total_parts > 1 else ""
            header = (
                f"[Belge: {doc_type} | İlaç: {clean_name} | Etken Maddeler: {', '.join(active_ingredients)} | "
                f"Kategori: {kategori} | Bölüm: {current_main} > {current_sub}{part_suffix} | Sayfa: {start_page}-{end_page}]"
            )
            chunks.append({
                "chunk_id": f"{pdf_path.stem}_c{len(chunks) + 1:03d}",
                "text": f"{header}\n{piece}",
                "raw_text": piece,
                "metadata": {
                    "ilac_adi": clean_name,
                    "etken_maddeler": active_ingredients,
                    "kategori": kategori,
                    "dokuman_tipi": doc_type,
                    "ana_bolum": current_main,
                    "alt_baslik": current_sub,
                    "sayfa_baslangic": start_page,
                    "sayfa_bitis": end_page,
                    "kaynak_url": entry["source_url"],
                    "sha256": entry["sha256"],
                },
            })

    for page_num, text in pages_text:
        for line in text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            if main_section_re.match(stripped) and len(stripped) < 120:
                flush_buffer(page_num)
                buffer = []
                current_main = stripped
                current_sub = "Genel"
                start_page = page_num
            elif sub_section_re.match(stripped) and len(stripped) < 120:
                flush_buffer(page_num)
                buffer = []
                current_sub = stripped
                start_page = page_num
            else:
                buffer.append(stripped)

    flush_buffer(pages_text[-1][0] if pages_text else 1)
    return chunks


def run_parser() -> None:
    if not MANIFEST_PATH.exists():
        console.print("[red]Hata: manifest.json bulunamadı. Önce 01_fetch_titck.py çalıştırın.[/red]")
        return

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    all_chunks: list[dict] = []
    drug_catalog: dict[str, dict] = {}

    kt_docs = 0
    kub_docs = 0

    for key, entry in manifest.items():
        if key == "files" or not isinstance(entry, dict):
            continue

        pdf_path = BASE_DIR / entry["file_path"]
        if not pdf_path.exists():
            continue

        doc_chunks = parse_single_pdf(pdf_path, entry)
        if not doc_chunks:
            continue

        all_chunks.extend(doc_chunks)

        if entry.get("doc_type") == "KUB":
            kub_docs += 1
        else:
            kt_docs += 1

        # Frontend ilaç arama kutusu ve otomatik tamamlama (autocomplete) için benzersiz katalog üret
        clean_name = doc_chunks[0]["metadata"]["ilac_adi"]
        if clean_name not in drug_catalog:
            drug_catalog[clean_name] = {
                "ilac_adi": clean_name,
                "etken_maddeler": doc_chunks[0]["metadata"]["etken_maddeler"],
                "kategori": doc_chunks[0]["metadata"]["kategori"],
                "belgeler": [],
            }
        if entry["doc_type"] not in drug_catalog[clean_name]["belgeler"]:
            drug_catalog[clean_name]["belgeler"].append(entry["doc_type"])

    master_chunks_out = PROCESSED_DIR / "all_chunks.json"
    master_chunks_out.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    catalog_out = PROCESSED_DIR / "drug_catalog.json"
    catalog_out.write_text(
        json.dumps(sorted(drug_catalog.values(), key=lambda x: x["ilac_adi"]), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = Table(title="PharmaTrace - Veri Ayrıştırma (Parsing) Özeti")
    summary.add_column("Metrik", style="cyan")
    summary.add_column("Değer", justify="right", style="bold green")
    summary.add_row("İşlenen Kullanma Talimatı (KT)", str(kt_docs))
    summary.add_row("İşlenen Kısa Ürün Bilgisi (KÜB)", str(kub_docs))
    summary.add_row("Benzersiz İlaç Sayısı (Katalog)", str(len(drug_catalog)))
    summary.add_row("Üretilen Toplam Vektör Parçası (Chunk)", str(len(all_chunks)))

    console.print(summary)
    console.print(f"\n[green]Master Chunks ->[/green] {master_chunks_out}")
    console.print(f"[green]İlaç Kataloğu ->[/green] {catalog_out}")


if __name__ == "__main__":
    run_parser()