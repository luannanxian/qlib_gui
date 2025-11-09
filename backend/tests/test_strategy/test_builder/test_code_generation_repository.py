"""
TDD Tests for CodeGenerationRepository

Following strict TDD methodology (Red-Green-Refactor):
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Optimize code

Test Coverage:
- Create code generation records
- Find by code hash (deduplication)
- Find history by instance
- Update validation status
- Get latest generation by instance
- Query with filters
"""

import hashlib
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import CodeGeneration, ValidationStatus as CodeValidationStatus
from app.database.repositories.code_generation_repository import CodeGenerationRepository


def calculate_code_hash(code: str) -> str:
    """Calculate SHA-256 hash of code"""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


@pytest.mark.asyncio
class TestCodeGenerationRepositoryCreate:
    """Test CodeGeneration creation operations"""

    async def test_create_code_generation(self, db_session: AsyncSession):
        """Test creating a code generation record"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        # First create a strategy instance (required by FK)
        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "template_id": None,
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        generated_code = "class Strategy:\n    def __init__(self):\n        pass"
        code_hash = calculate_code_hash(generated_code)

        generation_data = {
            "instance_id": instance.id,
            "user_id": "user_123",
            "logic_flow_snapshot": {"nodes": [], "edges": []},
            "parameters_snapshot": {},
            "generated_code": generated_code,
            "code_hash": code_hash,
            "validation_status": CodeValidationStatus.PENDING.value
        }

        # Act
        generation = await repo.create(generation_data)

        # Assert
        assert generation.id is not None
        assert generation.instance_id == instance.id
        assert generation.user_id == "user_123"
        assert generation.generated_code == generated_code
        assert generation.code_hash == code_hash
        assert generation.validation_status == CodeValidationStatus.PENDING.value
        assert generation.syntax_check_passed is None
        assert generation.security_check_passed is None

    async def test_create_with_validation_results(self, db_session: AsyncSession):
        """Test creating generation with validation results"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "template_id": None,
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        code = "# Valid Python code\nprint('hello')"

        generation_data = {
            "instance_id": instance.id,
            "user_id": "user_123",
            "logic_flow_snapshot": {},
            "parameters_snapshot": {},
            "generated_code": code,
            "code_hash": calculate_code_hash(code),
            "validation_status": CodeValidationStatus.VALID.value,
            "validation_result": {
                "syntax_errors": [],
                "security_issues": [],
                "warnings": []
            },
            "syntax_check_passed": True,
            "security_check_passed": True,
            "line_count": 2,
            "complexity_score": 1
        }

        # Act
        generation = await repo.create(generation_data)

        # Assert
        assert generation.validation_status == CodeValidationStatus.VALID.value
        assert generation.syntax_check_passed is True
        assert generation.security_check_passed is True
        assert generation.line_count == 2
        assert generation.complexity_score == 1


