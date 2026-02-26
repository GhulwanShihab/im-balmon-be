import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import async_session
from src.repositories.employee import EmployeeRepository
from src.models.employee import Employee
from src.schemas.employee import EmployeeCreate
from src.services.employee import EmployeeService

async def test_duplicate_employee():
    async with async_session() as session:
        repo = EmployeeRepository(session)
        service = EmployeeService(repo)
        
        print("--- Testing Duplicate Employee Name ---")
        
        # 1. Create first employee
        emp1_data = EmployeeCreate(nama="Budi Santoso", nip="1234567890", jabatan="Staff")
        try:
            emp1 = await service.create_employee(emp1_data)
            print(f"Created first employee: {emp1.nama} (ID: {emp1.id})")
        except Exception as e:
            print(f"Failed to create first employee: {e}")
            
        # 2. Attempt to create second employee with SAME NAME
        emp2_data = EmployeeCreate(nama="Budi Santoso", nip="0987654321", jabatan="Manager")
        try:
            emp2 = await service.create_employee(emp2_data)
            print(f"ERROR: Successfully created duplicate employee: {emp2.nama}")
        except Exception as e:
            print(f"SUCCESS: Caught expected error for duplicate name: {e}")

        # Cleanup
        try:
            if hasattr(emp1, "id"):
                await repo.delete(emp1)
                print("Cleaned up first employee.")
        except Exception as e:
            pass
            
if __name__ == "__main__":
    asyncio.run(test_duplicate_employee())
