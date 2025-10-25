Youtube Link:   https://youtu.be/JfrSn3Igiuc

UJIAN TENGAH SEMESTER

Sistem Paralel dan Terdistribusi


Nama	: Tengku Rayhan Saputra

NIM	: 11221044

Kelas	: Sistem Paralel dan Terdistribusi B


T1 (Bab 1): Karakteristik Utama Sistem Terdistribusi dan Trade-off yang Umum pada Desain Pub-Sub Log Aggregator


    Karakteristik utama dari sistem terdistribusi, seperti yang dibahas dalam C&D (Bab 1) dan T&vS (Bab 1), adalah adanya beberapa komponen komputasi otonom (autonomous components) yang terhubung melalui jaringan dan berkoordinasi untuk tampil sebagai satu sistem koheren. Karakteristik utamanya meliputi:
    Konkurensi (Concurrency): Komponen-komponen dalam sistem dieksekusi secara paralel.
    Tidak Adanya Jam Global (No Global Clock): Terdapat batasan praktis pada akurasi sinkronisasi jam, yang menciptakan ketidakpastian dalam mengurutkan event.
    Kegagalan Independen (Independent Failures): Komponen dapat gagal secara independen, sehingga sistem harus mampu menangani kegagalan parsial ini (fault tolerance).
    Keterbukaan (Openness): C&D (Bab 1) juga menekankan Openness, di mana sistem dirancang menggunakan antarmuka standar yang memungkinkannya untuk diekstensi dan berinteroperasi.
    Pada desain Pub-Sub log aggregator, trade-off utamanya adalah antara Kinerja (Performance) vs. Keandalan (Reliability). Untuk reliability tinggi, broker harus menjamin persistence (menyimpan pesan ke disk) sebelum mengirim acknowledgment (ACK). Ini melindungi dari crash failure, namun menambah latency (karena disk I/O). Trade-off lainnya adalah Skalabilitas (Scalability). Arsitektur pub-sub secara inheren lebih skalabel daripada client-server dalam hal jumlah koneksi, tetapi broker itu sendiri bisa menjadi bottleneck yang memerlukan partisi.


T2 (Bab 2): Perbandingan Arsitektur Client-Server vs. Publish-Subscribe untuk aggregator. Kapan memilih Pub-Sub? Berikan alasan teknis. 


    C&D (Bab 2) mendefinisikan Client-Server sebagai arsitektur di mana proses dibagi menjadi dua peran: server (penyedia layanan) dan client (peminta layanan). Komunikasi bersifat request-response, seringkali sinkron, dan client harus mengetahui alamat server secara eksplisit. Ini adalah model yang tightly coupled.
    Publish-Subscribe, yang oleh C&D (Bab 6) dan T&vS (Bab 4) dikategorikan sebagai indirect communication atau message-queuing system, adalah arsitektur yang berpusat pada perantara (broker). Publisher mengirimkan event ke broker, dan Subscriber menerima event dari broker.
    Kapan memilih Pub-Sub? Pub-Sub ideal untuk log aggregator karena menyediakan decoupling (pemisahan) yang kuat, seperti yang diuraikan dalam T&vS (Bab 2) mengenai model arsitektur:
    Space Decoupling: Publisher dan subscriber tidak perlu saling tahu lokasinya.
    Time Decoupling: Publisher dan subscriber tidak harus berjalan pada waktu yang bersamaan. Broker akan menyimpan pesan (store-and-forward).
    Synchronization Decoupling: Publisher dapat mengirim pesan secara asinkron tanpa diblokir, meskipun subscriber sedang sibuk atau offline.
    Alasan teknis ini menjadikan log aggregator sangat skalabel dan tangguh (resilient). Layanan baru (publisher) dapat ditambahkan tanpa mengubah konfigurasi aggregator (subscriber).


