const PIPELINE_STEPS = [
  {
    title: 'Sorgu güvenliği ve kapsam kontrolü',
    description:
      'Sorgular, prompt injection ve kapsam dışı içerik kontrollerinden geçirilir. Sistem yalnızca ilaç ve klinik bilgi alanındaki soruları yanıtlar.',
  },
  {
    title: 'Resmi KÜB ve KT belgelerinde arama',
    description:
      'Prospektüsler bölüm yapıları korunarak indekslenir. Yoğun anlamsal arama ve BM25 anahtar kelime araması birlikte kullanılır.',
  },
  {
    title: 'Sonuçların birleştirilmesi ve tekilleştirme',
    description:
      'Farklı arama yöntemlerinden gelen sonuçlar sıralama birleştirmesiyle değerlendirilir; yinelenen metinler elenir.',
  },
  {
    title: 'Kaynaklara bağlı yanıt üretimi',
    description:
      'Yanıtlar getirilen belge bölümlerine dayandırılır ve metin içi kaynak bağlantılarıyla sunulur. Tekrarlanan sorgular önbellekten karşılanabilir.',
  },
];

export function Methodology() {
  return (
    <div className="chat-scroll min-h-0 flex-1 overflow-y-auto bg-canvas px-5 py-8 sm:px-8 sm:py-12">
      <div className="mx-auto max-w-5xl">
        <div className="max-w-3xl border-b border-hairline pb-8">
          <p className="font-mono text-xs font-medium tracking-tight text-cobalt">
            SİSTEM NOTLARI
          </p>
          <h2 className="mt-5 text-3xl font-bold tracking-[-0.03em] text-primary sm:text-5xl">
            Kaynak odaklı bilgi erişimi
          </h2>
          <p className="mt-4 text-base leading-7 text-secondary">
            PharmaTrace, TİTCK onaylı Kısa Ürün Bilgisi (KÜB) ve Kullanma Talimatı (KT) belgelerini aranabilir hale getirir. Her yanıt, dayandığı belge bölümlerine geri izlenebilir.
          </p>
        </div>

        <div className="mt-8 border-t border-hairline">
          {PIPELINE_STEPS.map((step, index) => (
            <article
              key={step.title}
              className="grid gap-2 border-b border-hairline py-5 sm:grid-cols-[48px_240px_minmax(0,1fr)] sm:gap-5 sm:py-6"
            >
              <span className="font-mono text-xs font-medium tracking-tight text-muted">
                0{index + 1}
              </span>
              <h3 className="text-sm font-bold leading-6 text-primary">{step.title}</h3>
              <p className="text-[15.5px] leading-[1.75] text-secondary">{step.description}</p>
            </article>
          ))}
        </div>

        <p className="mt-8 max-w-3xl border-l-4 border-cyan bg-subtle px-4 py-3 text-sm leading-7 text-primary">
          PharmaTrace bilgilendirme ve kaynak inceleme aracıdır; tıbbi tavsiye, teşhis veya tedavi önerisi yerine geçmez.
        </p>
      </div>
    </div>
  );
}
