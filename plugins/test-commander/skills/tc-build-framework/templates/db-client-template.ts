// Database-client template - copy into tests/db/client.ts and adapt to your store.
// Database-layer assertions confirm that values written through the UI/API actually
// persisted with the right shape and relationships - not just what the API echoed back.
// See methodology/database-assertions.md.
//
// This example uses MongoDB; swap the driver and queries for your datastore. The
// pattern is the same: connect once per worker (a worker-scoped fixture), expose a
// few query helpers, and account for how the store represents IDs vs the API.
import { MongoClient, ObjectId, type Db, type Document } from 'mongodb';

// IDs are commonly stored differently from how the API returns them (here: ObjectId
// in the store vs a string over the wire). Centralize that translation.
const DB_URL = process.env.DB_URL ?? 'mongodb://localhost:27017';
const DB_NAME = process.env.DB_NAME ?? '<your-database>';

export class DbClient {
  private constructor(
    private readonly client: MongoClient,
    readonly db: Db,
  ) {}

  static async connect(): Promise<DbClient> {
    const client = new MongoClient(DB_URL);
    await client.connect();
    return new DbClient(client, client.db(DB_NAME));
  }

  async close(): Promise<void> {
    await this.client.close();
  }

  /** Find a document by the id the API returned (a string). */
  findById(collection: string, id: string): Promise<Document | null> {
    return this.db.collection(collection).findOne({ _id: new ObjectId(id) });
  }

  count(collection: string, query: Document = {}): Promise<number> {
    return this.db.collection(collection).countDocuments(query);
  }
}

/** Compare a stored relationship reference to an API string id. */
export function idEquals(stored: unknown, apiId: string): boolean {
  return stored instanceof ObjectId && stored.toString() === apiId;
}
