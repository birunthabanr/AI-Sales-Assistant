import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Load Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_all_customers() -> list:
    """Retrieve all customers from the database."""
    try:
        response = supabase.table("customer").select("*").execute()
        return response.data
    except Exception as e:
        raise Exception(f"Failed to retrieve customers: {str(e)}")

async def test_get_all_customers():
    """Test the get_all_customers functionality"""
    try:
        customers = await get_all_customers()
        
        print("=== Test: get_all_customers ===")
        print(f"Found {len(customers)} customers")
        
        if customers:
            print("\nCustomer data:")
            for customer in customers:
                print(f"ID: {customer.get('customerid')}, Name: {customer.get('full_name')}, "
                      f"Phone: {customer.get('phno')}, Address: {customer.get('address')}, "
                      f"DOB: {customer.get('dob')}")
        
        return customers
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

if __name__ == "__main__":
    asyncio.run(test_get_all_customers())