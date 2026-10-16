"""Tests with mocked API responses. No network, no key, no quota.

Run from inside code/:  ../.venv/bin/python -m unittest discover -s youtube_themes/tests -v
"""
import contextlib
import csv
import datetime as dt
import io
import json
import os
import pathlib
import sys
import tempfile
import types
import unittest
import warnings
from unittest import mock

import numpy as np

warnings.simplefilter("ignore", ResourceWarning)
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "repo_public" / "collect"))
sys.path.insert(0, str(HERE.parent))
import youtube_themes as yt  # noqa: E402
import weekly_measures as wm  # noqa: E402

THEMES_CSV = HERE.parent / "themes.csv"
THEME = {"theme_id": "T1", "label": "Horses", "search_terms": "horses; ponies", "terms": ["horses", "ponies"]}


def thread(cid, text, when="2020-03-10T10:00:00Z"):
    """A commentThreads item as the real API returns it, identity fields included."""
    return {"id": cid, "snippet": {"topLevelComment": {"id": cid, "snippet": {
        "authorDisplayName": "SECRET NAME", "authorChannelId": {"value": "UCSECRETCHANNEL"},
        "authorProfileImageUrl": "https://example.com/SECRETPIC.jpg",
        "authorChannelUrl": "http://www.youtube.com/channel/UCSECRETCHANNEL",
        "textDisplay": text, "publishedAt": when, "likeCount": 3}}}}


class FakeClient:
    """Stands in for yt.Client. Serves canned responses and counts units."""

    def __init__(self, videos=None, comments=None, quota_after=None, off_videos=()):
        self.videos = videos if videos is not None else {
            "v1": ("Riding horses for beginners", "a horse video", 900, "2020-03-02T08:00:00Z"),
            "v2": ("Unrelated cooking show", "pasta", 5000, "2020-03-09T08:00:00Z"),
            "v3": ("Pony club day", "ponies", 100, "2020-03-20T08:00:00Z")}
        self.comments = comments if comments is not None else {
            "v1": [thread("c1", "I love horses @SomeoneElse so much"), thread("c2", "nice")],
            "v3": [thread("c3", "cute pony")]}
        self.units = 0
        self.calls = []
        self.quota_after = quota_after
        self.off_videos = set(off_videos)

    def get(self, endpoint, params):
        if self.quota_after is not None and len(self.calls) >= self.quota_after:
            raise yt.QuotaExceeded("quotaExceeded")
        self.calls.append((endpoint, dict(params)))
        self.units += yt.UNITS[endpoint]
        if endpoint == "search":
            return {"items": [{"id": {"videoId": v}} for v in self.videos]}
        if endpoint == "videos":
            want = params["id"].split(",")
            return {"items": [{"id": v, "snippet": {"title": self.videos[v][0], "description": self.videos[v][1],
                                                    "publishedAt": self.videos[v][3]},
                               "statistics": {"viewCount": str(self.videos[v][2]), "likeCount": "5",
                                              "commentCount": "9"}}
                              for v in want if v in self.videos]}
        if endpoint == "commentThreads":
            vid = params["videoId"]
            if vid in self.off_videos:
                raise yt.CommentsUnavailable("commentsDisabled")
            return {"items": self.comments.get(vid, [])}
        raise AssertionError(endpoint)


def write_themes(path, n=2):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["theme_id", "label", "search_terms"])
        for i in range(n):
            w.writerow([f"T{i + 1}", f"Theme {i + 1}", "horses; ponies"])


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out")
        self.addCleanup(self.tmp.cleanup)
        self.quiet = contextlib.redirect_stdout(io.StringIO())
        self.quiet.__enter__()
        self.addCleanup(self.quiet.__exit__, None, None, None)

    def all_text(self):
        parts = []
        for root, _, files in os.walk(self.out):
            for f in files:
                parts.append(open(os.path.join(root, f), encoding="utf-8").read())
        return "\n".join(parts)


