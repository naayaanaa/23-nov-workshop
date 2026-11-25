"""Event browsing and registration API backed by Supabase."""

import os
from uuid import UUID

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
import httpx
from postgrest import APIError
from supabase import Client, create_client
from supabase.client import ClientOptions

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
FRONTEND_ASSETS = {"app.js", "config.js", "styles.css"}


@app.after_request
def add_cors_headers(response):
    # The static frontend is served separately from this API.
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client | None = (
    create_client(
        supabase_url,
        supabase_key,
        options=ClientOptions(httpx_client=httpx.Client(timeout=120, trust_env=False)),
    )
    if supabase_url and supabase_key
    else None
)


def db():
    if supabase is None:
        return None, (jsonify(error="Supabase is not configured; set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY."), 503)
    return supabase, None


def valid_uuid(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def database_error(error):
    # Supabase/PostgREST errors are returned as JSON rather than Flask HTML.
    return jsonify(error=getattr(error, "message", str(error))), 400


def supabase_connection_error():
    return jsonify(error="Could not connect to Supabase. Check the network and SUPABASE_URL."), 503


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:asset>")
def frontend_asset(asset):
    if asset not in FRONTEND_ASSETS:
        return jsonify(error="Not found"), 404
    return send_from_directory(FRONTEND_DIR, asset)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/api/events")
def list_events():
    client, error = db()
    if error:
        return error
    query = client.table("events").select("id,organizer_id,title,capacity,status")
    status = request.args.get("status")
    if status:
        query = query.eq("status", status)
    try:
        result = query.order("title").execute()
        return jsonify(data=result.data)
    except APIError as exc:
        return database_error(exc)
    except httpx.RequestError:
        return supabase_connection_error()


@app.get("/api/events/<event_id>")
def get_event(event_id):
    event_id = valid_uuid(event_id)
    if not event_id:
        return jsonify(error="event id must be a UUID"), 400
    client, error = db()
    if error:
        return error
    try:
        result = client.table("events").select("id,organizer_id,title,capacity,status").eq("id", event_id).limit(1).execute()
        if not result.data:
            return jsonify(error="Event not found"), 404
        return jsonify(data=result.data[0])
    except APIError as exc:
        return database_error(exc)
    except httpx.RequestError:
        return supabase_connection_error()


@app.post("/api/registrations")
def create_registration():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="Request body must be a JSON object"), 400
    user_id, event_id = valid_uuid(body.get("user_id")), valid_uuid(body.get("event_id"))
    if not user_id or not event_id:
        return jsonify(error="user_id and event_id are required UUIDs"), 400
    client, error = db()
    if error:
        return error
    try:
        event_result = client.table("events").select("id,capacity,status").eq("id", event_id).limit(1).execute()
        if not event_result.data:
            return jsonify(error="Event not found"), 404
        event = event_result.data[0]
        if event.get("status") and event["status"].lower() not in ("open", "active", "published"):
            return jsonify(error="Event is not open for registration"), 409
        if event.get("capacity") is not None:
            count_result = client.table("registrations").select("id", count="exact").eq("event_id", event_id).execute()
            if (count_result.count or 0) >= event["capacity"]:
                return jsonify(error="Event is full"), 409
        existing = client.table("registrations").select("id").eq("user_id", user_id).eq("event_id", event_id).limit(1).execute()
        if existing.data:
            return jsonify(error="User is already registered for this event"), 409
        result = client.table("registrations").insert({"user_id": user_id, "event_id": event_id}).execute()
        return jsonify(data=result.data[0] if result.data else {"user_id": user_id, "event_id": event_id}), 201
    except APIError as exc:
        # A unique constraint on (user_id, event_id) also prevents duplicate races.
        message = getattr(exc, "message", str(exc))
        if "duplicate" in message.lower() or "unique" in message.lower():
            return jsonify(error="User is already registered for this event"), 409
        return database_error(exc)
    except httpx.RequestError:
        return supabase_connection_error()


@app.get("/api/me/registrations")
def my_registrations():
    user_id = valid_uuid(request.args.get("user_id"))
    if not user_id:
        return jsonify(error="user_id query parameter must be a UUID"), 400
    client, error = db()
    if error:
        return error
    try:
        result = client.table("registrations").select("id,user_id,event_id,created_at,events(id,organizer_id,title,capacity,status)").eq("user_id", user_id).order("created_at", desc=True).execute()
        return jsonify(data=result.data)
    except APIError as exc:
        return database_error(exc)
    except httpx.RequestError:
        return supabase_connection_error()


@app.get("/api/events/<event_id>/registrations")
def event_registrations(event_id):
    event_id = valid_uuid(event_id)
    organizer_id = valid_uuid(request.args.get("organizer_id"))
    if not event_id:
        return jsonify(error="event id must be a UUID"), 400
    if not organizer_id:
        return jsonify(error="organizer_id query parameter must be a UUID"), 400
    client, error = db()
    if error:
        return error
    try:
        event = client.table("events").select("id,organizer_id").eq("id", event_id).limit(1).execute()
        if not event.data:
            return jsonify(error="Event not found"), 404
        if event.data[0]["organizer_id"] != organizer_id:
            return jsonify(error="Only the event organizer may view registrations"), 403
        result = client.table("registrations").select("id,user_id,event_id,created_at,users(id,email)").eq("event_id", event_id).order("created_at").execute()
        return jsonify(data=result.data)
    except APIError as exc:
        return database_error(exc)
    except httpx.RequestError:
        return supabase_connection_error()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
