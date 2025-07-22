import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import Book, User
from schemas import BookCreate, BookOut
from auth import pwd_context, verify_password, get_current_user_from_cookie
from typing import List

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/register")
def register_user(login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.login == login).first()
    if existing:
        raise HTTPException(400, "Користувач з таким логіном існує")
    hashed = pwd_context.hash(password)
    user = User(login=login, password=hashed)
    db.add(user)
    db.commit()
    return {"message": "Користувача створено"}

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, login: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == login).first()
    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Невірний логін або пароль"
        })
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="user", value=login)
    return response

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="user")
    return response

@app.post("/books/", response_model=BookOut)
def add_book(book: BookCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    existing = db.query(Book).filter(Book.title == book.title, Book.author == book.author).first()
    if existing:
        raise HTTPException(status_code=400, detail="Книга з таким автором і назвою існує")
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/books/{author}", response_model=List[BookOut])
def get_books_by_author(author: str, db: Session = Depends(get_db)):
    return db.query(Book).filter(Book.author == author).all()

@app.put("/books/", response_model=BookOut)
def update_book(book: BookCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    db_book = db.query(Book).filter(Book.title == book.title, Book.author == book.author).first()
    if not db_book:
        raise HTTPException(404, "Книга не знайдена")
    db_book.pages = book.pages
    db_book.image = book.image
    db_book.author_image = book.author_image
    db.commit()
    return db_book

@app.delete("/books/")
def delete_book(title: str, author: str, db: Session = Depends(get_db), user: User = Depends(get_current_user_from_cookie)):
    book = db.query(Book).filter(Book.title == title, Book.author == author).first()
    if not book:
        raise HTTPException(404, "Книга не знайдена")
    db.delete(book)
    db.commit()
    return {"message": "Книга видалена"}

@app.get("/html/{author}", response_class=HTMLResponse)
def html_page(author: str, request: Request, db: Session = Depends(get_db)):
    books = db.query(Book).filter(Book.author == author).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "author": author,
        "books": books
    })

@app.get("/", response_class=HTMLResponse)
def home(request: Request, user: User = Depends(get_current_user_from_cookie), db: Session = Depends(get_db)):
    authors = db.query(Book.author).distinct().all()
    authors = [a[0] for a in authors]
    return templates.TemplateResponse("home.html", {"request": request, "user": user, "authors": authors})



#http://127.0.0.1:8000/login 
#http://127.0.0.1:8000/ 
#http://127.0.0.1:8000/docs 
#python -m uvicorn main:app --reload
