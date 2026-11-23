from typing import List, Dict, Tuple, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score


class CourseSemanticClusterer:
    """
    ML Lapis 1: Course Semantic Clustering.
    Mengelompokkan mata kuliah pilihan berdasarkan kesamaan domain topik
    menggunakan representasi TF-IDF dan Agglomerative Hierarchical Clustering.
    Menghasilkan Conflict Weight Matrix antar pasangan mata kuliah pilihan.
    """

    def __init__(self):
        self.stop_words = ["dan", "pada", "dalam", "berbasis", "lanjut", "pengenalan", "teori", "sistem"]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=self.stop_words,
            lowercase=True
        )

    def fit(self, courses: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[Tuple[str, str], float], float]:
        """
        Input: list of course dicts (khusus MK pilihan semester 5 & 7)
        Output:
          - clusters: list cluster peminatan beserta anggota MK
          - conflict_weights: {(kode_mk_a, kode_mk_b): weight_float}
          - silhouette: float evaluasi kualitas ML
        """
        elective_courses = [c for c in courses if c.get("tipe") == "pilihan"]
        if len(elective_courses) < 2:
            return [], {}, 0.0

        names = [c["nama_mk"] for c in elective_courses]
        kodes = [c["kode_mk"] for c in elective_courses]

        # 1. TF-IDF & Cosine Similarity
        tfidf_mat = self.vectorizer.fit_transform(names)
        sim_mat = cosine_similarity(tfidf_mat)

        # 2. Optimal K via Silhouette Score
        max_k = min(len(elective_courses) - 1, 6)
        min_k = 2
        best_k = min_k
        best_score = -1.0
        best_labels = None

        for k in range(min_k, max_k + 1):
            cl = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
            labels = cl.fit_predict(sim_mat)
            if len(set(labels)) > 1:
                score = silhouette_score(sim_mat, labels, metric="cosine")
                if score > best_score:
                    best_score = score
                    best_k = k
                    best_labels = labels

        if best_labels is None:
            best_labels = np.zeros(len(elective_courses), dtype=int)
            best_score = 0.5

        # 3. Bentuk Grup Klaster
        clusters_dict: Dict[int, List[Dict[str, Any]]] = {}
        for idx, lbl in enumerate(best_labels):
            if lbl not in clusters_dict:
                clusters_dict[lbl] = []
            clusters_dict[lbl].append(elective_courses[idx])

        # 4. Beri Label Nama Tematik Klaster
        named_clusters = []
        for c_id, c_courses in clusters_dict.items():
            text_all = " ".join([c["nama_mk"] for c in c_courses]).lower()
            if any(w in text_all for w in ["visi", "citra", "pembelajaran mendalam", "mesin", "intelijen"]):
                c_name = "Peminatan AI & Computer Vision"
            elif any(w in text_all for w in ["iot", "jaringan", "siber", "keamanan", "telekomunikasi"]):
                c_name = "Peminatan Cyber Security & Jaringan Komputer"
            elif any(w in text_all for w in ["game", "imersif", "pengalaman pengguna", "komponen"]):
                c_name = "Peminatan Software Engineering & Interactive Media"
            elif any(w in text_all for w in ["basis data", "graf", "dokumen", "paralel"]):
                c_name = "Peminatan Data Engineering & Distributed Systems"
            else:
                c_name = f"Peminatan Terapan {c_id + 1}"

            named_clusters.append({
                "cluster_id": int(c_id),
                "cluster_name": c_name,
                "courses": c_courses,
            })

        # 5. Bangun Conflict Weight Matrix
        # MK dalam satu klaster peminatan diberi bobot konflik tinggi (prioritas tinggi untuk tidak bentrok)
        conflict_weights: Dict[Tuple[str, str], float] = {}
        n = len(elective_courses)
        for i in range(n):
            for j in range(i + 1, n):
                k_a, k_b = kodes[i], kodes[j]
                key = (min(k_a, k_b), max(k_a, k_b))
                base_sim = float(sim_mat[i, j])

                if best_labels[i] == best_labels[j]:
                    weight = max(0.70, min(1.0, base_sim + 0.4))
                else:
                    weight = min(0.30, base_sim)

                conflict_weights[key] = round(weight, 3)

        return named_clusters, conflict_weights, round(float(best_score), 3)
