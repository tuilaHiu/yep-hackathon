import unittest
from unittest.mock import patch, MagicMock
import os
import json
import shutil
from app.service.track_player import run_interactive_tracking

class TestTrackPlayer(unittest.TestCase):
    def setUp(self):
        self.test_output_dir = "test_output_main"
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
        os.makedirs(self.test_output_dir)
        
        self.video_path = "dummy_video.mp4"
        # Create a dummy file for existence check if needed, 
        # but since we mock the underlying services, we might not need it
        with open(self.video_path, "w") as f:
            f.write("dummy")

    def tearDown(self):
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
        if os.path.exists(self.video_path):
            os.remove(self.video_path)

    @patch("app.service.track_player.select_players_terminal")
    @patch("app.service.track_player.run_selective_tracking")
    @patch("app.service.track_player.crop_named_player_videos")
    def test_full_pipeline_terminal(self, mock_crop, mock_track, mock_select):
        # Setup mocks
        mock_select.return_value = {"players": [{"name": "Player1", "selection_id": 1, "initial_bbox": {}}]}
        mock_track.return_value = {}
        mock_crop.return_value = ["output/Player1.mp4"]

        # Run
        result = run_interactive_tracking(
            video_path=self.video_path,
            mode="terminal",
            output_dir=self.test_output_dir
        )

        # Assert
        mock_select.assert_called_once()
        mock_track.assert_called_once()
        mock_crop.assert_called_once()
        self.assertEqual(result, ["output/Player1.mp4"])

    @patch("app.service.track_player.select_players_gui")
    @patch("app.service.track_player.run_selective_tracking")
    @patch("app.service.track_player.crop_named_player_videos")
    def test_full_pipeline_gui(self, mock_crop, mock_track, mock_select):
        # Setup mocks
        mock_select.return_value = {"players": []}
        mock_track.return_value = {}
        mock_crop.return_value = []

        # Run
        run_interactive_tracking(
            video_path=self.video_path,
            mode="gui",
            output_dir=self.test_output_dir
        )

        # Assert
        mock_select.assert_called_once()
        mock_track.assert_called_once()
        mock_crop.assert_called_once()

    @patch("app.service.track_player.run_selective_tracking")
    @patch("app.service.track_player.crop_named_player_videos")
    def test_skip_selection(self, mock_crop, mock_track):
        # Setup mocks
        mock_track.return_value = {}
        mock_crop.return_value = []
        
        dummy_selected_path = os.path.join(self.test_output_dir, "existing_selection.json")
        with open(dummy_selected_path, "w") as f:
            json.dump({"players": []}, f)

        # Run
        run_interactive_tracking(
            video_path=self.video_path,
            selected_players_path=dummy_selected_path,
            output_dir=self.test_output_dir
        )

        # Assert
        mock_track.assert_called_once()
        mock_crop.assert_called_once()
        # mock_select should not be called (not even patched here, but you get the point)

    @patch("app.service.track_player.crop_named_player_videos")
    def test_skip_tracking(self, mock_crop):
        # Setup mocks
        mock_crop.return_value = []
        
        dummy_tracking_path = os.path.join(self.test_output_dir, "existing_tracking.json")
        with open(dummy_tracking_path, "w") as f:
            json.dump({}, f)

        # Run
        run_interactive_tracking(
            video_path=self.video_path,
            tracking_data_path=dummy_tracking_path,
            output_dir=self.test_output_dir
        )

        # Assert
        mock_crop.assert_called_once()

    @patch("sys.argv", ["track_player.py", "--video", "test.mp4", "--mode", "gui", "--max-players", "2"])
    @patch("app.service.track_player.run_interactive_tracking")
    def test_cli_parsing(self, mock_run):
        from app.service.track_player import main
        try:
            main()
        except SystemExit:
            pass
        
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs['video_path'], "test.mp4")
        self.assertEqual(kwargs['mode'], "gui")
        self.assertEqual(kwargs['max_players'], 2)

if __name__ == "__main__":
    unittest.main()
