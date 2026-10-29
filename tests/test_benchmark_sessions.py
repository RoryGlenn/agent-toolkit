"""Canonical staging and actual parent-bound session dispatch diagnostics."""

from __future__ import annotations

import json
import tempfile
import tomllib
import unittest
from pathlib import Path

import install
from benchmarks.runtime import (
    REPOSITORY,
    SOURCE_LIBRARIES,
    digest,
    observe_trace,
    resource_manifest,
    skill_names,
    stage_arm,
)


class CanonicalStagingTests(unittest.TestCase):
    """Use upstream's inventory while keeping optional library names independent."""

    def test_staged_names_follow_authoritative_inventory_and_role_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            home, client = root / "home", root / "client"
            home.mkdir()
            client.mkdir()
            stage_arm(home, client, "toolkit", "downloaded", "model", "ultra")
            self.assertEqual(set(skill_names()), set(install.inventory(REPOSITORY)))
            staged = {path.parent.name for path in (home / ".agents/skills").glob("*/SKILL.md")}
            self.assertEqual(staged, set(skill_names()))
            self.assertEqual(len(staged), 9)
            role_names = {
                tomllib.loads(path.read_text())["name"]
                for path in (client / "agents").glob("*.toml")
            }
            expected = {
                tomllib.loads(path.read_text())["name"]
                for path in (REPOSITORY / "agents/codex").glob("*.toml")
            }
            self.assertEqual(role_names, expected)
            self.assertEqual(len(role_names), 6)
            self.assertTrue(all(name.endswith("_agent") for name in role_names))

    def test_complete_sources_keep_legacy_library_paths_after_skill_rename(self) -> None:
        self.assertEqual(
            SOURCE_LIBRARIES,
            {
                "ddia-skill": "ddia-specialist",
                "software-design-skill": "software-design-specialist",
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            entries = []
            for library in SOURCE_LIBRARIES.values():
                source = root / f"{library}.epub"
                source.write_bytes(b"explicit test source")
                index = root / f"{library}.json"
                index.write_text(json.dumps({"source_sha256": digest(source)}))
                for path, name in ((source, "source.epub"), (index, "index.json")):
                    entries.append(
                        {
                            "source": str(path),
                            "target": f".local/share/{library}/{name}",
                            "sha256": digest(path),
                        }
                    )
            manifest = root / "sources.json"
            manifest.write_text(json.dumps({"version": 1, "files": entries}))
            resources = resource_manifest("reference-complete", manifest)
            home, client = root / "home", root / "client"
            home.mkdir()
            client.mkdir()
            stage_arm(
                home,
                client,
                "toolkit",
                "reference-complete",
                "model",
                "ultra",
                source_manifest=manifest,
            )
            for skill, library in SOURCE_LIBRARIES.items():
                self.assertIn(f".local/share/{library}/source.epub", resources)
                self.assertTrue((home / ".agents/skills" / skill / "SKILL.md").is_file())
                self.assertTrue((home / ".local/share" / library / "source.epub").is_file())
                self.assertFalse((home / ".local/share" / skill).exists())


class SessionObservationTests(unittest.TestCase):
    """Never derive role dispatch from catalog text or another session's copied context."""

    def write_session(
        self,
        directory: Path,
        identifier: str,
        parent: str | None = None,
        role: str | None = None,
        *,
        boundary: bool = True,
    ) -> Path:
        payload: dict[str, object] = {
            "id": identifier,
            "creator_user_id": "PRIVATE-USER",
            "base_instructions": "PRIVATE-INSTRUCTIONS",
            "source": "exec",
        }
        if parent is not None:
            payload.update(
                {
                    "agent_role": role,
                    "source": {
                        "subagent": {
                            "thread_spawn": {"parent_thread_id": parent, "agent_role": role}
                        }
                    },
                }
            )
            if boundary:
                payload["subagent_history_start_ordinal"] = 3
        events = [
            {"type": "session_meta", "payload": payload},
            {"type": "session_meta", "payload": {"id": "inherited-parent"}},
            {"type": "turn_context", "payload": {"model": "parent-model", "effort": "low"}},
            {
                "type": "turn_context",
                "payload": {
                    "model": "child-model",
                    "effort": "ultra",
                    "private_setting": "DO-NOT-COPY",
                },
            },
        ]
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{identifier}.jsonl"
        path.write_text("\n".join(json.dumps(event) for event in events) + "\n")
        return path

    def trace(self, root: str = "root") -> str:
        return json.dumps({"type": "thread.started", "thread_id": root})

    def test_parent_tree_recovers_actual_roles_without_stdout_spawn_events(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve() / "client-home"
            sessions = home / "sessions"
            self.write_session(sessions, "root")
            self.write_session(sessions, "worker", "root", "implementation_owner_agent")
            self.write_session(sessions, "review", "worker", "adversarial_reviewer_agent")
            self.write_session(sessions, "unrelated", "different-root", "verifier_agent")
            self.write_session(sessions, "cycle", "cycle", "ddia_agent")
            result = observe_trace(self.trace(), home)
            observed = result["role_dispatch_observed"]
            self.assertEqual({item["thread_id"] for item in observed}, {"worker", "review"})
            self.assertEqual(
                {item["agent_role"] for item in observed},
                {"implementation_owner_agent", "adversarial_reviewer_agent"},
            )
            self.assertTrue(all(item["model"] == "child-model" for item in observed))
            self.assertTrue(all(item["effort"] == "ultra" for item in observed))
            self.assertEqual(result["session_dispatch_evidence"]["status"], "observed")
            serialized = json.dumps(result)
            for private in ("PRIVATE-USER", "PRIVATE-INSTRUCTIONS", "DO-NOT-COPY", "parent-model"):
                self.assertNotIn(private, serialized)
            self.assertIsNone(result["aggregate_tree_tokens"])

    def test_generic_child_keeps_unknown_role_and_connects_its_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve() / "client-home"
            self.write_session(home / "sessions", "generic", "root", None)
            self.write_session(home / "sessions", "named", "generic", "ddia_agent")
            observed = observe_trace(self.trace(), home)["role_dispatch_observed"]
            self.assertEqual({row["thread_id"] for row in observed}, {"generic", "named"})
            self.assertIsNone(
                next(row for row in observed if row["thread_id"] == "generic")["agent_role"]
            )

    def test_missing_own_history_boundary_does_not_attribute_parent_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve() / "client-home"
            self.write_session(home / "sessions", "worker", "root", "ddia_agent", boundary=False)
            observed = observe_trace(self.trace(), home)["role_dispatch_observed"]
            self.assertEqual(observed[0]["agent_role"], "ddia_agent")
            self.assertIsNone(observed[0]["model"])
            self.assertIsNone(observed[0]["effort"])

    def test_no_root_event_does_not_infer_dispatch_from_local_or_global_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve() / "client-home"
            self.write_session(home / "sessions", "worker", "root", "ddia_agent")
            result = observe_trace(
                json.dumps({"type": "agent_message", "text": "used ddia_agent"}), home
            )
            self.assertEqual(result["role_dispatch_observed"], [])
            self.assertEqual(result["session_dispatch_evidence"]["headers_inspected"], 0)

    def test_session_directory_alias_is_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            home = root / "client-home"
            home.mkdir()
            self.write_session(root / "outside", "worker", "root", "ddia_agent")
            (home / "sessions").symlink_to(root / "outside", target_is_directory=True)
            result = observe_trace(self.trace(), home)
            self.assertEqual(result["role_dispatch_observed"], [])
            self.assertEqual(result["session_dispatch_evidence"]["headers_inspected"], 0)

    def test_metadata_and_stdout_do_not_duplicate_the_same_child(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve() / "client-home"
            self.write_session(home / "sessions", "worker", "root", "ddia_agent")
            event = {
                "type": "item.completed",
                "item": {
                    "type": "collab_tool_call",
                    "tool": "spawn_agent",
                    "receiver_thread_ids": ["worker"],
                },
            }
            result = observe_trace(self.trace() + "\n" + json.dumps(event), home)
            self.assertEqual(len(result["role_dispatch_observed"]), 1)
            self.assertEqual(len(result["stdout_role_dispatch_events"]), 1)

    def test_malformed_or_duplicate_metadata_is_reported_without_false_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory).resolve() / "client-home"
            path = self.write_session(home / "sessions", "worker", "root", "ddia_agent")
            (path.parent / "duplicate.jsonl").write_bytes(path.read_bytes())
            (path.parent / "malformed.jsonl").write_text("{}\n")
            result = observe_trace(self.trace(), home)
            self.assertEqual(result["role_dispatch_observed"], [])
            self.assertEqual(result["session_dispatch_evidence"]["status"], "partial")


if __name__ == "__main__":
    unittest.main()
