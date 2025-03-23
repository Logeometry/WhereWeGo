from fastapi import FastAPI
app = FastAPI()

from fastapi.responses import FileResponse


@app.get("/")
def whenEnterTheWeb():
    return "welcome USER"

@app.get("/attrations")
def 작명():
    #return 'hello' #들어갔을때 출력문장
    return FileResponse('busan_attractions.html')

@app.get("/accommodations")
def 작명():
    return FileResponse('busan_accommodation_butt.html')


@app.get("/data")
def 작명():
    return {'hello':1234}  #원본주소에 /data를하면 이와같은것이 출력이 된다

from pydantic import BaseModel

class Model(BaseModel):
    name :str
    phone :int



@app.post("/send") #유저가 데이터 전송할때
def 작명(data: Model):
    print(data)
    return '전송완료'