import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1") as client:
        # Login
        response = await client.post("/auth/login", json={"email": "admin@example.com", "password": "admin123"})
        if response.status_code != 200:
            print("Login failed:", response.text)
            return
        token = response.json()["access_token"]
        
        # Borrow device 8
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "pihak_1_id": 1,
            "pihak_2_id": 2,
            "assignment_letter_number": "01/BALMON.18/TEST/2026",
            "assignment_letter_date": "2026-04-24",
            "borrower_name": "Test User",
            "activity_name": "Testing",
            "usage_duration_days": 1,
            "loan_start_date": "2026-04-24",
            "purpose": "Test",
            "monitoring_devices": "Test",
            "loan_items": [
                {
                    "device_id": 8,
                    "quantity": 1,
                    "condition_before": "BAIK"
                }
            ]
        }
        resp = await client.post("/loans/", json=payload, headers=headers)
        print("Status:", resp.status_code)
        print("Response:", resp.text)

if __name__ == "__main__":
    asyncio.run(main())