T3 (Bab 3): Uraikan at-least-once vs exactly-once Delivery Semantics. Mengapa Idempotent Consumer krusial di presence of retries?


    Delivery semantics adalah jaminan yang diberikan oleh protokol komunikasi mengenai pengiriman pesan. Dalam konteks fault tolerance, C&D (Bab 15) dan T&vS (Bab 8) menguraikan dua jaminan utama:
    At-least-once: Sistem menjamin pesan akan terkirim, tetapi bisa saja terkirim lebih dari satu kali. Ini dicapai dengan mekanisme retry oleh pengirim jika acknowledgment (ACK) tidak diterima. Jika ACK-nya yang hilang, pengirim akan mengirim ulang, menyebabkan duplikasi.
    Exactly-once: Jaminan terkuat, di mana pesan dijamin terkirim dan diproses tepat satu kali. Ini sangat sulit dan mahal diimplementasikan.
    Idempotent Consumer Krusial Dalam sistem praktis, at-least-once adalah jaminan yang paling umum. T&vS (Bab 8) membahas ini dalam konteks Reliable Client-Server Communication. Karena at-least-once pasti menghasilkan duplikasi akibat retry, consumer harus idempoten. Sebuah operasi disebut idempoten jika menjalankannya berkali-kali memberikan hasil yang sama seperti menjalankannya satu kali. Consumer yang idempoten sangat krusial karena ia dapat memproses pesan duplikat tanpa merusak state sistem, biasanya dengan cara mendeteksi dan mengabaikan duplikat tersebut.


