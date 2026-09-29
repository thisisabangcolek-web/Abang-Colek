# ABANGCOLEK — Sintesis Projek dan Cadangan Penambahbaikan
Tarikh review: 29 September 2026 (Asia/Kuala_Lumpur)
Lokasi: D:\ABANGCOLEK | Peranti: NIAGA-HUB | Baseline Git: master @ 73ae98d
Status cadangan: baiki integriti dan penyelarasan data sebelum memperluas automasi atau meluluskan PRD.

## 1. Kesimpulan utama

Projek ini sudah mempunyai collector sebenar, penyimpanan bukti, integrasi TypeSafe JEV, taxonomy, kod analytics dan rangka Knowledge Graph. Namun, ia masih merupakan sistem research/discovery berasaskan bukti. Aplikasi operasi ABANGCOLEK belum dibina dan pemahaman operasi dalaman belum disahkan.

Pemulihan daripada data sintetik ialah kemajuan penting. Walau bagaimanapun, label “integrity PASS” dalam dokumentasi lebih luas daripada pemeriksaan yang benar-benar dibuat oleh validator. Ujian 33/33 lulus, tetapi audit ini menemukan kehilangan satu fail normalized, kiraan post yang salah, hasil downstream yang belum dikemas kini, dan kelemahan kontrak bukti/JEV.

Keutamaan paling bernilai ialah menjadikan bukti sedia ada konsisten, boleh dijejaki dan boleh disemak manusia. Menambah jumlah crawling sekarang akan membesarkan data di atas kelemahan yang sama.

## 2. Skop dan kaedah review

- Baca README, semua dokumen aktif dalam docs, tiga laporan aktif, kod teras collectors/evidence/JEV/models/media/analytics/knowledge/scripts dan keseluruhan suite ujian.
- Semak status Git, sejarah recovery, struktur direktori dan fail data semasa melalui Desktop Commander Remote.
- Jalankan semula pytest dan verify_integrity; kira semula inventori raw/normalized/decision serta hash payload dan artifak capture.
- Baca pangkalan SQLite menggunakan mode read-only; hitung BI dalam memori tanpa menimpa output produksi.
- Gunakan probe kecil dalam memori untuk mengesahkan kelemahan validator, normalizer, taxonomy, pemilihan model dan kontrak respons.
- Arkib legacy/quarantine/forensic tidak digunakan sebagai fakta bisnes semasa; kandungannya tidak diaudit satu per satu.
- Tiada crawling baharu, panggilan API JEV baharu, pembacaan nilai token, migrasi data, pembaikan kod, commit atau push dibuat.
- Hanya dokumentasi review dan README dikemas kini. Penemuan bersifat snapshot pada baseline di atas.

## 3. Apa yang projek ini cuba capai

Tujuan akhirnya ialah membina aplikasi yang sesuai dengan operasi sebenar ABANGCOLEK/STYLOAIRPOOL. Sistem discovery mengumpul jejak awam, sumber pemilik dan bukti dalaman untuk mengenal pasti produk, saluran jualan, lokasi, ejen, pertanyaan pelanggan dan masalah operasi.

ABANGCOLEK, STYLOAIRPOOL, LIURLELEH dan JERUX ialah identiti/nama yang sedang dikaji. Kehadiran nama dalam taxonomy atau akaun calon tidak membuktikan pemilikan, hubungan syarikat, status rasmi atau susunan sejarah jenama.

Aliran sasaran:
1. Temui sumber dan rekod liputan.
2. Simpan capture asal dengan asal-usul dan hash.
3. Normalisasikan entiti/post/comment/media dengan identiti stabil.
4. Klasifikasikan bukti melalui JEV sambil mengekalkan ketidakpastian.
5. Bina pengetahuan dan analytics dengan pautan kembali kepada bukti.
6. Sahkan model operasi bersama pemilik/pasukan.
7. Bentuk PRD dan pilih MVP berdasarkan workflow yang disahkan.

Aliran runtime semasa berhenti selepas collection, normalization, JEV dan laporan backfill. run_backfill tidak mengorkestrasi refresh media, BI atau Knowledge Graph.

## 4. Status yang benar-benar disahkan

