import asyncio
import hashlib
import json
import random
import re
import time
from pathlib import Path
import httpx
from playwright.async_api import async_playwright
from rich.console import Console

console = Console()

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
MANIFEST_PATH = BASE_DIR / "data" / "manifest.json"
INGREDIENTS_PATH = BASE_DIR / "data" / "target_ingredients.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)

TITCK_KUB_KT_URL = "https://www.titck.gov.tr/kubkt"
MAX_BRANDS_PER_INGREDIENT = 4  # 45 etken madde x 4 marka = ~180 benzersiz ilaç

HEADERS = {
    "User-Agent": "PharmaTrace-Research-Bot/1.0 (+https://github.com/tarihte1110/pharmatrace; Educational RAG Project)",
    "Accept": "application/pdf,text/html;q=0.9",
}


def load_json(path: Path, default: dict | list) -> dict | list:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path: Path, data: dict | list) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def slugify(text: str) -> str:
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = text.translate(tr_map).lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def extract_brand_root(drug_title: str) -> str:
    """'PAROL 500 MG TABLET' -> 'PAROL' kök ismini çıkararak aynı markanın tekrarını önler."""
    tokens = drug_title.upper().split()
    return tokens[0] if tokens else drug_title.upper()


def score_drug_row(full_row_text: str, row_title: str, ingredient: str) -> int:
    """
    1. Satırın gerçekten aranan etken maddeyi içerdiğini doğrular.
    2. Yetişkin oral formlara (Tablet / Kapsül) yüksek, pediatrik / harici formlara düşük puan verir.
    """
    upper_row = full_row_text.upper()
    upper_title = row_title.upper()
    upper_ing = ingredient.upper()

    # Tablo henüz güncellenmediyse veya ilgisiz bir satırsa doğrudan ele
    if upper_ing not in upper_row:
        return -100

    score = 10

    preferred = ["TABLET", "KAPSÜL", "KAPSUL", "DRAJE", "SAŞE", "SASE"]
    if any(p in upper_title for p in preferred):
        score += 15

    penalized = [
        "PEDİATRİK", "PEDIATRIK", "ŞURUP", "SURUP", "SÜSPANSİYON", "SUSPANSIYON",
        "AMPUL", "FLAKON", "ENJEKSİYON", "KREM", "JEL", "MERHEM", "DAMLA", "SPREY", "İNJEKSİYON"
    ]
    if any(bad in upper_title for bad in penalized):
        score -= 30

    return score


