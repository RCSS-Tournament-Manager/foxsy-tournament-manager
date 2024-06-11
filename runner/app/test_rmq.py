import asyncio
import json
import aio_pika as pika

game_info = json.dumps({
    'game_id': 1,
    'left_team_name': 'team1',
    'right_team_name': 'team2',
    'left_team_config_id': 1,
    'right_team_config_id': 2,
    'left_base_team_name': 'helios',
    'right_base_team_name': 'hermes',
    'server_config': ''
})

msg = json.dumps({
    'action': 'add_game',
    'game_info': game_info

})

async def main():
    connection = await pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()  # type: pika.Channel
        await channel.default_exchange.publish(
            pika.Message(body=msg.encode()),
            routing_key="games",
        )
        
# run main coroutine
asyncio.run(main())
asyncio.get_event_loop().run_forever()