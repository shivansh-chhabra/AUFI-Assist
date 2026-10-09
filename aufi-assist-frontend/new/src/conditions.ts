import type { ContentType } from './types';

/** The 11 conditions in the AUFI cluster. `id` values are what the backend should send. */
export const CONDITIONS: { id: string; name: string }[] = [
  { id: 'malaria', name: 'Malaria' },
  { id: 'dengue', name: 'Dengue' },
  { id: 'typhoid', name: 'Typhoid fever' },
  { id: 'scrub_typhus', name: 'Scrub typhus and murine typhus' },
  { id: 'leptospirosis', name: 'Leptospirosis' },
  { id: 'chikungunya', name: 'Chikungunya' },
  { id: 'viral_ili', name: 'Viral influenza-like illness' },
  { id: 'hepatitis_a_e', name: 'Hepatitis A and E' },
  { id: 'occult_bacteraemia', name: 'Occult bacteraemia' },
  { id: 'rheumatic_fever', name: 'Rheumatic fever' },
  { id: 'tb', name: 'TB' },
];

export const conditionName = (id: string): string =>
  CONDITIONS.find((c) => c.id === id)?.name ?? id;

export const CONTENT_TYPES: { id: ContentType; label: string }[] = [
  { id: 'clinical_features', label: 'Clinical features' },
  { id: 'confirmatory_tests', label: 'Confirmatory tests' },
  { id: 'treatment', label: 'Treatment and management' },
];

export const contentTypeLabel = (id?: ContentType): string =>
  CONTENT_TYPES.find((c) => c.id === id)?.label ?? '';

export const EXAMPLE_PROMPTS = [
  'Fever for three days with body ache',
  'Fever with chills every other day after a trip to a forest area',
  'Fever for five days with yellow eyes and dark urine',
];
