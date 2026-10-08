// Node-based smoke test against a running server: `npm start` then `npm run test:api`
const BASE = process.env.BASE || "http://127.0.0.1:5000";
const j = (m, p, b) => fetch(BASE + p, { method: m, headers: { "Content-Type": "application/json" }, body: b && JSON.stringify(b) });
const ok = (c, msg) => { console.log((c ? "PASS " : "FAIL ") + msg); if (!c) process.exitCode = 1; };

(async () => {
  const roll = "T" + Date.now().toString().slice(-8);
  const s = { name: "Node Tester", roll_no: roll, class: "9-B", marks: 70, contact: "9123456780" };
  let r = await j("POST", "/api/students", s); const created = await r.json();
  ok(r.status === 201, "create student");
  ok((await j("POST", "/api/students", s)).status === 409, "reject duplicate roll no");
  ok((await j("POST", "/api/students", { ...s, roll_no: "X1", contact: "1" })).status === 400, "reject bad contact");
  r = await j("GET", "/api/students?q=" + roll); ok((await r.json()).length === 1, "search by roll no");
  ok((await j("PUT", "/api/students/" + created.id, { ...s, marks: 91 })).status === 200, "update student");
  ok((await j("DELETE", "/api/students/" + created.id)).status === 200, "delete student");
  ok((await j("DELETE", "/api/students/" + created.id)).status === 404, "delete non-existent -> 404");
})();