| Perkara | Pemerhatian semasa | Maksud |
|---|---:|---|
| Ujian sedia ada | 33/33 lulus, 0.90 saat | Bukan bukti semua aliran end-to-end betul |
| verify_integrity | INTEGRITY_PASS; COVERAGE_READY=False | Validator semasa mempunyai blind spot |
| Raw capture | 167 | Snapshot; bukan 167 post unik |
| Raw payload SHA-256 | 167/167 sepadan | Payload konsisten dengan hash tersimpan |
| Flag synthetic raw | 0 | Pemeriksaan flag; bukan pembuktian bebas setiap kenyataan sosial |
| Unik mengikut platform/source/collector | 128 | 39 snapshot berulang diketepikan |
| Normalized dilaporkan oleh batch | 128 | Senarai dalam memori |
| Fail normalized sebenar | 127 | Satu collision rentas platform |
| Keputusan JEV tersimpan | 304 | 128 content + 128 signal + 42 interaction + 6 complaint |
| Model pada keputusan tersimpan | jev-1.13.0, 304 rekod | Connectivity semasa tidak diuji semula |
| Decision tanpa pasangan normalized platform/hash | 2 | Kedua-duanya daripada profil yang tertindih |
| Post/video/foto dalam normalized | 123 | 79 video + 2 foto + 42 snapshot post |
| total_posts daripada BI semasa | 0 | Bug pemetaan record_type |
| Structured comment/reply | 0 | Interaction classification bukan comment sebenar |
| Fail BI tersimpan | Semua kiraan 0; dijana 12:06 waktu Malaysia | Stale berbanding batch JEV 16:18 |
| Knowledge Graph tersimpan | Semua empat jadual kosong | Kod wujud, hasil semasa belum dibina |
| Media v3 tersimpan | 0 aset | ASR/OCR/vision belum berjalan |
| Liputan sumber | 11 lane; semuanya partial atau blocked | Bukan 11 akaun unik |
| Digital Twin / PRD akhir | BLOCKED | Wajar dikekalkan sehingga gate sebenar dipenuhi |

304 decision ialah beberapa pandangan daripada keputusan bundle JEV. Ia tidak bermaksud 304 panggilan API atau 304 fakta bebas. Cache juga boleh digunakan; audit ini tidak mengukur penggunaan API sejarah.

## 5. Liputan dan bacaan bisnes yang selamat

TikTok mempunyai 81 URL ditemui. yt-dlp berjaya pada 79 dan gagal pada 2; kedua-dua ID gagal itu terdapat dalam hasil gallery-dl. Maka 81/81 URL yang diketahui mempunyai metadata melalui gabungan extractor. Ini tidak bermaksud keseluruhan sejarah TikTok telah lengkap, komen dipulihkan atau media dimuat turun.

Snapshot post awam meliputi Threads @airpoolstylo (15), Instagram @airpoolstylo (11), Instagram calon @abangcolek (4), dan calon/reseller @jeruxsliurlelehterengganu (12). Hubungan rasmi akaun calon masih memerlukan pengesahan.

JEV tersimpan mengelaskan 21 item sebagai ABANGCOLEK, 18 JERUX, 10 LIURLELEH, 2 MULTI_BRAND dan 77 UNKNOWN. Label signal termasuk mobile team/pop-up 46, wilayah baharu 21, recruitment 12 dan varian baharu 5. Terdapat 6 complaint views: LEAKAGE 2, TASTE 1 dan UNKNOWN 3.

Gunakan angka ini sebagai petunjuk untuk menyemak sumber dan bertanya soalan. Ia bukan jumlah cawangan, ejen, produk, pekerja, transaksi atau insiden unik. Page text boleh mencampurkan caption, komen, navigasi dan cadangan kandungan; taxonomy turut mempunyai bias yang dibincangkan di bawah.

Perkara yang masih tidak terbukti termasuk aliran pesanan, pemilikan stok, polisi ejen, kaedah bayaran sebenar, margin, resipi/BOM, susunan pasukan dan punca aduan. Root cause kekal UNDETERMINED.

## 6. Penemuan dan tindakan pembaikan

