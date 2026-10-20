import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("auto_review", ROOT / "plugins/auto-review/__init__.py")
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)


class Env:
    """Home profil sementara + env terkontrol."""
    def __init__(self, profile="ops-holding", mode=None, policy=None):
        self.profile, self.mode, self.policy = profile, mode, policy

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "profiles" / self.profile
        self.home.mkdir(parents=True)
        self.saved = {k: os.environ.get(k) for k in ("HERMES_HOME", "AUTOREVIEW_MODE", "AUTOREVIEW_POLICY")}
        os.environ["HERMES_HOME"] = str(self.home)
        for k, v in (("AUTOREVIEW_MODE", self.mode), ("AUTOREVIEW_POLICY", self.policy)):
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        ar._cache.update(mtime=None, path=None, data={})
        return self

    def __exit__(self, *_):
        for k, v in self.saved.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.tmp.cleanup()

    def log(self):
        p = self.home / "auto-review.jsonl"
        return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


class Decide(unittest.TestCase):
    def setUp(self):
        self.policy = ar.yaml.safe_load((ROOT / "plugins/auto-review/policy.yaml").read_text())

    def d(self, profile, tool, **args):
        return ar.decide(self.policy, profile, tool, args)[0]

    def test_ops_rules(self):
        self.assertEqual(self.d("ops-holding", "terminal"), "deny")
        self.assertEqual(self.d("ops-holding", "execute_code"), "deny")
        self.assertEqual(self.d("ops-holding", "mcp__ops__browser_click", ref="e1"), "allow")
        self.assertEqual(self.d("ops-holding", "mcp__ops__browser_navigate", url="https://x"), "allow")
        self.assertEqual(self.d("ops-holding", "mcp__ops__files_write"), "approve")
        self.assertEqual(self.d("ops-holding", "mcp__ops__files_read"), "allow")

    def test_payment_text_needs_approval_before_generic_allow(self):
        self.assertEqual(self.d("ops-holding", "mcp__ops__browser_type", ref="e", text="Klik BAYAR sekarang"), "approve")
        self.assertEqual(self.d("ops-holding", "mcp__ops__browser_type", ref="e", text="halo"), "allow")

    def test_unknown_tool_defaults_to_approve_for_ops_and_deny_for_penyidikan(self):
        self.assertEqual(self.d("ops-holding", "send_message"), "approve")
        self.assertEqual(self.d("penyidikan", "send_message"), "deny")
        self.assertEqual(self.d("penyidikan", "mcp__ops__browser_navigate"), "deny")
        self.assertEqual(self.d("penyidikan", "memory"), "allow")

    def test_other_profiles_use_fallback(self):
        self.assertEqual(self.d("xaqu", "terminal"), "allow")

    def test_server_name_in_policy_matches_bot_config(self):
        cfg = ar.yaml.safe_load((ROOT / "bots/ops-holding/config.yaml").read_text())
        self.assertIn("ops", cfg["mcp_servers"])


class Hook(unittest.TestCase):
    def test_enforce_blocks_and_approves(self):
        with Env(mode="enforce") as e:
            self.assertEqual(ar.review("terminal", {"command": "ls"})["action"], "block")
            self.assertEqual(ar.review("mcp__ops__files_write", {"path": "a"})["action"], "approve")
            self.assertIsNone(ar.review("mcp__ops__browser_snapshot", {}))
            self.assertEqual([x["action"] for x in e.log()], ["deny", "approve", "allow"])

    def test_dry_run_never_blocks_but_logs_verdict(self):
        with Env(mode="dry-run") as e:
            self.assertIsNone(ar.review("terminal", {"command": "rm -rf /"}))
            self.assertEqual(e.log()[0]["action"], "deny")
            self.assertEqual(e.log()[0]["mode"], "dry-run")

    def test_policy_mode_is_used_when_env_unset(self):
        with Env() as e:  # policy.yaml membawa mode: dry-run
            self.assertIsNone(ar.review("terminal", {}))
            self.assertEqual(e.log()[0]["mode"], "dry-run")

    def test_fail_closed_on_broken_policy_in_enforce(self):
        with Env(mode="enforce", policy="/nonexistent/policy.yaml") as e:
            r = ar.review("mcp__ops__browser_click", {})
            self.assertEqual(r["action"], "block")
            self.assertEqual(e.log()[0]["rule"], "error")

    def test_broken_policy_in_dry_run_does_not_block(self):
        with Env(mode="dry-run", policy="/nonexistent/policy.yaml"):
            self.assertIsNone(ar.review("terminal", {}))

    def test_secrets_never_reach_audit_log(self):
        with Env(mode="enforce") as e:
            ar.review("mcp__ops__browser_type", {"ref": "e1", "text": "KATASANDI-RAHASIA", "password": "p"})
            raw = (e.home / "auto-review.jsonl").read_text()
            self.assertNotIn("KATASANDI-RAHASIA", raw)
            self.assertNotIn('"p"', raw)

    def test_profile_name_from_home(self):
        with Env(profile="penyidikan"):
            self.assertEqual(ar.profile_name(), "penyidikan")
            self.assertIsNone(ar.review("memory", {}))

    def test_policy_hot_reload(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "p.yaml"
            p.write_text("mode: enforce\nfallback: {default: allow}\n")
            with Env(policy=str(p)):
                self.assertIsNone(ar.review("x", {}))
                p.write_text("mode: enforce\nfallback: {default: deny}\n")
                os.utime(p, (os.stat(p).st_atime, os.stat(p).st_mtime + 5))
                self.assertEqual(ar.review("x", {})["action"], "block")

    def test_register_wires_pre_tool_call(self):
        calls = []
        ctx = type("C", (), {"register_hook": lambda s, n, f: calls.append((n, f))})()
        ar.register(ctx)
        self.assertEqual(calls, [("pre_tool_call", ar.review)])


class RedactNested(unittest.TestCase):
    def test_nested_secret_is_hidden(self):
        r = ar.redact({"headers": {"Authorization": "Bearer RAHASIA"}, "url": "https://x"})
        self.assertNotIn("RAHASIA", json.dumps(r))
        self.assertEqual(r["url"], "https://x")


if __name__ == "__main__":
    unittest.main()
