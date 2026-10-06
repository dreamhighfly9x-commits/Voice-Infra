"""Static integration checks across docker-compose.yml, nginx.conf and the
Dockerfiles — the contract that lets `docker compose up` actually wire
Voice-Frontend and Voice-Backend together correctly. These don't need Docker
running, so they run in any environment (`python -m unittest`); see
smoke_test.sh for the dynamic version that does need Docker.
"""

import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = yaml.safe_load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
NGINX_CONF = (ROOT / "nginx.conf").read_text(encoding="utf-8")
BACKEND_DOCKERFILE = (ROOT / "Dockerfile.backend").read_text(encoding="utf-8")
FRONTEND_DOCKERFILE = (ROOT / "Dockerfile.frontend").read_text(encoding="utf-8")


class TestNginxProxiesToBackend(unittest.TestCase):
    def test_nginxConfig_apiLocation_proxiesToBackendServiceOnCorrectPort(self):
        match = re.search(r"location /api/ \{[^}]*proxy_pass\s+(\S+);", NGINX_CONF)
        self.assertIsNotNone(match, "nginx.conf missing a proxy_pass for location /api/")
        proxy_target = match.group(1)

        backend_service = COMPOSE["services"]["backend"]
        # No explicit `ports:` on backend — reachable only via the compose
        # network under its service name, so nginx must address it that way.
        self.assertNotIn("ports", backend_service)
        self.assertEqual(proxy_target, "http://backend:8000/api/")

    def test_nginxConfig_goOwnedPrefixes_proxyToApiService(self):
        # Must match Voice-Frontend/vite.config.js: these prefixes belong to the Go api.
        for prefix in ("= /api/me", "/api/auth/", "/api/admin/", "/api/usage", "/api/projects",
                       "/api/segments/", "/api/jobs/", "/api/segment-jobs/", "/api/audio-versions/"):
            match = re.search(r"location (?:\^~ )?" + re.escape(prefix) + r"\s*\{[^}]*proxy_pass\s+(\S+);", NGINX_CONF)
            self.assertIsNotNone(match, f"nginx.conf has no Go route for {prefix}")
            self.assertEqual(match.group(1), "http://api:8080")

    def test_nginxConfig_backendPort_matchesDockerfileExposedPort(self):
        exposed = re.search(r"^EXPOSE\s+(\d+)", BACKEND_DOCKERFILE, re.MULTILINE)
        self.assertIsNotNone(exposed)
        self.assertIn(f":{exposed.group(1)}/api/", NGINX_CONF)


class TestDockerComposeServices(unittest.TestCase):
    def test_dockerCompose_backendService_mountsPersistentVolumeAtDataMatchingBackendConfig(self):
        backend = COMPOSE["services"]["backend"]
        volumes = backend.get("volumes", [])
        self.assertIn("voice_storage:/data", volumes)
        self.assertIn("voice_storage", COMPOSE.get("volumes", {}))

        # Dockerfile.backend must default VOICE_STORAGE_DIR to that same
        # mount point, or the volume mount is silently pointless.
        env_match = re.search(r"VOICE_STORAGE_DIR=(\S+)", BACKEND_DOCKERFILE)
        self.assertIsNotNone(env_match)
        self.assertEqual(env_match.group(1).rstrip("\\"), "/data")

    def test_dockerCompose_frontendService_dependsOnBackendAndExposesPort80(self):
        frontend = COMPOSE["services"]["frontend"]
        self.assertIn("backend", frontend.get("depends_on", []))
        self.assertIn("80:80", frontend.get("ports", []))
        self.assertIn("EXPOSE 80", FRONTEND_DOCKERFILE)

    def test_dockerCompose_backendService_hasHealthcheckHittingApiHealthEndpoint(self):
        backend = COMPOSE["services"]["backend"]
        healthcheck_cmd = " ".join(backend.get("healthcheck", {}).get("test", []))
        self.assertIn("/api/health", healthcheck_cmd)


if __name__ == "__main__":
    unittest.main()
