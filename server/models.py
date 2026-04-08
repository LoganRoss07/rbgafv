from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, List, Any
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

"""
Define internal Schema for our applications external API
This will force a consistent data structure for how we represent movies inside
our system, regardless of the website providing the data
all provider data will be transformed
"""

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    username = Column(String(50))

class Review(Base):
    """As all providers will represent ratings differently 
    Inside each movie, ratings field will be a dictionary with 
    the key (provider name, i.e. TMDB) and value (providers rating, RatingBundle)
    """
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    movie_id = Column(Integer, ForeignKey("movies.id"))
    rating = Column(Float)
    review_text = Column(String(1000))

class Movie(Base):
    """
    movie is CORE internal data model for our External API
    Every movie will follow this same structure, from any provider
    """
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    release_year = Column(String(50))
    ratings = Column(Float)

   
