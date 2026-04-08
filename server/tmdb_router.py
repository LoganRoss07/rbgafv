#tmdb_router.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import os
import requests

from auth import get_current_user
from dotenv import load_dotenv

load_dotenv()

TmdbAccessToken = os.getenv("TmdbAccessToken")
TmdbUrl = os.getenv("TmdbUrl")

router = APIRouter(
    prefix="/api/movies",
    tags=["movies"]
)

def _tmdb_headers():
    return {
        "Authorization": f"Bearer {TmdbAccessToken}",
        "accept": "application/json"
    }

def _tmdb_get(path: str, params: dict = None):
    url = f"{TmdbUrl}{path}"
    try:
        response = requests.get(url, headers=_tmdb_headers(), params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    except requests.exception.Timeout:
        raise HTTPException(status_code=503, detail="TMDB service unavailable. Please try again later.")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Could not reach TMDB service. Please try again later.")
    
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else 500
        raise HTTPException(status_code=status, detail="TMDB error")
    
    except Exception:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while communicating with TMDB.")
    
def _extract_movie(movie:dict):
    poster = movie.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster}" if poster else None

    return {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "overview": movie.get("overview"),
        "poster": poster_url,
        "rating": movie.get("vote_average"),
        "release_date": movie.get("release_date")
    }

@router.get("/search")
def search_movies(query: str = Query(...), page: int = Query(1), current_user=Depends(get_current_user)):

    data = _tmdb_get("/search/movie", {
        "query": query,
        "page": page,
    })

    return {
        "results": [_extract_movie(m) for m in data.get("results", [])]
    }

@router.get("/{tmdb_id}")
def get_movie(tmdb_id: int, current_user=Depends(get_current_user)):
    data = _tmdb_get(f"/movie/{tmdb_id}")

    return _extract_movie(data)

@router.get("/{tmdb_id}/recommendations")
def get_recommendations(tmdb_id: int, current_user=Depends(get_current_user)):
    data = _tmdb_get(f"/movie/{tmdb_id}/recommendations")

    return {
        "results": [_extract_movie(m) for m in data.get("results", [])]
    }

@router.get("/health")
def health():
    return {"status": "tmdb ok"}
    
