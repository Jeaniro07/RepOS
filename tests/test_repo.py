import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("seed", ROOT / "hermes/seed.py")
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)


def versions():
    return dict(l.split("=", 1) for l in (ROOT / "versions.env").read_text().splitlines() if l and not l.startswith("#"))


class Pins(unittest.TestCase):
    def test_everything_is_pinned(self):
        v = versions()
        self.assertRegex(v["OPENBOT_REF"], r"^[0-9a-f]{40}$")
        self.assertRegex(v["HERMES_IMAGE"], r"@sha256:[0-9a-f]{64}$")
        self.assertRegex(v["BUN_IMAGE"], r"@sha256:[0-9a-f]{64}$")
        self.assertRegex(v["MURMUR_IMAGE"], r":\d+\.\d+$")  # belum bisa digest-pin tanpa registry; dicatat di docs

    def test_no_latest_tags(self):
        self.assertNotIn(":latest", (ROOT / "versions.env").read_text() + (ROOT / "compose.yaml").read_text())


@unittest.skipUnless(shutil.which("docker"), "docker CLI tidak ada")
class Compose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.NamedTemporaryFile("w", suffix=".env", delete=False)
        # nilai unik per variabel, supaya test bisa membedakan token yang tertukar
        cls.tmp.write(re.sub(r"^(\w+)=$", r"\1=v-\1", (ROOT / ".env.example").read_text(), flags=re.M))
        cls.tmp.close()
        env = {**os.environ, "ENV_FILE": cls.tmp.name}
        out = subprocess.run([str(ROOT / "scripts/dc"), "config", "--format", "json"], capture_output=True, text=True, env=env)
        assert out.returncode == 0, out.stderr
        import json
        cls.cfg = json.loads(out.stdout)

    def test_services(self):
        self.assertEqual(set(self.cfg["services"]), {"murmur", "hermes", "ops-computer", "ops-mcp"})

    def test_only_murmur_publishes_a_port_and_only_on_loopback(self):
        pub = {n: s.get("ports") for n, s in self.cfg["services"].items() if s.get("ports")}
        self.assertEqual(list(pub), ["murmur"])
        self.assertEqual(pub["murmur"][0]["host_ip"], "127.0.0.1")

    def test_computer_is_reachable_only_via_its_sidecar(self):
        # Hermes (dan profil lain yang punya terminal) tidak boleh bisa memanggil /exec komputer langsung.
        s = self.cfg["services"]
        self.assertEqual(list(s["ops-computer"]["networks"]), ["ops-net"])
        self.assertEqual(set(s["ops-mcp"]["networks"]), {"bots", "ops-net"})
        self.assertNotIn("ops-net", s["hermes"]["networks"])
        self.assertNotIn("bots", s["murmur"]["networks"])

    def test_auto_review_is_mounted_into_every_bot_profile(self):
        # Hermes mencari plugin di <HERMES_HOME>/plugins; untuk profil = /opt/data/profiles/<bot>/plugins.
        targets = {v["target"] for v in self.cfg["services"]["hermes"]["volumes"] if v["type"] == "bind"}
        for bot in sorted(p.name for p in (ROOT / "bots").iterdir() if (p / "config.yaml").exists()):
            self.assertIn(f"/opt/data/profiles/{bot}/plugins/auto-review", targets, bot)

    def test_computer_is_hardened(self):
        c = self.cfg["services"]["ops-computer"]
        self.assertEqual(c["cap_drop"], ["ALL"])
        self.assertIn("no-new-privileges:true", c["security_opt"])
        self.assertTrue(c["pids_limit"] and c["mem_limit"])

    def test_mounts_exist(self):
        for s in self.cfg["services"].values():
            for v in s.get("volumes", []):
                if v["type"] == "bind":
                    self.assertTrue(Path(v["source"]).exists(), v["source"])

    def test_tokens_are_split_and_hermes_never_holds_the_computer_token(self):
        s = self.cfg["services"]
        self.assertEqual(s["ops-mcp"]["environment"]["COMPUTER_TOKEN"], s["ops-computer"]["environment"]["COMPUTER_TOKEN"])
        self.assertEqual(s["hermes"]["environment"]["OPS_MCP_TOKEN"], s["ops-mcp"]["environment"]["MCP_TOKEN"])
        self.assertNotIn("COMPUTER_TOKEN", " ".join(s["hermes"]["environment"]))
        self.assertNotIn(s["ops-computer"]["environment"]["COMPUTER_TOKEN"], s["hermes"]["environment"].values())

    def test_hermes_starts_after_its_mcp_sidecar(self):
        self.assertIn("ops-mcp", self.cfg["services"]["hermes"].get("depends_on", {}))

    def test_secrets_are_required(self):
        env = {**os.environ, "ENV_FILE": "/dev/null"}
        r = subprocess.run([str(ROOT / "scripts/dc"), "config", "-q"], capture_output=True, text=True, env=env)
        self.assertNotEqual(r.returncode, 0)


