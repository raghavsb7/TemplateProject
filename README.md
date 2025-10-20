# Template project

> A template project with React & Vite as frontend and fastapi as backend.


### How to run

- Frontend
```
cd frontend
npm install
npm run dev
```
- The application is then hosted on `localhost:5173`


- Backend
```
python -m venv .venv
source .venv/bin/activate
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload
```

- Database
```bash
sudo docker compose -f docker-compose-db.yml up
```
To connect to the dockerized db container, 

```bash
docker exec -it my-fastapi-db psql -U postgres -d app_db
```


### Deployment

#### Test local deployment

```bash
cd TemplateProject # You can rename this, just make sure the current directory has the docker compose file
sudo docker compose -f docker-compose-localhost.yml up --build
```

#### VCM

All duke students get access to a free vcm server to deploy a test web application. Find more details [here](https://vcm.duke.edu/).

- Add your public ssh key [here](https://idms-web-selfservice.oit.duke.edu/advanced).
- Then any vm you make should be ssh-able with the private key corresponding to the public key.

If you're deploying on vcm, change the vcm base url in `frontend/.env.production`. You can change the link to the url / ip address of the server you are hosting it on, if using GCP or Azure for deployment.

Commands to deploy:

```bash
cd TemplateProject # You can rename this, just make sure the current directory has the docker compose file
sudo docker compose -f docker-compose.yml up --build -d
```