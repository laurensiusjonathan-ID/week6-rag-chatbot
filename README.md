# week6-rag-chatbot

RAG chatbot end-to-end: chunk → embed → store (Qdrant) → retrieve → cited answer.

## Pipeline

```
corpus/*.* ──> chunker.py ──> ingest.py ──> Qdrant ("kb") <── rag.py <── question
                 (350 tok,        (stable ids,     │
                  50 overlap)      upsert)         └──> LLM ──> answer with [n] citations
```

## Idempotence proof (acceptance criterion)

Ingestion is safe to re-run. Each chunk's point id is derived deterministically
from its source file and chunk index — `md5("{filename}:{chunk_index}")` — so the
same chunk always maps to the **same id**. Qdrant's `upsert` overwrites points by
id instead of appending, so a second run updates the exact same 45 points rather
than duplicating them.

Proof — ingestion run twice in a row, collection count checked after each run:

```
> python ingest.py
ingested 45 chunks
total points in collection: 45
> python ingest.py
ingested 45 chunks
total points in collection: 45
```

The count stays **45** after both runs. If the ids were random (e.g. `uuid4()`),
the second run would have doubled the collection to 90 — the classic
"corpus indexed three times" RAG bug. Stable ids + upsert make re-ingestion
idempotent for free.

## Test 1 — five real questions (citations verified)

Each answer is the bot's verbatim output. Every `[n]` citation was verified by
reading the retrieved chunk and checking each claim against it.

### Q1 — dental annual limit

**Q:** Berapa plafon tahunan untuk kedokteran gigi dan layanan apa saja yang termasuk?

**A:** Berdasarkan sumber yang tersedia, plafon untuk kedokteran gigi adalah Rp 5.000.000 per tahun. Layanan yang termasuk dalam kategori ini adalah tambal, scaling, cabut, sarang akar, dan kawat gigi [3].

**Cited:** [3] `doc24.md` #1 — verified: the plafon table in that chunk lists kode 8 "Kedokteran gigi (tambal, scaling, cabut, sarang akar, kawat gigi) — Rp 5.000.000 per tahun".

### Q2 — most common claim-delaying mistakes

**Q:** Kesalahan apa yang paling sering ditemukan petugas HC sepanjang 2024 sehingga klaim tertunda?

**A:** Kesalahan yang paling sering ditemukan petugas HC sepanjang 2024 adalah:
1. Kode treatment tidak sesuai isi kwitansi (misalnya kwitansi laboratorium dikode 1/konsultasi umum alih-alih 3/diagnostik).
2. Kwitansi di atas Rp 1.000.000 tidak bermaterai.
3. Tanggal kwitansi telah melewati 30 hari kerja saat penyerahan.
4. Menggabungkan layanan beberapa anggota keluarga ke satu form padahal plafon anak terpisah dari plafon karyawan.
5. Menggunakan fotokopi kwitansi tanpa surat pengganti resmi berkop, bermaterai, dan bertanda tangan dari klinik [1].

**Cited:** [1] `doc23.md` #5 (SOP §6) — verified: all five items match the chunk text.

> Retrieval note: an earlier phrasing ("…kesalahan umum yang paling sering menunda
> pemrosesan klaim menurut SOP?") failed to rank `doc23.md` #5 highly; retrieval
> returned headers/directory chunks and the bot correctly refused per its rules.
> Rephrasing with the document's own vocabulary pulled the right chunk to rank 1.
> Retrieval, not generation, was the weak link — exactly the "what did retrieval
> return?" diagnosis from the guide.

### Q3 — partner clinics on national holidays

**Q:** Klinik rekanan mana saja yang tetap melayani pada hari libur nasional dan pada jam berapa?

**A:** Klinik rekanan yang tetap melayani pada hari libur nasional adalah Klinik Mitra Tangsel dan Klinik Surabaya Medika dengan jadwal khusus pukul 09.00-15.00 [2].

**Cited:** [2] `doc24.md` #3 — verified: the chunk ends with exactly that sentence (the klinik table + holiday rule).

### Q4 — reimbursement duration and the >Rp 10 juta rule

**Q:** Berapa lama proses reimbursement klaim dan bagaimana aturan untuk klaim di atas Rp 10 juta?

**A:** Berdasarkan sumber yang tersedia, berikut adalah jawaban untuk pertanyaan Anda:

- **Lama Proses Reimbursement:** Pembayaran dilakukan paling lambat **14 hari kerja** sejak klaim dinyatakan lengkap [1][3].
- **Aturan Klaim di atas Rp 10.000.000:** Klaim dengan nilai di atas Rp 10.000.000 memerlukan persetujuan dari **Manager HR** [1][3]. Dengan persetujuan ini (yang memiliki target 3 hari kerja), target pembayaran keseluruhan tetap 14 hari kerja dengan batas maksimum **21 hari kerja** [3].

**Cited:** [1] `doc21.md` #3 (Kebijakan §4) and [3] `doc23.md` #3 (SOP Langkah 7) — verified: both chunks contain the 14/21 working-day and Manager-HR-approval rules.

### Q5 — dependent age limit

**Q:** Anak saya berusia 23 tahun dan masih kuliah penuh waktu, apakah masih dijamin manfaat kesehatan?

**A:** Ya, anak Anda masih dijamin. Sesuai kebijakan, batas usia anak yang dijamin adalah di bawah 25 tahun apabila masih terdaftar sebagai pelajar penuh waktu [1].

**Cited:** [1] `doc21.md` #0 (Kebijakan §1) — verified: chunk states coverage for children "di bawah 21 tahun, atau di bawah 25 tahun apabila masih terdaftar sebagai pelajar penuh waktu".

## Test 2 — two out-of-corpus questions (refusal rule)

The system prompt enforces the exact refusal sentence
`I don't have that in the knowledge base.`

**Q:** Berapa jumlah karyawan yang bekerja di PT AIEA saat ini?

**A:** I don't have that in the knowledge base.

**Q:** Bagaimana cara mengajukan cuti tahunan di PT AIEA?

**A:** I don't have that in the knowledge base.

Both questions still returned a full top-5 of retrieved chunks (claim forms and
document headers that mention PT AIEA) — the model refused anyway instead of
improvising from them. No fabricated numbers, no citations: refusal held.