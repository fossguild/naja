#!/usr/bin/env python3
"""Tests for the Scoreboard class."""

import os
import tempfile
from datetime import datetime
import pytest

from game.scoreboard import Scoreboard, MAX_SCOREBOARD_ENTRIES
from game.settings import GameSettings


class TestScoreboard:
    """Test suite for Scoreboard functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.scoreboard = Scoreboard()
        self.settings = GameSettings(640, 20)

    def test_init(self):
        """Test Scoreboard initialization."""
        scoreboard = Scoreboard()
        assert hasattr(scoreboard, "_entries")
        assert isinstance(scoreboard._entries, dict)
        assert len(scoreboard._entries) == 0

    def test_add_entry(self):
        """Test adding a score entry."""
        self.scoreboard.add_entry(self.settings, 10)

        listing_hash = self.settings.scoreboard_hash()
        assert listing_hash in self.scoreboard._entries
        assert len(self.scoreboard._entries[listing_hash]["scores"]) == 1
        assert self.scoreboard._entries[listing_hash]["scores"][0]["value"] == 10

    def test_add_multiple_entries(self):
        """Test adding multiple score entries."""
        self.scoreboard.add_entry(self.settings, 10)
        self.scoreboard.add_entry(self.settings, 20)
        self.scoreboard.add_entry(self.settings, 15)

        listing_hash = self.settings.scoreboard_hash()
        scores = self.scoreboard._entries[listing_hash]["scores"]
        assert len(scores) == 3
        assert scores[0]["value"] == 10
        assert scores[1]["value"] == 20
        assert scores[2]["value"] == 15

    def test_sorted_scores(self):
        """Test retrieving sorted scores."""
        self.scoreboard.add_entry(self.settings, 30)
        self.scoreboard.add_entry(self.settings, 10)
        self.scoreboard.add_entry(self.settings, 20)

        sorted_scores = self.scoreboard.sorted_scores(self.settings)
        values = [entry["value"] for entry in sorted_scores]

        assert values == [30, 20, 10]  # sorted descending

    def test_sorted_scores_empty(self):
        """Test retrieving sorted scores when no scores exist."""
        sorted_scores = self.scoreboard.sorted_scores(self.settings)
        assert sorted_scores == []

    def test_sorted_scores_different_settings(self):
        """Test that scores are separated by settings."""
        # Add scores with default settings
        self.scoreboard.add_entry(self.settings, 10)
        self.scoreboard.add_entry(self.settings, 20)

        # Create different settings
        other_settings = GameSettings(640, 20)
        other_settings.set("electric_walls", False)

        # Add scores with different settings
        self.scoreboard.add_entry(other_settings, 100)

        # Verify scores are separate
        sorted_scores1 = self.scoreboard.sorted_scores(self.settings)
        sorted_scores2 = self.scoreboard.sorted_scores(other_settings)

        assert len(sorted_scores1) == 2
        assert len(sorted_scores2) == 1
        assert sorted_scores1[0]["value"] == 20  # highest first
        assert sorted_scores2[0]["value"] == 100

    def test_top_5_scores(self):
        """Test getting top scores."""
        # Add more than MAX_SCOREBOARD_ENTRIES scores
        for score in [10, 20, 30, 40, 50, 60, 70]:
            self.scoreboard.add_entry(self.settings, score)

        sorted_scores = self.scoreboard.sorted_scores(self.settings)
        top_scores = sorted_scores[:MAX_SCOREBOARD_ENTRIES]

        assert len(top_scores) == MAX_SCOREBOARD_ENTRIES
        assert top_scores[0]["value"] == 70  # highest first
        assert top_scores[4]["value"] == 30  # lowest of top scores

    def test_clear(self):
        """Test clearing the scoreboard."""
        self.scoreboard.add_entry(self.settings, 10)
        self.scoreboard.add_entry(self.settings, 20)

        assert len(self.scoreboard._entries) > 0

        self.scoreboard.clear()

        assert len(self.scoreboard._entries) == 0

    def test_all_entries(self):
        """Test retrieving all entries."""
        self.scoreboard.add_entry(self.settings, 10)

        other_settings = GameSettings(640, 20)
        other_settings.set("electric_walls", False)
        self.scoreboard.add_entry(other_settings, 20)

        all_entries = self.scoreboard.all_entries()

        assert len(all_entries) == 2
        assert all(isinstance(entry, dict) for entry in all_entries)

    def test_entry_has_timestamp(self):
        """Test that entries have timestamps."""
        self.scoreboard.add_entry(self.settings, 10)

        listing_hash = self.settings.scoreboard_hash()
        entry = self.scoreboard._entries[listing_hash]["scores"][0]

        assert "timestamp" in entry
        assert isinstance(entry["timestamp"], datetime)

    def test_entry_structure(self):
        """Test that entries have correct structure."""
        self.scoreboard.add_entry(self.settings, 10)

        listing_hash = self.settings.scoreboard_hash()
        listing = self.scoreboard._entries[listing_hash]

        assert "settings" in listing
        assert "hash" in listing
        assert "scores" in listing
        assert isinstance(listing["settings"], dict)
        assert isinstance(listing["hash"], str)
        assert isinstance(listing["scores"], list)

    def test_save_and_load(self):
        """Test saving and loading scoreboard."""
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Add some scores
            self.scoreboard.add_entry(self.settings, 10)
            self.scoreboard.add_entry(self.settings, 20)

            # Override data_dir for testing
            self.scoreboard.data_dir = tmpdir

            # Save
            self.scoreboard.save()

            # Verify file was created
            scoreboard_file = os.path.join(tmpdir, "scoreboard.json")
            assert os.path.exists(scoreboard_file)

            # Load into new scoreboard
            new_scoreboard = Scoreboard()
            new_scoreboard.data_dir = tmpdir
            new_scoreboard = new_scoreboard.reload()

            # Verify scores were loaded
            sorted_scores = new_scoreboard.sorted_scores(self.settings)
            assert len(sorted_scores) == 2
            values = [entry["value"] for entry in sorted_scores]
            assert values == [20, 10]  # descending order


class TestScoreboardSettings:
    """Test scoreboard interaction with settings."""

    def test_scoreboard_hash_consistency(self):
        """Test that the same settings produce the same hash."""
        settings1 = GameSettings(640, 20)
        settings2 = GameSettings(640, 20)

        hash1 = settings1.scoreboard_hash()
        hash2 = settings2.scoreboard_hash()

        assert hash1 == hash2

    def test_scoreboard_hash_differences(self):
        """Test that different settings produce different hashes."""
        settings1 = GameSettings(640, 20)

        settings2 = GameSettings(640, 20)
        settings2.set("electric_walls", False)

        hash1 = settings1.scoreboard_hash()
        hash2 = settings2.scoreboard_hash()

        assert hash1 != hash2

    def test_scoreboard_settings_filtering(self):
        """Test that scoreboard_settings only includes relevant settings."""
        settings = GameSettings(640, 20)
        scoreboard_settings = settings.scoreboard_settings()

        # These should be included (require_reset=True)
        assert "cells_per_side" in scoreboard_settings
        assert "initial_speed" in scoreboard_settings
        assert "max_speed" in scoreboard_settings
        assert "obstacle_difficulty" in scoreboard_settings
        assert "number_of_apples" in scoreboard_settings
        assert "electric_walls" in scoreboard_settings

        # Verify it's a dict
        assert isinstance(scoreboard_settings, dict)


class TestScoreboardIntegration:
    """Integration tests for scoreboard with game systems."""

    def test_scoreboard_persistence_across_sessions(self):
        """Test that scores persist across multiple scoreboard instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = GameSettings(640, 20)

            # Session 1: Add scores
            scoreboard1 = Scoreboard()
            scoreboard1.data_dir = tmpdir
            scoreboard1.add_entry(settings, 10)
            scoreboard1.add_entry(settings, 20)
            scoreboard1.save()

            # Session 2: Load and add more scores
            scoreboard2 = Scoreboard()
            scoreboard2.data_dir = tmpdir
            scoreboard2 = scoreboard2.reload()
            scoreboard2.add_entry(settings, 30)
            scoreboard2.save()

            # Session 3: Verify all scores are present
            scoreboard3 = Scoreboard()
            scoreboard3.data_dir = tmpdir
            scoreboard3 = scoreboard3.reload()

            sorted_scores = scoreboard3.sorted_scores(settings)
            values = [entry["value"] for entry in sorted_scores]
            assert values == [30, 20, 10]  # descending order

    def test_scoreboard_with_multiple_configurations(self):
        """Test scoreboard with multiple game configurations."""
        scoreboard = Scoreboard()

        # Configuration 1: Small grid, easy
        config1 = GameSettings(640, 20)
        config1.set("cells_per_side", 10)
        config1.set("obstacle_difficulty", "Easy")

        # Configuration 2: Large grid, hard
        config2 = GameSettings(640, 20)
        config2.set("cells_per_side", 30)
        config2.set("obstacle_difficulty", "Hard")

        # Add scores for each configuration
        scoreboard.add_entry(config1, 50)
        scoreboard.add_entry(config1, 60)
        scoreboard.add_entry(config2, 20)
        scoreboard.add_entry(config2, 25)

        # Verify scores are separated
        scores1 = scoreboard.sorted_scores(config1)
        scores2 = scoreboard.sorted_scores(config2)

        assert len(scores1) == 2
        assert len(scores2) == 2
        assert [s["value"] for s in scores1] == [60, 50]  # descending order
        assert [s["value"] for s in scores2] == [25, 20]  # descending order


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
