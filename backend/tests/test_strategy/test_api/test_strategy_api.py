"""Tests for Strategy API endpoints.

Following TDD approach - these tests are written BEFORE implementation.
Tests cover all template and instance operations, validation, error handling, and pagination.
"""

import pytest
from fastapi.testclient import TestClient


class TestStrategyTemplateAPI:
    """Test Strategy Template API endpoints."""

    # ==================== CREATE Template Tests ====================

    def test_create_template_success(self, client):
        """Test creating a strategy template successfully."""
        response = client.post("/api/strategy-templates", json={
            "name": "Moving Average Crossover",
            "description": "Classic MA crossover strategy",
            "category": "TREND_FOLLOWING",
            "logic_flow": {
                "nodes": [
                    {
                        "id": "node1",
                        "type": "INDICATOR",
                        "indicator": "MA",
                        "parameters": {"period": 20}
                    }
                ],
                "edges": []
            },
            "parameters": {
                "ma_short_period": {"default": 10, "min": 5, "max": 50, "type": "number"}
            },
            "is_system_template": True
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Moving Average Crossover"
        assert data["category"] == "TREND_FOLLOWING"
        assert data["is_system_template"] is True
        assert data["usage_count"] == 0
        assert data["rating_average"] == 0.0
        assert data["rating_count"] == 0
        assert "id" in data
        assert "created_at" in data

    def test_create_template_missing_required_fields(self, client):
        """Test creating template with missing fields returns 422."""
        response = client.post("/api/strategy-templates", json={
            "name": "Test Template"
        })
        assert response.status_code == 422

    def test_create_template_invalid_category(self, client):
        """Test creating template with invalid category returns 422."""
        response = client.post("/api/strategy-templates", json={
            "name": "Test Template",
            "category": "invalid_category",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        assert response.status_code == 422

    # ==================== LIST Templates Tests ====================

    def test_list_templates_empty(self, client):
        """Test listing templates when none exist."""
        response = client.get("/api/strategy-templates")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["skip"] == 0
        assert data["limit"] == 20

    def test_list_templates_with_data(self, client):
        """Test listing templates returns all templates."""
        # Create two templates
        client.post("/api/strategy-templates", json={
            "name": "Template 1",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        client.post("/api/strategy-templates", json={
            "name": "Template 2",
            "category": "OSCILLATION",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        response = client.get("/api/strategy-templates")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_templates_filter_by_category(self, client):
        """Test filtering templates by category."""
        # Create templates with different categories
        client.post("/api/strategy-templates", json={
            "name": "Trend Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        client.post("/api/strategy-templates", json={
            "name": "Mean Reversion Template",
            "category": "OSCILLATION",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        response = client.get("/api/strategy-templates?category=TREND_FOLLOWING")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["category"] == "TREND_FOLLOWING"

    def test_list_templates_filter_by_is_system(self, client):
        """Test filtering templates by is_system_template."""
        # Create system and custom templates
        client.post("/api/strategy-templates", json={
            "name": "System Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {},
            "is_system_template": True
        })
        client.post("/api/strategy-templates", json={
            "name": "Custom Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {},
            "is_system_template": False
        })

        response = client.get("/api/strategy-templates?is_system_template=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["is_system_template"] is True

    def test_list_templates_pagination(self, client):
        """Test template pagination."""
        # Create 3 templates
        for i in range(3):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Get first page
        response = client.get("/api/strategy-templates?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2

        # Get second page
        response = client.get("/api/strategy-templates?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 1

    # ==================== GET Template Tests ====================

    def test_get_template_success(self, client):
        """Test getting a specific template."""
        # Create template
        create_response = client.post("/api/strategy-templates", json={
            "name": "Test Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Get template
        response = client.get(f"/api/strategy-templates/{template_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == "Test Template"

    def test_get_template_not_found(self, client):
        """Test getting non-existent template returns 404."""
        response = client.get("/api/strategy-templates/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    # ==================== UPDATE Template Tests ====================

    def test_update_template_success(self, client):
        """Test updating a template."""
        # Create template
        create_response = client.post("/api/strategy-templates", json={
            "name": "Original Name",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Update template
        response = client.put(f"/api/strategy-templates/{template_id}", json={
            "name": "Updated Name",
            "description": "Updated description"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    def test_update_template_not_found(self, client):
        """Test updating non-existent template returns 404."""
        response = client.put("/api/strategy-templates/nonexistent-id", json={
            "name": "New Name"
        })
        assert response.status_code == 404

    # ==================== DELETE Template Tests ====================

    def test_delete_template_success(self, client):
        """Test deleting a template."""
        # Create template
        create_response = client.post("/api/strategy-templates", json={
            "name": "To Delete",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Delete template
        response = client.delete(f"/api/strategy-templates/{template_id}")
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/strategy-templates/{template_id}")
        assert get_response.status_code == 404

    def test_delete_template_not_found(self, client):
        """Test deleting non-existent template returns 404."""
        response = client.delete("/api/strategy-templates/nonexistent-id")
        assert response.status_code == 404

    # ==================== Popular Templates Tests ====================

    def test_get_popular_templates(self, client):
        """Test getting popular templates."""
        # Create templates with different usage counts
        for i in range(3):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        response = client.get("/api/strategy-templates/popular")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5  # Default limit

    def test_get_popular_templates_with_limit(self, client):
        """Test getting popular templates with custom limit."""
        # Create templates
        for i in range(5):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        response = client.get("/api/strategy-templates/popular?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    # ==================== Rating Tests ====================

    def test_add_rating_success(self, client):
        """Test adding a rating to a template."""
        # Create template
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template to Rate",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Add rating
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 5,
            "comment": "Excellent strategy!"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Excellent strategy!"
        assert data["template_id"] == template_id

    def test_update_existing_rating(self, client):
        """Test updating an existing rating."""
        # Create template
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Add initial rating
        client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 3,
            "comment": "Good"
        })

        # Update rating
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 5,
            "comment": "Excellent!"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Excellent!"

    def test_add_rating_invalid_value(self, client):
        """Test adding rating with invalid value returns 422."""
        # Create template
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Try invalid rating
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 6  # Invalid: must be 1-5
        })
        assert response.status_code == 422

    def test_add_rating_template_not_found(self, client):
        """Test adding rating to non-existent template returns 404."""
        response = client.post("/api/strategy-templates/nonexistent-id/rate", json={
            "rating": 5
        })
        assert response.status_code == 404


class TestStrategyInstanceAPI:
    """Test Strategy Instance API endpoints."""

    # ==================== CREATE Strategy Tests ====================

    def test_create_strategy_from_template(self, client):
        """Test creating strategy instance from template."""
        # Create template first
        template_response = client.post("/api/strategy-templates", json={
            "name": "MA Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {
                "ma_period": {"default": 20, "min": 5, "max": 50, "type": "number"}
            }
        })
        template_id = template_response.json()["id"]

        # Create strategy from template
        response = client.post("/api/strategies", json={
            "name": "My MA Strategy",
            "template_id": template_id,
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"ma_period": 30},
            "status": "DRAFT"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My MA Strategy"
        assert data["template_id"] == template_id
        assert data["parameters"]["ma_period"] == 30
        assert data["version"] == 1
        assert data["status"] == "DRAFT"
        assert "id" in data

    def test_create_custom_strategy(self, client):
        """Test creating custom strategy without template."""
        response = client.post("/api/strategies", json={
            "name": "Custom Strategy",
            "template_id": None,
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"custom_param": 100},
            "status": "DRAFT"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Custom Strategy"
        assert data["template_id"] is None
        assert data["parameters"]["custom_param"] == 100

    def test_create_strategy_missing_fields(self, client):
        """Test creating strategy with missing fields returns 422."""
        response = client.post("/api/strategies", json={
            "name": "Incomplete Strategy"
        })
        assert response.status_code == 422

    # ==================== LIST Strategies Tests ====================

    def test_list_strategies_empty(self, client):
        """Test listing strategies when none exist."""
        response = client.get("/api/strategies")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_strategies_with_data(self, client):
        """Test listing strategies returns user's strategies."""
        # Create two strategies
        client.post("/api/strategies", json={
            "name": "Strategy 1",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        client.post("/api/strategies", json={
            "name": "Strategy 2",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        response = client.get("/api/strategies")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_strategies_filter_by_status(self, client):
        """Test filtering strategies by status."""
        # Create strategies with different statuses
        client.post("/api/strategies", json={
            "name": "Draft Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {},
            "status": "DRAFT"
        })
        client.post("/api/strategies", json={
            "name": "Active Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {},
            "status": "ACTIVE"
        })

        response = client.get("/api/strategies?status=DRAFT")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "DRAFT"

    def test_list_strategies_pagination(self, client):
        """Test strategy pagination."""
        # Create 3 strategies
        for i in range(3):
            client.post("/api/strategies", json={
                "name": f"Strategy {i}",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        response = client.get("/api/strategies?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2

    # ==================== GET Strategy Tests ====================

    def test_get_strategy_success(self, client):
        """Test getting a specific strategy."""
        # Create strategy
        create_response = client.post("/api/strategies", json={
            "name": "Test Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Get strategy
        response = client.get(f"/api/strategies/{strategy_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == strategy_id
        assert data["name"] == "Test Strategy"

    def test_get_strategy_not_found(self, client):
        """Test getting non-existent strategy returns 404."""
        response = client.get("/api/strategies/nonexistent-id")
        assert response.status_code == 404

    # ==================== UPDATE Strategy Tests ====================

    def test_update_strategy_success(self, client):
        """Test updating a strategy."""
        # Create strategy
        create_response = client.post("/api/strategies", json={
            "name": "Original Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"param1": 10}
        })
        strategy_id = create_response.json()["id"]

        # Update strategy
        response = client.put(f"/api/strategies/{strategy_id}", json={
            "name": "Updated Strategy",
            "parameters": {"param1": 20}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Strategy"
        assert data["parameters"]["param1"] == 20

    def test_update_strategy_not_found(self, client):
        """Test updating non-existent strategy returns 404."""
        response = client.put("/api/strategies/nonexistent-id", json={
            "name": "New Name"
        })
        assert response.status_code == 404

    # ==================== DELETE Strategy Tests ====================

    def test_delete_strategy_success(self, client):
        """Test soft deleting a strategy."""
        # Create strategy
        create_response = client.post("/api/strategies", json={
            "name": "To Delete",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Delete strategy
        response = client.delete(f"/api/strategies/{strategy_id}")
        assert response.status_code == 204

        # Verify soft deleted (should return 404 or show as deleted)
        get_response = client.get(f"/api/strategies/{strategy_id}")
        assert get_response.status_code == 404

    def test_delete_strategy_not_found(self, client):
        """Test deleting non-existent strategy returns 404."""
        response = client.delete("/api/strategies/nonexistent-id")
        assert response.status_code == 404

    # ==================== Copy Strategy Tests ====================

    def test_copy_strategy_success(self, client):
        """Test duplicating a strategy."""
        # Create original strategy
        create_response = client.post("/api/strategies", json={
            "name": "Original Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"param1": 10}
        })
        strategy_id = create_response.json()["id"]

        # Copy strategy
        response = client.post(f"/api/strategies/{strategy_id}/copy", json={
            "name": "Copied Strategy"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Copied Strategy"
        assert data["parameters"]["param1"] == 10
        assert data["id"] != strategy_id  # Different ID
        assert data["version"] == 1  # New version

    def test_copy_strategy_not_found(self, client):
        """Test copying non-existent strategy returns 404."""
        response = client.post("/api/strategies/nonexistent-id/copy", json={
            "name": "Copy"
        })
        assert response.status_code == 404

    # ==================== Snapshot Tests ====================

    def test_create_snapshot_success(self, client):
        """Test creating a version snapshot."""
        # Create strategy
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"param1": 10}
        })
        strategy_id = create_response.json()["id"]

        # Create snapshot
        response = client.post(f"/api/strategies/{strategy_id}/snapshot")
        assert response.status_code == 201
        data = response.json()
        assert data["parent_version_id"] == strategy_id
        assert data["version"] == 2  # Next version

    def test_create_snapshot_max_limit(self, client):
        """Test creating snapshots respects max limit (5)."""
        # Create strategy
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Create 5 snapshots
        for i in range(5):
            response = client.post(f"/api/strategies/{strategy_id}/snapshot")
            assert response.status_code == 201

        # Create 6th snapshot - should still succeed (oldest deleted)
        response = client.post(f"/api/strategies/{strategy_id}/snapshot")
        assert response.status_code == 201

        # Verify only 5 versions exist
        versions_response = client.get(f"/api/strategies/{strategy_id}/versions")
        assert versions_response.status_code == 200
        versions = versions_response.json()
        assert len(versions) == 5

    def test_create_snapshot_not_found(self, client):
        """Test creating snapshot for non-existent strategy returns 404."""
        response = client.post("/api/strategies/nonexistent-id/snapshot")
        assert response.status_code == 404

    # ==================== Version History Tests ====================

    def test_get_versions_success(self, client):
        """Test getting version history."""
        # Create strategy
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Create snapshots
        client.post(f"/api/strategies/{strategy_id}/snapshot")
        client.post(f"/api/strategies/{strategy_id}/snapshot")

        # Get versions
        response = client.get(f"/api/strategies/{strategy_id}/versions")
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 2
        # Should be sorted by created_at descending
        assert versions[0]["version"] >= versions[1]["version"]

    def test_get_versions_empty(self, client):
        """Test getting versions when none exist."""
        # Create strategy
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        response = client.get(f"/api/strategies/{strategy_id}/versions")
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 0

    def test_get_versions_not_found(self, client):
        """Test getting versions for non-existent strategy returns 404."""
        response = client.get("/api/strategies/nonexistent-id/versions")
        assert response.status_code == 404

    # ==================== Validate Strategy Tests ====================

    def test_validate_strategy_success(self, client):
        """Test validating a strategy."""
        # Create strategy
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {
                "nodes": [
                    {
                        "id": "signal1",
                        "type": "SIGNAL",
                        "signal_type": "BUY"
                    }
                ],
                "edges": []
            },
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Validate
        response = client.post(f"/api/strategies/{strategy_id}/validate")
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data

    def test_validate_strategy_not_found(self, client):
        """Test validating non-existent strategy returns 404."""
        response = client.post("/api/strategies/nonexistent-id/validate")
        assert response.status_code == 404
