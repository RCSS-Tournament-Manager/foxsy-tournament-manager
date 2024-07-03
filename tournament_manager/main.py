from fastapi import FastAPI, HTTPException, Security, Depends
import uvicorn
import requests
import pika



app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/register")
def register(message_json: dict):
    print(message_json)
    return {"success": True}

@app.post("/game_started")
def game_started(message_json: dict):
    print(message_json)
    return {"success": True}

@app.post("/game_finished")
def game_finished(message_json: dict):
    print(message_json)
    return {"success": True}

async def send_message(message):
    response = requests.post(
        f"http://127.0.0.1:8082/add_game",
        headers={"api_key": "api-key"},
        json=message,
    )
    return response

game_id = 0
@app.post("/add_game")
async def add_game(message_json: dict):
    global game_id
    game_id += 1
    if message_json.get('type') != 'add_game':
        raise HTTPException(status_code=400, detail="Invalid message type")
    message_json['game_info']['game_id'] = game_id
    print(message_json)
    resp = await send_message(message_json)
    print(resp.json())
    return resp.json()

@app.post("/add_game_to_rabbit")
def add_game_to_rabbit(message_json: dict):
    global game_id
    game_id += 1
    if message_json.get('type') != 'add_game':
        raise HTTPException(status_code=400, detail="Invalid message type")
    message_json['game_info']['game_id'] = game_id
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='my_queue', durable=True)
    channel.basic_publish(exchange='', routing_key='to_runner', body=str(message_json), properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
    print(f" [{game_id}] Sent {message_json}")
    connection.close()
    return {"success": True}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)