from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier


class HistoricalPatternLearner:
    """
    ML Lapis 2: Historical Schedule Pattern Learning.
    Melatih model klasifikasi (Random Forest) untuk memprediksi kecenderungan
    slot waktu & tipe ruangan berdasarkan karakteristik mata kuliah (SKS, semester, lab/teori).
    Prediksi ini kemudian digunakan sebagai Warm-Start Hint untuk CP-SAT Solver.
    """

    def __init__(self):
        self.clf_timeslot = RandomForestClassifier(n_estimators=50, random_state=42)
        self.clf_room = RandomForestClassifier(n_estimators=50, random_state=42)
        self.is_trained = False

    def train_on_historical_schedules(
        self,
        historical_items: List[Dict[str, Any]]
    ):
        """
        Input: list of historical items with keys:
          - total_sks: int
          - is_lab: int (0 or 1)
          - semester: int
          - timeslot_id: int
          - room_id: int
        """
        if len(historical_items) < 5:
            # Not enough data to train reliably
            return

        X = []
        y_slot = []
        y_room = []

        for item in historical_items:
            X.append([
                item["total_sks"],
                item["is_lab"],
                item["semester"],
            ])
            y_slot.append(item["timeslot_id"])
            y_room.append(item["room_id"])

        X_arr = np.array(X)
        self.clf_timeslot.fit(X_arr, y_slot)
        self.clf_room.fit(X_arr, y_room)
        self.is_trained = True

    def predict_hints(
        self,
        pending_assignments: List[Dict[str, Any]],
        available_timeslots: List[Dict[str, Any]],
        available_rooms: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Menghasilkan rekomendasi assignment (warm start hint) untuk setiap pending task.
        """
        hints = []
        if not self.is_trained:
            # Default heuristic fallback jika belum ada data historis:
            # - Praktikum disarankan ke LAB
            # - Teori disarankan ke Kelas Teori
            # - Semester 1 & 3 diprioritaskan pagi, Semester 5 & 7 siang/pagi seimbang
            lab_rooms = [r["id"] for r in available_rooms if "PRAKTIKUM" in r["kategori"].upper()]
            theory_rooms = [r["id"] for r in available_rooms if "TEORI" in r["kategori"].upper()]

            for idx, task in enumerate(pending_assignments):
                sks = task["total_sks"]
                is_lab = task["is_lab"]
                sem = task["semester"]

                # Filter valid timeslots by SKS
                matching_slots = [s["id"] for s in available_timeslots if s["sks"] == sks]
                if not matching_slots:
                    matching_slots = [s["id"] for s in available_timeslots]

                chosen_slot = matching_slots[idx % len(matching_slots)]
                if is_lab and lab_rooms:
                    chosen_room = lab_rooms[idx % len(lab_rooms)]
                elif theory_rooms:
                    chosen_room = theory_rooms[idx % len(theory_rooms)]
                else:
                    chosen_room = available_rooms[0]["id"]

                hints.append({
                    "course_id": task["course_id"],
                    "class_id": task["class_id"],
                    "lecturer_id": task["lecturer_id"],
                    "suggested_slot_id": chosen_slot,
                    "suggested_room_id": chosen_room,
                })
            return hints

        # Jika model trained, gunakan prediksi Random Forest
        for task in pending_assignments:
            features = np.array([[task["total_sks"], task["is_lab"], task["semester"]]])
            pred_slot = int(self.clf_timeslot.predict(features)[0])
            pred_room = int(self.clf_room.predict(features)[0])

            hints.append({
                "course_id": task["course_id"],
                "class_id": task["class_id"],
                "lecturer_id": task["lecturer_id"],
                "suggested_slot_id": pred_slot,
                "suggested_room_id": pred_room,
            })

        return hints
