/** Shared frontend types for medication data. */
export interface SourceCitation {
  source_id: number;
  ilac_adi: string;
  etken_maddeler: string[];
  dokuman_tipi: string;
  score: number;
  excerpt: string;
  full_text?: string | null;
}

export type DocumentTypeFilter = 'all' | 'KÜB' | 'KT';

export interface ChatRequest {
  question: string;
  ilac_filtresi?: string | null;
  etken_madde_filtresi?: string | null;
  dokuman_tipi?: 'KUB' | 'KT' | null;
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
  is_pharmaceutical: boolean;
  cached: boolean;
}

export interface HealthResponse {
  status: string;
  model: string;
  qdrant_collection: string;
  indexed_chunks: number;
}

export interface DrugCatalogEntry {
  ilac_adi: string;
  etken_maddeler: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  drugTag?: string;
  sources?: SourceCitation[];
  isPharmaceutical?: boolean;
  cached?: boolean;
  timestamp: string;
}
