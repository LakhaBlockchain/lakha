import plyvel
import json
import os

def dump_leveldb(db_path):
    if not os.path.exists(db_path):
        print(f"DB path does not exist: {db_path}")
        return
    db = plyvel.DB(db_path, create_if_missing=False)
    print(f"\n--- Dumping LevelDB at {db_path} ---\n")
    for key, value in db:
        try:
            k = key.decode()
        except Exception:
            k = str(key)
        try:
            v = value.decode()
        except Exception:
            v = str(value)
        if k.startswith('block:'):
            try:
                v_json = json.loads(v)
                print(f"{k}: [Block index: {v_json.get('index')}, Hash: {v_json.get('hash')}]\n  Transactions: {len(v_json.get('transactions', []))}")
            except Exception:
                print(f"{k}: [Could not decode block JSON]")
        else:
            print(f"{k}: {v[:100]}{'...' if len(v) > 100 else ''}")
    db.close()

if __name__ == "__main__":
    dump_leveldb("test_lakha_db") 