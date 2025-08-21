from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import jwt
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable

# Helper functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, list):
                data[key] = [prepare_for_mongo(item) if isinstance(item, dict) else item for item in value]
    return data

def parse_from_mongo(item):
    """Parse ISO strings back to datetime objects and remove MongoDB _id"""
    if isinstance(item, dict):
        # Remove MongoDB _id field if present
        if '_id' in item:
            del item['_id']
        
        # Parse datetime fields
        if item.get('created_at'):
            if isinstance(item['created_at'], str):
                try:
                    item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                except:
                    pass
    return item

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    bio: Optional[str] = ""
    profile_image: Optional[str] = ""
    followed_users: List[str] = Field(default_factory=list)
    followers: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    email: str
    bio: Optional[str] = ""
    profile_image: Optional[str] = ""

class UserLogin(BaseModel):
    username: str

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    car_make: str
    car_model: str
    car_year: int
    description: str
    modifications: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    parts_list: List[Dict[str, Any]] = Field(default_factory=list)
    build_cost: Optional[float] = 0.0
    likes_count: int = 0
    comments_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectCreate(BaseModel):
    title: str
    car_make: str
    car_model: str
    car_year: int
    description: str
    modifications: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    parts_list: List[Dict[str, Any]] = Field(default_factory=list)
    build_cost: Optional[float] = 0.0

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    modifications: Optional[List[str]] = None
    images: Optional[List[str]] = None
    parts_list: Optional[List[Dict[str, Any]]] = None
    build_cost: Optional[float] = None

class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    user_id: str
    username: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CommentCreate(BaseModel):
    project_id: str
    content: str

