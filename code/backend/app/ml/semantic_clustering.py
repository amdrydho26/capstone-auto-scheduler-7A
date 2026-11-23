from typing import List, Dict, Tuple, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score


class CourseSemanticClusterer:
    """
    ML Lapis 1: Course Semantic Clustering.
    Mengelompokkan mata kuliah berdasarkan kemiripan semantik nama/topik
    menggunakan TF-IDF + Agglomerative Clustering + Silhouette Score.
    Menghasilkan Conflict Weight Matrix antar pasangan mata kuliah pilihan.
    """

    def __init__(self):
        # Indonesian tech stopwords & keywords enrichment
        self.stop_words = ["dan", "pada", "dalam", "berbasis", "lanjut", "pengenalan", "teori"]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=self.stop_words,
            lowercase=True
        )

    def fit_clusters(self, courses: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[Tuple[int, int], float], float]:
        """
        Input: list of course dicts [{'id': 1, 'kode_mk': '...', 'nama_mk': '...', 'tipe': 'pilihan'}]
        Output:
          - clusters: list of clusters with assigned courses and generated thematic cluster name
          - conflict_weights: {(course_id_1, course_id_2): weight_float}
          - best_silhouette: float
        """
        if len(courses) < 2:
            return [], {}, 0.0

        names = [c["nama_mk"] for c in courses]
        course_ids = [c["id"] for c in courses]

        # 1. TF-IDF Representation
        tfidf_matrix = self.vectorizer.fit_transform(names)
        sim_matrix = cosine_similarity(tfidf_matrix)

        # 2. Optimal K via Silhouette Score
        max_k = min(len(courses) - 1, 6)
        min_k = 2
        best_k = min_k
        best_score = -1.0
        best_labels = None

        if max_k >= min_k:
            for k in range(min_k, max_k + 1):
                clustering = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
                labels = clustering.fit_predict(sim_matrix)
                # Silhouette score requires at least 2 distinct clusters
                if len(set(labels)) > 1:
                    score = silhouette_score(sim_matrix, labels, metric="cosine")
                    if score > best_score:
                        best_score = score
                        best_k = k
                        best_labels = labels

        if best_labels is None:
            best_labels = np.zeros(len(courses), dtype=int)
            best_score = 0.5

        # 3. Group courses by cluster
        clusters_dict: Dict[int, List[Dict[str, Any]]] = {}
        for idx, label in enumerate(best_labels):
            if label not in clusters_dict:
                clusters_dict[label] = []
            clusters_dict[label].append(courses[idx])

        # 4. Generate cluster labels based on keywords
        named_clusters = []
        for cluster_id, cluster_courses in clusters_dict.items():
            cluster_text = " ".join([c["nama_mk"] for c in cluster_courses]).lower()
            if any(w in cluster_text for w in ["visi", "citra", "pembelajaran mendalam", "mesin", "intelijen"]):
                cluster_name = f"Cluster {cluster_id + 1}: Artificial Intelligence & Computer Vision"
            elif any(w in cluster_text for w in ["iot", "jaringan", "siber", "keamanan", "telekomunikasi"]):
                cluster_name = f"Cluster {cluster_id + 1}: Cyber Security & Network Systems"
            elif any(w in cluster_text for w in ["game", "imersif", "pengalaman pengguna", "komponen"]):
                cluster_name = f"Cluster {cluster_id + 1}: Interactive Media & Software Engineering"
            elif any(w in cluster_text for w in ["basis data", "graf", "dokumen", "paralel"]):
                cluster_name = f"Cluster {cluster_id + 1}: Data Engineering & Distributed Systems"
            else:
                cluster_name = f"Cluster {cluster_id + 1}: Peminatan Terapan"

            named_clusters.append({
                "cluster_id": int(cluster_id),
                "cluster_name": cluster_name,
                "courses": cluster_courses
            })

        # 5. Build Conflict Weight Matrix
        # MK di cluster yang sama punya bobot konflik tinggi (prioritas tinggi untuk tidak bentrok)
        conflict_weights: Dict[Tuple[int, int], float] = {}
        n = len(courses)
        for i in range(n):
            for j in range(i + 1, n):
                id_a, id_b = course_ids[i], course_ids[j]
                key = (min(id_a, id_b), max(id_a, id_b))
                # Base similarity from TF-IDF
                base_sim = float(sim_matrix[i, j])

                # Jika dalam cluster yang sama, perkuat bobot
                if best_labels[i] == best_labels[j]:
                    weight = max(0.65, min(1.0, base_sim + 0.4))
                else:
                    weight = min(0.35, base_sim)

                conflict_weights[key] = round(weight, 3)

        return named_clusters, conflict_weights, round(float(best_score), 3)