class Bots(unittest.TestCase):
    def cfg(self, bot):
        return yaml.safe_load((ROOT / f"bots/{bot}/config.yaml").read_text())

    def test_ops_uses_computer_only(self):
        c = self.cfg("ops-holding")
        self.assertTrue({"browser", "terminal", "computer_use", "code_execution"} <= set(c["agent"]["disabled_toolsets"]))
        self.assertEqual(c["mcp_servers"]["ops"]["url"], "http://ops-mcp:8700/mcp")
        self.assertEqual(c["mcp_servers"]["ops"]["headers"]["Authorization"], "Bearer ${OPS_MCP_TOKEN}")
        self.assertEqual(c["approvals"]["cron_mode"], "deny")
        self.assertIn("auto-review", c["plugins"]["enabled"])

    def test_penyidikan_has_no_outside_reach(self):
        c = self.cfg("penyidikan")
        self.assertTrue({"browser", "terminal", "computer_use", "code_execution", "web"} <= set(c["agent"]["disabled_toolsets"]))
        self.assertNotIn("mcp_servers", c)
        pol = yaml.safe_load((ROOT / "plugins/auto-review/policy.yaml").read_text())
        self.assertEqual(pol["profiles"]["penyidikan"]["default"], "deny")


class Seed(unittest.TestCase):
    def test_seed_creates_profiles_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as home:
            names = seed.seed(ROOT / "bots", home)
            self.assertEqual(names, ["ops-holding", "penyidikan"])
            p = Path(home) / "profiles/ops-holding/config.yaml"
            first = p.read_text()
            seed.seed(ROOT / "bots", home)
            self.assertEqual(first, p.read_text())
            self.assertTrue((Path(home) / "profiles/ops-holding/SOUL.md").exists())

    def test_seed_preserves_existing_keys(self):
        with tempfile.TemporaryDirectory() as home:
            d = Path(home) / "profiles/ops-holding"
            d.mkdir(parents=True)
            (d / "config.yaml").write_text("model: {default: x}\nagent: {max_turns: 9, disabled_toolsets: [old]}\n")
            seed.seed(ROOT / "bots", home)
            c = yaml.safe_load((d / "config.yaml").read_text())
            self.assertEqual(c["model"], {"default": "x"})
            self.assertEqual(c["agent"]["max_turns"], 9)
            self.assertIn("browser", c["agent"]["disabled_toolsets"])


class Hygiene(unittest.TestCase):
    def test_gitignore_and_no_secrets(self):
        gi = (ROOT / ".gitignore").read_text()
        self.assertIn(".env", gi.split())
        self.assertIn("vendor/", gi.split())
        self.assertNotRegex((ROOT / ".env.example").read_text(), r"=[A-Za-z0-9]{12,}")


if __name__ == "__main__":
    unittest.main()