class Like(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LikeToggle(BaseModel):
    project_id: str

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    event_date: str  # YYYY-MM-DD format
    event_time: str  # HH:MM format
    location: str
    event_type: str  # "car_meet", "car_show", "race", "workshop", "cruise", "track_day"
    max_participants: Optional[int] = None
    participants: List[str] = Field(default_factory=list)  # List of user IDs
    images: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EventCreate(BaseModel):
    title: str
    description: str
    event_date: str
    event_time: str
    location: str
    event_type: str
    max_participants: Optional[int] = None
    images: List[str] = Field(default_factory=list)

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    location: Optional[str] = None
    event_type: Optional[str] = None
    max_participants: Optional[int] = None
    images: Optional[List[str]] = None

class EventJoin(BaseModel):
    event_id: str

# Authentication helper
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        user = await db.users.find_one({"id": user_id})
        if user:
            return User(**user)
        return None
    except:
        return None

def create_access_token(user_id: str):
    payload = {"sub": user_id}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Routes
@api_router.get("/")
async def root():
    return {"message": "AutoSocial Hub API - Car Projects Social Platform"}

# Auth routes
@api_router.post("/auth/register", response_model=Dict[str, Any])
async def register(user_data: UserCreate):
    # Check if username exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user = User(**user_data.dict())
    user_dict = prepare_for_mongo(user.dict())
    await db.users.insert_one(user_dict)
    
    token = create_access_token(user.id)
    return {"user": user, "token": token}

@api_router.post("/auth/login", response_model=Dict[str, Any])
async def login(login_data: UserLogin):
    user = await db.users.find_one({"username": login_data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_obj = User(**user)
    token = create_access_token(user_obj.id)
    return {"user": user_obj, "token": token}

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user

# User routes
@api_router.get("/users/{user_id}", response_model=User)
async def get_user_profile(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.post("/users/{user_id}/follow")
async def follow_user(user_id: str, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")
    
    # Check if user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add to current user's following list
    await db.users.update_one(
        {"id": current_user.id},
        {"$addToSet": {"followed_users": user_id}}
    )
    
    # Add to target user's followers list
    await db.users.update_one(
        {"id": user_id},
        {"$addToSet": {"followers": current_user.id}}
    )
    
    return {"message": "Successfully followed user"}

@api_router.delete("/users/{user_id}/follow")
async def unfollow_user(user_id: str, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Remove from current user's following list
    await db.users.update_one(
        {"id": current_user.id},
        {"$pull": {"followed_users": user_id}}
    )
    
    # Remove from target user's followers list
    await db.users.update_one(
        {"id": user_id},
        {"$pull": {"followers": current_user.id}}
    )
    
    return {"message": "Successfully unfollowed user"}

# Project routes
@api_router.get("/projects", response_model=List[Dict[str, Any]])
async def get_projects(current_user: User = Depends(get_current_user)):
    projects = []
    if current_user:
        # Get projects from followed users + own projects
        followed_users = current_user.followed_users + [current_user.id]
        projects_cursor = db.projects.find({"user_id": {"$in": followed_users}}).sort("created_at", -1)
    else:
        # Public feed - all projects
        projects_cursor = db.projects.find().sort("created_at", -1)
    
    projects_list = await projects_cursor.to_list(length=50)
    
    # Enrich with user data and clean MongoDB fields
    cleaned_projects = []
    for project in projects_list:
        user = await db.users.find_one({"id": project["user_id"]})
        if user:
            project["user"] = {"id": user["id"], "username": user["username"], "profile_image": user.get("profile_image", "")}
        cleaned_project = parse_from_mongo(project)
        cleaned_projects.append(cleaned_project)
    
    return cleaned_projects

@api_router.get("/projects/{project_id}", response_model=Dict[str, Any])
async def get_project(project_id: str):
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get user data
    user = await db.users.find_one({"id": project["user_id"]})
    if user:
        project["user"] = {"id": user["id"], "username": user["username"], "profile_image": user.get("profile_image", "")}
    
    return parse_from_mongo(project)

@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    project = Project(**project_data.dict(), user_id=current_user.id)
    project_dict = prepare_for_mongo(project.dict())
    await db.projects.insert_one(project_dict)
    
    return project

@api_router.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project_update: ProjectUpdate, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    project = await db.projects.find_one({"id": project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")
    
    update_data = {k: v for k, v in project_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.projects.update_one({"id": project_id}, {"$set": update_data})
    
    updated_project = await db.projects.find_one({"id": project_id})
    return Project(**updated_project)

@api_router.get("/users/{user_id}/projects", response_model=List[Project])
async def get_user_projects(user_id: str):
    projects = await db.projects.find({"user_id": user_id}).sort("created_at", -1).to_list(length=100)
    return [Project(**project) for project in projects]

# Comment routes
@api_router.get("/projects/{project_id}/comments", response_model=List[Comment])
async def get_project_comments(project_id: str):
    comments = await db.comments.find({"project_id": project_id}).sort("created_at", 1).to_list(length=100)
    return [Comment(**comment) for comment in comments]

@api_router.post("/comments", response_model=Comment)
async def create_comment(comment_data: CommentCreate, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if project exists
    project = await db.projects.find_one({"id": comment_data.project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    comment = Comment(
        **comment_data.dict(),
        user_id=current_user.id,
        username=current_user.username
    )
    comment_dict = prepare_for_mongo(comment.dict())
    await db.comments.insert_one(comment_dict)
    
    # Update comment count
    await db.projects.update_one(
        {"id": comment_data.project_id},
        {"$inc": {"comments_count": 1}}
    )
    
    return comment

# Like routes
@api_router.post("/likes", response_model=Dict[str, Any])
async def toggle_like(like_data: LikeToggle, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if project exists
    project = await db.projects.find_one({"id": like_data.project_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if already liked
    existing_like = await db.likes.find_one({
        "project_id": like_data.project_id,
        "user_id": current_user.id
    })
    
    if existing_like:
        # Unlike
        await db.likes.delete_one({"id": existing_like["id"]})
        await db.projects.update_one(
            {"id": like_data.project_id},
            {"$inc": {"likes_count": -1}}
        )
        return {"liked": False, "message": "Project unliked"}
    else:
        # Like
        like = Like(project_id=like_data.project_id, user_id=current_user.id)
        like_dict = prepare_for_mongo(like.dict())
        await db.likes.insert_one(like_dict)
        
        await db.projects.update_one(
            {"id": like_data.project_id},
            {"$inc": {"likes_count": 1}}
        )
        return {"liked": True, "message": "Project liked"}

# Event routes
@api_router.get("/events", response_model=List[Dict[str, Any]])
async def get_events(current_user: User = Depends(get_current_user)):
    # Get all upcoming events (not past events)
    from datetime import date
    today = date.today().isoformat()
    
    events_cursor = db.events.find({"event_date": {"$gte": today}}).sort("event_date", 1)
    events_list = await events_cursor.to_list(length=100)
    
    # Enrich with user data and participant info
    cleaned_events = []
    for event in events_list:
        user = await db.users.find_one({"id": event["user_id"]})
        if user:
            event["user"] = {"id": user["id"], "username": user["username"], "profile_image": user.get("profile_image", "")}
        
        # Add participant count and check if current user joined
        event["participants_count"] = len(event.get("participants", []))
        if current_user:
            event["user_joined"] = current_user.id in event.get("participants", [])
        else:
            event["user_joined"] = False
            
        cleaned_event = parse_from_mongo(event)
        cleaned_events.append(cleaned_event)
    
    return cleaned_events

@api_router.get("/events/{event_id}", response_model=Dict[str, Any])
async def get_event(event_id: str, current_user: User = Depends(get_current_user)):
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get user data
    user = await db.users.find_one({"id": event["user_id"]})
    if user:
        event["user"] = {"id": user["id"], "username": user["username"], "profile_image": user.get("profile_image", "")}
    
    # Add participant info
    event["participants_count"] = len(event.get("participants", []))
    if current_user:
        event["user_joined"] = current_user.id in event.get("participants", [])
    else:
        event["user_joined"] = False
    
    # Get participant details
    participants_info = []
    for participant_id in event.get("participants", []):
        participant = await db.users.find_one({"id": participant_id})
        if participant:
            participants_info.append({
                "id": participant["id"],
                "username": participant["username"],
                "profile_image": participant.get("profile_image", "")
            })
    event["participants_info"] = participants_info
    
    return parse_from_mongo(event)

@api_router.post("/events", response_model=Event)
async def create_event(event_data: EventCreate, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    event = Event(**event_data.dict(), user_id=current_user.id)
    event_dict = prepare_for_mongo(event.dict())
    await db.events.insert_one(event_dict)
    
    return event

@api_router.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str, event_update: EventUpdate, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if event["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this event")
    
    update_data = {k: v for k, v in event_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.events.update_one({"id": event_id}, {"$set": update_data})
    
    updated_event = await db.events.find_one({"id": event_id})
    return Event(**updated_event)

@api_router.post("/events/{event_id}/join")
async def join_event(event_id: str, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if event exists
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user is already joined
    if current_user.id in event.get("participants", []):
        raise HTTPException(status_code=400, detail="Already joined this event")
    
    # Check if event is full
    max_participants = event.get("max_participants")
    if max_participants and len(event.get("participants", [])) >= max_participants:
        raise HTTPException(status_code=400, detail="Event is full")
    
    # Add user to participants
    await db.events.update_one(
        {"id": event_id},
        {"$addToSet": {"participants": current_user.id}}
    )
    
    return {"message": "Successfully joined event"}

@api_router.delete("/events/{event_id}/join")
async def leave_event(event_id: str, current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Remove user from participants
    await db.events.update_one(
        {"id": event_id},
        {"$pull": {"participants": current_user.id}}
    )
    
    return {"message": "Successfully left event"}

@api_router.get("/users/{user_id}/events", response_model=List[Event])
async def get_user_events(user_id: str):
    events = await db.events.find({"user_id": user_id}).sort("event_date", 1).to_list(length=100)
    return [Event(**event) for event in events]

# Discovery routes
@api_router.get("/discover/users", response_model=List[Dict[str, Any]])
async def discover_users(current_user: User = Depends(get_current_user), limit: int = 20):
    """Discover new users to follow"""
    if current_user:
        # Exclude already followed users and self
        excluded_users = current_user.followed_users + [current_user.id]
        users_cursor = db.users.find({"id": {"$nin": excluded_users}})
    else:
        users_cursor = db.users.find()
    
    users_list = await users_cursor.to_list(length=limit)
    
    # Enrich with stats
    discovered_users = []
    for user_data in users_list:
        user = parse_from_mongo(user_data)
        
        # Get user stats
        project_count = await db.projects.count_documents({"user_id": user["id"]})
        event_count = await db.events.count_documents({"user_id": user["id"]})
        follower_count = len(user.get("followers", []))
        
        user["stats"] = {
            "project_count": project_count,
            "event_count": event_count,
            "follower_count": follower_count
        }
        
        discovered_users.append(user)
    
    # Sort by activity (projects + events + followers)
    discovered_users.sort(key=lambda u: u["stats"]["project_count"] + u["stats"]["event_count"] + u["stats"]["follower_count"], reverse=True)
    
    return discovered_users[:limit]

@api_router.get("/discover/events", response_model=List[Dict[str, Any]])
async def discover_events(current_user: User = Depends(get_current_user), limit: int = 20):
    """Discover trending/popular events"""
    from datetime import date
    today = date.today().isoformat()
    
    # Get upcoming events
    events_cursor = db.events.find({"event_date": {"$gte": today}}).sort("event_date", 1)
    events_list = await events_cursor.to_list(length=limit * 2)  # Get more to filter
    
    # Enrich with user data and sort by popularity
    discovered_events = []
    for event in events_list:
        user = await db.users.find_one({"id": event["user_id"]})
        if user:
            event["user"] = {"id": user["id"], "username": user["username"], "profile_image": user.get("profile_image", "")}
        
        # Add participant info
        event["participants_count"] = len(event.get("participants", []))
        if current_user:
            event["user_joined"] = current_user.id in event.get("participants", [])
        else:
            event["user_joined"] = False
            
        # Calculate popularity score (participants + recency)
        from datetime import datetime
        try:
            event_date = datetime.fromisoformat(event["event_date"])
            days_until_event = (event_date.date() - date.today()).days
            recency_score = max(0, 30 - days_until_event) if days_until_event >= 0 else 0
        except:
            recency_score = 0
            
        event["popularity_score"] = event["participants_count"] * 2 + recency_score
        
        cleaned_event = parse_from_mongo(event)
        discovered_events.append(cleaned_event)
    
    # Sort by popularity score
    discovered_events.sort(key=lambda e: e.get("popularity_score", 0), reverse=True)
    
    return discovered_events[:limit]

@api_router.get("/discover/projects", response_model=List[Dict[str, Any]])
async def discover_projects(current_user: User = Depends(get_current_user), limit: int = 20):
    """Discover trending/popular projects"""
    # Get projects sorted by likes and comments
    projects_cursor = db.projects.find().sort([("likes_count", -1), ("comments_count", -1), ("created_at", -1)])
    projects_list = await projects_cursor.to_list(length=limit)
    
    # Enrich with user data
    discovered_projects = []
    for project in projects_list:
        user = await db.users.find_one({"id": project["user_id"]})
        if user:
            project["user"] = {"id": user["id"], "username": user["username"], "profile_image": user.get("profile_image", "")}
        
        cleaned_project = parse_from_mongo(project)
        discovered_projects.append(cleaned_project)
    
    return discovered_projects

@api_router.get("/search", response_model=Dict[str, Any])
async def universal_search(q: str, current_user: User = Depends(get_current_user), limit: int = 10):
    """Universal search across users, events, and projects"""
    if not q or len(q.strip()) < 2:
        return {"users": [], "events": [], "projects": []}
    
    search_term = q.strip()
    
    # Search users
    users_cursor = db.users.find({
        "$or": [
            {"username": {"$regex": search_term, "$options": "i"}},
            {"bio": {"$regex": search_term, "$options": "i"}}
        ]
    })
    users_list = await users_cursor.to_list(length=limit)
    users_results = []
    for user_data in users_list:
        user = parse_from_mongo(user_data)
        # Get basic stats
        project_count = await db.projects.count_documents({"user_id": user["id"]})
        user["project_count"] = project_count
        users_results.append(user)
    
    # Search events  
    from datetime import date
    today = date.today().isoformat()
    events_cursor = db.events.find({
        "event_date": {"$gte": today},
        "$or": [
            {"title": {"$regex": search_term, "$options": "i"}},
            {"description": {"$regex": search_term, "$options": "i"}},
            {"location": {"$regex": search_term, "$options": "i"}},
            {"event_type": {"$regex": search_term, "$options": "i"}}
        ]
    })
    events_list = await events_cursor.to_list(length=limit)
    events_results = []
    for event in events_list:
        user = await db.users.find_one({"id": event["user_id"]})
        if user:
            event["user"] = {"id": user["id"], "username": user["username"], "profile_image": user.get("profile_image", "")}
        event["participants_count"] = len(event.get("participants", []))
        if current_user:
            event["user_joined"] = current_user.id in event.get("participants", [])
        else:
            event["user_joined"] = False
        events_results.append(parse_from_mongo(event))
    
    # Search projects
    projects_cursor = db.projects.find({
        "$or": [
            {"title": {"$regex": search_term, "$options": "i"}},
            {"description": {"$regex": search_term, "$options": "i"}},
            {"car_make": {"$regex": search_term, "$options": "i"}},
            {"car_model": {"$regex": search_term, "$options": "i"}},
            {"modifications": {"$regex": search_term, "$options": "i"}}
        ]
    })
    projects_list = await projects_cursor.to_list(length=limit)
    projects_results = []
    for project in projects_list:
        user = await db.users.find_one({"id": project["user_id"]})
        if user:
            project["user"] = {"id": user["id"], "username": user["username"], "profile_image": user.get("profile_image", "")}
        projects_results.append(parse_from_mongo(project))
    
    return {
        "users": users_results,
        "events": events_results,
        "projects": projects_results,
        "query": search_term
    }

@api_router.get("/search/users", response_model=List[Dict[str, Any]])
async def search_users(q: str, limit: int = 20):
    """Search users specifically"""
    if not q or len(q.strip()) < 2:
        return []
    
    search_term = q.strip()
    users_cursor = db.users.find({
        "$or": [
            {"username": {"$regex": search_term, "$options": "i"}},
            {"bio": {"$regex": search_term, "$options": "i"}}
        ]
    })
    users_list = await users_cursor.to_list(length=limit)
    
    users_results = []
    for user_data in users_list:
        user = parse_from_mongo(user_data)
        # Get stats
        project_count = await db.projects.count_documents({"user_id": user["id"]})
        event_count = await db.events.count_documents({"user_id": user["id"]})
        user["stats"] = {
            "project_count": project_count,
            "event_count": event_count,
            "follower_count": len(user.get("followers", []))
        }
        users_results.append(user)
    
    return users_results

@api_router.get("/search/events", response_model=List[Dict[str, Any]])
async def search_events(q: str, current_user: User = Depends(get_current_user), limit: int = 20):
    """Search events specifically"""
    if not q or len(q.strip()) < 2:
        return []
    
    search_term = q.strip()
    from datetime import date
    today = date.today().isoformat()
    
    events_cursor = db.events.find({
        "event_date": {"$gte": today},
        "$or": [
            {"title": {"$regex": search_term, "$options": "i"}},
            {"description": {"$regex": search_term, "$options": "i"}},
            {"location": {"$regex": search_term, "$options": "i"}},
            {"event_type": {"$regex": search_term, "$options": "i"}}
        ]
    })
    events_list = await events_cursor.to_list(length=limit)
    
    events_results = []
    for event in events_list:
        user = await db.users.find_one({"id": event["user_id"]})
        if user:
            event["user"] = {"id": user["id"], "username": user["username"], "profile_image": user.get("profile_image", "")}
        event["participants_count"] = len(event.get("participants", []))
        if current_user:
            event["user_joined"] = current_user.id in event.get("participants", [])
        else:
            event["user_joined"] = False
        events_results.append(parse_from_mongo(event))
    
    return events_results

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()