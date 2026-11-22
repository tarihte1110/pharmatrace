
# PharmaTrace 🩺🔍

**PharmaTrace**, TİTCK onaylı resmi Kullanma Talimatları (KT) ve Kısa Ürün Bilgileri (KÜB) dokümanlarını analiz ederek ilaç-ilaç ve ilaç-gıda etkileşimlerini **kesin kaynak atfı (traceable citations)** ile sunan uçtan uca bir RAG (Retrieval-Augmented Generation) sistemidir.

> **Yasal ve Tıbbi Sorumluluk Reddi:** PharmaTrace tıbbi tavsiye, teşhis veya tedavi önerisi sunmaz. Yalnızca resmi prospektüs belgelerinde yer alan bilgileri hızlı ve anlaşılır şekilde erişilebilir kılan bir bilgi erişim aracıdır.

## Mimari Özellikler

- **Layout-Aware Ingestion:** TİTCK prospektüs PDF'lerini standart sağlık bakanlığı bölüm hiyerarşisine göre parçalayan yapısal ayrıştırıcı.
- **Hybrid Search + Reranking:** Qdrant üzerinde Dense (`BAAI/bge-m3`) + Sparse (BM25) araması ve `bge-reranker-v2-m3` ile çapraz doğrulama.
- **Multi-Layer Guardrails:** Acil durum tespiti, düşük güven skoru reddi ve NLI tabanlı halüsinasyon kontrolü.
- **İnteraktif Kaynak İnceleyici:** React arayüzünde her iddianın yanındaki rozete tıklayarak orijinal prospektüs paragrafını görüntüleme.
