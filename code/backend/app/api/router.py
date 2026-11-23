from fastapi import APIRouter
from app.api.endpoints import courses, lecturers, rooms, classes, ml, schedule, importer

api_router = APIRouter()

api_router.include_router(courses.router)
api_router.include_router(lecturers.router)
api_router.include_router(rooms.router)
api_router.include_router(classes.router)
api_router.include_router(ml.router)
api_router.include_router(schedule.router)
api_router.include_router(importer.router)
