import { DB } from "https://deno.land/x/sqlite/mod.ts";
import { join } from "https://deno.land/std/path/mod.ts";

// Database is in the parent folder
const dbPath = join(Deno.cwd(), "../emergency_support.db");
const db = new DB(dbPath);



const readAll = async () => {
  return await sql`SELECT * FROM resources`;
};

const readOne = async (id) => {
  const result = await sql`SELECT * FROM resources WHERE id = ${id}`;
  return result[0];
};

const update = async (id, book) => {
  const result = await sql`UPDATE resources
    SET title = ${}, year = ${book.year}
    WHERE id = ${id}
    RETURNING *`;
  return result[0];
};

const remove = async (id) => {
  const result = await sql`DELETE FROM resources WHERE id = ${id} RETURNING *`;
  return result[0];
};


export default db;
export { create, readAll, readOne, remove, update };