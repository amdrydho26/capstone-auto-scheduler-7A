# Automated University Course Scheduling System (Backend & Model)
### Program Studi Sistem dan Teknologi Informasi (STI) — Capstone Project

Repository ini berisi **mesin inti optimasi penjadwalan kuliah otomatis** dan **layanan backend API** menggunakan pendekatan hibrida: **Machine Learning (TF-IDF + Cosine Clustering + NLP Lab Affinity)** dan **Google OR-Tools CP-SAT Solver (Constraint Programming over Finite Domains)**.

---

## 🚀 Fitur Unggulan Sistem

1. **Auto-Split Sesi Teori & Praktikum**:
   - Program studi cukup menginput **164 rombel kelas** (1 baris per kelas pada `Template_Input_Jadwal_Prodi.xlsx`).
   - Sistem secara otomatis memecahnya menjadi **256 sesi perkuliahan** (164 sesi teori di ruang kelas dan 92 sesi praktikum di laboratorium komputer).
2. **Machine Learning Lapis 1 (Clustering Mata Kuliah Pilihan)**:
   - Mengelompokkan 15 mata kuliah pilihan kurikulum ke dalam klaster peminatan tematik (*AI & Vision*, *Cyber Security & Network*, *Software Engineering*, dll.) untuk meminimalkan potensi bentrok mata kuliah serumpun.
3. **Penentuan Laboratorium Otomatis (NLP Lab Affinity)**:
   - Model secara cerdas menganalisis nama dan topik mata kuliah untuk menempatkannya langsung ke laboratorium spesialisasi yang tepat (*Network Computer LAB*, *AI LAB*, *Mobile Lab*, *Computer System LAB*, atau *Basic Computer LAB*).
   - Efektivitas penempatan mencapai **83.7%** dengan mekanisme *dynamic fallback* agar kapasitas lab seimbang.
4. **Hard Constraint Ketersediaan Waktu Dosen (HC-09)**:
   - Dosen yang memiliki tugas struktural atau dinas luar pada hari/jam tertentu dijamin 100% tidak akan dijadwalkan pada waktu tersebut.
5. **Dekomposisi Interval Atomik Non-Overlapping**:
   - Pemodelan matematika interval atomik menjamin **100% Zero-Conflict** tanpa adanya tabrakan menit kuliah pada variasi durasi 100 menit (1-2 SKS), 150 menit (3 SKS), maupun 200 menit (4 SKS).
6. **Independent Zero-Conflict Constraint Auditor**:
   - Melakukan audit independen terhadap seluruh 9 Hard Constraints (HC-00 s/d HC-09) sebelum jadwal dinyatakan valid.
7. **Multi-Sheet Professional Excel Export**:
   - Menghasilkan laporan jadwal lengkap, jadwal per kelas mahasiswa, jadwal per ruangan, dan ringkasan metrik eksekutif.

---

## 📁 Struktur Direktori Repositori

```text
.
├── model-penjadwalan/                    # Engine Model Penjadwalan Inti
│   ├── data/
│   │   └── Template_Input_Jadwal_Prodi.xlsx  # 1 File Master Excel Input Prodi (5 Sheet)
│   ├── output/
│   │   └── jadwal_kuliah_optimal.xlsx        # Hasil Excel Jadwal Kuliah Optimal
│   ├── src/
│   │   ├── data_loader.py                    # Parser data Excel & auto-split penugasan
│   │   ├── ml_clustering.py                  # ML Semantic Clustering MK Pilihan
│   │   ├── cp_sat_solver.py                  # Google OR-Tools CP-SAT Solver
│   │   ├── constraint_auditor.py             # Auditor independen penjamin Zero-Conflict
│   │   └── excel_exporter.py                 # Multi-sheet Excel Generator
│   ├── run_scheduler.py                      # CLI Runner Eksekusi Sistem
│   ├── run.ps1 / run.bat                     # Shortcut Runner sekali klik
│   └── README.md                             # Dokumentasi model penjadwalan
├── code/
│   └── backend/                              # Layanan REST API (FastAPI)
│       ├── app/                              # Endpoint API & Integrasi Layanan
│       ├── requirements.txt                  # Dependensi Python
│       └── Dockerfile                        # Konfigurasi Container Backend
├── docs/                                     # Dokumen proposal & referensi kurikulum
├── .gitignore                                # Filter file lokal & virtual environment
└── README.md                                 # Dokumentasi utama repositori
```

---

## 🛠️ Panduan Instalasi & Eksekusi

### 1. Kebutuhan Sistem
- Python 3.10+ (Direkomendasikan Python 3.11 atau 3.12)
- Git

### 2. Setup Virtual Environment
```bash
# Buat virtual environment
python -m venv venv

# Aktivasi virtual environment
# Di Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Di Linux / macOS:
source venv/bin/activate

# Install dependensi
pip install -r code/backend/requirements.txt
```

### 3. Menjalankan Engine Model Penjadwalan (CLI)
```bash
# Jalankan langsung script runner:
python model-penjadwalan/run_scheduler.py
```
*Hasil optimasi dan jadwal lengkap akan langsung disimpan di folder `model-penjadwalan/output/jadwal_kuliah_optimal.xlsx`.*

---

## 👥 Tim Pengembang (Capstone Project)
- **Backend & AI/Optimization Engine**: Sistem dan Teknologi Informasi (STI)
- **Frontend Web Application**: Tim Kolaborator Frontend (Repository Terpisah)
