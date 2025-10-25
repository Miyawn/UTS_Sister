# UTS_Sister - Pub/Sub Log Aggregator

Small FastAPI-based Pub/Sub Log Aggregator menggunakan in-memory queue dan SQLite persistence untuk unique events.

`Dockerfile` & `docker-compose.yml` untuk dijalankan secara lokal di Docker. untuk development Docker didalam Kali VM (VirtualBox), menggunakan Bridged Networking.

### Tujuan
```
Mengeksekusi agregator log berbasis FastAPI yang mengonsumsi event melalui in-memory queue (asyncio.Queue) dan menyimpan event unik ke basis data SQLite.
```

### Fitur Utama
**Deduplikasi:** Menggunakan batasan `UNIQUE(topic, event_id)` pada SQLite untuk memastikan setiap event hanya diproses sekali.

* **Endpoint `/publish`:** Menerima event tunggal atau batch (array) event.
* **Endpoint `/events`:** Mengambil daftar event yang sudah diproses.
* **Endpoint `/stats:`** Menampilkan statistik agregator (total diterima, unik, duplikat).

### Panduan Pembangunan & Eksekusi (Lingkungan Kali VM - Bash)
Dokumen ini menjelaskan langkah-langkah untuk membangun dan menjalankan aplikasi menggunakan Docker secara lokal.

1) Prepare data dir (persistence):

Buat direktori `data` yang akan digunakan untuk menyimpan basis data SQLite, lalu ubah kepemilikan agar dapat diakses oleh container.
```bash
mkdir -p data
chown $USER:$USER data
```

2) Build image:

Bangun image Docker dan berikan tag `uts-aggregator`.
```bash
docker build -t uts-aggregator .
```

3) Run container (mount data and set DB path):

Jalankan container dengan mem-mount direktori `data` lokal ke dalam container dan menentukan path basis data melalui environment variable.
```bash
docker run --rm -p 8080:8080 \
	-v "$(pwd)/data":/app/data \
	-e DEDUP_DB=/app/data/dedup_store.db \
	uts-aggregator
```

4) Quick test endpoints:

Setelah container berjalan, Anda dapat menguji endpoint menggunakan alat seperti `curl` atau Postman:

* `POST /publish` $\rightarrow$ Kirim event tunggal atau array event.
* `GET /events?topic=topic-1` $\rightarrow$ Ambil event berdasarkan topik.
* `GET /stats` $\rightarrow$ Ambil statistik sistem.


Gunakan metode ini untuk menjalankan `Aggregator` dan `Publisher` Simulator sekaligus.

```bash
docker compose up --build
```

### Catatan dan Asumsi Penting
**Path SQLite DB:** Path ke basis data SQLite dikontrol oleh environment variable `DEDUP_DB`. Nilai default-nya adalah `log_store.db` jika variabel tidak diatur.

**Sistem Berkas (Filesystem):** Pastikan proyek dan direktori `data/` berada di dalam filesystem VM (bukan shared mount dari Windows) untuk menghindari masalah locking dan performa SQLite.

**Pengembangan:** Untuk alur kerja yang optimal saat mengedit kode, disarankan menggunakan **Remote-SSH** ke Kali VM.

