
# PharmaTrace — Resmi KÜB / KT Klinik RAG Sistemi

PharmaTrace, Türkiye İlaç ve Tıbbi Cihaz Kurumu (TİTCK) standartlarındaki **Kısa Ürün Bilgisi (KÜB)** ve **Kullanma Talimatı (KT)** belgelerini kaynak göstererek sorgulayan, sıfır halüsinasyon odaklı klinik araştırma asistanıdır.

## Temel Mimari & Özellikler

* **Hibrit Vektör Arama (Qdrant + RRF):** `intfloat/multilingual-e5-large` (1024-d dense) ve `Qdrant/bm25` (sparse) vektörleri Reciprocal Rank Fusion (RRF) ile birleştirilir.
* **Çok Katmanlı Guardrail (LangGraph):** Prompt-injection süzgeci ve farmasötik kapsam denetleyicisi, ilaç dışı veya veritabanında karşılığı olmayan soruları üretim aşamasına geçmeden reddeder.
* **Sıfır Halüsinasyonlu Sentez & Önbellek:** DeepSeek V4.1 Flash (`temperature=0.0`) yalnızca getirilen bağlam parçalarına dayanarak `[Kaynak X]` atıflı yanıt üretir; tekrarlanan sorgular Redis önbelleğinden milisaniyeler içinde sunulur.
* **Klinik Araştırma Konsolu (React + TypeScript + Tailwind v4):** Tıklanabilir satır içi kaynak rozetleri, yan panel prospektüs alıntı inceleyici ve `@` ile dinamik ilaç katalog etiketleme.

## İndekslenen Veri Kümesi

TİTCK resmi prospektüs arşivinden derlenen veri kümesinin güncel durumu:

| Metrik | Değer |
| :----- | ----: |
| Benzersiz İlaç Sayısı | 142 |
| Toplam Vektör Parçası (Chunk) | 7.758 |
| Belge Türleri | KÜB (Kısa Ürün Bilgisi) + KT (Kullanma Talimatı) |
| Vektör Koleksiyonu | `pharmatrace_prospectus` |

Sayılar, çalışan sistem üzerinde şu uçlardan canlı olarak doğrulanabilir:

* `GET /api/v1/drugs/catalog` — benzersiz ilaç kataloğu (liste uzunluğu = ilaç sayısı)
* `GET /api/v1/health` — koleksiyondaki toplam parça sayısı (`indexed_chunks`)

## Klinik Değerlendirme (RAG Eval) Sonuçları

`backend/tests/eval/run_rag_eval.py` üzerinde LLM-as-a-Judge denetimiyle elde edilen sonuçlar:

| Metrik                                                 |     Başarı Oranı     |
| :----------------------------------------------------- | :----------------------: |
| **Guardrail & Kapsam Dışı Reddi**             |        `%100.0`        |
| **Kaynak Atıf Bütünlüğü (`[Kaynak X]`)** |        `%100.0`        |
| **Bağlam Sadakati (Faithfulness)**              | `%100.0` (1.00 / 1.00) |
| **Genel Değerlendirme Başarısı**             |   **`%100.0`**   |

## Hızlı Kurulum (Docker Compose)

1. `backend/.env.example` dosyasını `backend/.env` olarak kopyalayıp `DEEPSEEK_API_KEY` değerini girin.
2. Tüm servisleri (`qdrant`, `redis`, `backend`, `frontend`) tek komutla başlatın:

```bash
docker compose up -d --build
```