T4 (Bab 4): Rancang Skema penamaan untuk topic dan event_id (unik, collision-resistant). Jelaskan dampaknya terhadap dedup.


    Penamaan (naming), seperti yang dijelaskan dalam C&D (Bab 9) dan T&vS (Bab 5), adalah aspek krusial untuk menemukan dan mengidentifikasi entitas dalam sistem terdistribusi.
    1. Skema Penamaan topic
    Struktur: Gunakan skema hierarkis berbasis path-name, mirip dengan struktur direktori file yang dibahas di C&D (Bab 9).
    Format: /[environment]/[service_name]/[event_type] (Contoh: /prod/billing_service/payment_success).
    Keuntungan: Skema ini memungkinkan filtering berbasis wildcard (misalnya, berlangganan ke /prod/billing_service/*).
    2. Skema Penamaan event_id
    Tujuan: Harus berupa identifier yang unik secara global (globally unique). T&vS (Bab 5) menyebutnya sebagai Identifiers.
    Pilihan: Pilihan terbaik adalah UUID (Universally Unique Identifier), angka 128-bit yang probabilitas tabrakannya (dua event berbeda memiliki ID yang sama) sangat kecil.
    Dampak terhadap Deduplikasi (Dedup) Event_id yang unik adalah kunci untuk mencapai idempotency (T3) di sisi consumer. Consumer akan memelihara durable store (penyimpanan yang andal) berisi event_id yang telah berhasil diproses. Saat consumer menerima event, ia memeriksa event_id tersebut di store. Jika sudah ada, event tersebut adalah duplikat dan dibuang. Jika belum ada, event diproses, dan event_id-nya dicatat ke store. Tanpa event_id yang unik, deduplikasi tidak mungkin dilakukan.


T5 (Bab 5): Kapan total ordering tidak diperlukan? Usulkan pendekatan praktis (mis. Event timestamp + monotonic counter) dan batasannya.


    Total ordering, sebuah konsep yang dibahas dalam C&D (Bab 10) dan T&vS (Bab 6), adalah jaminan bahwa semua proses dalam sistem akan mengirimkan (menerima) semua pesan dalam urutan global yang sama persis. Ini sulit dicapai dan memerlukan algoritma konsensus.
    Kapan Total Ordering Tidak Diperlukan? Untuk log aggregator, total ordering seringkali tidak diperlukan. Log dari layanan yang berbeda (misal, service A dan service B) biasanya independen. Yang lebih penting adalah causal ordering (urutan sebab-akibat) atau per-source ordering, di mana event dari satu sumber producer diproses sesuai urutan terjadinya.
    Pendekatan Praktis dan Batasannya: Pendekatan praktis bisa menggunakan Logical Clocks (Jam Logis), seperti Lamport Timestamps yang diuraikan dalam T&vS (Bab 6). Namun, pendekatan yang lebih sederhana adalah:
    Event Timestamp (dari Jam Fisik): Setiap event diberi timestamp oleh producer.
    Monotonic Counter (per Producer): Setiap producer menyertakan sequence number (nomor urut) yang selalu naik.
    Batasan utamanya adalah clock skew, sebuah tantangan fundamental yang juga dibahas dalam C&D (Bab 10) mengenai Time and Global States. Jam fisik di host yang berbeda tidak pernah sinkron sempurna, sehingga timestamp fisik hanya baik untuk pengurutan perkiraan. Sequence number memberikan jaminan urutan yang kuat, tetapi hanya dalam lingkup satu producer.


T6 (Bab 6): identifikasi failure modes (duplikasi, out-of-order, crash) Jelaskan strategi mitigasi (retry, backoff, durable dedup store) 


    C&D (Bab 15) dan T&vS (Bab 8) mendefinisikan beberapa model kegagalan (failure modes) yang relevan:
    Crash Failure: Sebuah proses berhenti beroperasi secara tiba-tiba (fail-stop).
    Omission Failure: Sebuah proses atau saluran komunikasi gagal mengirim atau menerima pesan (misal, dropped packet).
    Timing Failure (terkait duplikasi & out-of-order): Respons tiba di luar interval waktu yang ditentukan. Pesan duplikat (T3) adalah akibat dari retry pada timeout yang prematur. Pesan out-of-order terjadi ketika pesan yang dikirim kemudian tiba lebih dulu.
    Strategi Mitigasi:
    Masking Crash/Omission Failures (Retry & Backoff): Untuk mengatasi kegagalan pengiriman sementara, pengirim (producer) menerapkan retry. Untuk mencegah badai retry (retry storm), digunakan Exponential Backoff: jeda waktu antar retry ditingkatkan secara eksponensial (misal, 1s, 2s, 4s).
    Masking Duplikasi (Durable Dedup Store): Seperti dibahas di T4, consumer yang idempoten menggunakan durable store untuk mencatat event_id.
    Masking Out-of-Order (Sequence Numbers): Consumer dapat menggunakan buffer dan sequence number (T5) untuk menyusun ulang pesan sebelum diproses.
    Strategi reliable communication ini dibahas mendalam di T&vS (Bab 8).


T7 (Bab 7): Definisikan Eventual Consistency pada aggregator; Jelaskan bagaimana idempotency + dedup membantu mencapai konsistensi


    Eventual Consistency (Konsistensi Pada Akhirnya), seperti yang dikategorikan dalam C&D (Bab 14) dan T&vS (Bab 7), adalah salah satu model konsistensi data-sentris (data-centric consistency model). Model ini menjamin bahwa jika tidak ada pembaruan baru, pada akhirnya semua replika (salinan) data akan konvergen ke nilai yang sama.
    Dalam konteks log aggregator, ini berarti storage akhir mungkin tidak langsung merefleksikan log yang baru saja dikirim (inconsistency window). Namun, sistem menjamin bahwa pada akhirnya, storage tersebut akan berisi satu salinan yang benar dari setiap log. Ini adalah trade-off yang diterima untuk mendapatkan availability dan performance yang tinggi, sebuah konsep inti dalam replication (T&vS, Bab 7).
    Bagaimana Idempotency + Dedup Membantu: Dalam sistem at-least-once (T3), duplikasi pesan tidak terhindarkan. Jika consumer tidak idempoten, replika data tidak akan pernah konvergen ke keadaan yang benar. Idempotency (yang dicapai melalui deduplikasi) adalah mekanisme yang memastikan konvergensi. Dengan menyaring duplikat, consumer memastikan setiap event logis hanya diproses satu kali, sehingga data store akhir akan mencapai keadaan yang konsisten (pada akhirnya).


T8 (Bab 1–7): Metrik Evaluasi Sistem (throughput, latency, duplicate rate) dan Kaitan ke Keputusan Desain


    Metrik utama untuk mengevaluasi log aggregator berfokus pada tujuan desain sistem terdistribusi, seperti yang ditetapkan dalam C&D (Bab 1) dan T&vS (Bab 1):
    Kinerja (Performance):
    Throughput: Jumlah event yang bisa diproses per detik.
    Latency: Waktu tunda dari event dikirim producer hingga siap di-query (sering diukur dalam p99 latency).
    Keandalan (Reliability & Correctness):
    Message Loss Rate: Persentase event yang gagal dikirim permanen (Idealnya 0%).
    Duplicate Rate: Persentase event yang diproses lebih dari sekali (Idealnya 0%).
    Skalabilitas (Scalability): Kemampuan sistem untuk menangani peningkatan beban dengan menambahkan hardware (horizontal scaling).
    Kaitan ke Keputusan Desain: Setiap keputusan desain adalah trade-off. Tantangan desain seperti Scalability dan Fault Tolerance ini adalah inti dari C&D (Bab 1).
    Keputusan: Menggunakan Pub-Sub (T2).
    Kaitan: Meningkatkan Skalabilitas dan Reliability (karena decoupling), tapi mungkin sedikit menambah Latency (karena broker).
    Keputusan: Menerapkan At-least-once (T3) dengan retries.
    Kaitan: Memberikan Reliability (mengurangi Message Loss Rate) dengan Throughput tinggi. Trade-off-nya adalah risiko Duplicate Rate, yang harus ditangani deduplikasi.
    Keputusan: Menerapkan Eventual Consistency (T7).
    Kaitan: Ini adalah trade-off untuk mendapatkan Throughput dan Availability yang tinggi, dengan menerima Latency konsistensi sesaat.


1. Deskripsi Proyek


proyek ini merupakan implementasi sistem Event Aggregator asynchronous berbasis FastAPI yang dikembangkan untuk demonstrasi konsep distributed systems dan event-driven architecture.
Sistem ini dirancang untuk menerima, memproses, dan menyimpan event dari berbagai sumber dengan pendekatan deduplication untuk memastikan tidak terjadi pemrosesan data duplikat.

Tujuan utama proyek ini adalah menunjukkan kemampuan integrasi teknologi modern seperti asynchronous I/O, queue-based processing, dan containerization dalam membangun sistem yang efisien, scalable, dan fault-tolerant.

2. Teknologi yang Digunakan


Teknologi	Deskripsi
FastAPI	Framework web modern berbasis Python untuk membangun RESTful API dengan performa tinggi
Uvicorn	ASGI server untuk menjalankan aplikasi FastAPI dengan dukungan asynchronous
aiosqlite	Library async untuk komunikasi non-blocking dengan SQLite
Pydantic	Validasi data menggunakan Python type hints
HTTPx	Async HTTP client yang digunakan untuk simulasi publisher event
Pytest	Framework pengujian untuk unit dan integration testing
Docker & Docker Compose	Containerization dan manajemen multi-service environment
SQLite	Database ringan untuk penyimpanan data deduplication


3. Arsitektur Sistem
a) Komponen Utama:

API Server (FastAPI) — Menerima event dari publisher.

Consumer Async (Queue Worker) — Memproses event secara asynchronous.

Deduplication Store (SQLite + aiosqlite) — Memeriksa dan menyimpan event unik.

Publisher Simulator (HTTPx) — Mengirim event simulasi ke endpoint /publish.

b) Alur Kerja Sistem:

Publisher mengirim event ke endpoint /publish.

API server menerima dan memvalidasi payload event menggunakan Pydantic.

Event diteruskan ke asynchronous queue (asyncio.Queue).

Consumer mengambil event dari queue dan melakukan pengecekan deduplication.

Jika event unik, data disimpan ke database; jika duplikat, dilewati.

Statistik event diperbarui dan dapat diakses melalui endpoint /stats.

4. Fitur Utama
a) Event Processing

Mendukung pengiriman single event dan batch event.

Validasi otomatis menggunakan Pydantic model.

Pemrosesan asynchronous dengan event queue.

b) Deduplication System

Setiap event memiliki event_id unik.

SQLite digunakan untuk menyimpan hash event yang sudah diproses.

Mencegah pengolahan event berulang.

c) Monitoring & Statistik

Endpoint /stats menampilkan:

Total event diterima

Event unik yang diproses

Event duplikat yang terdeteksi

Uptime sistem dan status consumer

5. API Endpoints
Endpoint	Method	Deskripsi
/publish	POST	Menerima event dari publisher
/events	GET	Mengambil daftar event yang sudah diproses
/stats	GET	Menampilkan statistik agregator

Contoh request ke /publish:

{
  "event_id": "12345",
  "topic": "sensor_data",
  "payload": {
    "temperature": 31.4,
    "humidity": 80
  }
}

6. Simulator Publisher

Simulator dikembangkan menggunakan HTTPx untuk:

Menghasilkan event dengan topik acak.

Mengirim event ke endpoint /publish.

Mengatur rasio duplikasi event untuk pengujian deduplication.

Menjalankan pengiriman event secara parallel (async).

Contoh eksekusi:

python publisher_simulator.py --events 5000 --duplicate 0.2


➡️ Menghasilkan 5.000 event total, dengan 20% event duplikat.

7. Containerization

Seluruh layanan dikemas dalam Docker menggunakan docker-compose.yml untuk kemudahan deployment.

Konfigurasi Docker:

Service:

aggregator → menjalankan FastAPI + consumer

publisher → simulasi pengirim event

Volume:

./data → menyimpan database SQLite

Environment Variables:

DB_PATH, API_PORT, DUP_RATE

Port Mapping:

8000:8000 untuk akses API server

Menjalankan proyek:

docker compose up --build

8. Performa dan Skalabilitas
a) Hasil Implementasi:

Simulator berhasil mengirim 5.000 event, dengan rasio duplikasi 20%.

Sistem berhasil mengidentifikasi dan mem-filter event duplikat.

Semua event unik disimpan dengan sukses ke database.

b) Analisis Performa:
Aspek	Observasi
Asynchronous Queue	Memastikan throughput tinggi dan non-blocking I/O
Deduplication Check	Beban tertinggi di SQLite write I/O
Response Time	Rata-rata < 30 ms untuk /publish
CPU Usage	Stabil di bawah 60% saat 5K event
Scalability	Dapat ditingkatkan dengan worker async tambahan
9. Testing dan Validasi
a) Unit Testing

Framework: pytest

Test case mencakup:

Publish event (single & batch)

Fetch /events

Validasi /stats

Integrasi queue dan deduplication

b) Area Pengujian yang Direkomendasikan

Health endpoint test

Stress test dengan 10.000 event

Deduplication edge-case (ID kosong, hash sama)

Latency measurement untuk batch besar

10. File requirements.txt

Berikut isi requirements.txt final yang sudah diperbaiki dan disederhanakan dari duplikasi:

fastapi>=0.95.0
uvicorn[standard]>=0.22.0
aiosqlite>=0.18.0
pydantic>=1.10.0
pytest>=7.0.0
httpx>=0.24.0

11. Referensi

Van Steen, M., & Tanenbaum, A. S. (2023). Distributed Systems (4th ed.). Maarten Van Steen.
https://distributed-systems.net/index.php/books/ds4/

FastAPI Documentation — https://fastapi.tiangolo.com

AsyncIO Documentation — https://docs.python.org/3/library/asyncio.html

SQLite & aiosqlite Documentation — https://aiosqlite.omnilib.dev/en/stable/