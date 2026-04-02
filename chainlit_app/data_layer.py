import chainlit.data as cl_data
from chainlit.user import PersistedUser, User
from typing import List, Optional, Dict
from chainlit.types import (
    Feedback,
    PaginatedResponse,
    Pagination,
    PageInfo,
    ThreadDict,
    ThreadFilter,
)
from datetime import datetime, timezone
from tinydb import TinyDB, Query
import os
from dotenv import load_dotenv

tinydb = TinyDB("chat_db.json")
Conversation = Query()


load_dotenv()

CHAINLIT_AUTH_SECRET_key = os.getenv("CHAINLIT_AUTH_SECRET", "")

os.environ["CHAINLIT_AUTH_SECRET"] = CHAINLIT_AUTH_SECRET_key

class CustomDataLayer(cl_data.BaseDataLayer):

    async def close(self):
        print("close called")
        pass

    async def get_element(self, element_id: str):
        print("get_element called")
        pass

    async def get_favorite_steps(self):
        print("get_favorite_steps called")
        pass

    async def get_user(self, identifier: str) -> Optional["PersistedUser"]:
        print("get_user called")
        return PersistedUser(
            identifier=identifier,
            display_name=identifier,
            metadata={},
            id=identifier,
            createdAt="2026-03-07T12:00:00Z"
        )
    
    async def create_user(self, user: "User") -> Optional["PersistedUser"]:
        print("create_user called")
        pass

    async def delete_feedback(self, feedback_id: str) -> bool:
        print("delete_feedback called")
        pass

    async def upsert_feedback(self, feedback: Feedback) -> str:
        print("upsert_feedback called")
        
        existing_thread = tinydb.get(Conversation.id == feedback.threadId)
        now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        feedback_json = {"value": feedback.value, "comment": feedback.comment, "createdAt": now}

        steps = existing_thread["steps"]
        for step in steps:
            if step["feedbackId"] == feedback.forId:
                step["feedback"] = feedback_json
                break

        tinydb.update({"steps": steps}, Conversation.id == feedback.threadId)

    async def create_element(self, element: "Element"):
        print("create_element called")
        pass

    async def get_element(self, thread_id: str, element_id: str) -> Optional["ElementDict"]:
        print("get_element called")
        pass

    async def delete_element(self, element_id: str, thread_id: Optional[str] = None):
        print("delete_element called")
        pass

    # async def create_step(self, step_dict: "StepDict"):
    #     print("create_step called")
    #     if "_message" in step_dict["type"]:
    #         step_dict["feedbackId"] = step_dict["parentId"]
    #         step_dict["parentId"] = None

    #         existing_thread = tinydb.get(Conversation.id == step_dict["threadId"])

    #         steps = existing_thread["steps"]
    #         steps.append(step_dict)

    #         tinydb.update({"steps": steps}, Conversation.id == step_dict["threadId"])

    async def create_step(self, step_dict: "StepDict"):
        print("create_step called")

        # ✅ Ensure timestamp exists (FIXES KeyError: createdAt)
        now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        step_dict["createdAt"] = now

        if "_message" in step_dict["type"]:
            step_dict["feedbackId"] = step_dict.get("parentId")
            step_dict["parentId"] = None

        # ✅ Ensure thread exists (FIXES NoneType error)
        existing_thread = tinydb.get(Conversation.id == step_dict["threadId"])

        if not existing_thread:
            print("⚠️ Thread not found, creating new thread")

            thread = {
                "id": step_dict["threadId"],
                "createdAt": now,
                "name": "New Chat",
                "userId": "anonymous",
                "userIdentifier": "anonymous",
                "tags": [],
                "metadata": {},
                "steps": []
            }
            tinydb.insert(thread)
            existing_thread = thread

        steps = existing_thread.get("steps", [])
        steps.append(step_dict)

        tinydb.update({"steps": steps}, Conversation.id == step_dict["threadId"])



    async def update_step(self, step_dict: "StepDict"):
        print("update_step called")
        pass

    async def delete_step(self, step_id: str):
        print("delete_step called")
        pass

    async def get_thread_author(self, thread_id: str) -> str:
        print("get_thread_author called")
        item = tinydb.get(Conversation.id == thread_id)
        return item.get("userIdentifier", "")

    async def delete_thread(self, thread_id: str):
        print("delete_thread called")
        tinydb.remove(Conversation.id == thread_id)

    async def list_threads(self, pagination: "Pagination", filters: "ThreadFilter") -> "PaginatedResponse[ThreadDict]":
        print("list_threads called")

        results = tinydb.all()

        page_info = PageInfo(
            hasNextPage=False,
            startCursor=None,
            endCursor=None
        )

        return PaginatedResponse(pageInfo=page_info, data=results)

    # async def get_thread(self, thread_id: str) -> Optional[ThreadDict]:
    #     print("get_thread called")
    #     item = tinydb.get(Conversation.id == thread_id)
    #     return item
    
    async def get_thread(self, thread_id: str) -> Optional[ThreadDict]:
        print("get_thread called")

        item = tinydb.get(Conversation.id == thread_id)

        if item and "steps" in item:
            for step in item["steps"]:
                if "createdAt" not in step:
                    step["createdAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        return item



    async def update_thread(
            self,
            thread_id: str,
            name: Optional[str] = None,
            user_id: Optional[str] = None,
            metadata: Optional[Dict] = None,
            tags: Optional[List[str]] = None,
    ):
        print("update_thread called")  

        existing_thread = tinydb.get(Conversation.id == thread_id)
        if existing_thread:
            if name is not None:
                tinydb.update(
                    {"name": name},
                    Conversation.id == thread_id
                )
        else:
            now = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
            thread = {
                "id": thread_id,
                "createdAt": now,
                "name": name,
                "userId": user_id,
                "userIdentifier": user_id,
                "tags": tags,
                "metadata": metadata,
                "steps": []
            }
            tinydb.insert(thread)

    async def build_debug_url(self) -> str:
        print("build_debug_url called")
        pass