P0 = perlu selesai sebelum output dianggap boleh dipercayai untuk keputusan lanjut.
P1 = perlu sebelum memperluas collection dan membina discovery interface.
P2 = peningkatan kebolehgunaan/operasi selepas asas stabil.

### AC-01 — P0: Validator provenance tidak mengesahkan hash atau capture sebenar
Sumber: src/evidence/integrity.py::validate_raw_record; src/scripts/verify_integrity.py.
Validator menerima raw_hash yang sekadar tidak kosong. source_url sahaja bersama flag authoritative/provenance_verified mencukupi tanpa receipt. Probe dengan hash “not-a-sha256” diterima. BaseCollector.verify_integrity memang boleh mengira hash, tetapi tidak digunakan oleh gate produksi tersebut.
Cadangan: wajibkan schema, jenis boolean sebenar, SHA-256 sah, pengiraan semula payload hash dan receipt mengikut collector; semak kewujudan/hash capture. Bezakan capture_verified daripada claim_verified.
Penerimaan: payload yang diubah, receipt hilang dan hash palsu mesti gagal; rekod sah mesti lulus.

### AC-02 — P0: Identiti normalized bertembung rentas platform
Sumber: src/jev/batch_runner.py::normalize_verified_records; src/knowledge/graph.py::build_from_verified_evidence.
Nama fail menggunakan norm_<source_id>. Instagram dan Threads sama-sama mempunyai profile_airpoolstylo; hasilnya 128 item dalam batch menjadi 127 fail. Dua decision tidak mempunyai pasangan normalized platform/hash. Graph juga menggunakan evidence:<source_id> tanpa platform.
Cadangan: asingkan content_id=(platform,native_id), capture_id=(content_id,collector,capture hash), normalized_id=(capture_id,normalizer version), dan decision_id yang merujuk versi tepat. Fail menggunakan ID selamat berasaskan hash; jangan bina laluan daripada ID luaran mentah.
Penerimaan: ID sama di dua platform tidak menimpa satu sama lain; semua decision mempunyai lineage tepat; dedupe rentas collector tidak mengira post sama dua kali.

### AC-03 — P0: BI tidak mengenali jenis post semasa dan melabel page sebagai inquiry
Sumber: src/analytics/bi_engine.py::compute_total_counts; src/jev/batch_runner.py::run_all.
Senarai jenis post BI tidak merangkumi public_post_snapshot, public_video_metadata atau public_photo_metadata. 123 rekod post menghasilkan total_posts=0. total_inquiries=36 dikira daripada label interaction pada page snapshot, termasuk PRAISE dan COMPLAINT; tiada structured comments.
Cadangan: satu enum canonical record_kind, mapping setiap collector dan unit kiraan jelas. Pisahkan post-level intent signals, customer messages, inquiries dan deduplicated incidents.
Penerimaan: dataset sekarang menghasilkan 123 rekod post sebelum semakan kualiti kandungan; profile tidak dikira sebagai post; tiada page-level label dipanggil jumlah pertanyaan pelanggan sebenar.

### AC-04 — P0: Kontrak keputusan JEV belum ketat
Sumber: src/jev/engine.py::_live, evaluate_bundle; src/jev/batch_runner.py::_assert_live.
Respons dengan model_requested tetapi tanpa model sebenar dan answers kosong masih boleh dilabel authoritative. Soalan tiada jawapan boleh berubah menjadi UNKNOWN atau False melalui default. _assert_live menyemak nama model tetapi kemudian menetapkan engine/authoritative sendiri.
Cadangan: validate semua jawapan wajib, jenis/range/enum, provenance respons dan model_requested berasingan daripada model_resolved. Respons tidak lengkap mesti INVALID_RESPONSE; ketiadaan jawapan tidak sama dengan False. Cache sah perlu dinyatakan sebagai hasil live terdahulu, bukan panggilan baharu.
Penerimaan: respons kosong/salah jenis/model tidak diketahui ditolak atau digantung; tiada silent promotion.

