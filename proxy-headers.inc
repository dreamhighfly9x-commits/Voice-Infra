# Shared by every /api location in nginx.conf (copied next to it by Dockerfile.frontend).
# $http_host keeps the port (e.g. localhost:8081 through an SSH tunnel) so the
# Go API's same-origin CORS check matches the browser's Origin header.
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Request-ID $req_id;
# TTS synthesis on CPU can take minutes for long text.
proxy_read_timeout 300s;