class TestCollect(Base):
    def test_identities_never_written(self):
        yt.run_collect(FakeClient(), [THEME], "2020-03", "2020-03", self.out)
        text = self.all_text()
        for secret in ["SECRET NAME", "UCSECRETCHANNEL", "SECRETPIC", "authorDisplayName",
                       "authorChannelId", "SomeoneElse", "authorProfileImageUrl"]:
            self.assertNotIn(secret, text)
        rec = json.load(open(yt.rec_path(self.out, "T1", "2020-03")))
        self.assertEqual(set(rec["comments"][0]), {"id", "video", "published", "likes", "text"})
        self.assertIn("@user", rec["comments"][0]["text"])

    def test_relevance_check_and_comment_targets(self):
        c = FakeClient()
        yt.run_collect(c, [THEME], "2020-03", "2020-03", self.out)
        rec = json.load(open(yt.rec_path(self.out, "T1", "2020-03")))
        self.assertEqual(rec["videos_found"], 3)
        self.assertEqual([v["id"] for v in rec["videos"]], ["v1", "v3"])  # cooking video dropped
        asked = [p["videoId"] for e, p in c.calls if e == "commentThreads"]
        self.assertEqual(asked, ["v1", "v3"])
        s = c.calls[0][1]
        self.assertEqual((s["type"], s["relevanceLanguage"], s["order"], s["maxResults"]),
                         ("video", "en", "relevance", 50))
        self.assertEqual((s["publishedAfter"], s["publishedBefore"]), ("2020-03-01T00:00:00Z", "2020-04-01T00:00:00Z"))
        self.assertEqual(s["q"], "horses | ponies")

    def test_pagination_up_to_5_pages(self):
        pages = {"n": 0}

        class Paged(FakeClient):
            def get(self, endpoint, params):
                if endpoint == "commentThreads":
                    self.calls.append((endpoint, dict(params)))
                    pages["n"] += 1
                    return {"items": [thread(f"c{pages['n']}", "horses")], "nextPageToken": "more"}
                return super().get(endpoint, params)
        yt.run_collect(Paged(), [THEME], "2020-03", "2020-03", self.out)
        self.assertEqual(pages["n"], 10)  # 2 kept videos x 5 pages

    def test_comments_disabled_is_skipped(self):
        yt.run_collect(FakeClient(off_videos={"v1"}), [THEME], "2020-03", "2020-03", self.out)
        rec = json.load(open(yt.rec_path(self.out, "T1", "2020-03")))
        self.assertEqual({c["video"] for c in rec["comments"]}, {"v3"})

    def test_resume_skips_finished_theme_months(self):
        c1 = FakeClient()
        yt.run_collect(c1, [THEME], "2020-03", "2020-04", self.out)
        first = len(c1.calls)
        self.assertGreater(first, 0)
        c2 = FakeClient()
        done, stopped = yt.run_collect(c2, [THEME], "2020-03", "2020-05", self.out)
        self.assertEqual((done, stopped), (1, False))  # only 2020-05 is new
        self.assertEqual(len([1 for e, _ in c2.calls if e == "search"]), 1)

    def test_quota_stop_is_clean_and_resumable(self):
        # 4 calls = one full theme-month (search, videos, 2 comment pages); the 5th hits the quota
        c = FakeClient(quota_after=5)
        done, stopped = yt.run_collect(c, [THEME], "2020-03", "2020-06", self.out)
        self.assertTrue(stopped)
        self.assertEqual(done, 1)
        ledger = json.load(open(yt.ledger_path(self.out)))
        self.assertEqual(list(ledger), ["T1_2020-03"])
        self.assertFalse(os.path.exists(yt.rec_path(self.out, "T1", "2020-04")))  # no half record
        done2, stopped2 = yt.run_collect(FakeClient(), [THEME], "2020-03", "2020-06", self.out)
        self.assertEqual((done2, stopped2), (3, False))

    def test_own_unit_budget_stops(self):
        real = yt.Client(key="test-key-not-real", budget=150, sleep=lambda s: None)
        fake_resp = mock.Mock(status_code=200)
        fake_resp.json.return_value = {"items": []}
        with mock.patch.dict(sys.modules, {"requests": mock.Mock(get=mock.Mock(return_value=fake_resp),
                                                                  RequestException=Exception)}):
            real.get("search", {})
            with self.assertRaises(yt.QuotaExceeded):
                real.get("search", {})