### AC-05 — P0: Gate PRD dalam BI tidak sepadan dengan governance
Sumber: src/analytics/bi_engine.py::_coverage_ready, run_all; reports/ABANGCOLEK-OS-PRD.md.
authoritative_for_prd boleh menjadi True hanya apabila semua status coverage complete dan raw_records tidak kosong. Ia tidak memerlukan Digital Twin disahkan, workflow dalaman, structured conversations, lineage atau human sign-off. Sebaliknya, mewajibkan SEMUA lane complete boleh menghalang kemajuan apabila lane OAuth pilihan blocked.
Cadangan: gate berasingan untuk integrity, evidence usability, sufficiency mengikut workflow, internal validation dan PRD approval. Optional lane tidak menjadi veto automatik; gap mesti direkod dan diterima secara eksplisit.
Penerimaan: status collection sahaja tidak boleh meluluskan PRD; workflow yang cukup bukti boleh maju dengan gap yang dipersetujui.

### AC-06 — P1: Hash HTML menggunakan teks sebelum penulisan Windows
Sumber: src/collectors/browser_public_adapter.py::_page_snapshot.
85 rujukan snapshot HTML tidak sepadan dengan SHA-256 bytes pada cakera. Semua 85 padan apabila teks dinormalisasikan daripada CRLF ke LF. 82 rujukan output extractor padan pada bytes. Ini menunjukkan perbezaan format baris, bukan bukti kandungan telah dipalsukan.
Cadangan: simpan bytes yang sama dengan yang dihash, atau rekod kedua-dua bytes_sha256 dan canonical_text_sha256 beserta versi canonicalization. Simpan metadata asal sebelum migration; jangan overwrite bukti untuk membuat audit kelihatan lulus.
Penerimaan: setiap capture boleh diverifikasi menggunakan algoritma yang dinyatakan secara eksplisit.

### AC-07 — P1: Owner export diterima tetapi kandungannya terlepas normalizer
Sumber: src/collectors/owner_export_importer.py; src/jev/batch_runner.py::_extract_text.
Importer meletakkan data dalam raw_payload.export_payload; normalizer tidak membaca medan itu. Probe menghasilkan string kosong. Import JSON juga dilabel COMPLETE_VERIFIED hanya kerana parsing selesai.
Cadangan: adapter mengikut struktur export platform, rekod post/comment/media berasingan, extract parent/author/timestamp, dan beza “fail selesai diparse” dengan “liputan akaun lengkap”.
Penerimaan: fixture export sebenar yang telah dinyahkenal pasti menghasilkan canonical records dan JEV inputs; JSON kosong/format tidak dikenali tidak dilabel coverage lengkap.

### AC-08 — P1: Pipeline downstream dan penerbitan output belum konsisten
Sumber: src/scripts/run_backfill.py; src/jev/batch_runner.py; src/knowledge/graph.py.
Backfill tidak refresh BI/graph/media. Normalizer memadam semua fail lama sebelum keseluruhan JEV berjaya; graph clear dibuat sebelum rebuild. Kegagalan pertengahan boleh menghasilkan normalized baharu bersama decision lama atau graph separa.
Cadangan: run_id dan manifest setiap peringkat; tulis ke staging, validate, kemudian terbitkan satu run aktif secara atomik. Rebuild graph dalam transaksi atau DB baharu. Simpan output terakhir yang sah jika run gagal.
Penerimaan: simulated failure tidak merosakkan run aktif; semua output mempunyai input hash/run_id yang sama; paparkan freshness.

### AC-09 — P1: Dedupe memilih “terbaharu”, tanpa menilai kegunaan capture
Sumber: src/collectors/browser_public_adapter.py::collect_profile; src/jev/batch_runner.py::load_raw_sources.
Profile tetap diingest sebelum keputusan challenge digunakan untuk menghentikan collection. Page body digunakan sebagai teks bukti; capture yang lebih baharu tetapi blocked/kurang lengkap boleh menggantikan capture yang lebih kaya untuk classification.
Cadangan: capture_state dan usable_for_business_interpretation berasingan; kekalkan capture kegagalan sebagai bukti operasi collector. Pilih snapshot mengikut kelayakan dan kualiti sebelum timestamp; parse caption/author/comments secara berasingan.
Penerimaan: challenge-only page tidak menjadi bukti bisnes atau menggantikan capture usable.

