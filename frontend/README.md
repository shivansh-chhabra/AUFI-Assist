# AUFI Assist: frontend

React + Vite chat interface for the agentic decision-support system for acute undifferentiated fever.

```bash
npm install
cp .env.example .env.local   # VITE_USE_MOCK_DATA=true runs the scripted demo, no backend needed
npm run dev
```

Set `VITE_USE_MOCK_DATA=false` to talk to FastAPI (proxied from `/api` to `localhost:8000`, see `vite.config.ts`).
The product name, model label and setting are in `src/brand.ts`.

## What the UI shows for each reply

| Piece | Source field | Purpose |
|---|---|---|
| Progress strip | `progress` | Question n of max, conditions remaining, why the loop stopped |
| Follow-up question + Yes/No/Not sure buttons | `question` | The one question the scoring component chose |
| Likely conditions | `candidates` | Ranked probabilities with the shift since the previous answer |
| From the guidelines | `explanation` + `evidence.sources` | Per-disease features / tests / treatment, each statement cited |
| Guideline sources | `evidence` | Cited passages with body (ICMR/MoHFW), disease and content-type tags |
| What the system did | `steps` | Reasoning trace (streamed live while the reply is generated) |

## Backend contract

All fields except `reply` and `steps` are optional. Probabilities are 0..1.

**`POST /chat`** and **`POST /chat/stream`** (SSE: `{"type":"step","text":...}` events, then one `{"type":"final", ...ChatResponse}`)

Request:
```json
{ "message": "Yes", "conversation_id": "c1", "answer": { "feature": "rash_or_bleeding", "value": "yes" } }
```
`answer` is present only when the user tapped a button, so the scoring code can update from the structured value instead of parsing text. `value` is `yes | no | unsure | skip`.

Response (`ChatResponse`, see `src/types.ts`):
```json
{
  "reply": "Noted. Next question:",
  "steps": ["Updated probabilities from your answer.", "..."],
  "candidates": [{ "id": "dengue", "name": "Dengue", "probability": 0.44, "previous": 0.27, "shortlisted": false }],
  "question": { "feature": "severe_joint_pain", "text": "Is there joint pain ...?", "informationGain": 0.62, "candidatesSeparated": 2 },
  "progress": { "questionsAsked": 2, "maxQuestions": 8, "candidatesRemaining": 8, "stopReason": null },
  "explanation": null,
  "evidence": null
}
```
- When the loop stops, send `question: null`, `progress.stopReason` (`shortlist | question_limit | no_discriminating_question`), `explanation` and `evidence`.
- `explanation[].sections[].citations` are `evidence.sources[].id` values (1-based). The `[n]` buttons open that source.
- If retrieval finds nothing above the relevance threshold, send `evidence` with an empty `sources` array. The UI then says no medical claim is made.
- Candidate `id`s should be the ids in `src/conditions.ts`.

**`POST /search`**: `{ query, disease?, content_type? }` returns `{ results: [{ text, source, distance, disease?, content_type?, body?, location? }] }`.
`content_type` is `clinical_features | confirmatory_tests | treatment`.

**`GET /knowledge-base/status`**: `{ documentCount, lastIndexed }`. **`GET /kb-docs/{file}`** and **`/kb-docs/{file}/content`** are unchanged.
`GET /conversations` and `/conversations/{id}/messages` are unchanged (messages use the new fields above).

## Notes

- With the backend down the UI shows an error. It never falls back to demo data silently, because the content is clinical.
- Fonts are bundled (`@fontsource`), so the page makes no outside requests.
- All mock probabilities and guideline excerpts are scripted for demonstration and are not clinical content.
