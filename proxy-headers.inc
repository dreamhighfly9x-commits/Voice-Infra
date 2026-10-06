# Shared by every /api location in nginx.conf (copied next to it by Dockerfile.frontend).
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Request-ID $req_id;
# TTS synthesis on CPU can take minutes for long text.
proxy_read_timeout 300s;
