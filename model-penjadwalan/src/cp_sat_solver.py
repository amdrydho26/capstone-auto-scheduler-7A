import time
from typing import Dict, List, Any, Tuple
from ortools.sat.python import cp_model


class CPSATScheduler:
    """
    CP-SAT Optimization Engine untuk Penjadwalan Mata Kuliah Otomatis.
    Menggunakan Google OR-Tools CP-SAT Solver dengan pemodelan interval atomik
    untuk menjamin zero-conflict pada Dosen, Ruangan, dan Kelas.
    """

    def __init__(
        self,
        data: Dict[str, Any],
        conflict_weights: Dict[Tuple[str, str], float] = None,
        max_time_seconds: int = 60,
    ):
        self.tasks = data["tasks"]
        self.rooms = data["rooms"]
        self.timeslots = data["timeslots"]
        self.courses = data.get("courses", [])
        self.lecturers = data.get("lecturers", [])
        self.classes = data.get("classes", [])
        self.room_blocks = data.get("room_blocks", [])
        self.lecturer_unavailability = data.get("lecturer_unavailability", [])
        self.conflict_weights = conflict_weights or {}
        self.max_time_seconds = max_time_seconds

        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = float(max_time_seconds)
        self.solver.parameters.num_search_workers = 8
        self.solver.parameters.log_search_progress = False

        # Preprocessing lookup tables
        self._time_to_minutes_cache = {}
        self.days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
        self.day_order = {d: i for i, d in enumerate(self.days)}

    def _to_minutes(self, time_str: str) -> int:
        if time_str not in self._time_to_minutes_cache:
            parts = time_str.split(":")
            self._time_to_minutes_cache[time_str] = int(parts[0]) * 60 + int(parts[1])
        return self._time_to_minutes_cache[time_str]

    def _build_atomic_intervals(self) -> Dict[str, List[Tuple[int, int, List[int]]]]:
        """
        Membagi waktu tiap hari menjadi interval atomik non-overlapping terkecil.
        Mengembalikan: {hari: [(start_min, end_min, [slot_id, ...]), ...]}
        """
        day_atomic: Dict[str, List[Tuple[int, int, List[int]]]] = {}

        for day in self.days:
            day_slots = [s for s in self.timeslots if s["hari"] == day]
            # Kumpulkan semua waktu transisi (start dan end)
            timestamps = set()
            for s in day_slots:
                timestamps.add(self._to_minutes(s["jam_mulai"]))
                timestamps.add(self._to_minutes(s["jam_selesai"]))

            sorted_ts = sorted(list(timestamps))
            intervals = []
            for i in range(len(sorted_ts) - 1):
                t_start = sorted_ts[i]
                t_end = sorted_ts[i + 1]
                # Cari slot yang meng-cover interval ini
                covering_slots = []
                for s in day_slots:
                    s_start = self._to_minutes(s["jam_mulai"])
                    s_end = self._to_minutes(s["jam_selesai"])
                    if s_start <= t_start and s_end >= t_end:
                        covering_slots.append(s["id"])

                if covering_slots:
                    intervals.append((t_start, t_end, covering_slots))

            day_atomic[day] = intervals

        return day_atomic

    def _is_room_blocked(self, room_code: str, slot: Dict[str, Any]) -> bool:
        """Cek apakah ruangan diblokir pada hari dan jam slot tersebut."""
        s_start = self._to_minutes(slot["jam_mulai"])
        s_end = self._to_minutes(slot["jam_selesai"])

        for block in self.room_blocks:
            if block["kode_ruangan"] == room_code and block["hari"] == slot["hari"]:
                b_start = self._to_minutes(block["jam_mulai"])
                b_end = self._to_minutes(block["jam_selesai"])
                # Overlap check
                if s_start < b_end and b_start < s_end:
                    return True
        return False

    def _is_lecturer_unavailable(self, lecturer_name: str, slot: Dict[str, Any]) -> bool:
        """Cek apakah dosen berhalangan hadir pada hari dan jam slot tersebut (HC-09)."""
        s_start = self._to_minutes(slot["jam_mulai"])
        s_end = self._to_minutes(slot["jam_selesai"])

        for block in self.lecturer_unavailability:
            if block["nama_dosen"] == lecturer_name and block["hari"] == slot["hari"]:
                b_start = self._to_minutes(block["jam_mulai"])
                b_end = self._to_minutes(block["jam_selesai"])
                if s_start < b_end and b_start < s_end:
                    return True
        return False

    def solve(self) -> Dict[str, Any]:
        """
        Membangun model CP-SAT dan mengeksekusi pencarian solusi optimal.
        """
        start_time = time.time()
        atomic_intervals = self._build_atomic_intervals()

        # -------------------------------------------------------------
        # 1. GENERATE DECISION VARIABLES (Pruning terintegrasi)
        # -------------------------------------------------------------
        # X[t_id, s_id, r_id] = 1 jika task t ditempatkan pada slot s dan ruangan r
        X = {}
        task_vars: Dict[int, List[Any]] = {t["id"]: [] for t in self.tasks}
        task_slot_vars: Dict[Tuple[int, int], Any] = {}  # (t_id, s_id) -> bool_var

        # Lookup pembantu
        room_by_id = {r["id"]: r for r in self.rooms}
        slot_by_id = {s["id"]: s for s in self.timeslots}

        for t in self.tasks:
            t_id = t["id"]
            t_sks = t["sks"]
            dosen = t["dosen_pengampu"]
            is_praktikum = t["tipe_pertemuan"].lower() == "praktikum"

            # 1. Filter candidate slots (HC-06 SKS Duration & HC-09 Lecturer Availability)
            candidate_slots = [
                s for s in self.timeslots
                if (t_sks in s["sks_match"]) and not self._is_lecturer_unavailable(dosen, s)
            ]

            # 2. Filter candidate rooms (HC-05: Praktikum di Lab, Teori di Ruang Teori)
            candidate_rooms = [
                r for r in self.rooms
                if (r["is_lab"] if is_praktikum else not r["is_lab"])
            ]

            for s in candidate_slots:
                s_id = s["id"]
                s_vars_for_task = []

                for r in candidate_rooms:
                    r_id = r["id"]

                    # HC-02 / Room Blockade pruning
                    if self._is_room_blocked(r["kode_ruangan"], s):
                        continue

                    # Valid assignment variable
                    var = self.model.NewBoolVar(f"x_t{t_id}_s{s_id}_r{r_id}")
                    X[(t_id, s_id, r_id)] = var
                    task_vars[t_id].append(var)
                    s_vars_for_task.append(var)

                if s_vars_for_task:
                    # Slot-level indicator for task: task_slot[t_id, s_id] = sum(X[t_id, s_id, r])
                    t_s_var = self.model.NewBoolVar(f"ts_t{t_id}_s{s_id}")
                    self.model.Add(sum(s_vars_for_task) == t_s_var)
                    task_slot_vars[(t_id, s_id)] = t_s_var

        # -------------------------------------------------------------
        # 2. HARD CONSTRAINTS
        # -------------------------------------------------------------

        # HC-00: Setiap task harus dijadwalkan tepat 1 kali
        for t in self.tasks:
            t_id = t["id"]
            vars_for_t = task_vars[t_id]
            if not vars_for_t:
                return {
                    "status": "INFEASIBLE",
                    "message": f"Task ID {t_id} ({t['nama_mk']} - {t['nama_kelas']}) tidak memiliki kombinasi slot/ruangan yang valid.",
                    "solve_time_seconds": round(time.time() - start_time, 2),
                    "assignments": [],
                }
            self.model.Add(sum(vars_for_t) == 1)

        # HC-02: Konflik Ruangan via Atomic Interval
        # Di setiap ruangan dan tiap interval atomik, maksimal 1 task aktif
        for r in self.rooms:
            r_id = r["id"]
            for day, intervals in atomic_intervals.items():
                for t_start, t_end, covering_slot_ids in intervals:
                    active_vars = []
                    for t in self.tasks:
                        t_id = t["id"]
                        for s_id in covering_slot_ids:
                            if (t_id, s_id, r_id) in X:
                                active_vars.append(X[(t_id, s_id, r_id)])
                    if len(active_vars) > 1:
                        self.model.Add(sum(active_vars) <= 1)

        # HC-01: Konflik Dosen via Atomic Interval
        # Seorang dosen tidak boleh mengajar lebih dari 1 kelas pada interval atomik yang sama
        lecturer_tasks: Dict[str, List[int]] = {}
        for t in self.tasks:
            dosen = t["dosen_pengampu"]
            if dosen not in lecturer_tasks:
                lecturer_tasks[dosen] = []
            lecturer_tasks[dosen].append(t["id"])

        for dosen, t_ids in lecturer_tasks.items():
            if len(t_ids) <= 1:
                continue
            for day, intervals in atomic_intervals.items():
                for t_start, t_end, covering_slot_ids in intervals:
                    active_vars = []
                    for t_id in t_ids:
                        for s_id in covering_slot_ids:
                            if (t_id, s_id) in task_slot_vars:
                                active_vars.append(task_slot_vars[(t_id, s_id)])
                    if len(active_vars) > 1:
                        self.model.Add(sum(active_vars) <= 1)

        # HC-03: Konflik Kelas Mahasiswa via Atomic Interval
        # Satu kelas (misal: 1A, 3B, 5C) tidak boleh memiliki 2 jadwal kuliah pada interval yang sama
        class_tasks: Dict[str, List[int]] = {}
        for t in self.tasks:
            cls = t["nama_kelas"]
            if cls not in class_tasks:
                class_tasks[cls] = []
            class_tasks[cls].append(t["id"])

        for cls, t_ids in class_tasks.items():
            if len(t_ids) <= 1:
                continue
            for day, intervals in atomic_intervals.items():
                for t_start, t_end, covering_slot_ids in intervals:
                    active_vars = []
                    for t_id in t_ids:
                        for s_id in covering_slot_ids:
                            if (t_id, s_id) in task_slot_vars:
                                active_vars.append(task_slot_vars[(t_id, s_id)])
                    if len(active_vars) > 1:
                        self.model.Add(sum(active_vars) <= 1)

        # -------------------------------------------------------------
        # 3. SOFT CONSTRAINTS (Objective Function)
        # -------------------------------------------------------------
        objective_terms = []

        # SC-08: Hindari bentrok mata kuliah pilihan serumpun (ML Clustering)
        # Jika dua MK pilihan memiliki bobot kemiripan tinggi, beri penalti jika dijadwalkan pada waktu bersamaan
        if self.conflict_weights:
            elective_tasks = [t for t in self.tasks if "pilihan" in t.get("tipe_mk", "").lower() or t["semester"] in (5, 7)]
            elective_pairs = []
            n_elec = len(elective_tasks)
            for i in range(n_elec):
                for j in range(i + 1, n_elec):
                    t1, t2 = elective_tasks[i], elective_tasks[j]
                    if t1["kode_mk"] != t2["kode_mk"] and t1["semester"] == t2["semester"]:
                        k_pair = (min(t1["kode_mk"], t2["kode_mk"]), max(t1["kode_mk"], t2["kode_mk"]))
                        weight = self.conflict_weights.get(k_pair, 0.0)
                        if weight >= 0.5:
                            elective_pairs.append((t1["id"], t2["id"], weight))

            for t1_id, t2_id, weight in elective_pairs:
                for day, intervals in atomic_intervals.items():
                    for _, _, covering_slot_ids in intervals:
                        slots_1 = [task_slot_vars[(t1_id, sid)] for sid in covering_slot_ids if (t1_id, sid) in task_slot_vars]
                        slots_2 = [task_slot_vars[(t2_id, sid)] for sid in covering_slot_ids if (t2_id, sid) in task_slot_vars]
                        if slots_1 and slots_2:
                            clash_var = self.model.NewBoolVar(f"ml_clash_{t1_id}_{t2_id}_{day}")
                            # clash_var >= sum(slots_1) + sum(slots_2) - 1
                            self.model.Add(clash_var >= sum(slots_1) + sum(slots_2) - 1)
                            penalty = int(weight * 50)
                            objective_terms.append(penalty * clash_var)

        # SC-01: Distribusi Beban Kelas per Hari (Maksimal 3 kuliah per hari disukai)
        for cls, t_ids in class_tasks.items():
            for day in self.days:
                day_slot_ids = [s["id"] for s in self.timeslots if s["hari"] == day]
                class_day_vars = []
                for t_id in t_ids:
                    for s_id in day_slot_ids:
                        if (t_id, s_id) in task_slot_vars:
                            class_day_vars.append(task_slot_vars[(t_id, s_id)])
                if len(class_day_vars) > 3:
                    overload_var = self.model.NewIntVar(0, 10, f"overload_{cls}_{day}")
                    self.model.Add(overload_var >= sum(class_day_vars) - 3)
                    objective_terms.append(15 * overload_var)

        # SC-03: Penalti ringan untuk jadwal Jumat Siang (preferensi kenyamanan ibadah & akhir pekan)
        jumat_siang_slots = [
            s["id"] for s in self.timeslots
            if s["hari"] == "Jumat" and s["sesi"] == "siang"
        ]
        for s_id in jumat_siang_slots:
            for t in self.tasks:
                t_id = t["id"]
                if (t_id, s_id) in task_slot_vars:
                    objective_terms.append(2 * task_slot_vars[(t_id, s_id)])

        # SC-04: Preferensi Ruangan Lab Ditentukan Model (Intelligent Lab Affinity Matching)
        # Memberikan penalti jika praktikum ditempatkan di luar lab preferensi model, sehingga solver
        # memprioritaskan lab ideal (misal: AI Lab untuk MK AI, Network Lab untuk MK Jaringan),
        # namun tetap mengizinkan fallback fleksibel bila lab tersebut penuh di jam tersebut.
        for t in self.tasks:
            if t["tipe_pertemuan"].lower() == "praktikum":
                t_id = t["id"]
                pref_lab = t.get("preferensi_lab", "-")
                if pref_lab and pref_lab != "-":
                    for s in self.timeslots:
                        s_id = s["id"]
                        for r in self.rooms:
                            r_id = r["id"]
                            if (t_id, s_id, r_id) in X:
                                if r["kode_ruangan"] != pref_lab:
                                    # Penalti jika tidak cocok dengan preferensi model
                                    objective_terms.append(10 * X[(t_id, s_id, r_id)])

        # Minimalkan total penalti objektif
        if objective_terms:
            self.model.Minimize(sum(objective_terms))

        # -------------------------------------------------------------
        # 4. SOLVE MODEL
        # -------------------------------------------------------------
        status_code = self.solver.Solve(self.model)
        solve_time = time.time() - start_time

        status_map = {
            cp_model.OPTIMAL: "OPTIMAL",
            cp_model.FEASIBLE: "FEASIBLE",
            cp_model.INFEASIBLE: "INFEASIBLE",
            cp_model.MODEL_INVALID: "MODEL_INVALID",
            cp_model.UNKNOWN: "UNKNOWN",
        }
        status_str = status_map.get(status_code, "UNKNOWN")

        if status_str not in ("OPTIMAL", "FEASIBLE"):
            return {
                "status": status_str,
                "message": f"Solver gagal menemukan solusi ({status_str}).",
                "solve_time_seconds": round(solve_time, 2),
                "assignments": [],
                "statistics": {
                    "total_variables": len(X),
                    "total_constraints": len(self.model.Proto().constraints),
                }
            }

        # -------------------------------------------------------------
        # 5. EKSTRAKSI HASIL JADWAL
        # -------------------------------------------------------------
        assignments = []
        for (t_id, s_id, r_id), var in X.items():
            if self.solver.Value(var) == 1:
                task = self.tasks[t_id]
                slot = slot_by_id[s_id]
                room = room_by_id[r_id]

                is_prak = task["tipe_pertemuan"].lower() == "praktikum"
                pref_lab = task.get("preferensi_lab", "-")

                assignments.append({
                    "task_id": t_id,
                    "penugasan_id": task["penugasan_id"],
                    "kode_mk": task["kode_mk"],
                    "nama_mk": task["nama_mk"],
                    "semester": task["semester"],
                    "nama_kelas": task["nama_kelas"],
                    "tipe_pertemuan": task["tipe_pertemuan"],
                    "sks": task["sks"],
                    "dosen_pengampu": task["dosen_pengampu"],
                    "hari": slot["hari"],
                    "jam_mulai": slot["jam_mulai"],
                    "jam_selesai": slot["jam_selesai"],
                    "durasi_menit": slot["durasi_menit"],
                    "sesi": slot["sesi"],
                    "kode_ruangan": room["kode_ruangan"],
                    "gedung": room["gedung"],
                    "kategori_ruangan": room["kategori"],
                    "kapasitas_ruangan": room["kapasitas"],
                    "preferensi_lab": pref_lab,
                    "lab_matched": (room["kode_ruangan"] == pref_lab) if is_prak else True,
                })

        # Urutkan jadwal secara kronologis: Hari -> Jam Mulai -> Ruangan
        assignments.sort(key=lambda a: (
            self.day_order.get(a["hari"], 99),
            self._to_minutes(a["jam_mulai"]),
            a["kode_ruangan"],
            a["nama_kelas"]
        ))

        return {
            "status": status_str,
            "message": "Solusi penjadwalan berhasil di-generate.",
            "solve_time_seconds": round(solve_time, 2),
            "objective_value": round(self.solver.ObjectiveValue(), 2) if objective_terms else 0.0,
            "assignments": assignments,
            "statistics": {
                "total_tasks": len(self.tasks),
                "total_variables": len(X),
                "total_constraints": len(self.model.Proto().constraints),
                "conflicts_count": 0,
            }
        }