### AC-10 — P1: Liputan collector boleh terlebih dakwa atau terlepas URL
Sumber: browser_public_adapter.py::_extract_post_links; instagram_adapter.py::collect_all; facebook_adapter.py::collect_all_managed_pages; tiktok_adapter.py::collect_user_videos.
Regex Instagram memerlukan /<handle>/p/ atau /<handle>/reel/; probe bentuk /p/ABC/ dan /reel/DEF/ menghasilkan kosong. Instagram/Facebook menelan exception collection comments tetapi masih boleh melaporkan COMPLETE_WITHIN_API_SCOPE. Facebook mengambil satu page senarai managed pages; TikTok boleh menanda exhausted apabila rows kosong tanpa validasi error envelope.
Cadangan: parse URL canonically dan sahkan author selepas capture; coverage per posts/comments/replies; rekod setiap kegagalan; cursor guard, error-envelope validation dan completion reason. Gabungkan status fallback mengikut content ID.
Penerimaan: kegagalan comments tidak disembunyikan; known URL backlog selepas fallback dikira tepat; pagination berulang tidak menyebabkan loop tanpa had.

### AC-11 — P1: Taxonomy boleh memaksa label dan memasukkan andaian bisnes
Sumber: src/jev/taxonomy.py::*criteria.
BusinessFunction mempunyai enum UNKNOWN tetapi tidak menawarkan UNKNOWN dalam criteria kepada JEV. Beberapa enum lain juga tiada dalam criteria. Brand criteria memasukkan gambaran “parent identity” bagi LIURLELEH walaupun hubungan jenama belum disahkan dalam laporan.
Cadangan: pastikan criteria dan enum sepadan; UNKNOWN/NOT_APPLICABLE tersedia bila relevan. Gunakan definisi neutral yang mengenali sebutan jenama tanpa mendakwa pemilikan/sejarah. Wujudkan set semakan manusia meliputi bahasa Melayu, slang, caption campur komen dan sumber tidak relevan.
Penerimaan: tiada enum wajib hilang; bahan tidak berkaitan boleh abstain; label sampel disemak manusia sebelum angka dijadikan kesimpulan.

### AC-12 — P1: Model selection dan cache belum cukup reproducible
Sumber: src/jev/typesafe_client.py::resolve_model; src/jev/engine.py::compute_cache_key.
Pemilihan model menggunakan sorted string; probe memilih jev-1.9.0 melebihi jev-1.13.0. Cache tidak memasukkan resolved model atau hash penuh arahan/criteria dan metadata input.
Cadangan: pin model yang dibenarkan atau parse versi dengan betul; fail jelas jika pin tidak tersedia. Cache key merangkumi content fingerprint, normalizer/prompt/taxonomy/schema version dan model. Rekod original evaluation time berasingan daripada cache retrieval time.
Penerimaan: model/prompt berubah tidak menggunakan cache lama secara senyap; offline reuse cache sah tidak didakwa sebagai connectivity live.

### AC-13 — P1: Graph menyimpan senarai ID tetapi tidak menjamin kewujudan bukti
Sumber: src/knowledge/graph.py::add_relationship, add_epistemology_item, build_from_verified_evidence.
evidence_ids mesti tidak kosong tetapi rujukan tidak disahkan terhadap registry bukti. Classification ditulis dengan confidence=1.0. Rebuild membaca semua snapshot, boleh menghasilkan hubungan berulang dan menimpa metadata entiti ID sama.
Cadangan: evidence registry dengan foreign keys, capture-specific lineage, confidence nullable/tidak dikalibrasi, idempotent edge key dan pemisahan fakta/classification/inference. Bezakan mention jenama daripada hubungan ownership.
Penerimaan: orphan evidence ditolak; rebuild input sama stabil; tidak semua classification ditunjukkan 100% yakin.

