/** Backend API client helpers will be added here. */
import {
  ChatRequest,
  ChatResponse,
  DrugCatalogEntry,
  HealthResponse,
} from '@/types/drug';

const API_V1_PREFIX = '/api/v1';

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_V1_PREFIX}/health`);
  if (!response.ok) {
    throw new Error('Backend sağlık kontrolüne ulaşılamadı.');
  }
  return response.json();
}

export async function fetchDrugCatalog(): Promise<DrugCatalogEntry[]> {
  const response = await fetch(`${API_V1_PREFIX}/drugs/catalog`);
  if (!response.ok) {
    throw new Error('İlaç kataloğu alınamadı.');
  }
  return response.json();
}

export async function sendChatQuery(payload: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_V1_PREFIX}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question: payload.question.trim(),
      ilac_filtresi: payload.ilac_filtresi?.trim() || null,
      etken_madde_filtresi: payload.etken_madde_filtresi?.trim() || null,
      dokuman_tipi: payload.dokuman_tipi ?? null,
    }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || 'Sorgu işlenirken sunucu hatası oluştu.');
  }

  return response.json();
}