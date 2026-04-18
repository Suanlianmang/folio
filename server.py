"""
server.py — Folio dashboard. Run from host project root:
    python3 tools/folio/server.py
"""

import atexit
import json
import mimetypes
import os
import re
import signal
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

_PID_FILE = Path.home() / ".folio" / "server.pid"
_UI_DIR = Path(__file__).resolve().parent / "ui"


def _write_pid() -> None:
    _PID_FILE.write_text(str(os.getpid()))


def _remove_pid() -> None:
    _PID_FILE.unlink(missing_ok=True)


def _handle_signal(sig, frame) -> None:
    _remove_pid()
    sys.exit(0)

# ---------------------------------------------------------------------------
# Path setup — db.py lives in the folio lib directory
# ---------------------------------------------------------------------------

_FOLIO_LIB = str(Path.home() / ".folio" / "lib")
if _FOLIO_LIB not in sys.path:
    sys.path.insert(0, _FOLIO_LIB)

import db

db.configure(Path.cwd())



# ---------------------------------------------------------------------------
# Request handler
# ---------------------------------------------------------------------------

# Compiled route patterns for parameterised paths.
_RE_UI          = re.compile(r"^/ui/([\w.\-]+)$")
_RE_DESIGN      = re.compile(r"^/design/(.+)$")
_RE_SCREENSHOTS = re.compile(r"^/screenshots/(.+)$")
_RE_SCREENSHOT  = re.compile(r"^/variants/(\d+)/screenshot$")

_RE_SCREENS        = re.compile(r"^/api/screens$")
_RE_SCREEN         = re.compile(r"^/api/screens/(\d+)$")
_RE_SCREEN_PARENT  = re.compile(r"^/api/screens/(\d+)/parent$")
_RE_SCREEN_VARS    = re.compile(r"^/api/screens/(\d+)/variants$")
_RE_SCREEN_VAR_SEL = re.compile(r"^/api/screen-variants/(\d+)/select$")
_RE_SCREEN_VAR     = re.compile(r"^/api/screen-variants/(\d+)$")

_RE_COMPONENTS        = re.compile(r"^/api/components$")
_RE_COMPONENT         = re.compile(r"^/api/components/(\d+)$")
_RE_COMPONENT_VARS    = re.compile(r"^/api/components/(\d+)/variants$")
_RE_COMPONENT_VAR_SEL = re.compile(r"^/api/component-variants/(\d+)/select$")
_RE_COMPONENT_VAR     = re.compile(r"^/api/component-variants/(\d+)$")
_RE_COMPONENT_LINK    = re.compile(r"^/api/components/(\d+)/link-screen$")

_RE_FLOWS        = re.compile(r"^/api/flows$")
_RE_FLOW         = re.compile(r"^/api/flows/(\d+)$")
_RE_FLOW_VARS    = re.compile(r"^/api/flows/(\d+)/variants$")
_RE_FLOW_VAR_SEL = re.compile(r"^/api/flow-variants/(\d+)/select$")
_RE_FLOW_VAR     = re.compile(r"^/api/flow-variants/(\d+)$")
_RE_FLOW_LINK    = re.compile(r"^/api/flows/(\d+)/link-screen$")