### AC-14 — P1: Model data berganda dan default terlalu yakin
Sumber: src/models/canonical.py, epistemology.py, traceability.py, jev_types.py dan models/__init__.py.
Terdapat definisi bertindih. ProductBatch yang dieksport daripada canonical default QC=PASSED, sedangkan traceability default=PENDING. Metrics yang belum diketahui lazimnya default 0; beberapa model membenarkan fact/inference tanpa evidence.
Cadangan: satu sumber schema, migration version, unknown=null, QC=PENDING dan validation evidence untuk promotion fakta. Model stok/batch adalah calon struktur teknikal, bukan pengesahan workflow sebenar.
Penerimaan: import mana-mana public model memberikan semantics konsisten; tiada kelulusan QC tanpa pemeriksaan.

### AC-15 — P1: Setup bergantung pada satu PC dan skop local discovery terlalu tersirat
Sumber: hard-coded D:/ABANGCOLEK dan C:/Users/megat; src/scripts/local_pc_discovery.py; root repository.
Tiada pyproject.toml, requirements atau lockfile pada root. Local discovery berjalan secara automatik dari run_backfill dan boleh membaca excerpt projek lain serta metadata history/personal filenames, kemudian menghantarnya ke JEV.
Cadangan: central settings, project root relatif/env, dependency manifest/lock, doctor/setup, dry-run dan config allowlist sumber. Jadikan local discovery lane yang jelas dan boleh dimatikan; preview/redact excerpt sebelum penghantaran luar. Asingkan collection daripada kebergantungan JEV.
Penerimaan: install bersih boleh diulang; ujian tidak bergantung data produksi; run standard mempunyai skop input yang jelas; outage JEV tidak menghalang capture yang dibenarkan.

