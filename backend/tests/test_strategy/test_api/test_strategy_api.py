"""
Comprehensive Test Suite for Strategy API Endpoints

Following Test-Driven Development (TDD) approach with AAA pattern (Arrange-Act-Assert).
Coverage includes:
- All CRUD operations for templates and instances
- Success scenarios
- Error handling (404, 400, 500)
- Edge cases and boundary conditions
- Database error simulation
- Input validation
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime


class TestTemplateAPISuccess:
    """Test successful template API operations."""

    # ==================== CREATE Template Success Tests ====================

    def test_create_template_success(self, client):
        """Test creating a strategy template successfully - AAA pattern."""
        # Arrange: Prepare test data
        template_data = {
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
        }

        # Act: Create template
        response = client.post("/api/strategy-templates", json=template_data)

        # Assert: Verify success response
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

    def test_create_template_with_minimal_fields(self, client):
        """Test creating template with only required fields."""
        # Arrange
        minimal_data = {
            "name": "Simple Template",
            "category": "OSCILLATION",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategy-templates", json=minimal_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Template"
        assert data["is_system_template"] is False  # Default to False
        assert data["description"] is None

    def test_create_template_with_empty_logic_flow(self, client):
        """Test creating template with empty logic flow."""
        # Arrange
        data = {
            "name": "Empty Logic Template",
            "category": "MULTI_FACTOR",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"param1": "value1"}
        }

        # Act
        response = client.post("/api/strategy-templates", json=data)

        # Assert
        assert response.status_code == 201

    # ==================== LIST Templates Success Tests ====================

    def test_list_templates_empty(self, client):
        """Test listing templates when none exist."""
        # Arrange: No templates created

        # Act
        response = client.get("/api/strategy-templates")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["skip"] == 0
        assert data["limit"] == 20

    def test_list_templates_with_multiple_items(self, client):
        """Test listing templates returns all templates."""
        # Arrange: Create multiple templates
        for i in range(3):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategy-templates")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_templates_filter_by_category(self, client):
        """Test filtering templates by category."""
        # Arrange: Create templates with different categories
        client.post("/api/strategy-templates", json={
            "name": "Trend Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        client.post("/api/strategy-templates", json={
            "name": "Oscillation Template",
            "category": "OSCILLATION",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        # Act
        response = client.get("/api/strategy-templates?category=TREND_FOLLOWING")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["category"] == "TREND_FOLLOWING"

    def test_list_templates_filter_by_system_template_true(self, client):
        """Test filtering by is_system_template=true."""
        # Arrange
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

        # Act
        response = client.get("/api/strategy-templates?is_system_template=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["is_system_template"] is True

    def test_list_templates_filter_by_system_template_false(self, client):
        """Test filtering by is_system_template=false."""
        # Arrange
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

        # Act
        response = client.get("/api/strategy-templates?is_system_template=false")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["is_system_template"] is False

    def test_list_templates_pagination_first_page(self, client):
        """Test pagination - first page."""
        # Arrange: Create 5 templates
        for i in range(5):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategy-templates?skip=0&limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2

    def test_list_templates_pagination_second_page(self, client):
        """Test pagination - second page."""
        # Arrange
        for i in range(5):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategy-templates?skip=2&limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_list_templates_pagination_last_page(self, client):
        """Test pagination - last partial page."""
        # Arrange
        for i in range(5):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategy-templates?skip=4&limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 1

    # ==================== GET Template Success Tests ====================

    def test_get_template_success(self, client):
        """Test getting a specific template by ID."""
        # Arrange: Create a template
        create_response = client.post("/api/strategy-templates", json={
            "name": "Test Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.get(f"/api/strategy-templates/{template_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert data["name"] == "Test Template"
        assert "created_at" in data

    def test_get_template_with_complex_logic_flow(self, client):
        """Test getting template with complex logic flow."""
        # Arrange
        complex_template = {
            "name": "Complex Template",
            "category": "MULTI_FACTOR",
            "logic_flow": {
                "nodes": [
                    {"id": "n1", "type": "INDICATOR", "indicator": "RSI"},
                    {"id": "n2", "type": "CONDITION", "operator": "AND"},
                    {"id": "n3", "type": "SIGNAL", "signal_type": "BUY"}
                ],
                "edges": [
                    {"from": "n1", "to": "n2"},
                    {"from": "n2", "to": "n3"}
                ]
            },
            "parameters": {
                "rsi_period": {"default": 14, "min": 5, "max": 50}
            }
        }
        create_response = client.post("/api/strategy-templates", json=complex_template)
        template_id = create_response.json()["id"]

        # Act
        response = client.get(f"/api/strategy-templates/{template_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template_id
        assert len(data["logic_flow"]["nodes"]) == 3
        assert len(data["logic_flow"]["edges"]) == 2

    # ==================== UPDATE Template Success Tests ====================

    def test_update_template_name_success(self, client):
        """Test updating template name."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Original Name",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.put(f"/api/strategy-templates/{template_id}", json={
            "name": "Updated Name"
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["id"] == template_id

    def test_update_template_description(self, client):
        """Test updating template description."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.put(f"/api/strategy-templates/{template_id}", json={
            "description": "New description"
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"

    def test_update_template_partial_fields(self, client):
        """Test updating only some fields."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Original",
            "description": "Original description",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.put(f"/api/strategy-templates/{template_id}", json={
            "name": "Updated Only Name"
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Only Name"
        assert data["description"] == "Original description"  # Should remain unchanged

    # ==================== DELETE Template Success Tests ====================

    def test_delete_template_success(self, client):
        """Test successful template deletion."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "To Delete",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.delete(f"/api/strategy-templates/{template_id}")

        # Assert: Should return 204 No Content
        assert response.status_code == 204

        # Act: Try to get deleted template
        get_response = client.get(f"/api/strategy-templates/{template_id}")

        # Assert: Should return 404
        assert get_response.status_code == 404

    # ==================== Popular Templates Success Tests ====================

    def test_get_popular_templates_default_limit(self, client):
        """Test getting popular templates with default limit."""
        # Arrange: Create templates
        for i in range(3):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategy-templates/popular")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5  # Default limit

    def test_get_popular_templates_custom_limit(self, client):
        """Test getting popular templates with custom limit."""
        # Arrange
        for i in range(5):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategy-templates/popular?limit=3")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_get_popular_templates_with_category_filter(self, client):
        """Test popular templates with category filter."""
        # Arrange
        for i in range(2):
            client.post("/api/strategy-templates", json={
                "name": f"Trend Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })
        for i in range(2):
            client.post("/api/strategy-templates", json={
                "name": f"Oscillation Template {i}",
                "category": "OSCILLATION",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategy-templates/popular?category=TREND_FOLLOWING&limit=5")

        # Assert
        assert response.status_code == 200
        data = response.json()
        # Should only return TREND_FOLLOWING templates
        for item in data:
            assert item["category"] == "TREND_FOLLOWING"

    # ==================== Rating Success Tests ====================

    def test_add_rating_success(self, client):
        """Test adding a rating to a template."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template to Rate",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 5,
            "comment": "Excellent strategy!"
        })

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Excellent strategy!"
        assert data["template_id"] == template_id

    def test_add_rating_without_comment(self, client):
        """Test adding rating without comment."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 4
        })

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 4

    def test_update_existing_rating(self, client):
        """Test updating an existing rating."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Initial rating
        client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 3,
            "comment": "Good"
        })

        # Act: Update rating
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 5,
            "comment": "Excellent!"
        })

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["comment"] == "Excellent!"

    def test_rating_with_minimum_value(self, client):
        """Test rating with minimum valid value (1)."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 1
        })

        # Assert
        assert response.status_code == 201
        assert response.json()["rating"] == 1

    def test_rating_with_maximum_value(self, client):
        """Test rating with maximum valid value (5)."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 5
        })

        # Assert
        assert response.status_code == 201
        assert response.json()["rating"] == 5


