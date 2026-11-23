# Dokumentasi Data Mentah Input Admin (`data/data-jadwal`)
**Program Studi Sistem dan Teknologi Informasi (STI)**

Folder ini berisi kumpulan **data mentah (raw input)** yang ditransformasikan dari jadwal riil semester sebelumnya (`jadwal_lengkap.csv`). Data ini merepresentasikan apa yang sebenarnya perlu disiapkan dan diinputkan oleh **Admin Program Studi** ke dalam sistem sebelum proses otomatisasi jadwal dijalankan.

---

## 1. Filosofi Pemisahan Data: Input vs Output

| Komponen | Status | Penjelasan |
|---|---|---|
| **Data Mentah (Input Admin)** | Disediakan Admin | Berisi **apa yang harus diajarkan**: Mata kuliah, Dosen pengampu, Kelas target, Tipe sesi (Teori/Praktikum), dan SKS. |
| **Variabel Keputusan (Output Sistem)** | Dihasilkan CP-SAT | Berisi **kapan & di mana**: Hari, Jam Mulai, Jam Selesai, dan Ruangan. Kolom ini dikosongkan/dihapus dari data mentah karena menjadi tugas solver untuk mengisinya tanpa bentrok. |

---

## 2. Struktur File Data Mentah

### A. `penugasan_pengampu.csv` (256 Baris) — *Core Scheduling Tasks*
Merupakan data penugasan mengajar (plotting dosen). Setiap baris adalah 1 sesi perkuliahan mingguan yang harus dicarikan slot waktu dan ruangannya oleh solver.

* **Kolom:**
  * `penugasan_id`: ID unik tugas (misal: `TSK001`, `TSK002`, ...)
  * `kode_mk`: Kode mata kuliah kurikulum (misal: `STI2541110`, `STI2543183`)
  * `nama_mk`: Nama mata kuliah
  * `semester`: Semester mata kuliah (1, 3, 5, 7)
  * `nama_kelas`: Kelas rombel target (misal: `1A`, `3B`, `5E`, `7D`)
  * `tipe_pertemuan`: `Teori` atau `Praktikum`
  * `sks`: Beban SKS sesi tersebut (1 SKS praktikum, 2 SKS teori, atau 3 SKS teori murni)
  * `dosen_pengampu`: Nama dosen yang ditugaskan mengajar
  * `kebutuhan_ruangan`: `Kelas Teori` atau `Kelas Praktikum` (menjadi constraint HC-05)

---

### B. `matakuliah_semester.csv` (38 Mata Kuliah) — *Curriculum Catalog*
Daftar seluruh mata kuliah yang ditawarkan pada semester aktif beserta rincian sks teori dan praktikum.

* **Kolom:** `kode_mk`, `nama_mk`, `sks_teori`, `sks_praktikum`, `total_sks`, `semester`

---

### C. `dosen_pengampu.csv` (39 Dosen) — *Faculty Registry*
Daftar seluruh dosen pengampu yang aktif mengajar di semester ini beserta rekapitulasi beban mengajar.

* **Kolom:**
  * `dosen_id`: ID dosen (`D001`, `D002`, ...)
  * `dosen_pengampu`: Nama lengkap beserta gelar
  * `total_sks`: Total beban SKS yang diampu dosen
  * `jumlah_kelas`: Total kelas rombel yang diajar

---

### D. `kelas_aktif.csv` (23 Kelas) — *Cohort Registry*
Daftar seluruh kelas mahasiswa aktif semester ini:
* **Semester 1**: 1A, 1B, 1C, 1D, 1E (5 kelas)
* **Semester 3**: 3A, 3B, 3C, 3D, 3E (5 kelas)
* **Semester 5**: 5A, 5B, 5C, 5D, 5E, 5F, 5G (7 kelas)
* **Semester 7**: 7A, 7B, 7C, 7D, 7E, 7F (6 kelas)

* **Kolom:** `semester`, `nama_kelas`, `total_sks_diambil`, `jumlah_pertemuan_minggu`

---

### E. `ruangan_tersedia.csv` (14 Ruangan) — *Physical Rooms*
Daftar ruangan milik fakultas/prodi yang dapat digunakan untuk alokasi jadwal.
* **9 Ruang Kelas Teori**: Gedung Teknik A (3A.1.08, 3A.1.09), Teknik C (3C.1.03, 3C.1.04, 3C.2.05, 3C.2.06, 3C.2.07, 3C.2.08), Teknik D (3D.3.15).
* **5 Ruang Laboratorium Komputer**: Artificial Intelligence LAB, Basic Computer LAB, Computer System LAB, Mobile Lab, Network Computer LAB.

* **Kolom:** `kode_ruangan`, `gedung`, `kategori`, `kapasitas`

---

### F. `arsip_jadwal_historis.csv` (256 Jadwal) — *Training Corpus for ML*
Salinan jadwal lengkap semester lalu yang mencakup penugasan slot hari, jam, dan ruangan. File ini digunakan sebagai **dataset pembelajaran (training set)** untuk **Machine Learning Lapis 2 (Random Forest)** guna menghasilkan *Warm-Start Hints* bagi solver CP-SAT.
