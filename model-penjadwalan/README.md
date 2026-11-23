# Backend & Model Penjadwalan Mata Kuliah Otomatis (Hybrid ML + CP-SAT)

Sistem penjadwalan otomatis Program Studi Sistem dan Teknologi Informasi (STI) berbasis **Machine Learning (Semantic Clustering & NLP Lab Affinity)** dan **Google OR-Tools CP-SAT Solver**.

---

## 1. Satu-Satunya File Input Prodi

Prodi **TIDAK PERLU** lagi menyiapkan file CSV yang terpisah-pisah. Seluruh data perkuliahan, kurikulum, dosen, ruangan, dan kendala khusus terangkum dalam **1 file Master Excel**:

📁 **`model-penjadwalan/data/Template_Input_Jadwal_Prodi.xlsx`**

Di dalam file Excel tersebut terdapat 5 sheet:
1. **`1. Penugasan Semester`** *(Satu-satunya sheet yang diedit prodi tiap semester baru - Hanya 5 kolom dasar!)*:
   - `Kode MK`, `Nama Mata Kuliah`, `Semester`, `Kelas`, `Dosen Pengampu`.
2. **`2. Master Kurikulum MK`** *(Data acuan 38 mata kuliah kurikulum - Jarang berubah)*:
   - `Kode MK`, `Nama Mata Kuliah`, `SKS Teori`, `SKS Praktikum`, `Total SKS`, `Tipe MK` (Wajib/Pilihan).
3. **`3. Dosen Berhalangan`** *(Aturan waktu dosen berhalangan mengajar - Hard Constraint HC-09)*:
   - `Nama Lengkap Dosen`, `Hari Berhalangan`, `Jam Mulai`, `Jam Selesai`, `Keterangan`.
4. **`4. Master Ruangan & Lab`** *(Daftar 9 kelas teori dan 5 lab komputer)*:
   - `Kode Ruangan`, `Gedung`, `Kategori Ruangan`.
5. **`5. Blokir Ruang Bersama`** *(Jadwal ruangan yang dipakai prodi lain / Shared Rooms)*:
   - `Kode Ruangan`, `Hari`, `Jam Mulai`, `Jam Selesai`, `Keterangan`.

---

## 2. Cara Kerja Cerdas Sistem

* **Auto-Split Teori & Praktikum**: Prodi cukup menginput 164 rombel kelas. Sistem otomatis melipatgandakan mata kuliah yang memiliki praktikum menjadi 256 sesi.
* **Penentuan Lab Otomatis oleh Model**: Model NLP menganalisis nama mata kuliah dan topik silabus untuk menempatkan praktikum ke laboratorium spesialisasi yang tepat (*AI Lab*, *Network Lab*, *Mobile Lab*, *Computer System Lab*, *Basic Lab*).
* **Hard Constraint Kepatuhan Dosen (HC-09)**: Dosen yang berhalangan di hari/jam tertentu dijamin 100% tidak akan dijadwalkan di waktu tersebut.

---

## 3. Cara Menjalankan Eksekusi di Terminal

```powershell
& "code/backend/venv/Scripts/python" "model-penjadwalan/run_scheduler.py"
```

---

## 4. Hasil Luaran Jadwal

Hasil jadwal otomatis disimpan dalam format Excel profesional di:
📁 **`model-penjadwalan/output/jadwal_kuliah_optimal.xlsx`**
(Terdiri dari sheet: *Jadwal Keseluruhan*, *Jadwal per Kelas*, *Jadwal per Ruangan*, dan *Ringkasan & Metrik Zero-Conflict*).