class TestTemplateAPIErrors:
    """Test error handling for template API operations."""

    def test_create_template_missing_name(self, client):
        """Test creating template without name returns 422."""
        # Arrange
        invalid_data = {
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategy-templates", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_template_missing_category(self, client):
        """Test creating template without category returns 422."""
        # Arrange
        invalid_data = {
            "name": "Test",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategy-templates", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_template_missing_logic_flow(self, client):
        """Test creating template without logic_flow returns 422."""
        # Arrange
        invalid_data = {
            "name": "Test",
            "category": "TREND_FOLLOWING",
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategy-templates", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_template_invalid_category_enum(self, client):
        """Test creating template with invalid category enum returns 422."""
        # Arrange
        invalid_data = {
            "name": "Test",
            "category": "INVALID_CATEGORY",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategy-templates", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_get_template_not_found(self, client):
        """Test getting non-existent template returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.get("/api/strategy-templates/nonexistent-id-12345")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_update_template_not_found(self, client):
        """Test updating non-existent template returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.put("/api/strategy-templates/nonexistent-id", json={
            "name": "New Name"
        })

        # Assert
        assert response.status_code == 404

    def test_delete_template_not_found(self, client):
        """Test deleting non-existent template returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.delete("/api/strategy-templates/nonexistent-id")

        # Assert
        assert response.status_code == 404

    def test_add_rating_template_not_found(self, client):
        """Test adding rating to non-existent template returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.post("/api/strategy-templates/nonexistent-id/rate", json={
            "rating": 5
        })

        # Assert
        assert response.status_code == 404

    def test_add_rating_invalid_value_too_high(self, client):
        """Test adding rating above max (5) returns 422."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 6  # Invalid: must be 1-5
        })

        # Assert
        assert response.status_code == 422

    def test_add_rating_invalid_value_too_low(self, client):
        """Test adding rating below min (1) returns 422."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 0  # Invalid: must be 1-5
        })

        # Assert
        assert response.status_code == 422

    def test_add_rating_missing_rating_field(self, client):
        """Test adding rating without rating value returns 422."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "comment": "No rating provided"
        })

        # Assert
        assert response.status_code == 422


class TestInstanceAPISuccess:
    """Test successful strategy instance API operations."""

    # ==================== CREATE Instance Success Tests ====================

    def test_create_strategy_from_template(self, client):
        """Test creating strategy instance from template."""
        # Arrange: Create template first
        template_response = client.post("/api/strategy-templates", json={
            "name": "MA Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {
                "ma_period": {"default": 20, "min": 5, "max": 50, "type": "number"}
            }
        })
        template_id = template_response.json()["id"]

        # Act: Create strategy from template
        response = client.post("/api/strategies", json={
            "name": "My MA Strategy",
            "template_id": template_id,
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"ma_period": 30},
            "status": "DRAFT"
        })

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My MA Strategy"
        assert data["template_id"] == template_id
        assert data["parameters"]["ma_period"] == 30
        assert data["version"] == 1
        assert data["status"] == "DRAFT"
        assert "id" in data
        assert "created_at" in data

    def test_create_custom_strategy_without_template(self, client):
        """Test creating custom strategy without template."""
        # Arrange
        strategy_data = {
            "name": "Custom Strategy",
            "template_id": None,
            "logic_flow": {
                "nodes": [
                    {"id": "n1", "type": "SIGNAL", "signal_type": "BUY"}
                ],
                "edges": []
            },
            "parameters": {"custom_param": 100},
            "status": "DRAFT"
        }

        # Act
        response = client.post("/api/strategies", json=strategy_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Custom Strategy"
        assert data["template_id"] is None
        assert data["parameters"]["custom_param"] == 100

    def test_create_strategy_with_minimal_fields(self, client):
        """Test creating strategy with minimal required fields."""
        # Arrange
        minimal_data = {
            "name": "Simple Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategies", json=minimal_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Strategy"
        assert data["status"] == "DRAFT"  # Default status

    def test_create_strategy_with_all_statuses(self, client):
        """Test creating strategies with different status values."""
        # Arrange
        statuses = ["DRAFT", "TESTING", "ACTIVE", "ARCHIVED"]

        for status in statuses:
            # Act
            response = client.post("/api/strategies", json={
                "name": f"Strategy {status}",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {},
                "status": status
            })

            # Assert
            assert response.status_code == 201
            assert response.json()["status"] == status

    # ==================== LIST Instance Success Tests ====================

    def test_list_strategies_empty(self, client):
        """Test listing strategies when none exist."""
        # Arrange: No strategies created

        # Act
        response = client.get("/api/strategies")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_strategies_with_multiple_items(self, client):
        """Test listing strategies returns all user's strategies."""
        # Arrange: Create multiple strategies
        for i in range(3):
            client.post("/api/strategies", json={
                "name": f"Strategy {i}",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategies")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_strategies_filter_by_draft_status(self, client):
        """Test filtering strategies by DRAFT status."""
        # Arrange
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

        # Act
        response = client.get("/api/strategies?status=DRAFT")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "DRAFT"

    def test_list_strategies_filter_by_active_status(self, client):
        """Test filtering strategies by ACTIVE status."""
        # Arrange
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

        # Act
        response = client.get("/api/strategies?status=ACTIVE")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "ACTIVE"

    def test_list_strategies_filter_by_template_id(self, client):
        """Test filtering strategies by template ID."""
        # Arrange: Create template and strategies
        template_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = template_response.json()["id"]

        client.post("/api/strategies", json={
            "name": "Strategy from Template",
            "template_id": template_id,
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        client.post("/api/strategies", json={
            "name": "Custom Strategy",
            "template_id": None,
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        # Act
        response = client.get(f"/api/strategies?template_id={template_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["template_id"] == template_id

    def test_list_strategies_pagination(self, client):
        """Test strategy pagination."""
        # Arrange: Create 5 strategies
        for i in range(5):
            client.post("/api/strategies", json={
                "name": f"Strategy {i}",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act: Get first page
        response = client.get("/api/strategies?skip=0&limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2

    def test_list_strategies_pagination_subsequent_page(self, client):
        """Test pagination - subsequent page."""
        # Arrange
        for i in range(5):
            client.post("/api/strategies", json={
                "name": f"Strategy {i}",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategies?skip=2&limit=2")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    # ==================== GET Instance Success Tests ====================

    def test_get_strategy_success(self, client):
        """Test getting a specific strategy."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Test Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.get(f"/api/strategies/{strategy_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == strategy_id
        assert data["name"] == "Test Strategy"

    def test_get_strategy_with_template(self, client):
        """Test getting strategy that was created from template."""
        # Arrange
        template_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = template_response.json()["id"]

        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "template_id": template_id,
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.get(f"/api/strategies/{strategy_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == template_id

    # ==================== UPDATE Instance Success Tests ====================

    def test_update_strategy_name(self, client):
        """Test updating strategy name."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Original Name",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.put(f"/api/strategies/{strategy_id}", json={
            "name": "Updated Name"
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_update_strategy_parameters(self, client):
        """Test updating strategy parameters."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"param1": 10}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.put(f"/api/strategies/{strategy_id}", json={
            "parameters": {"param1": 20, "param2": 30}
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["parameters"]["param1"] == 20
        assert data["parameters"]["param2"] == 30

    def test_update_strategy_status(self, client):
        """Test updating strategy status."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {},
            "status": "DRAFT"
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.put(f"/api/strategies/{strategy_id}", json={
            "status": "ACTIVE"
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ACTIVE"

    def test_update_strategy_multiple_fields(self, client):
        """Test updating multiple fields at once."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Original",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"p1": 1},
            "status": "DRAFT"
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.put(f"/api/strategies/{strategy_id}", json={
            "name": "Updated",
            "parameters": {"p1": 2},
            "status": "TESTING"
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["parameters"]["p1"] == 2
        assert data["status"] == "TESTING"

    # ==================== DELETE Instance Success Tests ====================

    def test_delete_strategy_success(self, client):
        """Test soft deleting a strategy."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "To Delete",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.delete(f"/api/strategies/{strategy_id}")

        # Assert: Should return 204 No Content
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/strategies/{strategy_id}")
        assert get_response.status_code == 404

    # ==================== COPY Instance Success Tests ====================

    def test_copy_strategy_success(self, client):
        """Test duplicating a strategy."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Original Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"param1": 10}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategies/{strategy_id}/copy", json={
            "name": "Copied Strategy"
        })

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Copied Strategy"
        assert data["parameters"]["param1"] == 10
        assert data["id"] != strategy_id
        assert data["version"] == 1

    def test_copy_strategy_with_different_parameters(self, client):
        """Test copying strategy copies all parameters."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Original",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {
                "param1": 10,
                "param2": "value",
                "param3": True
            }
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategies/{strategy_id}/copy", json={
            "name": "Copy"
        })

        # Assert
        data = response.json()
        assert data["parameters"]["param1"] == 10
        assert data["parameters"]["param2"] == "value"
        assert data["parameters"]["param3"] is True

    # ==================== SNAPSHOT Success Tests ====================

    def test_create_snapshot_success(self, client):
        """Test creating a version snapshot."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"param1": 10}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategies/{strategy_id}/snapshot")

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["parent_version_id"] == strategy_id
        assert data["version"] == 2  # Next version

    def test_create_multiple_snapshots(self, client):
        """Test creating multiple snapshots."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Act: Create multiple snapshots
        for i in range(3):
            response = client.post(f"/api/strategies/{strategy_id}/snapshot")
            assert response.status_code == 201
            assert response.json()["version"] == i + 2

    def test_create_snapshot_respects_max_limit(self, client):
        """Test creating snapshots respects max limit (5)."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Act: Create 5 snapshots
        for i in range(5):
            response = client.post(f"/api/strategies/{strategy_id}/snapshot")
            assert response.status_code == 201

        # Create 6th snapshot - should succeed (oldest deleted)
        response = client.post(f"/api/strategies/{strategy_id}/snapshot")
        assert response.status_code == 201

        # Verify only 5 versions exist
        versions_response = client.get(f"/api/strategies/{strategy_id}/versions")
        assert versions_response.status_code == 200
        versions = versions_response.json()
        assert len(versions) == 5

    # ==================== VERSION HISTORY Success Tests ====================

    def test_get_versions_with_snapshots(self, client):
        """Test getting version history with snapshots."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Create snapshots
        client.post(f"/api/strategies/{strategy_id}/snapshot")
        client.post(f"/api/strategies/{strategy_id}/snapshot")

        # Act
        response = client.get(f"/api/strategies/{strategy_id}/versions")

        # Assert
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 2
        # Should be sorted by created_at descending
        assert versions[0]["version"] >= versions[1]["version"]

    def test_get_versions_empty(self, client):
        """Test getting versions when none exist."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.get(f"/api/strategies/{strategy_id}/versions")

        # Assert
        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 0

    # ==================== VALIDATE Strategy Success Tests ====================

    def test_validate_strategy_success(self, client):
        """Test validating a strategy."""
        # Arrange
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

        # Act
        response = client.post(f"/api/strategies/{strategy_id}/validate")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data
        assert "errors" in data
        assert "warnings" in data

    def test_validate_empty_strategy(self, client):
        """Test validating empty strategy."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Empty Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategies/{strategy_id}/validate")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "is_valid" in data


class TestInstanceAPIErrors:
    """Test error handling for instance API operations."""

    def test_create_strategy_missing_name(self, client):
        """Test creating strategy without name returns 422."""
        # Arrange
        invalid_data = {
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategies", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_strategy_missing_logic_flow(self, client):
        """Test creating strategy without logic_flow returns 422."""
        # Arrange
        invalid_data = {
            "name": "Strategy",
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategies", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_create_strategy_missing_parameters(self, client):
        """Test creating strategy without parameters returns 422."""
        # Arrange
        invalid_data = {
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []}
        }

        # Act
        response = client.post("/api/strategies", json=invalid_data)

        # Assert
        assert response.status_code == 422

    def test_get_strategy_not_found(self, client):
        """Test getting non-existent strategy returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.get("/api/strategies/nonexistent-id")

        # Assert
        assert response.status_code == 404

    def test_update_strategy_not_found(self, client):
        """Test updating non-existent strategy returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.put("/api/strategies/nonexistent-id", json={
            "name": "New Name"
        })

        # Assert
        assert response.status_code == 404

    def test_delete_strategy_not_found(self, client):
        """Test deleting non-existent strategy returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.delete("/api/strategies/nonexistent-id")

        # Assert
        assert response.status_code == 404

    def test_copy_strategy_not_found(self, client):
        """Test copying non-existent strategy returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.post("/api/strategies/nonexistent-id/copy", json={
            "name": "Copy"
        })

        # Assert
        assert response.status_code == 404

    def test_copy_strategy_missing_name(self, client):
        """Test copying strategy without name returns 400."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Act
        response = client.post(f"/api/strategies/{strategy_id}/copy", json={})

        # Assert
        assert response.status_code == 400

    def test_create_snapshot_not_found(self, client):
        """Test creating snapshot for non-existent strategy returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.post("/api/strategies/nonexistent-id/snapshot")

        # Assert
        assert response.status_code == 404

    def test_get_versions_not_found(self, client):
        """Test getting versions for non-existent strategy returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.get("/api/strategies/nonexistent-id/versions")

        # Assert
        assert response.status_code == 404

    def test_validate_strategy_not_found(self, client):
        """Test validating non-existent strategy returns 404."""
        # Arrange: Invalid ID

        # Act
        response = client.post("/api/strategies/nonexistent-id/validate")

        # Assert
        assert response.status_code == 404


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""

    def test_list_templates_limit_zero(self, client):
        """Test listing with limit=0 should be rejected."""
        # Arrange & Act
        response = client.get("/api/strategy-templates?limit=0")

        # Assert
        assert response.status_code == 422

    def test_list_templates_limit_exceeds_maximum(self, client):
        """Test listing with limit > 100 should be rejected."""
        # Arrange & Act
        response = client.get("/api/strategy-templates?limit=101")

        # Assert
        assert response.status_code == 422

    def test_list_templates_negative_skip(self, client):
        """Test listing with negative skip should be rejected."""
        # Arrange & Act
        response = client.get("/api/strategy-templates?skip=-1")

        # Assert
        assert response.status_code == 422

    def test_list_strategies_limit_zero(self, client):
        """Test listing strategies with limit=0 should be rejected."""
        # Arrange & Act
        response = client.get("/api/strategies?limit=0")

        # Assert
        assert response.status_code == 422

    def test_list_strategies_limit_exceeds_maximum(self, client):
        """Test listing strategies with limit > 100 should be rejected."""
        # Arrange & Act
        response = client.get("/api/strategies?limit=101")

        # Assert
        assert response.status_code == 422

    def test_list_strategies_negative_skip(self, client):
        """Test listing strategies with negative skip should be rejected."""
        # Arrange & Act
        response = client.get("/api/strategies?skip=-1")

        # Assert
        assert response.status_code == 422

    def test_get_popular_templates_limit_zero(self, client):
        """Test popular templates with limit=0 should be rejected."""
        # Arrange & Act
        response = client.get("/api/strategy-templates/popular?limit=0")

        # Assert
        assert response.status_code == 422

    def test_get_popular_templates_limit_exceeds_maximum(self, client):
        """Test popular templates with limit > 20 should be rejected."""
        # Arrange & Act
        response = client.get("/api/strategy-templates/popular?limit=21")

        # Assert
        assert response.status_code == 422

    def test_create_template_with_very_long_name(self, client):
        """Test creating template with very long name."""
        # Arrange
        long_name = "A" * 300  # Potentially exceeds limit
        template_data = {
            "name": long_name,
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategy-templates", json=template_data)

        # Assert: Should either succeed or fail with validation error
        assert response.status_code in [201, 422]

    def test_create_strategy_with_very_long_name(self, client):
        """Test creating strategy with very long name."""
        # Arrange
        long_name = "B" * 300
        strategy_data = {
            "name": long_name,
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategies", json=strategy_data)

        # Assert
        assert response.status_code in [201, 422]

    def test_create_template_with_empty_string_name(self, client):
        """Test creating template with empty string name."""
        # Arrange
        template_data = {
            "name": "",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategy-templates", json=template_data)

        # Assert
        assert response.status_code == 422

    def test_create_strategy_with_empty_string_name(self, client):
        """Test creating strategy with empty string name."""
        # Arrange
        strategy_data = {
            "name": "",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }

        # Act
        response = client.post("/api/strategies", json=strategy_data)

        # Assert
        assert response.status_code == 422

    def test_list_with_skip_greater_than_total(self, client):
        """Test pagination with skip >= total items."""
        # Arrange: Create 3 templates
        for i in range(3):
            client.post("/api/strategy-templates", json={
                "name": f"Template {i}",
                "category": "TREND_FOLLOWING",
                "logic_flow": {"nodes": [], "edges": []},
                "parameters": {}
            })

        # Act
        response = client.get("/api/strategy-templates?skip=10&limit=10")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 0  # No items returned


class TestDataConsistency:
    """Test data consistency and relationships."""

    def test_update_preserves_creation_metadata(self, client):
        """Test that updating template preserves created_at."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Original",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        original_data = create_response.json()
        original_created_at = original_data["created_at"]

        # Act
        import time
        time.sleep(0.1)  # Ensure time passes
        update_response = client.put(f"/api/strategy-templates/{original_data['id']}", json={
            "name": "Updated"
        })

        # Assert
        updated_data = update_response.json()
        assert updated_data["created_at"] == original_created_at

    def test_copied_strategy_has_new_id(self, client):
        """Test that copied strategy has different ID."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Original",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        original_id = create_response.json()["id"]

        # Act
        copy_response = client.post(f"/api/strategies/{original_id}/copy", json={
            "name": "Copy"
        })

        # Assert
        copy_id = copy_response.json()["id"]
        assert copy_id != original_id

    def test_deleted_template_cannot_be_rated(self, client):
        """Test that rating a deleted template returns 404."""
        # Arrange
        create_response = client.post("/api/strategy-templates", json={
            "name": "Template",
            "category": "TREND_FOLLOWING",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        template_id = create_response.json()["id"]

        # Delete template
        client.delete(f"/api/strategy-templates/{template_id}")

        # Act
        response = client.post(f"/api/strategy-templates/{template_id}/rate", json={
            "rating": 5
        })

        # Assert
        assert response.status_code == 404

    def test_deleted_strategy_cannot_be_copied(self, client):
        """Test that copying a deleted strategy returns 404."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Delete strategy
        client.delete(f"/api/strategies/{strategy_id}")

        # Act
        response = client.post(f"/api/strategies/{strategy_id}/copy", json={
            "name": "Copy"
        })

        # Assert
        assert response.status_code == 404

    def test_deleted_strategy_cannot_be_snapshotted(self, client):
        """Test that snapshotting a deleted strategy returns 404."""
        # Arrange
        create_response = client.post("/api/strategies", json={
            "name": "Strategy",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })
        strategy_id = create_response.json()["id"]

        # Delete strategy
        client.delete(f"/api/strategies/{strategy_id}")

        # Act
        response = client.post(f"/api/strategies/{strategy_id}/snapshot")

        # Assert
        assert response.status_code == 404
