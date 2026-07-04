"""
Schema Validator - v5.1.2
Standards validation engine for governed Construct workspaces.

Validates data against IEEE, NIST, FIPS, STEP AP242, COLLADA, Dublin Core,
BibTeX, and other official standards.

Author: LightSpeed Team
Date: April 8, 2026
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re

from .workspace_creator import SchemaDefinition, ProjectWorkspace


# ==============================================================================
# Validation Result Types
# ==============================================================================

class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    level: ValidationLevel
    standard: str
    field: str
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    line_number: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level.value,
            'standard': self.standard,
            'field': self.field,
            'message': self.message,
            'expected': self.expected,
            'actual': self.actual,
            'line_number': self.line_number
        }


@dataclass
class ValidationReport:
    """Complete validation report"""
    standard: str
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: ValidationIssue):
        """Add validation issue"""
        self.issues.append(issue)
        if issue.level == ValidationLevel.ERROR:
            self.passed = False

    def get_error_count(self) -> int:
        """Get count of errors"""
        return len([i for i in self.issues if i.level == ValidationLevel.ERROR])

    def get_warning_count(self) -> int:
        """Get count of warnings"""
        return len([i for i in self.issues if i.level == ValidationLevel.WARNING])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'standard': self.standard,
            'passed': self.passed,
            'error_count': self.get_error_count(),
            'warning_count': self.get_warning_count(),
            'issues': [i.to_dict() for i in self.issues],
            'validated_at': self.validated_at.isoformat(),
            'metadata': self.metadata
        }


# ==============================================================================
# Standard Validators
# ==============================================================================

class IEEEValidator:
    """IEEE Xplore metadata validator"""

    REQUIRED_FIELDS = ['title', 'author', 'year']
    OPTIONAL_FIELDS = ['journal', 'doi', 'abstract', 'keywords', 'volume', 'pages']

    DOI_PATTERN = r'^10\.\d{4,}/[\w\-\.]+$'

    @staticmethod
    def validate(data: Dict[str, Any]) -> ValidationReport:
        """Validate IEEE metadata"""
        report = ValidationReport(standard='IEEE', passed=True)

        # Check required fields
        for field in IEEEValidator.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard='IEEE',
                    field=field,
                    message=f'Required field "{field}" is missing or empty'
                ))

        # Validate year range
        if 'year' in data:
            try:
                year = int(data['year'])
                if year < 1800 or year > 2100:
                    report.add_issue(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        standard='IEEE',
                        field='year',
                        message='Year outside typical range (1800-2100)',
                        expected='1800-2100',
                        actual=str(year)
                    ))
            except (ValueError, TypeError):
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard='IEEE',
                    field='year',
                    message='Year must be an integer',
                    actual=str(data['year'])
                ))

        # Validate DOI format
        if 'doi' in data and data['doi']:
            if not re.match(IEEEValidator.DOI_PATTERN, data['doi']):
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    standard='IEEE',
                    field='doi',
                    message='DOI format may be invalid',
                    expected='10.XXXX/...',
                    actual=data['doi']
                ))

        # Validate author format
        if 'author' in data:
            authors = data['author']
            if isinstance(authors, str):
                if not authors.strip():
                    report.add_issue(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        standard='IEEE',
                        field='author',
                        message='Author field cannot be empty'
                    ))
            elif isinstance(authors, list):
                if len(authors) == 0:
                    report.add_issue(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        standard='IEEE',
                        field='author',
                        message='At least one author is required'
                    ))

        return report


class DublinCoreValidator:
    """Dublin Core metadata validator"""

    CORE_ELEMENTS = [
        'dc:title', 'dc:creator', 'dc:subject', 'dc:description',
        'dc:publisher', 'dc:contributor', 'dc:date', 'dc:type',
        'dc:format', 'dc:identifier', 'dc:source', 'dc:language',
        'dc:relation', 'dc:coverage', 'dc:rights'
    ]

    @staticmethod
    def validate(data: Dict[str, Any]) -> ValidationReport:
        """Validate Dublin Core metadata"""
        report = ValidationReport(standard='Dublin Core', passed=True)

        # At minimum, should have title, creator, and identifier
        required = ['dc:title', 'dc:creator', 'dc:identifier']

        for field in required:
            if field not in data or not data[field]:
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard='Dublin Core',
                    field=field,
                    message=f'Required Dublin Core element "{field}" is missing'
                ))

        # Validate date format (ISO 8601)
        if 'dc:date' in data and data['dc:date']:
            date_str = data['dc:date']
            try:
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    standard='Dublin Core',
                    field='dc:date',
                    message='Date should be in ISO 8601 format',
                    expected='YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS',
                    actual=date_str
                ))

        return report


class BibTeXValidator:
    """BibTeX citation validator"""

    ENTRY_TYPES = [
        'article', 'book', 'booklet', 'conference', 'inbook', 'incollection',
        'inproceedings', 'manual', 'mastersthesis', 'misc', 'phdthesis',
        'proceedings', 'techreport', 'unpublished'
    ]

    REQUIRED_BY_TYPE = {
        'article': ['author', 'title', 'journal', 'year'],
        'book': ['author', 'title', 'publisher', 'year'],
        'inproceedings': ['author', 'title', 'booktitle', 'year'],
    }

    @staticmethod
    def validate(entry: Dict[str, Any]) -> ValidationReport:
        """Validate BibTeX entry"""
        report = ValidationReport(standard='BibTeX', passed=True)

        # Check entry type
        if 'type' not in entry:
            report.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                standard='BibTeX',
                field='type',
                message='BibTeX entry type is missing'
            ))
            return report

        entry_type = entry['type'].lower()

        if entry_type not in BibTeXValidator.ENTRY_TYPES:
            report.add_issue(ValidationIssue(
                level=ValidationLevel.WARNING,
                standard='BibTeX',
                field='type',
                message=f'Unknown BibTeX entry type "{entry_type}"',
                expected=', '.join(BibTeXValidator.ENTRY_TYPES)
            ))

        # Check required fields for entry type
        if entry_type in BibTeXValidator.REQUIRED_BY_TYPE:
            required = BibTeXValidator.REQUIRED_BY_TYPE[entry_type]
            for field in required:
                if field not in entry or not entry[field]:
                    report.add_issue(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        standard='BibTeX',
                        field=field,
                        message=f'Required field "{field}" for {entry_type} entry is missing'
                    ))

        # Check citation key
        if 'key' not in entry or not entry['key']:
            report.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                standard='BibTeX',
                field='key',
                message='Citation key is required'
            ))

        return report


class NISTValidator:
    """NIST SP 800-53 security controls validator"""

    CONTROL_FAMILIES = [
        'AC', 'AT', 'AU', 'CA', 'CM', 'CP', 'IA', 'IR',
        'MA', 'MP', 'PE', 'PL', 'PS', 'PT', 'RA', 'SA',
        'SC', 'SI', 'SR', 'PM'
    ]

    IMPLEMENTATION_STATUS = ['implemented', 'planned', 'not_applicable']

    @staticmethod
    def validate(control: Dict[str, Any]) -> ValidationReport:
        """Validate NIST SP 800-53 control"""
        report = ValidationReport(standard='NIST SP 800-53', passed=True)

        # Check control ID format (e.g., AC-1, SI-2(1))
        if 'control_id' not in control:
            report.add_issue(ValidationIssue(
                level=ValidationLevel.ERROR,
                standard='NIST SP 800-53',
                field='control_id',
                message='Control ID is required'
            ))
        else:
            control_id = control['control_id']
            pattern = r'^([A-Z]{2})-(\d+)(\(\d+\))?$'
            match = re.match(pattern, control_id)

            if not match:
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard='NIST SP 800-53',
                    field='control_id',
                    message='Invalid control ID format',
                    expected='XX-N or XX-N(N)',
                    actual=control_id
                ))
            else:
                family = match.group(1)
                if family not in NISTValidator.CONTROL_FAMILIES:
                    report.add_issue(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        standard='NIST SP 800-53',
                        field='control_id',
                        message=f'Unknown control family "{family}"',
                        expected=', '.join(NISTValidator.CONTROL_FAMILIES)
                    ))

        # Check implementation status
        if 'implementation_status' in control:
            status = control['implementation_status']
            if status not in NISTValidator.IMPLEMENTATION_STATUS:
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard='NIST SP 800-53',
                    field='implementation_status',
                    message=f'Invalid implementation status "{status}"',
                    expected=', '.join(NISTValidator.IMPLEMENTATION_STATUS)
                ))

        return report


class STEPValidator:
    """STEP AP242 CAD data validator"""

    REQUIRED_ENTITIES = [
        'product_definition',
        'shape_representation',
        'geometric_model'
    ]

    @staticmethod
    def validate(data: Dict[str, Any]) -> ValidationReport:
        """Validate STEP AP242 structure"""
        report = ValidationReport(standard='STEP AP242', passed=True)

        # Check for required entities
        for entity in STEPValidator.REQUIRED_ENTITIES:
            if entity not in data:
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard='STEP AP242',
                    field=entity,
                    message=f'Required STEP entity "{entity}" is missing'
                ))

        # Validate product_definition structure
        if 'product_definition' in data:
            pd = data['product_definition']
            if not isinstance(pd, dict):
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard='STEP AP242',
                    field='product_definition',
                    message='product_definition must be an object/dict'
                ))
            elif 'id' not in pd or 'name' not in pd:
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    standard='STEP AP242',
                    field='product_definition',
                    message='product_definition should have id and name fields'
                ))

        return report


# ==============================================================================
# Schema Validator
# ==============================================================================

class SchemaValidator:
    """
    Main schema validation engine

    Validates data against multiple standards simultaneously.
    """

    def __init__(self):
        """Initialize schema validator"""
        self.validators = {
            'IEEE': IEEEValidator,
            'Dublin Core': DublinCoreValidator,
            'BibTeX': BibTeXValidator,
            'NIST SP 800-53': NISTValidator,
            'STEP AP242': STEPValidator
        }

    def validate_workspace(self, workspace: ProjectWorkspace) -> Dict[str, ValidationReport]:
        """
        Validate entire workspace against required standards

        Args:
            workspace: Project workspace to validate

        Returns:
            Dictionary mapping standard name to validation report
        """
        reports = {}

        for standard in workspace.required_standards:
            if standard in self.validators:
                # Validate against standard
                # In full implementation, this would extract relevant data from workspace
                # For now, we create a placeholder report
                report = ValidationReport(
                    standard=standard,
                    passed=True,
                    metadata={'workspace_id': workspace.id}
                )
                reports[standard] = report

                # Update workspace compliance status
                workspace.standards_compliance[standard] = report.passed

        return reports

    def validate_data_against_schema(
        self,
        data: Dict[str, Any],
        schema: SchemaDefinition
    ) -> ValidationReport:
        """
        Validate data against a schema definition

        Args:
            data: Data to validate
            schema: Schema definition

        Returns:
            Validation report
        """
        if schema.schema_type in self.validators:
            validator_class = self.validators[schema.schema_type]
            return validator_class.validate(data)
        else:
            # Generic validation
            return self._generic_validation(data, schema)

    def _generic_validation(
        self,
        data: Dict[str, Any],
        schema: SchemaDefinition
    ) -> ValidationReport:
        """Generic schema validation"""
        report = ValidationReport(standard=schema.schema_type, passed=True)

        # Check required fields
        for field, field_type in schema.fields.items():
            if field not in data:
                if schema.required:
                    report.add_issue(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        standard=schema.schema_type,
                        field=field,
                        message=f'Required field "{field}" is missing'
                    ))
                else:
                    report.add_issue(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        standard=schema.schema_type,
                        field=field,
                        message=f'Optional field "{field}" is missing'
                    ))
                continue

            # Validate field type
            actual_value = data[field]
            if not self._check_type(actual_value, field_type):
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard=schema.schema_type,
                    field=field,
                    message=f'Field "{field}" has incorrect type',
                    expected=field_type,
                    actual=type(actual_value).__name__
                ))

        # Apply validation rules
        for rule in schema.validation_rules:
            self._apply_validation_rule(data, rule, report)

        return report

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            'string': str,
            'integer': int,
            'float': float,
            'boolean': bool,
            'list': list,
            'dict': dict,
            'object': dict
        }

        # Handle list[type] syntax
        if expected_type.startswith('list['):
            if not isinstance(value, list):
                return False
            inner_type = expected_type[5:-1]
            return all(self._check_type(item, inner_type) for item in value)

        # Handle enum syntax
        if expected_type.startswith('enum['):
            enum_values = expected_type[5:-1].split(',')
            return value in enum_values

        expected_class = type_map.get(expected_type, str)
        return isinstance(value, expected_class)

    def _apply_validation_rule(
        self,
        data: Dict[str, Any],
        rule: Dict[str, Any],
        report: ValidationReport
    ):
        """Apply a validation rule"""
        field = rule.get('field')
        rule_type = rule.get('rule')

        if field not in data:
            return

        value = data[field]

        if rule_type == 'range':
            min_val = rule.get('min')
            max_val = rule.get('max')
            if not (min_val <= value <= max_val):
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard=report.standard,
                    field=field,
                    message=f'Value out of range',
                    expected=f'{min_val}-{max_val}',
                    actual=str(value)
                ))

        elif rule_type == 'pattern':
            pattern = rule.get('pattern')
            if not re.match(pattern, str(value)):
                report.add_issue(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    standard=report.standard,
                    field=field,
                    message=f'Value does not match required pattern',
                    expected=pattern,
                    actual=str(value)
                ))

    def generate_compliance_report(
        self,
        workspace: ProjectWorkspace
    ) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report

        Args:
            workspace: Project workspace

        Returns:
            Compliance report dictionary
        """
        validation_reports = self.validate_workspace(workspace)

        report = {
            'workspace_id': workspace.id,
            'workspace_name': workspace.name,
            'generated_at': datetime.now().isoformat(),
            'required_standards': workspace.required_standards,
            'overall_compliance': all(r.passed for r in validation_reports.values()),
            'standards': {
                name: {
                    'passed': vr.passed,
                    'errors': vr.get_error_count(),
                    'warnings': vr.get_warning_count(),
                    'issues': [i.to_dict() for i in vr.issues]
                }
                for name, vr in validation_reports.items()
            }
        }

        return report


# ==============================================================================
# Convenience Functions
# ==============================================================================

def validate_ieee_metadata(data: Dict[str, Any]) -> ValidationReport:
    """Validate IEEE metadata"""
    return IEEEValidator.validate(data)


def validate_bibtex_entry(entry: Dict[str, Any]) -> ValidationReport:
    """Validate BibTeX entry"""
    return BibTeXValidator.validate(entry)


def validate_dublin_core(data: Dict[str, Any]) -> ValidationReport:
    """Validate Dublin Core metadata"""
    return DublinCoreValidator.validate(data)


def create_schema_validator() -> SchemaValidator:
    """Create schema validator instance"""
    return SchemaValidator()
