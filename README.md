# Congestion-Worker

## install dependencies

Use following command to install dependencies.
`pip install -r requirements.txt`

## Set environments

Make .env file in your cloned local repository, and paste following in the file.
```
ITS_API_KEY = "YOUR_API_KEY"
```
Change `YOUR_API_KEY` to your api key that you got from [ITS webpage](https://www.its.go.kr/user/mypage). (Sign up is required)

## Run
If required, you should run via nohup and make it run on background.

### Worker

Run `NewDaejeonworker.py`.

`python3 NewDaejeonworker.py`

### Server

Run `Workerflask.py`

`flask --app Workerflask.py run`

When run on server with port number `60001`

`flask --app Workerflask.py run --port=60001 --host=0.0.0.0`
