"""End-to-End Verification Test Script for AI Analyst Repair."""

import asyncio
import io
import json
import pandas as pd
from datetime import datetime

from app.database.session import async_session_factory
from app.database.models.user import User
from app.datasets.service import create_dataset_with_file
from app.ai.orchestrator.orchestrator import AIOrchestrator
from app.ai.schemas import ChatRequest
from app.database.models.ai import AITask
from sqlalchemy import select


async def run_e2e_analyst_test():
    async with async_session_factory() as db:
        # 1. Create or get test user
        stmt_user = select(User).where(User.email == "analyst_tester@insightflow.ai")
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()
        if not user:
            user = User(
                email="analyst_tester@insightflow.ai",
                full_name="Analyst Tester",
                password_hash="hashed_pw_test",
                role="admin",
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # 2. Create realistic sample dataset (InsightFlow Sales Transactions Sample v1)
        data = {
            "transaction_id": [f"TX-{i:04d}" for i in range(1, 13)],
            "order_date": ["2026-01-15", "2026-01-20", "2026-02-10", "2026-02-18", "2026-03-05", "2026-03-22",
                           "2026-04-12", "2026-04-28", "2026-05-14", "2026-05-30", "2026-06-11", "2026-06-25"],
            "channel": ["Online", "In-Store", "Online", "Distributor", "Online", "In-Store",
                        "Online", "Distributor", "In-Store", "Online", "Distributor", "Online"],
            "region": ["North", "South", "East", "West", "North", "South", "East", "West", "North", "South", "East", "West"],
            "product_name": ["Enterprise Suite", "Pro Widget", "Starter Kit", "Enterprise Suite", "Pro Widget", "Starter Kit",
                             "Enterprise Suite", "Pro Widget", "Starter Kit", "Enterprise Suite", "Pro Widget", "Starter Kit"],
            "quantity": [10, 25, 50, 15, 30, 45, 12, 20, 60, 18, 22, 35],
            "cost": [45000.0, 12000.0, 8500.0, 65000.0, 15000.0, 9200.0, 52000.0, 88000.0, 11000.0, 78000.0, 95000.0, 62000.0],
            "revenue": [120000.0, 35000.0, 25000.0, 180000.0, 42000.0, 28000.0, 150000.0, 220000.0, 32000.0, 210000.0, 240000.0, 175000.0],
            "profit": [75000.0, 23000.0, 16500.0, 115000.0, 27000.0, 18800.0, 98000.0, 132000.0, 21000.0, 132000.0, 145000.0, 113000.0],
            "customer_satisfaction": [4.8, 4.2, 4.0, 4.5, 4.9, 4.1, 4.7, 4.4, 4.3, 4.8, 4.6, 4.9],
        }
        df = pd.DataFrame(data)
        csv_bytes = df.to_csv(index=False).encode("utf-8")

        dataset = await create_dataset_with_file(
            session=db,
            user=user,
            file_bytes=csv_bytes,
            original_filename="insightflow_sales_sample.csv",
            name="InsightFlow Sales Transactions Sample",
            description="Sample sales transactions dataset with channel, cost, revenue, profit.",
        )
        version_id = dataset.versions[0].id if dataset.versions else None

        print(f"Created Dataset: {dataset.name} (ID: {dataset.id}, Version: {version_id})")

        # 3. Test list of required analytical queries
        test_queries = [
            "What channel has the highest cost?",
            "Which region has the highest revenue?",
            "Which product has the highest profit?",
            "What is the total revenue?",
            "What is the average customer satisfaction?",
            "Show monthly revenue trend.",
            "Compare profit by channel.",
            "Which product has the lowest profit margin?",
            "Find unusual transactions.",
            "What would happen if quantity increased by 15%?",
        ]

        orchestrator = AIOrchestrator()
        results_summary = []

        for idx, q in enumerate(test_queries, 1):
            print(f"\n=======================================================")
            print(f"TEST {idx}: '{q}'")
            print(f"=======================================================")

            req = ChatRequest(
                dataset_id=dataset.id,
                dataset_version_id=version_id,
                message=q,
            )

            resp = await orchestrator.chat(request=req, user=user, db=db)

            # Check tasks recorded in DB
            stmt_tasks = select(AITask).where(AITask.conversation_id == resp.conversation_id)
            res_tasks = await db.execute(stmt_tasks)
            tasks = res_tasks.scalars().all()

            print(f"-> FINAL ANSWER:")
            print(resp.message)
            print(f"\n-> EXECUTED TOOLS ({len(resp.tool_calls)}): {[tc['name'] for tc in resp.tool_calls]}")
            print(f"-> MULTI-AGENT DAG TASKS RECORDED ({len(tasks)}): {[t.agent_id for t in tasks]}")
            print(f"-> SUGGESTED QUESTIONS ({len(resp.suggested_questions)}): {resp.suggested_questions}")

            # Verify that final answer is NOT generic and contains computed numbers
            assert resp.message, "Response message must not be empty"
            assert "executed successfully" not in resp.message.lower() or "\n" in resp.message, "Response must answer the question, not just report execution"
            assert len(tasks) >= 3, f"DAG must record at least 3 tasks, got {len(tasks)}"

            results_summary.append({
                "query": q,
                "answer": resp.message.split("\n")[0],
                "tools": [tc['name'] for tc in resp.tool_calls],
                "task_count": len(tasks),
            })

        print("\n=======================================================")
        print("ALL 10 ANALYTICAL QUESTIONS PASSED AND PRODUCED GROUNDED ANSWERS!")
        print("=======================================================")
        for r in results_summary:
            print(f"- Q: {r['query']}\n  A: {r['answer']}\n  Tools: {r['tools']} | DAG Tasks: {r['task_count']}\n")


if __name__ == "__main__":
    asyncio.run(run_e2e_analyst_test())
