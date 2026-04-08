"""
Inference Script — SQL Query Craft
===================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
    LOCAL_IMAGE_NAME The name of the local image to use for the environment if you are using from_docker_image()

STDOUT FORMAT
- The script emits exactly three line types to stdout:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> rewards=<r1,r2,...,rn>
"""

import asyncio
import os
import textwrap
from typing import List, Optional

from openai import OpenAI

from client import SQLQueryCraftEnv
from models import SQLAction

IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME") or os.getenv("IMAGE_NAME")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
BENCHMARK = "sql_query_craft"
TEMPERATURE = 0.3
MAX_TOKENS = 512
MIN_REWARD = 0.05
MAX_REWARD = 0.95

ALL_TASKS = [
    "easy_employee_lookup",
    "medium_sales_analysis",
    "hard_department_top_earner",
    "hard_customer_spending",
]

SYSTEM_PROMPT = textwrap.dedent("""\
You are an expert SQL analyst. You are given a natural language question about a business database
and the database schema. Your job is to write a SQL query that answers the question.

Rules:
- Write only a single SELECT statement.
- Do NOT include any explanation, only the SQL query.
- Use the exact column aliases specified in the question.
- Pay attention to filtering conditions (WHERE, HAVING).
- Use JOINs when data spans multiple tables.
- For rounding, use ROUND(value, decimals).
- Ensure correct ORDER BY as specified.
- Do NOT use semicolons at the end.

Respond with ONLY the SQL query, nothing else.
""")


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_clean = action.replace("\n", " ").strip()
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)


def build_user_prompt(
    question: str,
    schema: str,
    expected_columns: List[str],
    hints: str,
    last_result: str,
    last_error: str,
    step: int,
    reward_breakdown: dict,
) -> str:
    parts = [f"QUESTION:\n{question}\n"]
    parts.append(f"EXPECTED COLUMNS: {', '.join(expected_columns)}\n")

    if step == 1:
        parts.append(f"SCHEMA:\n{schema}\n")
        if hints:
            parts.append(f"HINTS:\n{hints}\n")
    else:
        if last_error:
            parts.append(f"YOUR PREVIOUS QUERY HAD AN ERROR:\n{last_error}\n")
        elif last_result:
            parts.append(f"YOUR PREVIOUS QUERY RETURNED:\n{last_result}\n")
        if reward_breakdown:
            parts.append(f"REWARD BREAKDOWN: {reward_breakdown}\n")
        parts.append("Fix the issues and write an improved SQL query.")

    parts.append("Write your SQL query:")
    return "\n".join(parts)


def get_model_query(client: OpenAI, user_prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            text = "\n".join(lines).strip()
        return text if text else "SELECT 1"
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "SELECT 1"


async def run_task(llm_client: OpenAI, env: SQLQueryCraftEnv, task_name: str) -> None:
    rewards: List[float] = []
    steps_taken = 0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task_name=task_name)
        obs = result.observation

        max_steps = obs.max_steps

        for step in range(1, max_steps + 1):
            if result.done:
                break

            user_prompt = build_user_prompt(
                question=obs.question,
                schema=obs.schema_description,
                expected_columns=obs.expected_columns,
                hints=obs.hints,
                last_result=obs.query_result,
                last_error=obs.query_error,
                step=step,
                reward_breakdown=obs.reward_breakdown,
            )

            query = get_model_query(llm_client, user_prompt)

            result = await env.step(SQLAction(query=query))
            obs = result.observation

            reward = result.reward if result.reward is not None else MIN_REWARD
            done = result.done
            error = obs.query_error if obs.query_error else None

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=query, reward=reward, done=done, error=error)

            if done:
                break

        success = any(r >= 0.95 for r in rewards) if rewards else False

    finally:
        log_end(success=success, steps=steps_taken, rewards=rewards)


async def main() -> None:
    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    for task_name in ALL_TASKS:
        if IMAGE_NAME:
            env = await SQLQueryCraftEnv.from_docker_image(IMAGE_NAME)
        else:
            base_url = os.getenv("ENV_BASE_URL", "http://localhost:8000")
            env = SQLQueryCraftEnv(base_url=base_url)

        try:
            await run_task(llm_client, env, task_name)
        finally:
            try:
                await env.close()
            except Exception as e:
                print(f"[DEBUG] env.close() error: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
