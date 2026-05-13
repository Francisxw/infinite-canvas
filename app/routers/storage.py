from fastapi import APIRouter, Header, Request

from app.models.schemas import CanvasCreateRequest, CanvasSaveRequest, ConversationCreateRequest, DeleteHistoryRequest
from app.runtime import get_queue_status_for_client
from app.services.canvas_service import delete_canvas as delete_canvas_record, list_canvases, list_deleted_canvases, load_canvas, new_canvas, purge_canvas as purge_canvas_record, restore_canvas as restore_canvas_record, update_canvas as update_canvas_record
from app.services.conversation_service import delete_conversation, load_conversation, new_conversation, safe_user_id
from app.services.conversation_service import list_conversations
from app.services.history_service import delete_history_entry, get_history


router = APIRouter()


@router.get("/api/conversations")
async def conversations(request: Request, x_user_id: str = Header(default="")):
    user_id = safe_user_id(x_user_id, request)
    return {"user_id": user_id, "conversations": list_conversations(user_id)}


@router.post("/api/conversations")
async def create_conversation(payload: ConversationCreateRequest, request: Request, x_user_id: str = Header(default="")):
    user_id = safe_user_id(x_user_id, request)
    return {"conversation": new_conversation(user_id, payload.title)}


@router.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, request: Request, x_user_id: str = Header(default="")):
    user_id = safe_user_id(x_user_id, request)
    return {"conversation": load_conversation(user_id, conversation_id)}


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation_route(conversation_id: str, request: Request, x_user_id: str = Header(default="")):
    user_id = safe_user_id(x_user_id, request)
    delete_conversation(user_id, conversation_id)
    return {"ok": True}


@router.get("/api/canvases")
async def canvases():
    return {"canvases": list_canvases()}


@router.get("/api/canvases/trash")
async def trashed_canvases():
    return {"canvases": list_deleted_canvases(), "retention_days": 30}


@router.post("/api/canvases")
async def create_canvas(payload: CanvasCreateRequest):
    return {"canvas": new_canvas(payload.title, payload.icon)}


@router.get("/api/canvases/{canvas_id}")
async def get_canvas(canvas_id: str):
    return {"canvas": load_canvas(canvas_id)}


@router.put("/api/canvases/{canvas_id}")
async def update_canvas(canvas_id: str, payload: CanvasSaveRequest):
    canvas = update_canvas_record(canvas_id, payload.title, payload.icon, payload.nodes, payload.connections, payload.viewport)
    return {"canvas": canvas}


@router.delete("/api/canvases/{canvas_id}")
async def delete_canvas(canvas_id: str):
    delete_canvas_record(canvas_id)
    return {"ok": True}


@router.post("/api/canvases/{canvas_id}/restore")
async def restore_canvas(canvas_id: str):
    canvas = restore_canvas_record(canvas_id)
    return {"canvas": canvas}


@router.delete("/api/canvases/{canvas_id}/purge")
async def purge_canvas(canvas_id: str):
    purge_canvas_record(canvas_id)
    return {"ok": True}


@router.get("/api/history")
async def get_history_api(type: str = None):
    return get_history(type)


@router.get("/api/queue_status")
async def get_queue_status(client_id: str):
    return get_queue_status_for_client(client_id)


@router.post("/api/history/delete")
async def delete_history(req: DeleteHistoryRequest):
    return delete_history_entry(req.timestamp)