async def download_pdf(
    client: httpx.AsyncClient,
    pdf_url: str,
    ilac_adi: str,
    etken_madde: str,
    kategori: str,
    doc_type: str,  # "KT" veya "KUB"
    manifest: dict,
) -> bool:
    doc_key = f"{slugify(ilac_adi[:55])}_{doc_type.lower()}"

    if doc_key in manifest and (BASE_DIR / manifest[doc_key]["file_path"]).exists():
        return True

    wait_sec = random.uniform(2.0, 3.5)
    await asyncio.sleep(wait_sec)

    try:
        resp = await client.get(pdf_url, headers=HEADERS, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()

        if "pdf" not in resp.headers.get("Content-Type", "").lower():
            return False

        file_path = RAW_DIR / f"{doc_key}.pdf"
        file_path.write_bytes(resp.content)
        sha256_hash = hashlib.sha256(resp.content).hexdigest()

        manifest[doc_key] = {
            "ilac_adi": ilac_adi,
            "etken_madde": etken_madde,
            "kategori": kategori,
            "doc_type": doc_type,
            "source_url": pdf_url,
            "file_path": str(file_path.relative_to(BASE_DIR)),
            "sha256": sha256_hash,
            "size_kb": round(len(resp.content) / 1024, 1),
            "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        save_json(MANIFEST_PATH, manifest)
        console.print(f"  [green][+ {doc_type}][/green] {ilac_adi} ({manifest[doc_key]['size_kb']} KB)")
        return True

    except Exception as exc:
        console.print(f"  [red][HATA {doc_type}][/red] {ilac_adi}: {exc}")
        return False


async def discover_and_fetch() -> None:
    if not INGREDIENTS_PATH.exists():
        console.print("[red]Hata: pipelines/data/target_ingredients.json bulunamadı![/red]")
        return

    ingredients = load_json(INGREDIENTS_PATH, [])
    manifest = load_json(MANIFEST_PATH, {})
    downloaded_brands: set[str] = {
        extract_brand_root(v["ilac_adi"])
        for k, v in manifest.items()
        if isinstance(v, dict) and "ilac_adi" in v
    }

    console.rule(
        f"[bold cyan]PharmaTrace - {len(ingredients)} Etken Maddeden ~{len(ingredients) * MAX_BRANDS_PER_INGREDIENT} İlaç Keşfi[/bold cyan]"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])
        page = await context.new_page()

        await page.goto(TITCK_KUB_KT_URL, wait_until="networkidle", timeout=45000)

        async with httpx.AsyncClient() as http_client:
            for idx, item in enumerate(ingredients, start=1):
                ing = item["etken_madde"]
                kat = item["kategori"]
                console.print(f"\n[bold cyan][{idx}/{len(ingredients)}] Etken Madde:[/bold cyan] {ing} ({kat})")

                try:
                    search_input = page.locator("input[type='search'], input[placeholder*='Ara']").first
                    if await search_input.count() == 0:
                        await page.goto(TITCK_KUB_KT_URL, wait_until="networkidle", timeout=45000)
                        search_input = page.locator("input[type='search'], input[placeholder*='Ara']").first

                    # Kutuyu temizle ve DataTables/AJAX aramasını tetiklemek için karakter karakter yaz
                    await search_input.click()
                    await search_input.fill("")
                    await search_input.press_sequentially(ing, delay=60)
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(random.uniform(2.5, 3.8))

                    rows = page.locator("table tbody tr")
                    row_count = await rows.count()
                    if row_count == 0:
                        console.print(f"  [yellow]Sonuç bulunamadı: {ing}[/yellow]")
                        continue

                    candidates = []
                    scan_limit = min(row_count, 25)
                    for i in range(scan_limit):
                        row = rows.nth(i)
                        raw_text = (await row.inner_text()).strip()
                        clean_title = raw_text.split("\t")[0].split("\n")[0].strip()

                        s = score_drug_row(raw_text, clean_title, ing)
                        if s < 0:
                            continue

                        # Satırdaki tüm PDF bağlantılarını yakala
                        pdf_links = row.locator("a[href*='.pdf'], a[href*='kubKtAttachments']")
                        link_count = await pdf_links.count()
                        if link_count == 0:
                            continue

                        kt_href = None
                        kub_href = None

                        for j in range(link_count):
                            link_el = pdf_links.nth(j)
                            href = await link_el.get_attribute("href")
                            link_text = (await link_el.inner_text()).strip().upper()
                            if not href:
                                continue

                            # URL dosya adından veya sütun sırasından KT / KÜB ayrımı yap
                            upper_href = href.upper()
                            if "KT" in link_text or "ONAYLIKT" in upper_href or "_KT" in upper_href:
                                kt_href = href
                            elif "KÜB" in link_text or "KUB" in link_text or "ONAYLIKB" in upper_href or "_KB" in upper_href or "_KUB" in upper_href:
                                kub_href = href
                            else:
                                # TİTCK tablosunda genellikle 1. ikon KÜB, 2. ikon KT'dir
                                if link_count >= 2 and j == 0 and kub_href is None:
                                    kub_href = href
                                elif kt_href is None:
                                    kt_href = href

                        if kt_href or kub_href:
                            candidates.append((s, clean_title, kt_href, kub_href))

                    if not candidates:
                        console.print(f"  [yellow]Uygun yetişkin tablet/kapsül formu eşleşmedi: {ing}[/yellow]")
                        continue

                    candidates.sort(key=lambda x: x[0], reverse=True)

                    selected_count = 0
                    for _, title, kt_href, kub_href in candidates:
                        if selected_count >= MAX_BRANDS_PER_INGREDIENT:
                            break

                        brand_root = extract_brand_root(title)
                        if brand_root in downloaded_brands:
                            continue

                        downloaded_brands.add(brand_root)
                        selected_count += 1

                        if kt_href:
                            full_kt = kt_href if kt_href.startswith("http") else f"https://www.titck.gov.tr{kt_href}"
                            await download_pdf(http_client, full_kt, title, ing, kat, "KT", manifest)

                        if kub_href:
                            full_kub = kub_href if kub_href.startswith("http") else f"https://www.titck.gov.tr{kub_href}"
                            await download_pdf(http_client, full_kub, title, ing, kat, "KUB", manifest)

                except Exception as exc:
                    console.print(f"  [red]Tarama hatası ({ing}):[/red] {exc}")

        await browser.close()

    total_docs = sum(1 for k, v in manifest.items() if isinstance(v, dict))
    console.rule(f"[bold green]Tamamlandı! Toplam İndirilen Resmi Belge (KT + KÜB): {total_docs}[/bold green]")


if __name__ == "__main__":
    asyncio.run(discover_and_fetch())