from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session
import os

from database import SessionLocal, engine, get_db
import models

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# 렌더(프록시) 환경에서 https 주소를 정확히 인식하도록 설정
@app.middleware("http")
async def proxy_fix_middleware(request: Request, call_next):
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        request.scope["scheme"] = forwarded_proto
    response = await call_next(request)
    return response

# 세션 미들웨어 설정
app.add_middleware(SessionMiddleware, secret_key="your-super-secret-key-dongdong")

templates = Jinja2Templates(directory="templates")
templates.env.cache = None

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

ALLOWED_EMAILS = [
    "legendkai987654321@gmail.com",
    "jja8718@gmail.com",
    "raykim00@gmail.com",
]

# 1. 메인 페이지 (DB에서 글 불러오기)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, room: str = "우리 가족", db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return templates.TemplateResponse(request, "login.html", {})
    
    room_posts = db.query(models.Post).filter(models.Post.room == room).all()
    
    return templates.TemplateResponse(
        request,
        "index.html",
        {"user": user, "posts": room_posts, "current_room": room}
    )

# 2. 로그인 및 인증
@app.get("/login")
async def login(request: Request):
    redirect_uri = "https://family-room.onrender.com/auth"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get("userinfo")
        if userinfo:
            email = userinfo.get("email")
            if email not in ALLOWED_EMAILS:
                return HTMLResponse("<h3>허용되지 않은 사용자입니다.</h3>", status_code=403)
            request.session["user"] = {
                "name": userinfo.get("name"),
                "email": email,
                "picture": userinfo.get("picture")
            }
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return HTMLResponse(f"로그인 오류: {str(e)}", status_code=400)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

# 3. 게시글 작성 (DB에 저장)
@app.post("/add_post")
async def create_post(
    request: Request,
    content: str = Form(...),
    room: str = Form("우리 가족"),
    category: str = Form("일상"),
    title: str = Form(""),
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)
        
    new_post = models.Post(
        author=user["name"],
        email=user["email"],
        picture=user["picture"],
        content=content,
        room=room,
        category=category,
        title=title
    )
    db.add(new_post)
    db.commit()
    
    return RedirectResponse(url=f"/?room={room}", status_code=303)