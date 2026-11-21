// Local PostgreSQL (WASM), no connection to Supabase or ImageKit.
// npm install --prefix .venv/imagekit-cleanup-sql --no-audit --no-fund @electric-sql/pglite
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { PGlite } from "../../.venv/imagekit-cleanup-sql/node_modules/@electric-sql/pglite/dist/index.js";

const db = new PGlite();
const token = "test-only-".repeat(8);
const id = "00000000-0000-4000-8000-000000000001";
const otherId = "00000000-0000-4000-8000-000000000002";
const urls = ["original", "gradcam", "energy"];
const sql = (await readFile(new URL("../sql/imagekit_cleanup.sql", import.meta.url), "utf8"))
  .replaceAll("__TOKEN_SHA256__", createHash("sha256").update(token).digest("hex"));
const serialSql = await readFile(new URL("../sql/imagekit_sequential_names.sql", import.meta.url), "utf8");
const rows = async (query, params = []) => (await db.query(query, params)).rows;
const count = async (table) => (await rows(`select count(*)::integer as n from ${table}`))[0].n;
const asAnon = async (action) => {
  await db.exec("set role anon");
  try { return await action(); } finally { await db.exec("reset role"); }
};
const claim = (key = token) => rows("select * from public.imagekit_cleanup_claim($1)", [key]);
const finish = (job, error = null) => rows("select public.imagekit_cleanup_finish($1, $2, $3, $4)", [token, job.id, job.lease_token, error]);
const insert = (rowId, images = urls) => rows("insert into public.prediction_logs values ($1,$2,$3,$4)", [rowId, ...images]);
const nextNumber = async (category, key = token) => Number((await rows("select public.imagekit_next_number($1, $2) as serial", [category, key]))[0].serial);

try {
  await db.exec(`
    create role anon; create role authenticated; create role service_role;
    create table public.prediction_logs (
      id uuid primary key, image_url text, xai_overlay_url text, xai_energy_overlay_url text
    );
  `);
  await insert(id);
  await db.exec(sql);
  assert.equal(await count("public.prediction_logs"), 1);
  assert.equal(await count("imagekit_cleanup.jobs"), 0);
  await assert.rejects(asAnon(() => rows("select * from imagekit_cleanup.jobs")), /permission denied/);
  await assert.rejects(asAnon(() => rows("select * from imagekit_cleanup.config")), /permission denied/);
  await assert.rejects(asAnon(() => claim("wrong")), /Invalid cleanup token/);
  assert.deepEqual(await asAnon(() => claim()), []);

  await db.exec("begin");
  await rows("delete from public.prediction_logs where id=$1", [id]);
  assert.equal(await count("imagekit_cleanup.jobs"), 1);
  await db.exec("rollback");
  assert.equal(await count("imagekit_cleanup.jobs"), 0);
  assert.equal(await count("public.prediction_logs"), 1);

  await rows("delete from public.prediction_logs where id=$1", [id]);
  const job = (await asAnon(() => claim()))[0];
  assert.equal(job.prediction_id, id);
  assert.deepEqual(job.image_urls, urls);
  assert.deepEqual(await asAnon(() => claim()), []); // Lease prevents duplicate workers.
  await asAnon(() => finish({ ...job, lease_token: otherId }));
  assert.equal(await count("imagekit_cleanup.jobs"), 1);
  await asAnon(() => finish(job, "ProviderError"));
  assert.deepEqual(await asAnon(() => claim()), []); // Backoff, not immediate retry.
  let pending = (await rows("select *, next_attempt_at > now() as delayed from imagekit_cleanup.jobs"))[0];
  assert.equal(pending.attempts, 1);
  assert.equal(pending.last_error, "ProviderError");
  assert.equal(pending.delayed, true);
  await db.exec("update imagekit_cleanup.jobs set next_attempt_at=now()");
  const second = (await asAnon(() => claim()))[0];
  assert.notEqual(second.lease_token, job.lease_token);
  await asAnon(() => finish(job)); // Stale acknowledgement cannot consume a new lease.
  assert.equal(await count("imagekit_cleanup.jobs"), 1);
  await db.exec("update imagekit_cleanup.jobs set leased_until=now()-interval '1 second'");
  const recovered = (await asAnon(() => claim()))[0];
  assert.ok(recovered);
  await asAnon(() => finish(recovered));
  assert.equal(await count("imagekit_cleanup.jobs"), 0);

  // Restored/shared live URLs are never claimed for deletion.
  await insert(id);
  await rows("delete from public.prediction_logs where id=$1", [id]);
  await insert(otherId);
  assert.deepEqual(await asAnon(() => claim()), []);
  await db.exec("truncate public.prediction_logs");
  assert.equal(await count("imagekit_cleanup.jobs"), 2);
  await db.exec(sql); // Reapplying preserves pending jobs.
  assert.equal(await count("imagekit_cleanup.jobs"), 2);
  while ((pending = (await asAnon(() => claim()))[0])) {
    await asAnon(() => finish(pending));
  }
  assert.equal(await count("imagekit_cleanup.jobs"), 0);

  await insert(id, [null, null, null]);
  await rows("delete from public.prediction_logs where id=$1", [id]);
  assert.equal(await count("imagekit_cleanup.jobs"), 0);

  await db.exec(serialSql);
  await assert.rejects(asAnon(() => rows("select * from imagekit_cleanup.image_numbers")), /permission denied/);
  await assert.rejects(asAnon(() => nextNumber("plastic", "wrong")), /Invalid cleanup token/);
  await assert.rejects(asAnon(() => nextNumber("other")), /check constraint/);
  assert.equal(await asAnon(() => nextNumber("plastic")), 1);
  assert.equal(await asAnon(() => nextNumber("manual")), 1);
  const numbers = await Promise.all(Array.from({ length: 12 }, () => nextNumber("plastic")));
  assert.deepEqual(numbers.sort((a, b) => a - b), Array.from({ length: 12 }, (_, i) => i + 2));
  await db.exec("truncate public.prediction_logs");
  await db.exec(serialSql);
  assert.equal(await asAnon(() => nextNumber("plastic")), 14);
  assert.equal(await asAnon(() => nextNumber("manual")), 2);
  console.log("PASS: cleanup migration, permissions, ownership of live URLs, retries, and persistent numbering by group.");
} finally {
  await db.close();
}