class TestClient(unittest.TestCase):
    def test_rate_limit_and_key_in_header_only(self):
        now = {"t": 0.0}
        sleeps = []

        def sleep(s):
            sleeps.append(s)
            now["t"] += s
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {}
        fake_requests = mock.Mock(get=mock.Mock(return_value=resp), RequestException=Exception)
        c = yt.Client(key="KEY123", sleep=sleep, clock=lambda: now["t"])
        with mock.patch.dict(sys.modules, {"requests": fake_requests}):
            for _ in range(3):
                c.get("videos", {"id": "x"})
        self.assertEqual(len(sleeps), 2)
        self.assertTrue(all(abs(s - 0.5) < 1e-9 for s in sleeps))  # 2 calls a second at most
        for call in fake_requests.get.call_args_list:
            self.assertNotIn("KEY123", repr(call.args) + repr(call.kwargs.get("params")))
            self.assertEqual(call.kwargs["headers"], {"x-goog-api-key": "KEY123"})

    def test_quota_error_raises(self):
        resp = mock.Mock(status_code=403)
        resp.json.return_value = {"error": {"errors": [{"reason": "quotaExceeded"}]}}
        c = yt.Client(key="k", sleep=lambda s: None)
        with mock.patch.dict(sys.modules, {"requests": mock.Mock(get=mock.Mock(return_value=resp),
                                                                  RequestException=Exception)}):
            with self.assertRaises(yt.QuotaExceeded):
                c.get("search", {})

    def test_key_only_from_environment(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                yt.Client()


class TestRefreshPurge(Base):
    def collect_and_age(self, days):
        yt.run_collect(FakeClient(), [THEME], "2020-03", "2020-03", self.out)
        ledger = json.load(open(yt.ledger_path(self.out)))
        old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for k in ledger:
            ledger[k]["collected_at"] = old
        yt.write_json(yt.ledger_path(self.out), ledger)
        rec = json.load(open(yt.rec_path(self.out, "T1", "2020-03")))
        rec["collected_at"] = old
        yt.write_json(yt.rec_path(self.out, "T1", "2020-03"), rec)

    def test_refresh_deletes_removed_items(self):
        self.collect_and_age(31)
        # v3 removed from YouTube; comment c2 on v1 removed
        after = FakeClient(videos={"v1": ("Riding horses", "horse", 1200, "2020-03-02T08:00:00Z")},
                           comments={"v1": [thread("c1", "I love horses")]})
        done, _ = yt.run_refresh(after, self.out)
        self.assertEqual(done, 1)
        rec = json.load(open(yt.rec_path(self.out, "T1", "2020-03")))
        self.assertEqual([v["id"] for v in rec["videos"]], ["v1"])
        self.assertEqual(rec["videos"][0]["views"], 1200)  # statistics updated
        self.assertEqual([c["id"] for c in rec["comments"]], ["c1"])
        self.assertIsNotNone(rec["refreshed_at"])
        again, _ = yt.run_refresh(FakeClient(), self.out)
        self.assertEqual(again, 0)  # fixed after one refresh

    def test_refresh_waits_30_days(self):
        self.collect_and_age(10)
        c = FakeClient()
        self.assertEqual(yt.run_refresh(c, self.out)[0], 0)
        self.assertEqual(c.calls, [])

    def test_purge_deletes_old_raw_only_when_measures_exist(self):
        self.collect_and_age(100)
        path = yt.rec_path(self.out, "T1", "2020-03")
        self.assertEqual(yt.run_purge(self.out), (0, 1))  # no weekly measures yet: keep
        self.assertTrue(os.path.exists(path))
        mpath = os.path.join(self.out, "measures", "T1_2020-03.csv")
        os.makedirs(os.path.dirname(mpath))
        open(mpath, "w").write("week\n")
        os.utime(mpath, (os.path.getmtime(path) + 10,) * 2)
        self.assertEqual(yt.run_purge(self.out), (1, 0))
        self.assertFalse(os.path.exists(path))
        self.assertTrue(json.load(open(yt.ledger_path(self.out)))["T1_2020-03"]["purged"])
        # purged theme-months are not collected again
        c = FakeClient()
        yt.run_collect(c, [THEME], "2020-03", "2020-03", self.out)
        self.assertEqual(c.calls, [])

    def test_purge_keeps_recent_raw(self):
        self.collect_and_age(20)
        mpath = os.path.join(self.out, "measures", "T1_2020-03.csv")
        os.makedirs(os.path.dirname(mpath))
        open(mpath, "w").write("week\n")
        self.assertEqual(yt.run_purge(self.out)[0], 0)
        self.assertTrue(os.path.exists(yt.rec_path(self.out, "T1", "2020-03")))


class TestDryRun(Base):
    def test_quota_arithmetic_matches_design_document(self):
        themes = yt.read_themes(THEMES_CSV)
        self.assertEqual(len(themes), 86)
        p = yt.plan(themes, "2016-01", "2026-09", self.out)
        self.assertEqual(len(list(yt.months("2016-01", "2026-09"))), 129)
        self.assertEqual(p["theme_months"], 11094)
        self.assertEqual(p["units"]["search"], 1109400)
        self.assertEqual(p["units"]["videos"], 11094)
        self.assertEqual(p["units"]["commentThreads (at most)"], 554700)
        self.assertEqual(p["total_units"], 1675194)  # about 1.68 million
        self.assertAlmostEqual(p["total_units"] / 1e6, 1.68, places=2)

    def test_dry_run_makes_no_api_calls_and_needs_no_key(self):
        write_themes(os.path.join(self.out + "_themes.csv"))
        buf = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(yt, "Client", side_effect=AssertionError("API client created")), \
                contextlib.redirect_stdout(buf):
            yt.main([self.out + "_themes.csv", "2016-01", "2016-02", self.out, "--dry-run"])
        self.assertIn("still to collect: 4", buf.getvalue())
        self.assertIn("No API calls were made", buf.getvalue())
        self.assertFalse(os.path.exists(self.out))


class StubModels:
    """Tiny stand-in for the embedding and tone models."""

    def embed(self, texts):
        return np.array([[1.0, 0.0] if "horse" in t.lower() or "pony" in t.lower() else [0.0, 1.0] for t in texts])

    def tone(self, texts):
        return np.array([1.0 if "love" in t else -1.0 if "hate" in t else 0.0 for t in texts])


class TestWeekly(Base):
    def test_weekly_measures(self):
        rec = {"theme": "T1", "month": "2020-03", "videos": [
            {"id": "v1", "published": "2020-03-02T08:00:00Z", "views": 900, "likes": 1, "comments": 1},
            {"id": "v3", "published": "2020-03-04T08:00:00Z", "views": 100, "likes": 1, "comments": 1}],
            "comments": [
                {"id": "c1", "video": "v1", "published": "2020-03-03T10:00:00Z", "likes": 0, "text": "I love horses"},
                {"id": "c2", "video": "v1", "published": "2020-03-05T10:00:00Z", "likes": 0, "text": "I hate this traffic"},
                {"id": "c3", "video": "v1", "published": "2020-03-10T10:00:00Z", "likes": 0, "text": "cute pony"}]}
        os.makedirs(os.path.join(self.out, "records"))
        yt.write_json(yt.rec_path(self.out, "T1", "2020-03"), rec)
        write_themes(os.path.join(self.out, "themes.csv"), 1)
        path = wm.build(self.out, os.path.join(self.out, "themes.csv"), models=StubModels())
        rows = list(csv.DictReader(open(path)))
        w1, w2 = rows
        self.assertEqual((w1["week"], w1["videos"], w1["views"], w1["comments"], w1["matched"]),
                         ("2020-03-02", "2", "1000", "2", "1"))
        self.assertEqual(float(w1["match_share"]), 0.5)
        self.assertEqual(float(w1["mean_tone"]), 0.0)
        self.assertEqual(float(w1["mean_tone_matched"]), 1.0)
        self.assertEqual((w2["week"], w2["comments"], w2["matched"]), ("2020-03-09", "1", "1"))
        # no text in any output
        self.assertNotIn("horses", open(path).read())
        mfile = open(os.path.join(self.out, "measures", "T1_2020-03.csv")).read()
        self.assertNotIn("horses", mfile)


if __name__ == "__main__":
    unittest.main()
