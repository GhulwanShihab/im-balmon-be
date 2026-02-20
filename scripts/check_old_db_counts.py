
from sqlalchemy import create_engine, text

# Try common names
dbs = ["im_balmon", "imbalmon_old", "im-balmon", "imbalmon"]

for db in dbs:
    uri = f"postgresql://postgres:password@127.0.0.1:5432/{db}"
    print(f"Trying {db}...")
    try:
        engine = create_engine(uri)
        with engine.connect() as conn:
            res = conn.execute(text("SELECT count(*) FROM devices"))
            count = res.scalar()
            print(f"Connected to {db}. Devices count: {count}")
            
            res = conn.execute(text("SELECT id FROM devices"))
            ids = [r[0] for r in res]
            print(f"Device IDs: {ids}")

            res = conn.execute(text("SELECT count(*) FROM device_children"))
            c_count = res.scalar()
            print(f"Device Children count: {c_count}")
            
            res = conn.execute(text("SELECT count(*) FROM device_loan_items"))
            i_count = res.scalar()
            print(f"Device Loan Items count: {i_count}")
    except Exception as e:
        print(f"Failed {db}: {e}")
