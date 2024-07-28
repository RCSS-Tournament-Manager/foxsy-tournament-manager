# Tournament Manager V2

## Run Dev

```bash 
mkdir "$(pwd)/data/app-data"
mkidr "$(pwd)/data/log-dir" 

python app/main.py --data-dir "$(pwd)/data/app-data" --log-dir "$(pwd)/data/log-dir" --db "test.db" --api "testtest" --fast-api-port "8081" --rabbitmq-host "localhost" --rabbitmq-port "5672" --rabbitmq-username "guest" --rabbitmq-password "guest1234" --to-runner-queue "to-runner"
```