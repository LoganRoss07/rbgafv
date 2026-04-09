from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
import os
from database import get_db, Base, engine
from auth import authenticate_user, create_access_token, get_current_user
from models import User, Movie, Review, Rating
from schemas import UserCreate, UserOut, RatingSchema
from tmdb_router import router as tmdb_router
from auth_routes import router as auth_router
from auth import require_admin

Base.metadata.create_all(bind=engine)

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tmdb_router)

app.mount("/static", StaticFiles(directory="client"), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse("client/index.html")

@app.get("/browse", response_class=HTMLResponse)
def browser():
    return FileResponse("client/browse.html")

@app.get("/recommendations", response_class=HTMLResponse)
def recommendations_page():
    return FileResponse("client/recommendations.html")

@app.get("/ratings", response_class=HTMLResponse)
def ratings_page():
    return FileResponse("client/ratings.html")

@app.get("/reviews", response_class=HTMLResponse)
def reviews_page():
    return FileResponse("client/reviews.html")
    
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page():
    return FileResponse("client/dashboard.html")

@app.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": db_user.email})
    return {"access_token": token}

@app.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    return db.query(Movie).all()
    

@app.post("/rate")
def rate_movie(data: RatingSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    
    rating = Rating(user_id=current_user.id, movie_id=data.movie_id, rating=data.rating)

    db.add(rating)
    db.commit()
    return {"message": "Rating submitted successfully!"}

@app.get("/user/ratings")
def get_user_ratings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    ratings = db.query(Rating).filter(Rating.user_id == current_user.id).all()

    return ratings

@app.post("/reviews")
def submit_review(movie_id: int, rating: int, review_text: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    reviews = Review(user_id=current_user.id, movie_id=movie_id, rating=rating, review_text=review_text, status="pending")

    db.add(reviews)
    db.commit()
    return {"message": "Review submitted and pending approval!"}

@app.get("/admin/reviews")
def get_reviews(db: Session = Depends(get_db), admin: User = Depends(require_admin)):

    return db.query(Review).all()

@app.post("/admin/reviews/{review_id}/approve")
def approve_review(review_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):

    review = db.query(Review).filter(Review.id == review_id).first()
    review.status = "approved"
    db.commit()
    return {"message": "Review approved!"}

@app.post("/admin/reviews/{review_id}/reject")
def reject_review(review_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):

    review = db.query(Review).get(review_id)
    review.status = "rejected"
    db.commit()
    return {"message": "Review rejected!"}

@app.get("/admin/stats")
def get_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):

    movies = db.query(Movie).count()
    users = db.query(User).count()
    reviews = db.query(Review).count()
    pending = db.query(Review).filter(Review.status == "pending").count()

    return {
        "total_movies": movies,
        "total_users": users,
        "total_reviews": reviews,
        "pending_reviews": pending,
        "recent_activity": [
            "User submitted a review",
            "Admin approved a review",
            "User rated a movie"
        ]
    }

@app.get("/health")
def health():
    return {"status": "ok"}
    
