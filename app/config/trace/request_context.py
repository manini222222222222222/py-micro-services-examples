from contextvars import ContextVar
import contextvars

trace_id_var: ContextVar[str] = ContextVar("trace")

def set_trace_id(trace_id: str):
    trace_id_var.set(trace_id)

def get_trace_id() -> str:
    try:
        return trace_id_var.get()
    except LookupError:
        return None

def async_copy_ctx():
    return contextvars.copy_context()