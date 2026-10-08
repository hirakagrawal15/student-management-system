import os, tempfile, unittest
import app as appmod

GOOD = {"name": "Asha Verma", "roll_no": "cs-101", "class": "10-A", "marks": 88.5, "contact": "9876543210"}


class StudentAPITest(unittest.TestCase):
    def setUp(self):
        self.fd, path = tempfile.mkstemp(suffix=".db")
        appmod.app.config["DATABASE"] = path
        appmod.init_db()
        self.c = appmod.app.test_client()

    def tearDown(self):
        os.close(self.fd)
        os.unlink(appmod.app.config["DATABASE"])

    def test_add_and_list(self):
        r = self.c.post("/api/students", json=GOOD)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["roll_no"], "CS-101")
        self.assertEqual(len(self.c.get("/api/students").get_json()), 1)

    def test_duplicate_roll(self):
        self.c.post("/api/students", json=GOOD)
        r = self.c.post("/api/students", json=GOOD)
        self.assertEqual(r.status_code, 409)

    def test_invalid_contact_and_marks(self):
        bad = dict(GOOD, contact="12345", marks=150)
        r = self.c.post("/api/students", json=bad)
        self.assertEqual(r.status_code, 400)
        self.assertIn("contact", r.get_json()["fields"])
        self.assertIn("marks", r.get_json()["fields"])

    def test_search(self):
        self.c.post("/api/students", json=GOOD)
        self.assertEqual(len(self.c.get("/api/students?q=asha").get_json()), 1)
        self.assertEqual(len(self.c.get("/api/students?q=cs-1").get_json()), 1)
        self.assertEqual(self.c.get("/api/students?q=nobody").get_json(), [])

    def test_update(self):
        sid = self.c.post("/api/students", json=GOOD).get_json()["id"]
        r = self.c.put(f"/api/students/{sid}", json=dict(GOOD, marks=95))
        self.assertEqual(r.get_json()["marks"], 95)

    def test_update_to_duplicate_roll(self):
        self.c.post("/api/students", json=GOOD)
        sid = self.c.post("/api/students", json=dict(GOOD, roll_no="CS-102")).get_json()["id"]
        r = self.c.put(f"/api/students/{sid}", json=GOOD)
        self.assertEqual(r.status_code, 409)

    def test_delete_and_missing(self):
        sid = self.c.post("/api/students", json=GOOD).get_json()["id"]
        self.assertEqual(self.c.delete(f"/api/students/{sid}").status_code, 200)
        self.assertEqual(self.c.delete(f"/api/students/{sid}").status_code, 404)
        self.assertEqual(self.c.put("/api/students/999", json=GOOD).status_code, 404)
        self.assertEqual(self.c.get("/api/students/999").status_code, 404)


if __name__ == "__main__":
    unittest.main()
