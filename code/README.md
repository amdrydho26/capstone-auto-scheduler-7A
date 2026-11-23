# Sistem Penjadwalan Mata Kuliah Otomatis (AutoScheduler STI)
**Capstone Project - Program Studi Sistem dan Teknologi Informasi**

Sistem penjadwalan mata kuliah otomatis berbasis **Hybrid Machine Learning (Course Semantic Clustering & Pattern Learning)** dan **Google OR-Tools CP-SAT Solver**.

---

## Struktur Folder `code/`

```
code/
├── backend/                       # Backend FastAPI + OR-Tools + Scikit-Learn
│   ├── app/
│   │   ├── api/                   # REST API Endpoints (Courses, Schedules, ML, dll)
│   │   ├── core/                  # Database & App Configuration
│   │   ├── ml/                    # ML Lapis 1 (Semantic Clustering) & Lapis 2 (Pattern Learner)
│   │   ├── models/                # SQLAlchemy Database Models
│   │   ├── schemas/               # Pydantic Schemas
│   │   ├── services/              # CSV Data Seeder & Exporter (Excel/PDF)
│   │   ├── solver/                # Google OR-Tools CP-SAT Optimization Solver
│   │   └── main.py                # FastAPI Application Entrypoint
│   ├── requirements.txt           # Python Dependencies
│   ├── test_system.py             # Script pengujian komprehensif
│   └── Dockerfile
├── frontend/                      # Frontend Dashboard (React + Vite + TailwindCSS)
│   ├── src/
│   │   ├── components/            # UI Components (Navbar, Cards, Modals)
│   │   ├── pages/                 # Dashboard, ScheduleGrid, MLInsights, DataMaster
│   │   ├── services/              # API Client (Axios)
│   │   └── types/                 # TypeScript Interfaces
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml             # Orkestrasi Docker (PostgreSQL, Backend, Frontend)
```

---

## Cara Menjalankan Sistem

### 1. Menjalankan Backend (Python FastAPI)

1. Masuk ke direktori backend:
   ```powershell
   cd "code/backend"
   ```

2. Aktifkan virtual environment yang sudah dibuat:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. Jalankan server backend (FastAPI):
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```
   * Backend API berjalan di: `http://localhost:8000`
   * Dokumentasi Swagger UI: `http://localhost:8000/docs`
   * Saat pertama kali dijalankan, sistem otomatis melakukan seed data dari folder `data/` (41 dosen, 38 MK, 14 ruangan, 23 kelas, 50 slot waktu).

4. (Opsional) Menjalankan Test Komprehensif:
   ```powershell
   python test_system.py
   ```

---

### 2. Menjalankan Frontend (React + Vite)

1. Masuk ke direktori frontend:
   ```powershell
   cd "code/frontend"
   ```

2. Jalankan development server:
   ```powershell
   npm run dev
   ```
   * Frontend Web UI berjalan di: `http://localhost:5173`

---

### 3. Menjalankan Menggunakan Docker Compose (Production Ready)

Jika ingin menjalankan seluruh sistem (Database PostgreSQL, Backend, dan Frontend) dalam kontainer terisolasi:

```powershell
cd "code"
docker-compose up --build -d
```

---

## Fitur Utama yang Sudah Diimplementasikan

1. **Google OR-Tools CP-SAT Solver**:
   * Menjamin **0 Hard Constraint Violations** (HC-01 bentrok dosen, HC-02 bentrok ruangan, HC-03 bentrok kelas, HC-04 kapasitas, HC-05 jenis lab vs teori, HC-06 durasi SKS, HC-07 batas istirahat).
2. **Machine Learning Lapis 1 (Course Semantic Clustering)**:
   * Mengelompokkan mata kuliah pilihan ke ranah peminatan (AI, Cyber Security, Software Engineering, dll) menggunakan TF-IDF + Agglomerative Clustering + Silhouette Score.
   * Menghasilkan *Conflict Weight Matrix* yang diteruskan ke soft constraints CP-SAT untuk memisahkan jadwal MK yang sering diambil mahasiswa secara bersamaan.
3. **Machine Learning Lapis 2 (Warm-Start Hints)**:
   * Menggunakan Random Forest Classifier untuk memprediksi rekomendasi slot & ruangan awal ke solver.
4. **Interactive Timetable Grid & Conflict Validator**:
   * Melihat jadwal mingguan per Kelas, per Dosen, atau per Ruangan.
   * Drag & drop / edit manual dengan validasi bentrok real-time.
5. **Export Dokumen Resmi**:
   * Unduh jadwal dalam format Excel (`.xlsx`) via openpyxl dan cetak PDF (`.pdf`) via ReportLab.
