from typing import List, Dict, Tuple, Any, Optional
import time
from ortools.sat.python import cp_model


class CP_SATScheduler:
    """
    Core Optimization Engine using Google OR-Tools CP-SAT Solver.
    Menerapkan:
    - Hard Constraints: HC-01 s/d HC-08
    - Soft Constraints: SC-01 s/d SC-04
    - ML Lapis 1: Conflict Weight Matrix di Soft Constraint SC-08
    - ML Lapis 2: Warm-Start Hints via model.AddHint()
    """

    def __init__(self, time_limit_seconds: int = 300, num_workers: int = 8):
        self.time_limit_seconds = time_limit_seconds
        self.num_workers = num_workers

    def solve(
        self,
        tasks: List[Dict[str, Any]],
        rooms: List[Dict[str, Any]],
        timeslots: List[Dict[str, Any]],
        lecturers: List[Dict[str, Any]],
        classes: List[Dict[str, Any]],
        room_blocks: List[Dict[str, Any]],
        lecturer_preferences: List[Dict[str, Any]],
        ml_conflict_weights: Optional[Dict[Tuple[int, int], float]] = None,
        warmstart_hints: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Main solve routine.
        """
        start_time = time.time()
        model = cp_model.CpModel()

        # Lookup maps
        room_map = {r["id"]: r for r in rooms}
        slot_map = {s["id"]: s for s in timeslots}
        class_map = {c["id"]: c for c in classes}

        # Set of blocked (room_id, timeslot_id)
        blocked_pairs = set()
        for b in room_blocks:
            blocked_pairs.add((b["room_id"], b["timeslot_id"]))

        # Lecturer preferences map: (lecturer_id, timeslot_id) -> "unavailable" / "preferred"
        pref_map = {}
        for lp in lecturer_preferences:
            pref_map[(lp["lecturer_id"], lp["timeslot_id"])] = lp["tipe"]

        # -------------------------------------------------------------
        # 1. Decision Variables Creation with Domain Pruning (HC-04, HC-05, HC-06)
        # -------------------------------------------------------------
        # x[t_idx, s_id, r_id] = 1 if task t is assigned to timeslot s and room r
        x = {}
        task_valid_options = {}

        for t_idx, task in enumerate(tasks):
            task_valid_options[t_idx] = []
            sks = task["total_sks"]
            is_lab = task.get("is_lab", False)
            c_info = class_map.get(task["class_id"], {})
            student_count = c_info.get("jumlah_mahasiswa", 35)

            for s_id, slot in slot_map.items():
                # HC-06: Slot duration must match SKS
                if slot["sks"] != sks:
                    continue

                for r_id, room in room_map.items():
                    # HC-02: Check manual room blocks by other study programs
                    if (r_id, s_id) in blocked_pairs:
                        continue

                    # HC-04: Room capacity check
                    if room["kapasitas"] < student_count:
                        continue

                    # HC-05: Kesesuaian Ruangan
                    # - MK Teori Murni (is_lab == False): DILARANG keras memakai LAB Komputer agar LAB tidak boros.
                    # - MK Praktikum (is_lab == True): Bisa memakai LAB (prioritas utama) atau Ruang Teori (fallback jika kapasitas lab penuh)
                    is_room_lab = "PRAKTIKUM" in room["kategori"].upper() or "LAB" in room["kode_ruangan"].upper()
                    if not is_lab and is_room_lab:
                        continue  # HC-05: MK Teori murni tidak boleh mengambil slot LAB

                    var_name = f"x_t{t_idx}_s{s_id}_r{r_id}"
                    var = model.NewBoolVar(var_name)
                    x[(t_idx, s_id, r_id)] = var
                    task_valid_options[t_idx].append((s_id, r_id))

        # Check for immediate infeasibility before solving
        for t_idx, task in enumerate(tasks):
            if not task_valid_options[t_idx]:
                return {
                    "status": "INFEASIBLE",
                    "solve_time_seconds": round(time.time() - start_time, 2),
                    "items": [],
                    "message": f"Infeasible: Tidak ada slot/ruang yang valid untuk MK ID {task['course_id']} kelas {task['class_id']}",
                }

        # -------------------------------------------------------------
        # 2. Hard Constraints (HC)
        # -------------------------------------------------------------

        # Setiap task harus dijadwalkan tepat 1 kali
        for t_idx in range(len(tasks)):
            model.AddExactlyOne(x[(t_idx, s_id, r_id)] for (s_id, r_id) in task_valid_options[t_idx])

        # HC-01: Dosen tidak bentrok di slot yang sama
        # Kumpulkan task per dosen
        tasks_by_lecturer: Dict[int, List[int]] = {}
        for t_idx, task in enumerate(tasks):
            l_id = task["lecturer_id"]
            if l_id not in tasks_by_lecturer:
                tasks_by_lecturer[l_id] = []
            tasks_by_lecturer[l_id].append(t_idx)

        for l_id, t_indices in tasks_by_lecturer.items():
            for s_id in slot_map.keys():
                active_vars = []
                for t_idx in t_indices:
                    for (opt_s, r_id) in task_valid_options[t_idx]:
                        if opt_s == s_id:
                            active_vars.append(x[(t_idx, s_id, r_id)])
                if len(active_vars) > 1:
                    model.Add(sum(active_vars) <= 1)

        # HC-02: Ruangan tidak bentrok di slot yang sama
        for r_id in room_map.keys():
            for s_id in slot_map.keys():
                room_slot_vars = []
                for t_idx in range(len(tasks)):
                    if (s_id, r_id) in task_valid_options[t_idx]:
                        room_slot_vars.append(x[(t_idx, s_id, r_id)])
                if len(room_slot_vars) > 1:
                    model.Add(sum(room_slot_vars) <= 1)

        # HC-03: Kelas tidak bentrok di slot yang sama
        tasks_by_class: Dict[int, List[int]] = {}
        for t_idx, task in enumerate(tasks):
            c_id = task["class_id"]
            if c_id not in tasks_by_class:
                tasks_by_class[c_id] = []
            tasks_by_class[c_id].append(t_idx)

        for c_id, t_indices in tasks_by_class.items():
            for s_id in slot_map.keys():
                class_slot_vars = []
                for t_idx in t_indices:
                    for (opt_s, r_id) in task_valid_options[t_idx]:
                        if opt_s == s_id:
                            class_slot_vars.append(x[(t_idx, s_id, r_id)])
                if len(class_slot_vars) > 1:
                    model.Add(sum(class_slot_vars) <= 1)

        # -------------------------------------------------------------
        # 3. Soft Constraints & Objective Function
        # -------------------------------------------------------------
        objective_penalties = []

        # SC-01: Preferensi Dosen & SC-05: Prioritas LAB untuk MK Praktikum
        for (t_idx, s_id, r_id), var in x.items():
            l_id = tasks[t_idx]["lecturer_id"]
            pref = pref_map.get((l_id, s_id))
            if pref == "unavailable":
                objective_penalties.append(var * 100)
            elif pref == "preferred":
                objective_penalties.append(var * -20)

            # SC-05: Prioritaskan MK Praktikum di Ruang LAB (penalti 60 jika terpaksa di Ruang Teori)
            task_is_lab = tasks[t_idx].get("is_lab", False)
            room_info = room_map.get(r_id, {})
            is_room_lab = "PRAKTIKUM" in room_info.get("kategori", "").upper() or "LAB" in room_info.get("kode_ruangan", "").upper()
            if task_is_lab and not is_room_lab:
                objective_penalties.append(var * 60)

        # SC-08 (ML Lapis 1): Minimasi bentrok MK pilihan berdasarkan Conflict Weight Matrix
        if ml_conflict_weights:
            # Cari pasangan task yang merupakan mata kuliah pilihan berbeda
            elective_tasks = [
                (t_idx, t) for t_idx, t in enumerate(tasks) if t.get("tipe") == "pilihan"
            ]

            for i in range(len(elective_tasks)):
                t_idx1, t1 = elective_tasks[i]
                for j in range(i + 1, len(elective_tasks)):
                    t_idx2, t2 = elective_tasks[j]

                    c_id1 = t1["course_id"]
                    c_id2 = t2["course_id"]
                    if c_id1 == c_id2:
                        continue

                    pair_key = (min(c_id1, c_id2), max(c_id1, c_id2))
                    weight = ml_conflict_weights.get(pair_key, 0.0)

                    if weight > 0.3:
                        # Skalakan bobot ML (0.3 - 1.0) menjadi penalti integer (30 - 150)
                        penalty_val = int(weight * 150)

                        for s_id in slot_map.keys():
                            vars1 = [x[(t_idx1, s_id, r)] for (s, r) in task_valid_options[t_idx1] if s == s_id]
                            vars2 = [x[(t_idx2, s_id, r)] for (s, r) in task_valid_options[t_idx2] if s == s_id]

                            if vars1 and vars2:
                                # clash_bool = 1 jika kedua MK aktif di slot s_id yang sama
                                clash_var = model.NewBoolVar(f"clash_ml_{t_idx1}_{t_idx2}_s{s_id}")
                                model.Add(sum(vars1) + sum(vars2) <= 1 + clash_var)
                                objective_penalties.append(clash_var * penalty_val)

        # Set objective
        if objective_penalties:
            model.Minimize(sum(objective_penalties))

        # -------------------------------------------------------------
        # 4. ML Lapis 2: Warm-Start Hints
        # -------------------------------------------------------------
        if warmstart_hints:
            hint_count = 0
            for hint in warmstart_hints:
                c_id = hint.get("course_id")
                cl_id = hint.get("class_id")
                s_id = hint.get("suggested_slot_id")
                r_id = hint.get("suggested_room_id")

                for t_idx, task in enumerate(tasks):
                    if task["course_id"] == c_id and task["class_id"] == cl_id:
                        if (t_idx, s_id, r_id) in x:
                            model.AddHint(x[(t_idx, s_id, r_id)], 1)
                            hint_count += 1
            # print(f"Loaded {hint_count} warm-start hints into CP-SAT")

        # -------------------------------------------------------------
        # 5. Solver Execution
        # -------------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = float(self.time_limit_seconds)
        solver.parameters.num_workers = self.num_workers

        status = solver.Solve(model)
        solve_duration = round(time.time() - start_time, 2)

        status_str = solver.StatusName(status)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            results = []
            for (t_idx, s_id, r_id), var in x.items():
                if solver.Value(var) == 1:
                    task = tasks[t_idx]
                    results.append({
                        "course_id": task["course_id"],
                        "class_id": task["class_id"],
                        "lecturer_id": task["lecturer_id"],
                        "room_id": r_id,
                        "timeslot_id": s_id,
                    })

            return {
                "status": status_str,
                "solve_time_seconds": solve_duration,
                "objective_value": solver.ObjectiveValue() if objective_penalties else 0,
                "items": results,
                "message": f"Jadwal berhasil dibuat ({status_str}) dalam {solve_duration}s."
            }
        else:
            return {
                "status": status_str,
                "solve_time_seconds": solve_duration,
                "items": [],
                "message": f"Solver gagal menemukan solusi ({status_str}). Periksa kembali apakah ada konflik constraint.",
            }
