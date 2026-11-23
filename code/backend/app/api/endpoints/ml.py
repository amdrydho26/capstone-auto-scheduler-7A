from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Course
from app.ml.semantic_clustering import CourseSemanticClusterer
from app.schemas.schemas import SemanticClusteringResponse, ClusterResultItem, CourseResponse

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.get("/semantic-clustering", response_model=SemanticClusteringResponse)
def get_semantic_clustering(db: Session = Depends(get_db)):
    """
    ML Lapis 1: Menjalankan Course Semantic Clustering pada Mata Kuliah Pilihan.
    Menghasilkan kelompok peminatan (AI, Cyber Security, Software Engineering, dll)
    beserta Conflict Weight Matrix antar pasangan MK pilihan.
    """
    # Ambil semua mata kuliah pilihan (Semester 5 & 7)
    elective_courses = db.query(Course).filter(Course.tipe == "pilihan").all()

    if not elective_courses:
        # Fallback jika belum ada flag pilihan, ambil semua courses semester 5 & 7
        elective_courses = db.query(Course).filter(Course.semester.in_([5, 7])).all()

    course_dicts = [
        {
            "id": c.id,
            "kode_mk": c.kode_mk,
            "nama_mk": c.nama_mk,
            "sks_teori": c.sks_teori,
            "sks_praktikum": c.sks_praktikum,
            "total_sks": c.total_sks,
            "semester": c.semester,
            "tipe": c.tipe,
            "tipe_ruangan": c.tipe_ruangan,
        }
        for c in elective_courses
    ]

    clusterer = CourseSemanticClusterer()
    named_clusters, conflict_weights, silhouette = clusterer.fit_clusters(course_dicts)

    # Format conflict weights keys to string for JSON serialization
    serialized_weights = {
        f"{k[0]}-{k[1]}": v for k, v in conflict_weights.items()
    }

    formatted_clusters = [
        ClusterResultItem(
            cluster_id=cl["cluster_id"],
            cluster_name=cl["cluster_name"],
            courses=[CourseResponse.model_validate(c) for c in cl["courses"]]
        )
        for cl in named_clusters
    ]

    return SemanticClusteringResponse(
        silhouette_score=silhouette,
        clusters=formatted_clusters,
        conflict_weights=serialized_weights
    )
