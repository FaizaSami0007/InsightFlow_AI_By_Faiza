import asyncio
import httpx
import json
from app.database.session import async_session_factory
from app.database.models.user import User
from app.database.models.dataset import Dataset
from app.users.security import create_access_token
from sqlalchemy import select

QUESTIONS = [
    "What channel has the highest cost?",
    "Which region has the highest revenue?",
    "Which product has the highest profit?",
    "What is the total revenue?",
    "What is the average customer satisfaction?",
    "Show profit by channel.",
    "Show revenue by region.",
    "Which product has the lowest profit margin?",
    "Show monthly revenue.",
    "Which channel has the lowest cost?"
]

async def test_generalization():
    async with async_session_factory() as db:
        res_u = await db.execute(select(User).where(User.email == "demo@insightflow.ai"))
        user = res_u.scalar_one()
        token = create_access_token({"sub": user.id, "email": user.email})
        
        res_d = await db.execute(select(Dataset).where(Dataset.owner_id == user.id))
        ds = res_d.scalars().first()
        ver = ds.versions[0]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
            print(f"=== TESTING 10 ANALYTICAL QUESTIONS ON DATASET: {ds.name} ===\n")
            for idx, q in enumerate(QUESTIONS, 1):
                payload = {
                    "dataset_id": ds.id,
                    "dataset_version_id": ver.id,
                    "message": q
                }
                res = await client.post("/api/v1/ai/chat", headers=headers, json=payload, timeout=30.0)
                assert res.status_code == 200, f"Failed for {q}: {res.text}"
                data = res.json()
                conv_id = data["conversation_id"]
                
                res_tasks = await client.get(f"/api/v1/ai/conversations/{conv_id}/tasks", headers=headers)
                task_count = len(res_tasks.json())
                
                tool_names = [tc["name"] for tc in data.get("tool_calls", [])]
                tool_args = [tc.get("arguments", {}) for tc in data.get("tool_calls", [])]
                
                args_str = json.dumps(tool_args)
                has_placeholder = ("\"dimension\"" in args_str) or ("\"metric\"" in args_str)
                
                first_line = data["message"].split("\n")[0]
                print(f"[{idx}/10] Q: {q}")
                print(f"  -> Tools: {tool_names}")
                print(f"  -> Placeholder present: {has_placeholder}")
                print(f"  -> DAG Task Count: {task_count}")
                print(f"  -> Answer:\n     {first_line}")
                if "\n\n**Complete Breakdown:**" in data["message"]:
                    breakdown = data["message"].split("\n\n**Complete Breakdown:**")[1]
                    for line in breakdown.strip().splitlines()[:3]:
                        print(f"     {line}")
                print()

if __name__ == "__main__":
    asyncio.run(test_generalization())
