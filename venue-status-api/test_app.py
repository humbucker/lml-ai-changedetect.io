import os
import json
import unittest
import tempfile
import shutil
from unittest.mock import patch
import app as app_module
from app import app

class TestVenueStatusAPI(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the datastore
        self.test_dir = tempfile.mkdtemp()
        self.original_datastore_path = app_module.DATASTORE_PATH
        app_module.DATASTORE_PATH = self.test_dir
        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        # Restore original path
        app_module.DATASTORE_PATH = self.original_datastore_path
        # Remove the temporary directory after test
        shutil.rmtree(self.test_dir)

    def create_mock_watch_json(self, watch_uuid, data):
        watch_dir = os.path.join(self.test_dir, watch_uuid)
        os.makedirs(watch_dir, exist_ok=True)
        with open(os.path.join(watch_dir, "watch.json"), "w") as f:
            json.dump(data, f)

    @patch("app.requests.get")
    def test_venue_change_status_with_structured_ai_data(self, mock_get):
        # Mock the list of watches returned from changedetection API
        mock_watches = {
            "a6b71abd-ceca-4470-8c46-593f10e3de0f": {
                "title": "Goldfields: Northern Arts Hotel | a6b71abd-ceca-4470-8c46-593f10e3de0f",
                "url": "https://events.humanitix.com/host/the-coolroom-at-the-northern-arts-hotel",
                "last_changed": 1783907499,
                "last_checked": 1783907499
            }
        }
        
        # Configure mock_get to return the watches dictionary
        mock_get.return_value.json.return_value = mock_watches
        mock_get.return_value.status_code = 200

        # Create the local watch.json with structured AI summary (valid JSON)
        ai_summary_content = {
            "gigs": [
                {
                    "venue": "The Espy",
                    "date": "Sun, 26 Jul",
                    "time": "6:30pm",
                    "acts": ["Ade Ishs", "Jack Pantazis"]
                }
            ]
        }
        self.create_mock_watch_json(
            "a6b71abd-ceca-4470-8c46-593f10e3de0f",
            {"_llm_change_summary": json.dumps(ai_summary_content)}
        )

        response = self.app.get("/venue-change-status")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["lml_uuid"], "a6b71abd-ceca-4470-8c46-593f10e3de0f")
        self.assertEqual(data[0]["name"], "Northern Arts Hotel")
        
        # Check that the structured AI summary is returned correctly
        self.assertIn("ai_summary", data[0])
        self.assertEqual(data[0]["ai_summary"], ai_summary_content)

    @patch("app.requests.get")
    def test_venue_change_status_with_fallback_venue_name(self, mock_get):
        mock_watches = {
            "a6b71abd-ceca-4470-8c46-593f10e3de0f": {
                "title": "Goldfields: Northern Arts Hotel | a6b71abd-ceca-4470-8c46-593f10e3de0f",
                "url": "https://events.humanitix.com/host/the-coolroom-at-the-northern-arts-hotel",
                "last_changed": 1783907499,
                "last_checked": 1783907499
            }
        }
        mock_get.return_value.json.return_value = mock_watches
        mock_get.return_value.status_code = 200

        # Create watch.json where venue is null in the AI output
        ai_summary_content = {
            "gigs": [
                {
                    "venue": None,
                    "date": "Sun, 26 Jul",
                    "time": "6:30pm",
                    "acts": ["Ade Ishs", "Jack Pantazis"]
                }
            ]
        }
        self.create_mock_watch_json(
            "a6b71abd-ceca-4470-8c46-593f10e3de0f",
            {"_llm_change_summary": json.dumps(ai_summary_content)}
        )

        response = self.app.get("/venue-change-status")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        
        # The gig's venue should fall back to the parsed watch name: "Northern Arts Hotel"
        self.assertEqual(data[0]["ai_summary"]["gigs"][0]["venue"], "Northern Arts Hotel")

    @patch("app.requests.get")
    def test_venue_change_status_with_unstructured_ai_data(self, mock_get):
        mock_watches = {
            "a6b71abd-ceca-4470-8c46-593f10e3de0f": {
                "title": "Goldfields: Northern Arts Hotel | a6b71abd-ceca-4470-8c46-593f10e3de0f",
                "url": "https://events.humanitix.com/host/the-coolroom-at-the-northern-arts-hotel",
                "last_changed": 1783907499,
                "last_checked": 1783907499
            }
        }
        mock_get.return_value.json.return_value = mock_watches
        mock_get.return_value.status_code = 200

        # Create watch.json with unstructured text/markdown AI summary
        markdown_summary = "- **Date:** Sun, 26 Jul\n- **Time:** 6:30pm - 9:30pm\n- **Acts:** Ade Ishs & Jack Pantazis"
        self.create_mock_watch_json(
            "a6b71abd-ceca-4470-8c46-593f10e3de0f",
            {"_llm_change_summary": markdown_summary}
        )

        response = self.app.get("/venue-change-status")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        
        # Should fall back to raw string output if not valid JSON
        self.assertEqual(data[0]["ai_summary"], markdown_summary)

    @patch("app.requests.get")
    def test_venue_change_status_with_markdown_wrapped_json(self, mock_get):
        mock_watches = {
            "a6b71abd-ceca-4470-8c46-593f10e3de0f": {
                "title": "Goldfields: Northern Arts Hotel | a6b71abd-ceca-4470-8c46-593f10e3de0f",
                "url": "https://events.humanitix.com/host/the-coolroom-at-the-northern-arts-hotel",
                "last_changed": 1783907499,
                "last_checked": 1783907499
            }
        }
        mock_get.return_value.json.return_value = mock_watches
        mock_get.return_value.status_code = 200

        # Create watch.json with JSON wrapped in markdown code blocks
        wrapped_summary = "```json\n{\n  \"gigs\": [\n    {\n      \"venue\": null,\n      \"date\": \"Sun, 26 Jul\",\n      \"time\": \"6:30pm\",\n      \"acts\": [\"Ade Ishs\", \"Jack Pantazis\"]\n    }\n  ]\n}\n```"
        self.create_mock_watch_json(
            "a6b71abd-ceca-4470-8c46-593f10e3de0f",
            {"_llm_change_summary": wrapped_summary}
        )

        response = self.app.get("/venue-change-status")
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        
        # Should clean the markdown wrapper, parse, and apply fallback venue
        self.assertEqual(data[0]["ai_summary"]["gigs"][0]["venue"], "Northern Arts Hotel")

if __name__ == "__main__":
    unittest.main()
