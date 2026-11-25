
# PharmaTrace — Design System & Anti-AI Slop Specification

## 1. Tasarım Yönü (Design Direction)

**Ekol:** Swiss Editorial + Clinical Precision (Linear keskinliği + modern tıbbi dergi okunabilirliği).
**Marka Kimliği:** Soğuk, keskin, otoriter ve yüksek kontrastlı. Logodaki **Derin Lacivert (`#06285A`)** ve **Hassas Camgöbeği (`#00A8C6`)** ekseninde kurulu, görsel gürültüden arındırılmış bir klinik araştırma çalışma alanı.

## 2. Kesin Yasaklar (Anti-AI Slop Rules)

Kodlama ajanı aşağıdaki kalıpları **KESİNLİKLE** kullanmayacaktır:

- **Varsayılan Font Yasağı:** `Inter`, `Roboto`, `Arial`, `Open Sans` veya sistem varsayılan sans fontları kullanılmayacak.
- **Kart Enflasyonu Yasağı:** Her bilgi bloğunu `rounded-xl shadow-sm bg-white` kutular içine hapsetme. Bilgi hiyerarşisi kartlarla değil; **tipografik ölçek, `1px` keskin ayırıcı çizgiler (hairline borders) ve yüzey tonu farklarıyla** kurulacak.
- **Gradyan Yasağı:** Butonlarda, arka planlarda veya kart başlıklarında kesinlikle gradyan (`bg-gradient-*`) kullanılmayacak. Arayüzdeki tek gradyan marka logosunun kendisidir.
- **Dekoratif İkon Yasağı:** Her başlığın, her maddenin veya her bölümün başına süs amaçlı ikon koyma. İkonlar yalnızca gerçek bir kullanıcı aksiyonu (kopyala, kapat, filtrele, genişlet) veya durum göstergesi taşıdığında kullanılacak.
- **Sıcak/Soğuk Karışımı Yasağı:** Krem, bej veya sıcak gri (`stone`, `warmGray`) tonları tamamen kaldırılacak. Tüm nötrler soğuk lacivert-alttonlu (`cool slate / clinical ice`) olacak.
- **Ağır Gölge Yasağı:** `shadow-md`, `shadow-lg` gibi kabarık gölgeler yalnızca havada asılı duran popover/dropdown (`@` ilaç seçici) bileşenlerinde kullanılacak; ana yerleşimde gölge yerine `1px` sınır çizgisi kullanılacak.

## 3. Logo Kullanımı

- **Dosya Yolu:** `frontend/src/assets/logo/logo.png` (ES modülü olarak import edilecek: `import brandLogo from '@/assets/logo/logo.png'`).
- **Header Kullanımı:** Çerçevesiz, kutusuz, doğrudan şeffaf zemin üzerinde `h-9 w-auto object-contain`. Yanında `PharmaTrace` (`font-bold tracking-tight text-[#061B3A]`) ve altında küçük monospace etiket `KÜB / KT KLİNİK ARŞİVİ`.
- **Empty State / Hakkında:** Küçük, abartısız marka imzası olarak kullanılabilir.

## 4. Renk Tokenları (Logo ile %100 Uyumlu)

| Token                 | Hex         | Kullanım Alanı                                                             |
| :-------------------- | :---------- | :--------------------------------------------------------------------------- |
| `--bg-canvas`       | `#F7F9FC` | Ana zemin, yan paneller, filtre çubuğu                                     |
| `--bg-surface`      | `#FFFFFF` | Ana okuma alanı, giriş alanı, aktif kaynak satırı                       |
| `--bg-subtle`       | `#EDF2F8` | Hover durumları, tablo başlıkları, seçili satır                        |
| `--border-hairline` | `#E2E8F0` | Tüm ana bölüm ayırıcıları (`1px solid`)                             |
| `--border-strong`   | `#CBD5E1` | Input sınırları, aktif odak öncesi çerçeve                             |
| `--ink-primary`     | `#061B3A` | Ana başlıklar ve klinik metin (logodan türetilmiş koyu mürekkep)        |
| `--ink-secondary`   | `#334155` | Gövde metni                                                                 |
| `--ink-muted`       | `#64748B` | Yardımcı etiketler, zaman damgaları, yer tutucular                        |
| `--brand-navy`      | `#06285A` | Birincil aksiyon butonları, aktif sekme göstergesi, KÜB vurgusu           |
| `--brand-cobalt`    | `#0068A8` | Linkler, aktif odak (`focus-ring`), tıklanabilir `[Kaynak X]` rozetleri |
| `--brand-cyan`      | `#00A8C6` | Canlı sistem göstergesi, klinik özet şeridi, KT vurgusu                  |
| `--status-online`   | `#059669` | Sistem aktif göstergesi                                                     |

### Belge Türü Renk Kodlaması (Monokrom-Uyumlu)

- **KÜB (Hekim/Eczacı Belgesi):** `bg-[#EBF3FA] text-[#06285A] border-[#B8D4EE]`
- **KT (Hasta Kullanma Talimatı):** `bg-[#ECFEFF] text-[#0E7490] border-[#A5F3FC]`

## 5. Tipografi

Google Fonts üzerinden `index.html` dosyasına şu iki font yüklenecek:

1. **UI & Okuma:** `Plus Jakarta Sans` (400, 500, 600, 700)
2. **Teknik Veri & Etiketler:** `JetBrains Mono` (400, 500, 600)

- **Sayfa Başlığı (H1):** `text-3xl font-bold tracking-[-0.03em] text-[#061B3A]`
- **Klinik Bölüm Başlıkları (H3):** `text-[15px] font-bold uppercase tracking-[0.04em] text-[#06285A]`
- **Yanıt Gövde Metni:** `text-[15.5px] leading-[1.75] text-[#1E293B]` (Geniş satır aralığı, maksimum `max-w-[74ch]` okuma genişliği)
- **Teknik Meta (RRF Skoru, KÜB/KT, Tarih, Parça Sayısı):** `font-mono text-[11.5px] tracking-tight`

## 6. Yerleşim ve Boyutlandırma Kuralları

- **Köşe Yuvarlaklığı:** Keskin ve mimari. Input ve butonlarda `rounded-md` (`6px`), rozetlerde `rounded` (`4px`), büyük panellerde `rounded-none` (tam kenardan kenara `1px` çizgi ayrımı).
- **Kırpılma Önleme:** Sohbet/araştırma akışı `flex-1 overflow-y-auto` olacak ve alt arama çubuğu akışın **üstüne binmeyecek** (mutlak/fixed değil, flex kolonunun bağımsız alt elemanı olacak; içerik altında `pb-10` nefes payı bulunacak).
- **Sağ Kaynak İnceleyici (Source Inspector):** Sabit `w-[420px] xl:w-[460px]`, kenarlıklı (`border-l border-[#E2E8F0]`), tam metni genişletilebilir akordeon yapısında.
- **Kontrol Boyutları:** Üst bar `h-16`, arama kutusu `min-h-[56px]`, filtre alanları `h-10`.
