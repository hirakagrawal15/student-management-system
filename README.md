# Student Management System (Aim 3)

HTML / CSS / JavaScript frontend · Python Flask backend · SQLite database

## Run
```bash
pip install -r requirements.txt
python app.py            # open http://127.0.0.1:5000
```
`students.db` is created automatically on first run.

## Test
```bash
python -m unittest test_app.py -v     # backend unit tests (temp database)
node test_api.js                      # Node-based API test (server must be running)
```

## REST API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/students?q=term | List all / search by name or roll no |
| GET | /api/students/<id> | Get one student |
| POST | /api/students | Add student |
| PUT | /api/students/<id> | Update student |
| DELETE | /api/students/<id> | Delete student |

## Schema
`students(id PK, name, roll_no UNIQUE, class, marks CHECK 0-100, contact)`

## Validation (client and server)
Name letters only · roll number unique · marks 0-100 · contact 10-digit Indian mobile (starts 6-9).
Errors: 400 invalid, 409 duplicate roll no, 404 student not found.