class FolioHandler(BaseHTTPRequestHandler):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            return {}

    def _send_response_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
        assert isinstance(body, bytes), "body must be bytes"
        assert content_type, "content_type must not be empty"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self._send_response_bytes(body, "application/json", status)

    def _send_html(self, html: str) -> None:
        assert html, "html must not be empty"
        body = html.encode("utf-8")
        self._send_response_bytes(body, "text/html; charset=utf-8", 200)

    def _serve_static(self, path: Path) -> None:
        assert path is not None, "path must not be None"
        if not path.exists():
            self._not_found()
            return
        mime, _ = mimetypes.guess_type(str(path))
        if mime is None:
            mime = "application/octet-stream"
        body = path.read_bytes()
        self._send_response_bytes(body, mime, 200)

    def _serve_dashboard(self) -> None:
        html = (_UI_DIR / "dashboard.html").read_text(encoding="utf-8")
        project = Path.cwd().name
        html = html.replace("{{PROJECT_NAME}}", project)
        self._send_html(html)

    def _not_found(self, msg: str = "Not found") -> None:
        self._send_json({"error": msg}, 404)

    def _parse_multipart_file(self) -> bytes | None:
        """Extract first file payload from multipart/form-data body."""
        from email.parser import BytesParser
        content_type = self.headers.get("Content-Type", "")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        raw = f"Content-Type: {content_type}\r\n\r\n".encode() + body
        msg = BytesParser().parsebytes(raw)
        for part in msg.walk():
            cd = part.get("Content-Disposition", "")
            if "filename" in cd:
                return part.get_payload(decode=True)
        return None

    def log_message(self, *args) -> None:
        # Suppress default Apache-style per-request logging.
        pass

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._serve_dashboard()
            return

        match = _RE_UI.match(path)
        if match:
            self._serve_static(_UI_DIR / match.group(1))
            return

        match = _RE_DESIGN.match(path)
        if match:
            self._serve_static(db.DESIGN_DIR / unquote(match.group(1)))
            return

        match = _RE_SCREENSHOTS.match(path)
        if match:
            self._serve_static(db.SCREENSHOTS_DIR / unquote(match.group(1)))
            return

        if path == "/system.md":
            if not db.SYSTEM_MD_PATH.exists():
                self._not_found("system.md not found")
                return
            body = db.SYSTEM_MD_PATH.read_text(encoding="utf-8").encode("utf-8")
            self._send_response_bytes(body, "text/plain; charset=utf-8", 200)
            return

        if _RE_SCREENS.match(path):
            self._send_json(db.list_screens())
            return

        if _RE_COMPONENTS.match(path):
            self._send_json(db.list_components())
            return

        if _RE_FLOWS.match(path):
            self._send_json(db.list_flows())
            return

        self._not_found()

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if _RE_SCREENS.match(path):
            self._handle_create_screen()
            return

        match = _RE_SCREEN_VARS.match(path)
        if match:
            self._handle_create_screen_variant(int(match.group(1)))
            return

        if _RE_COMPONENTS.match(path):
            self._handle_create_component()
            return

        match = _RE_COMPONENT_VARS.match(path)
        if match:
            self._handle_create_component_variant(int(match.group(1)))
            return

        match = _RE_COMPONENT_LINK.match(path)
        if match:
            self._handle_link_component_screen(int(match.group(1)))
            return

        if _RE_FLOWS.match(path):
            self._handle_create_flow()
            return

        match = _RE_FLOW_VARS.match(path)
        if match:
            self._handle_create_flow_variant(int(match.group(1)))
            return

        match = _RE_FLOW_LINK.match(path)
        if match:
            self._handle_link_flow_screen(int(match.group(1)))
            return

        match = _RE_SCREENSHOT.match(path)
        if match:
            self._handle_upload_screenshot(int(match.group(1)))
            return

        self._not_found()

    def _handle_create_screen(self) -> None:
        data = self._read_json()
        try:
            screen = db.create_screen(
                name=data.get("name", ""),
                description=data.get("description"),
                usage=data.get("usage"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return

        first_file = data.get("file")
        if first_file:
            try:
                variant = db.create_screen_variant(
                    screen_id=screen["id"],
                    file=first_file,
                    label="v1",
                    ui_description=None,
                    notes=None,
                )
                db.select_screen_variant(variant["id"])
                screen = db.get_screen(screen["id"])
            except (ValueError, AssertionError) as exc:
                self._send_json({"error": str(exc)}, 400)
                return

        self._send_json(screen, 201)

    def _handle_create_component(self) -> None:
        data = self._read_json()
        try:
            component = db.create_component(
                name=data.get("name", ""),
                description=data.get("description"),
                usage=data.get("usage"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return

        first_file = data.get("file")
        if first_file:
            try:
                variant = db.create_component_variant(
                    component_id=component["id"],
                    file=first_file,
                    label="v1",
                    ui_description=None,
                    notes=None,
                )
                db.select_component_variant(variant["id"])
                component = db.get_component(component["id"])
            except (ValueError, AssertionError) as exc:
                self._send_json({"error": str(exc)}, 400)
                return

        self._send_json(component, 201)

    def _handle_create_flow(self) -> None:
        data = self._read_json()
        try:
            flow = db.create_flow(
                name=data.get("name", ""),
                description=data.get("description"),
                usage=data.get("usage"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(flow, 201)

    def _handle_create_screen_variant(self, screen_id: int) -> None:
        assert screen_id > 0, "screen_id must be positive"
        data = self._read_json()
        try:
            variant = db.create_screen_variant(
                screen_id=screen_id,
                file=data.get("file", ""),
                label=data.get("label"),
                ui_description=data.get("ui_description"),
                notes=data.get("notes"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(variant, 201)

    def _handle_create_component_variant(self, component_id: int) -> None:
        assert component_id > 0, "component_id must be positive"
        data = self._read_json()
        try:
            variant = db.create_component_variant(
                component_id=component_id,
                file=data.get("file", ""),
                label=data.get("label"),
                ui_description=data.get("ui_description"),
                notes=data.get("notes"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(variant, 201)

    def _handle_create_flow_variant(self, flow_id: int) -> None:
        assert flow_id > 0, "flow_id must be positive"
        data = self._read_json()
        try:
            variant = db.create_flow_variant(
                flow_id=flow_id,
                file=data.get("file", ""),
                label=data.get("label"),
                ui_description=data.get("ui_description"),
                notes=data.get("notes"),
            )
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(variant, 201)

    def _handle_link_component_screen(self, component_id: int) -> None:
        assert component_id > 0, "component_id must be positive"
        data = self._read_json()
        screen_id = data.get("screen_id")
        if not isinstance(screen_id, int) or screen_id <= 0:
            self._send_json({"error": "screen_id must be a positive integer"}, 400)
            return
        try:
            result = db.link_component_screen(component_id, screen_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(result)

    def _handle_link_flow_screen(self, flow_id: int) -> None:
        assert flow_id > 0, "flow_id must be positive"
        data = self._read_json()
        screen_id = data.get("screen_id")
        if not isinstance(screen_id, int) or screen_id <= 0:
            self._send_json({"error": "screen_id must be a positive integer"}, 400)
            return
        try:
            result = db.link_flow_screen(flow_id, screen_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(result)

    def _handle_upload_screenshot(self, variant_id: int) -> None:
        assert variant_id > 0, "variant_id must be positive"
        file_bytes = self._parse_multipart_file()
        if file_bytes is None:
            self._send_json({"error": "No file in request"}, 400)
            return

        db.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

        safe_name = f"variant_{variant_id}.png"
        save_path = db.SCREENSHOTS_DIR / safe_name
        save_path.write_bytes(file_bytes)

        updated = db.update_variant_screenshot(variant_id, safe_name)
        if not updated:
            self._send_json({"error": f"Variant {variant_id} not found"}, 404)
            return

        self._send_json({"screenshot": safe_name})

    # ------------------------------------------------------------------
    # PUT
    # ------------------------------------------------------------------

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        match = _RE_SCREEN_VAR_SEL.match(path)
        if match:
            self._handle_select_variant(int(match.group(1)), db.select_screen_variant)
            return

        match = _RE_SCREEN_PARENT.match(path)
        if match:
            self._handle_set_screen_parent(int(match.group(1)))
            return

        match = _RE_SCREEN.match(path)
        if match:
            self._handle_update_entity(int(match.group(1)), db.update_screen)
            return

        match = _RE_COMPONENT_VAR_SEL.match(path)
        if match:
            self._handle_select_variant(int(match.group(1)), db.select_component_variant)
            return

        match = _RE_COMPONENT.match(path)
        if match:
            self._handle_update_entity(int(match.group(1)), db.update_component)
            return

        match = _RE_FLOW_VAR_SEL.match(path)
        if match:
            self._handle_select_variant(int(match.group(1)), db.select_flow_variant)
            return

        match = _RE_FLOW.match(path)
        if match:
            self._handle_update_entity(int(match.group(1)), db.update_flow)
            return

        self._not_found()

    def _handle_update_entity(self, entity_id: int, update_fn) -> None:
        assert entity_id > 0, "entity_id must be positive"
        data = self._read_json()
        if not data:
            self._send_json({"error": "No fields provided"}, 400)
            return
        try:
            result = update_fn(entity_id, **data)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if result is None:
            self._send_json({"error": f"Entity {entity_id} not found"}, 404)
            return
        self._send_json(result)

    def _handle_select_variant(self, variant_id: int, select_fn) -> None:
        assert variant_id > 0, "variant_id must be positive"
        try:
            result = select_fn(variant_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if result is None:
            self._send_json({"error": f"Variant {variant_id} not found"}, 404)
            return
        self._send_json(result)

    def _handle_set_screen_parent(self, screen_id: int) -> None:
        assert screen_id > 0, "screen_id must be positive"
        data = self._read_json()
        parent_id = data.get("parent_id")
        if parent_id is not None and (not isinstance(parent_id, int) or parent_id <= 0):
            self._send_json({"error": "parent_id must be a positive integer or null"}, 400)
            return
        try:
            result = db.set_screen_parent(screen_id, parent_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if result is None:
            self._send_json({"error": f"Screen {screen_id} not found"}, 404)
            return
        self._send_json(result)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        match = _RE_SCREEN_VAR.match(path)
        if match:
            self._handle_delete_variant(int(match.group(1)), db.delete_screen_variant)
            return

        match = _RE_SCREEN.match(path)
        if match:
            self._handle_delete_entity(int(match.group(1)), db.delete_screen)
            return

        match = _RE_COMPONENT_VAR.match(path)
        if match:
            self._handle_delete_variant(int(match.group(1)), db.delete_component_variant)
            return

        match = _RE_COMPONENT_LINK.match(path)
        if match:
            self._handle_unlink_component_screen(int(match.group(1)))
            return

        match = _RE_COMPONENT.match(path)
        if match:
            self._handle_delete_entity(int(match.group(1)), db.delete_component)
            return

        match = _RE_FLOW_VAR.match(path)
        if match:
            self._handle_delete_variant(int(match.group(1)), db.delete_flow_variant)
            return

        match = _RE_FLOW_LINK.match(path)
        if match:
            self._handle_unlink_flow_screen(int(match.group(1)))
            return

        match = _RE_FLOW.match(path)
        if match:
            self._handle_delete_entity(int(match.group(1)), db.delete_flow)
            return

        self._not_found()

    def _handle_delete_entity(self, entity_id: int, delete_fn) -> None:
        assert entity_id > 0, "entity_id must be positive"
        try:
            deleted = delete_fn(entity_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if not deleted:
            self._send_json({"error": f"Entity {entity_id} not found"}, 404)
            return
        self._send_json({"deleted": True})

    def _handle_delete_variant(self, variant_id: int, delete_fn) -> None:
        assert variant_id > 0, "variant_id must be positive"
        try:
            deleted = delete_fn(variant_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        if not deleted:
            self._send_json({"error": f"Variant {variant_id} not found"}, 404)
            return
        self._send_json({"deleted": True})

    def _handle_unlink_component_screen(self, component_id: int) -> None:
        assert component_id > 0, "component_id must be positive"
        data = self._read_json()
        screen_id = data.get("screen_id")
        if not isinstance(screen_id, int) or screen_id <= 0:
            self._send_json({"error": "screen_id must be a positive integer"}, 400)
            return
        try:
            result = db.unlink_component_screen(component_id, screen_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(result)

    def _handle_unlink_flow_screen(self, flow_id: int) -> None:
        assert flow_id > 0, "flow_id must be positive"
        data = self._read_json()
        screen_id = data.get("screen_id")
        if not isinstance(screen_id, int) or screen_id <= 0:
            self._send_json({"error": "screen_id must be a positive integer"}, 400)
            return
        try:
            result = db.unlink_flow_screen(flow_id, screen_id)
        except (ValueError, AssertionError) as exc:
            self._send_json({"error": str(exc)}, 400)
            return
        self._send_json(result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.environ.get("FOLIO_PORT", 7842))

    _write_pid()
    atexit.register(_remove_pid)
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    print(f"Folio → http://{host}:{port}  (PID {os.getpid()})")
    print(f"  DB:     {db.DB_PATH}")
    print(f"  Design: {db.DESIGN_DIR}")
    print(f"  System: {db.SYSTEM_MD_PATH}")
    HTTPServer((host, port), FolioHandler).serve_forever()
