from fastapi import FastAPI

# создаём приложение
app = FastAPI()

# простой маршрут
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI is working!"}

# пример с параметром
@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}
