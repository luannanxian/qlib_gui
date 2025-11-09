"""
CodeGeneratorService

Service for generating Python code from logic flows using Jinja2 templates.
Supports Qlib framework integration and comprehensive code validation.
"""

import hashlib
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import (
    CodeGeneration,
    NodeTemplate,
    ValidationStatus
)
from app.database.repositories.code_generation_repository import CodeGenerationRepository
from app.database.repositories.node_template_repository import NodeTemplateRepository
from app.modules.strategy.exceptions import (
    CodeGenerationError,
    TemplateNotFoundError,
    TemplateRenderError,
    ValidationError,
    ResourceNotFoundError
)


class CodeGeneratorService:
    """
    Code generation service for converting logic flows to Python code.

    Core responsibilities:
    1. Logic flow → Python code conversion
    2. Jinja2 template rendering
    3. Support for 6 node types: INDICATOR, CONDITION, SIGNAL, POSITION, STOP_LOSS, STOP_PROFIT
    4. SHA-256 code deduplication
    5. Qlib framework compatible code generation
    """

    def __init__(
        self,
        db: AsyncSession,
        code_generation_repo: CodeGenerationRepository,
        node_template_repo: NodeTemplateRepository,
        template_env: Optional[Environment] = None
    ):
        """
        Initialize code generator service.

        Args:
            db: Database session
            code_generation_repo: Repository for code generation history
            node_template_repo: Repository for node templates
            template_env: Optional Jinja2 environment (for testing)
        """
        self.db = db
        self.code_generation_repo = code_generation_repo
        self.node_template_repo = node_template_repo

        # Initialize Jinja2 environment
        if template_env:
            self.template_env = template_env
        else:
            template_dir = Path(__file__).parent.parent / "templates" / "strategy_builder"
            self.template_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True
            )

        logger.info("CodeGeneratorService initialized")

    async def generate_code(
        self,
        instance_id: str,
        user_id: str,
        logic_flow: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> CodeGeneration:
        """
        Generate Python code from logic flow.

        Process:
        1. Validate logic flow structure
        2. Retrieve node templates
        3. Generate code for each node
        4. Combine into complete strategy class
        5. Calculate code hash (SHA-256)
        6. Store generation record

        Args:
            instance_id: Strategy instance ID
            user_id: User requesting code generation
            logic_flow: Logic flow JSON structure
            parameters: Parameter values for nodes

        Returns:
            CodeGeneration instance with generated code and validation results

        Raises:
            ValidationError: If logic flow validation fails
            CodeGenerationError: If code generation fails
        """
        try:
            logger.info(f"Starting code generation for instance {instance_id}")

            # Validate logic flow structure
            if not isinstance(logic_flow, dict):
                raise ValidationError("Logic flow must be a dictionary")

            # Check for required fields
            if "nodes" not in logic_flow:
                raise ValidationError("Logic flow must contain 'nodes' field")

            nodes = logic_flow.get("nodes", [])
            edges = logic_flow.get("edges", [])

            # Validate nodes structure
            if not isinstance(nodes, list):
                raise ValidationError("Logic flow 'nodes' must be a list")

            logger.debug(f"Logic flow has {len(nodes)} nodes and {len(edges)} edges")

            # Generate code for each node
            node_code_snippets = []
            for node in nodes:
                node_id = node.get("id")
                template_id = node.get("template_id")

                if not template_id:
                    logger.warning(f"Node {node_id} has no template_id, skipping")
                    continue

                # Retrieve node template
                node_template = await self.node_template_repo.get(template_id)
                if not node_template:
                    raise ResourceNotFoundError(f"Node template {template_id} not found")

                # Get node parameters
                node_params = parameters.get(node_id, {})

                # Generate node code
                node_code = await self.generate_node_code(
                    node=node,
                    node_template=node_template,
                    parameters=node_params
                )

                node_code_snippets.append(node_code)

            # Combine code snippets
            code_body = "\n\n".join(node_code_snippets)

            # Generate complete strategy class
            complete_code = await self.render_template(
                template_name="strategy_class.py.j2",
                context={
                    "code_body": code_body,
                    "parameters": parameters
                }
            )

            # Calculate code hash
            code_hash = await self.calculate_code_hash(complete_code)

            # Check for duplicates
            existing = await self.check_code_duplicate(instance_id, code_hash)
            if existing:
                logger.info(f"Code already exists with hash {code_hash[:8]}...")
                return existing

            # Create code generation record
            code_generation_data = {
                "instance_id": instance_id,
                "user_id": user_id,
                "generated_code": complete_code,
                "code_hash": code_hash,
                "logic_flow_snapshot": logic_flow,
                "parameters_snapshot": parameters,
                "validation_status": ValidationStatus.PENDING.value,
                "syntax_check_passed": None,
                "security_check_passed": None
            }

            created = await self.code_generation_repo.create(code_generation_data)
            logger.info(f"Code generation created: {created.id}")

            return created

        except (ValidationError, ResourceNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise CodeGenerationError(f"Failed to generate code: {str(e)}")

    async def generate_node_code(
        self,
        node: Dict[str, Any],
        node_template: NodeTemplate,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Generate code for a single node.

        Args:
            node: Node definition from logic flow
            node_template: Node template with generation hints
            parameters: Parameter values for this node

        Returns:
            Generated code snippet for this node

        Raises:
            CodeGenerationError: If code generation fails
        """
        try:
            node_type = node_template.node_type.lower()
            template_name = f"{node_type}_node.py.j2"

            context = {
                "node": node_template,
                "params": parameters,
                "node_id": node.get("id"),
                "input_var": "signal"  # Default input variable
            }

            code = await self.render_template(template_name, context)
            return code

        except TemplateNotFoundError:
            # Fallback to generic template
            logger.warning(f"Template {template_name} not found, using generic template")
            return f"# {node_template.display_name}\n# TODO: Implement {node_type} logic"
        except Exception as e:
            logger.error(f"Failed to generate node code: {e}")
            raise CodeGenerationError(f"Node code generation failed: {str(e)}")

    async def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render Jinja2 code template.

        Args:
            template_name: Template file name (e.g., "indicator_node.py.j2")
            context: Template context variables

        Returns:
            Rendered code string

        Raises:
            TemplateNotFoundError: If template file not found
            TemplateRenderError: If template rendering fails
        """
        try:
            template = self.template_env.get_template(template_name)
            rendered = template.render(**context)
            return rendered

        except TemplateNotFound as e:
            logger.error(f"Template not found: {template_name}")
            raise TemplateNotFoundError(f"Template {template_name} not found")
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise TemplateRenderError(f"Failed to render template {template_name}: {str(e)}")

    async def calculate_code_hash(self, code: str) -> str:
        """
        Calculate SHA-256 hash of code for deduplication.

        Args:
            code: Python code string

        Returns:
            SHA-256 hash (hex string)
        """
        # Normalize code (strip whitespace)
        normalized_code = code.strip()

        # Calculate SHA-256 hash
        hash_object = hashlib.sha256(normalized_code.encode('utf-8'))
        code_hash = hash_object.hexdigest()

        logger.debug(f"Calculated code hash: {code_hash[:8]}...")
        return code_hash

    async def get_code_history(
        self,
        instance_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[CodeGeneration], int]:
        """
        Get code generation history for strategy instance.

        Args:
            instance_id: Strategy instance ID
            user_id: User ID for authorization
            skip: Pagination offset
            limit: Max records

        Returns:
            Tuple of (code generation list, total count)

        Raises:
            ResourceNotFoundError: If instance not found
        """
        try:
            # Get code generations
            generations = await self.code_generation_repo.find_history_by_instance(
                instance_id=instance_id,
                skip=skip,
                limit=limit
            )

            # Filter by user_id (authorization)
            user_generations = [g for g in generations if g.user_id == user_id]

            # Get total count
            stmt = select(func.count(CodeGeneration.id)).where(
                CodeGeneration.instance_id == instance_id,
                CodeGeneration.user_id == user_id,
                CodeGeneration.is_deleted == False
            )
            result = await self.db.execute(stmt)
            total = result.scalar() or 0

            logger.info(f"Retrieved {len(user_generations)} code generations for instance {instance_id}")
            return user_generations, total

        except Exception as e:
            logger.error(f"Failed to get code history: {e}")
            raise CodeGenerationError(f"Failed to retrieve code history: {str(e)}")

    async def check_code_duplicate(
        self,
        instance_id: str,
        code_hash: str
    ) -> Optional[CodeGeneration]:
        """
        Check if code with same hash already exists.

        Args:
            instance_id: Strategy instance ID
            code_hash: Code hash to check

        Returns:
            Existing CodeGeneration if found, None otherwise
        """
        try:
            generations = await self.code_generation_repo.find_by_code_hash(
                code_hash=code_hash,
                instance_id=instance_id
            )

            if generations:
                logger.info(f"Found duplicate code with hash {code_hash[:8]}...")
                return generations[0]

            return None

        except Exception as e:
            logger.error(f"Failed to check code duplicate: {e}")
            return None


__all__ = ["CodeGeneratorService"]