### AC-16 — P2: Ujian dan dokumentasi belum melindungi kontrak end-to-end
Sumber: tests/*; docs/*; README.md.
Suite mempunyai nilai tetapi sebahagian ujian bergantung path/data PC dan melarang semua coverage complete. Tiada ujian yang mengesan collision, post count, export normalization, hasil kosong JEV, gate PRD atau run separa. Counter status disalin ke banyak dokumen. Fail media lama masih wujud bersebelahan output aktif.
Cadangan: tambah regression tests untuk AC-01 hingga AC-15 dengan fixture terasing; generate status daripada manifest run; label/deprecate artifak lama; lindungi skrip recovery daripada rerun yang menimpa snapshot/manifest.
Penerimaan: suite gagal pada bug yang direproduksi audit ini dan lulus selepas pembaikan; status laporan menyatakan masa/baseline/sumber pengiraan.

## 7. Apa yang patut dikekalkan

- Prinsip UNKNOWN dan root cause UNDETERMINED, pemisahan discovery lead daripada fakta, serta larangan menggantikan data hilang dengan kandungan rekaan.
- Raw capture dan arkib pemulihan, metadata asal-usul, stable extractor metadata serta penyisihan token daripada hasil authoritative.
- Bundled JEV evaluation untuk mengurangkan panggilan berulang, dengan kontrak/cache yang diperketat.
- Pemisahan collector daripada interpreter, dan PRD akhir yang belum diluluskan.
- SQLite dan fail JSON boleh diteruskan untuk skop semasa; audit ini tidak menemukan alasan untuk memaksa pertukaran stack.

## 8. Pelan improvement yang disyorkan

| Fasa | Fokus | Hasil yang perlu boleh disemak |
|---|---|---|
| A — Betulkan kebenaran data | AC-01 hingga AC-06; AC-11 | Payload/capture hashes sah, ID tanpa collision, counts tepat, JEV contract ketat, gate tidak premature |
| B — Jadikan pipeline boleh diulang | AC-07 hingga AC-10; AC-12 hingga AC-16 | Normalizer export, run staging, lineage, refreshed BI/graph, dependency/setup dan regression tests |
| C — Discovery workspace | Source library, evidence viewer, claim review, coverage matrix, identity resolution | Setiap kenyataan boleh dibuka kembali kepada capture dan disahkan/ditolak manusia |
| D — Tutup jurang bernilai tinggi | Structured comments/replies, media sebenar, sejarah terpilih dan interview operasi | Bukti menjawab persoalan bisnes tertentu, bukan hanya pertambahan record count |
| E — Satu MVP operasi | Workflow disahkan dan requirement traceability | Satu aliran lengkap diuji pengguna sebenar dengan ukuran kejayaan |

Internal discovery boleh bermula serentak dengan fasa A/B. Tidak perlu menunggu semua sejarah sosial dipulihkan untuk meminta pemilik menerangkan satu transaksi sebenar. Yang mesti ditangguh ialah dakwaan menyeluruh dan PRD yang dianggap telah diluluskan.

## 9. Cadangan produk terdekat: Discovery Workspace

Bina antaramuka kecil di atas pipeline yang dibetulkan supaya Bo boleh melihat bahan dan keputusan, bukan perlu membaca JSON atau mengulang konteks dalam chat.

- Source library: URL/fail, platform, waktu capture, status akses, liputan dan versi.
- Evidence viewer: paparan capture dengan petikan yang menyokong sesuatu label; beza author caption, customer comment dan inferens AI.
- Claim ledger: kenyataan, jenis fakta/classification/inference, supporting/contradicting evidence, reviewer dan status.
- Coverage matrix: persoalan bisnes yang sudah/belum boleh dijawab, missing evidence dan tindakan seterusnya.
- Entity review: sahkan akaun/jenama/produk/lokasi tanpa menggabungkan identiti secara automatik.
- Interview board: gap -> soalan -> jawapan pemilik -> bukti sokongan -> workflow -> requirement.

Jika fungsi soal jawab ditambah, jawapan perlu memetik evidence ID/URL dan menyatakan “belum cukup bukti” apabila sokongan tiada. Fakta dari laporan lama tidak boleh menjadi bukti kepada laporan baharu melalui kitaran rujukan.

## 10. Internal discovery dan calon MVP

Mulakan dengan satu contoh sebenar dari mula hingga selesai. Minta pemilik/pasukan menunjukkan dokumen atau rekod yang memang digunakan, kemudian sahkan peranan, langkah, keputusan, exception dan masalah yang berulang.

| Persoalan | Bukti yang diperlukan | Calon fungsi, jika disahkan |
|---|---|---|
| Bagaimana order diterima, disahkan dan ditutup? | Contoh order dan proses sebenar | Order register, status dan follow-up |
| Siapa memiliki stok di setiap lokasi/ejen? | Rekod keluar/terima/pulangan dan polisi | Stock movement serta reconciliation |
| Bagaimana lokasi/event dan crew disusun? | Jadual, pembahagian tugas, perubahan saat akhir | Event/crew scheduling |
| Bagaimana ejen dilantik dan restock? | Rekod permohonan, syarat dan contoh restock | Agent onboarding/restock |
| Bagaimana aduan dipadankan dengan produk/transaksi? | Aduan sebenar dan tindakan penyelesaian | Complaint case management |
| Di mana kerja manual paling banyak membuang masa? | Pemerhatian tugas dan tempoh kerja | Automasi satu workflow yang dipilih |

Jangan anggap semua modul perlu dibina. Pilih satu workflow berdasarkan kekerapan, kesan masalah, keyakinan bukti dan kos implementasi. Ukur keadaan sebelum dan selepas pilot; target angka ditetapkan selepas baseline diperoleh.

## 11. Urutan kerja praktikal seterusnya

1. Simpan baseline code dan data dengan manifest sebelum migration ID/hash.
2. Baiki gate integriti, collision ID, pemetaan record_kind, taxonomy UNKNOWN dan kontrak JEV.
3. Tambah regression tests bagi penemuan tersebut.
4. Rebuild normalized/BI/graph ke staging menggunakan bukti sedia ada; jangan recrawl sekadar untuk membaiki processing.
5. Banding kiraan, lineage dan perubahan label; aktifkan run baharu hanya setelah konsisten.
6. Sediakan evidence viewer dan claim ledger minimum.
7. Jalankan interview satu workflow sebenar sambil melengkapkan media/comments yang membantu persoalan itu.
8. Tulis PRD skop kecil yang dipautkan kepada bukti dan pengesahan pemilik; barulah implement pilot.

Tiada pembaikan kod dalam pelan ini telah dilaksanakan oleh review ini. Laporan ini ialah asas kerja yang boleh diteliti, bukannya pengesahan bahawa sistem atau Business OS sudah siap.