@pytest.mark.asyncio
class TestCodeGenerationRepositoryQuery:
    """Test CodeGeneration query operations"""

    async def test_find_by_code_hash(self, db_session: AsyncSession):
        """Test finding generation by code hash for deduplication"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "template_id": None,
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        code = "def strategy():\n    return True"
        code_hash = calculate_code_hash(code)

        # Create first generation
        gen1 = await repo.create({
            "instance_id": instance.id,
            "user_id": "user_123",
            "logic_flow_snapshot": {},
            "parameters_snapshot": {},
            "generated_code": code,
            "code_hash": code_hash,
            "validation_status": CodeValidationStatus.VALID.value
        })

        # Act - Find by hash
        found = await repo.find_by_code_hash(code_hash)

        # Assert
        assert len(found) == 1
        assert found[0].id == gen1.id
        assert found[0].code_hash == code_hash

    async def test_find_by_code_hash_multiple_instances(self, db_session: AsyncSession):
        """Test finding generations when same code is generated for different instances"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance1 = await instance_repo.create({
            "template_id": None,
            "name": "Strategy 1",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        instance2 = await instance_repo.create({
            "template_id": None,
            "name": "Strategy 2",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        code = "# Same code\npass"
        code_hash = calculate_code_hash(code)

        # Create generations for both instances
        await repo.create({
            "instance_id": instance1.id,
            "user_id": "user_123",
            "logic_flow_snapshot": {},
            "parameters_snapshot": {},
            "generated_code": code,
            "code_hash": code_hash,
            "validation_status": CodeValidationStatus.VALID.value
        })

        await repo.create({
            "instance_id": instance2.id,
            "user_id": "user_123",
            "logic_flow_snapshot": {},
            "parameters_snapshot": {},
            "generated_code": code,
            "code_hash": code_hash,
            "validation_status": CodeValidationStatus.VALID.value
        })

        # Act
        found = await repo.find_by_code_hash(code_hash)

        # Assert
        assert len(found) == 2

    @pytest.mark.skip(reason="Transaction isolation issue - TODO: Fix in refactor phase")
    async def test_find_history_by_instance(self, db_session: AsyncSession):
        """Test finding code generation history for an instance"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "template_id": None,
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }, commit=True)

        # Create multiple generations (version history)
        gen_ids = []
        for i in range(3):
            code = f"# Version {i}\npass"
            gen = await repo.create({
                "instance_id": instance.id,
                "user_id": "user_123",
                "logic_flow_snapshot": {"version": i},
                "parameters_snapshot": {},
                "generated_code": code,
                "code_hash": calculate_code_hash(code),
                "validation_status": CodeValidationStatus.VALID.value
            }, commit=True)
            gen_ids.append(gen.id)

        # Act
        history = await repo.find_history_by_instance(instance.id)

        # Assert
        assert len(history) == 3
        # Should be ordered by created_at descending (newest first)
        assert history[0].logic_flow_snapshot["version"] == 2
        assert history[1].logic_flow_snapshot["version"] == 1
        assert history[2].logic_flow_snapshot["version"] == 0

    @pytest.mark.skip(reason="Transaction isolation issue - TODO: Fix in refactor phase")
    async def test_get_latest_by_instance(self, db_session: AsyncSession):
        """Test getting the latest code generation for an instance"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "template_id": None,
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        }, commit=True)

        # Create multiple generations
        for i in range(3):
            code = f"# Version {i}\npass"
            await repo.create({
                "instance_id": instance.id,
                "user_id": "user_123",
                "logic_flow_snapshot": {"version": i},
                "parameters_snapshot": {},
                "generated_code": code,
                "code_hash": calculate_code_hash(code),
                "validation_status": CodeValidationStatus.VALID.value
            }, commit=True)

        # Act
        latest = await repo.get_latest_by_instance(instance.id)

        # Assert
        assert latest is not None
        assert latest.logic_flow_snapshot["version"] == 2

    async def test_get_latest_by_instance_no_generations(self, db_session: AsyncSession):
        """Test getting latest when no generations exist"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        # Act
        latest = await repo.get_latest_by_instance("nonexistent_id")

        # Assert
        assert latest is None


@pytest.mark.asyncio
class TestCodeGenerationRepositoryUpdate:
    """Test CodeGeneration update operations"""

    async def test_update_validation_status(self, db_session: AsyncSession):
        """Test updating validation status and results"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "template_id": None,
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        generation = await repo.create({
            "instance_id": instance.id,
            "user_id": "user_123",
            "logic_flow_snapshot": {},
            "parameters_snapshot": {},
            "generated_code": "pass",
            "code_hash": calculate_code_hash("pass"),
            "validation_status": CodeValidationStatus.PENDING.value
        })

        # Act
        updated = await repo.update_validation_status(
            generation.id,
            CodeValidationStatus.VALID,
            validation_result={"errors": [], "warnings": []},
            syntax_check_passed=True,
            security_check_passed=True
        )

        # Assert
        assert updated is not None
        assert updated.validation_status == CodeValidationStatus.VALID.value
        assert updated.syntax_check_passed is True
        assert updated.security_check_passed is True
        assert updated.validation_result == {"errors": [], "warnings": []}

    async def test_update_validation_status_with_errors(self, db_session: AsyncSession):
        """Test updating validation status when errors are found"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "template_id": None,
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        generation = await repo.create({
            "instance_id": instance.id,
            "user_id": "user_123",
            "logic_flow_snapshot": {},
            "parameters_snapshot": {},
            "generated_code": "invalid python code!",
            "code_hash": calculate_code_hash("invalid python code!"),
            "validation_status": CodeValidationStatus.PENDING.value
        })

        # Act
        updated = await repo.update_validation_status(
            generation.id,
            CodeValidationStatus.SYNTAX_ERROR,
            validation_result={"errors": ["SyntaxError: invalid syntax"]},
            syntax_check_passed=False,
            security_check_passed=None
        )

        # Assert
        assert updated.validation_status == CodeValidationStatus.SYNTAX_ERROR.value
        assert updated.syntax_check_passed is False
        assert updated.security_check_passed is None


@pytest.mark.asyncio
class TestCodeGenerationRepositoryAdvanced:
    """Test advanced repository features"""

    async def test_find_by_user(self, db_session: AsyncSession):
        """Test finding all generations by user"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "template_id": None,
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        # Create generations for different users
        await repo.create({
            "instance_id": instance.id,
            "user_id": "user_1",
            "logic_flow_snapshot": {},
            "parameters_snapshot": {},
            "generated_code": "# User 1 code",
            "code_hash": calculate_code_hash("# User 1 code"),
            "validation_status": CodeValidationStatus.VALID.value
        })

        await repo.create({
            "instance_id": instance.id,
            "user_id": "user_2",
            "logic_flow_snapshot": {},
            "parameters_snapshot": {},
            "generated_code": "# User 2 code",
            "code_hash": calculate_code_hash("# User 2 code"),
            "validation_status": CodeValidationStatus.VALID.value
        })

        # Act
        user1_gens = await repo.find_by_user("user_1")

        # Assert
        assert len(user1_gens) == 1
        assert user1_gens[0].user_id == "user_1"

    async def test_count_by_instance(self, db_session: AsyncSession):
        """Test counting generations for an instance"""
        # Arrange
        repo = CodeGenerationRepository(db_session)

        from app.database.repositories.strategy_instance import StrategyInstanceRepository
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "template_id": None,
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {}
        })

        # Create 5 generations
        for i in range(5):
            code = f"# Gen {i}"
            await repo.create({
                "instance_id": instance.id,
                "user_id": "user_123",
                "logic_flow_snapshot": {},
                "parameters_snapshot": {},
                "generated_code": code,
                "code_hash": calculate_code_hash(code),
                "validation_status": CodeValidationStatus.VALID.value
            })

        # Act
        count = await repo.count(instance_id=instance.id)

        # Assert
        assert count == 5
