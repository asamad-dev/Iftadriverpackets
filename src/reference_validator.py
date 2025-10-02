#!/usr/bin/env python3
"""
Reference validator module
Handles validation of extracted data against reference CSV files for accuracy testing
"""

import os
import csv
from typing import Dict, List, Optional

from .logging_utils import get_logger
from .config import config


class ReferenceValidator:
    """
    Validate extracted data against reference CSV files for accuracy testing
    """
    
    def __init__(self, reference_csv_path: Optional[str] = None):
        """
        Initialize the reference validator
        
        Args:
            reference_csv_path: Path to reference CSV file (defaults to input/driver - Sheet1.csv)
        """
        self.logger = get_logger()
        
        if not reference_csv_path:
            reference_csv_path = config.DEFAULT_REFERENCE_CSV
        
        self.reference_csv_path = reference_csv_path
        self.reference_data = None
        
        # Field mapping between extracted data and reference CSV
        self.field_mapping = {
            'drivers_name': 'Driver Name',
            'unit': 'Unit',
            'trailer': 'Trailer',
            'date_trip_started': 'Date Trip Started',
            'date_trip_ended': 'Date Trip Ended',
            'trip': 'Trip',
            'trip_started_from': 'Trip Started form',  # Note: typo in CSV header
            'first_drop': '1st Drop',
            'second_drop': '2nd Drop',
            'third_drop': '3rd Drop',
            'forth_drop': '4th Drop',
            'inbound_pu': 'inbound PU',
            'drop_off': 'Drop Off',
            'total_miles': 'Total Miles'
        }
    
    def validate_against_reference(self, extracted_data: Dict) -> Dict:
        """
        Validate extracted data against reference CSV file
        
        Args:
            extracted_data: Dictionary with extracted data including source_image
            
        Returns:
            Dictionary with validation results and discrepancy warnings
        """
        validation_result = {
            'validation_success': False,
            'reference_found': False,
            'discrepancies': [],
            'accuracy_metrics': {},
            'validation_warnings': []
        }
        
        try:
            # Check if reference file exists
            if not os.path.exists(self.reference_csv_path):
                self.logger.info(f"No reference test file available (skipping validation): {os.path.basename(self.reference_csv_path)}")
                return validation_result
            
            # Load reference data
            if not self._load_reference_data():
                validation_result['validation_warnings'].append("Failed to load reference data")
                return validation_result
            
            # Find matching reference entry
            source_image = extracted_data.get('source_image', '')
            reference_entry = self._find_reference_entry(source_image)
            
            if not reference_entry:
                validation_result['validation_warnings'].append(f"No reference data found for image: {source_image}")
                return validation_result
            
            validation_result['reference_found'] = True
            
            # Compare fields and generate discrepancies
            discrepancies = self._compare_extracted_vs_reference(extracted_data, reference_entry)
            validation_result['discrepancies'] = discrepancies
            
            # Calculate accuracy metrics
            accuracy_metrics = self._calculate_accuracy_metrics(extracted_data, reference_entry, discrepancies)
            validation_result['accuracy_metrics'] = accuracy_metrics
            
            # Generate validation warnings for discrepancies
            validation_warnings = self._generate_validation_warnings(discrepancies)
            validation_result['validation_warnings'] = validation_warnings
            
            validation_result['validation_success'] = True
            
            self.logger.info(f"Validation completed for {source_image}:")
            self.logger.info(f"  Reference found: ✅")
            self.logger.info(f"  Discrepancies found: {len(discrepancies)}")
            self.logger.info(f"  Field accuracy: {accuracy_metrics.get('field_accuracy', 0):.1%}")
            
            if discrepancies:
                self.logger.warning(f"Discrepancies detected:")
                for discrepancy in discrepancies[:5]:  # Show first 5
                    self.logger.warning(f"  - {discrepancy['field']}: {discrepancy['extracted']} ≠ {discrepancy['reference']}")
                if len(discrepancies) > 5:
                    self.logger.warning(f"  ... and {len(discrepancies) - 5} more")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            validation_result['validation_warnings'].append(f"Validation error: {str(e)}")
            return validation_result
    
    def _load_reference_data(self) -> bool:
        """Load reference data from CSV file"""
        try:
            self.reference_data = []
            with open(self.reference_csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.reference_data.append(row)
            
            self.logger.info(f"Loaded {len(self.reference_data)} reference entries from CSV")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading reference CSV: {e}")
            return False
    
    def _find_reference_entry(self, source_image: str) -> Optional[Dict]:
        """Find matching reference entry for the source image"""
        if not self.reference_data:
            return None
        
        # Try exact match first
        for entry in self.reference_data:
            if entry.get('Image Name', '').strip() == source_image:
                return entry
        
        # Try partial match (remove extension)
        image_name_base = source_image.replace('.jpg', '').replace('.jpeg', '').replace('.png', '')
        for entry in self.reference_data:
            ref_name = entry.get('Image Name', '').strip()
            if ref_name == image_name_base:
                return entry
        
        # Try contains match
        for entry in self.reference_data:
            ref_name = entry.get('Image Name', '').strip()
            if image_name_base in ref_name or ref_name in image_name_base:
                return entry
        
        return None
    
    def _compare_extracted_vs_reference(self, extracted_data: Dict, reference_entry: Dict) -> List[Dict]:
        """Compare extracted data with reference data and return discrepancies"""
        discrepancies = []
        
        for extracted_field, reference_field in self.field_mapping.items():
            extracted_value = self._normalize_field_value(extracted_data.get(extracted_field, ''))
            reference_value = self._normalize_field_value(reference_entry.get(reference_field, ''))
            
            # Special handling for drop_off arrays
            if extracted_field == 'drop_off' and isinstance(extracted_data.get('drop_off'), list):
                # Check if reference has multiple drop offs
                drop_off_fields = ['Drop Off', 'Drop Off 2', 'Drop Off 3']
                reference_drop_offs = []
                for drop_field in drop_off_fields:
                    drop_value = self._normalize_field_value(reference_entry.get(drop_field, ''))
                    if drop_value:
                        reference_drop_offs.append(drop_value)
                
                # Compare arrays
                extracted_drop_offs = [self._normalize_field_value(v) for v in extracted_data.get('drop_off', [])]
                if set(extracted_drop_offs) != set(reference_drop_offs):
                    discrepancies.append({
                        'field': extracted_field,
                        'extracted': extracted_drop_offs,
                        'reference': reference_drop_offs,
                        'severity': 'high',
                        'type': 'array_mismatch'
                    })
                continue
            
            # Compare normalized values
            if extracted_value != reference_value:
                severity = self._determine_discrepancy_severity(extracted_field, extracted_value, reference_value)
                discrepancies.append({
                    'field': extracted_field,
                    'extracted': extracted_value,
                    'reference': reference_value,
                    'severity': severity,
                    'type': 'value_mismatch'
                })
        
        return discrepancies
    
    def _normalize_field_value(self, value) -> str:
        """Normalize field value for comparison"""
        if value is None:
            return ''
        
        # Convert to string and normalize
        value_str = str(value).strip()
        
        # Remove extra spaces
        value_str = ' '.join(value_str.split())
        
        # Normalize common variations
        value_str = value_str.replace('  ', ' ')
        
        return value_str
    
    def _determine_discrepancy_severity(self, field: str, extracted: str, reference: str) -> str:
        """Determine severity of discrepancy"""
        # Critical fields that must match exactly
        critical_fields = ['drivers_name', 'unit', 'trailer', 'total_miles']
        
        # High importance fields
        high_importance_fields = ['date_trip_started', 'date_trip_ended', 'trip_started_from', 'inbound_pu', 'drop_off']
        
        # Check if it's just a minor formatting difference
        if self._is_minor_formatting_difference(extracted, reference):
            return 'low'
        
        if field in critical_fields:
            return 'critical'
        elif field in high_importance_fields:
            return 'high'
        else:
            return 'medium'
    
    def _is_minor_formatting_difference(self, extracted: str, reference: str) -> bool:
        """Check if difference is just minor formatting"""
        # Remove common formatting differences
        extracted_clean = extracted.lower().replace('.', '').replace('-', '/').replace(' ', '')
        reference_clean = reference.lower().replace('.', '').replace('-', '/').replace(' ', '')
        
        return extracted_clean == reference_clean
    
    def _calculate_accuracy_metrics(self, extracted_data: Dict, reference_entry: Dict, discrepancies: List[Dict]) -> Dict:
        """Calculate accuracy metrics"""
        total_fields = len(self.field_mapping)
        matching_fields = total_fields - len(discrepancies)
        
        # Calculate accuracy by severity
        critical_discrepancies = sum(1 for d in discrepancies if d['severity'] == 'critical')
        high_discrepancies = sum(1 for d in discrepancies if d['severity'] == 'high')
        medium_discrepancies = sum(1 for d in discrepancies if d['severity'] == 'medium')
        low_discrepancies = sum(1 for d in discrepancies if d['severity'] == 'low')
        
        return {
            'field_accuracy': matching_fields / total_fields,
            'total_fields': total_fields,
            'matching_fields': matching_fields,
            'total_discrepancies': len(discrepancies),
            'critical_discrepancies': critical_discrepancies,
            'high_discrepancies': high_discrepancies,
            'medium_discrepancies': medium_discrepancies,
            'low_discrepancies': low_discrepancies
        }
    
    def _generate_validation_warnings(self, discrepancies: List[Dict]) -> List[str]:
        """Generate validation warnings based on discrepancies"""
        warnings = []
        
        for discrepancy in discrepancies:
            field = discrepancy['field']
            extracted = discrepancy['extracted']
            reference = discrepancy['reference']
            severity = discrepancy['severity']
            
            if severity == 'critical':
                warnings.append(f"🔴 CRITICAL: {field} mismatch - extracted: '{extracted}' ≠ reference: '{reference}'")
            elif severity == 'high':
                warnings.append(f"🟠 HIGH: {field} mismatch - extracted: '{extracted}' ≠ reference: '{reference}'")
            elif severity == 'medium':
                warnings.append(f"🟡 MEDIUM: {field} mismatch - extracted: '{extracted}' ≠ reference: '{reference}'")
            else:
                warnings.append(f"🔵 LOW: {field} formatting difference - extracted: '{extracted}' ≠ reference: '{reference}'")
        
        return warnings
    
    def generate_accuracy_report(self, validation_results: List[Dict]) -> Dict:
        """
        Generate accuracy report from multiple validation results
        
        Args:
            validation_results: List of validation result dictionaries
            
        Returns:
            Dictionary with overall accuracy metrics and summary
        """
        report = {
            'total_images': len(validation_results),
            'successfully_validated': 0,
            'reference_matches_found': 0,
            'overall_field_accuracy': 0,
            'severity_breakdown': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'field_accuracy_by_field': {},
            'common_issues': []
        }
        
        # Initialize field accuracy tracking
        for field in self.field_mapping.keys():
            report['field_accuracy_by_field'][field] = {'correct': 0, 'total': 0}
        
        total_fields_checked = 0
        total_fields_correct = 0
        
        for result in validation_results:
            if result.get('validation_success'):
                report['successfully_validated'] += 1
                
                if result.get('reference_found'):
                    report['reference_matches_found'] += 1
                    
                    # Process accuracy metrics
                    metrics = result.get('accuracy_metrics', {})
                    if metrics:
                        total_fields_checked += metrics.get('total_fields', 0)
                        total_fields_correct += metrics.get('matching_fields', 0)
                        
                        # Count severity breakdown
                        report['severity_breakdown']['critical'] += metrics.get('critical_discrepancies', 0)
                        report['severity_breakdown']['high'] += metrics.get('high_discrepancies', 0)
                        report['severity_breakdown']['medium'] += metrics.get('medium_discrepancies', 0)
                        report['severity_breakdown']['low'] += metrics.get('low_discrepancies', 0)
                    
                    # Track field-specific accuracy
                    discrepancies = result.get('discrepancies', [])
                    discrepant_fields = {d['field'] for d in discrepancies}
                    
                    for field in self.field_mapping.keys():
                        report['field_accuracy_by_field'][field]['total'] += 1
                        if field not in discrepant_fields:
                            report['field_accuracy_by_field'][field]['correct'] += 1
        
        # Calculate overall accuracy
        if total_fields_checked > 0:
            report['overall_field_accuracy'] = total_fields_correct / total_fields_checked
        
        # Calculate field-specific accuracy percentages
        for field, stats in report['field_accuracy_by_field'].items():
            if stats['total'] > 0:
                stats['accuracy'] = stats['correct'] / stats['total']
            else:
                stats['accuracy'] = 0
        
        # Identify common issues (fields with low accuracy)
        for field, stats in report['field_accuracy_by_field'].items():
            if stats['total'] > 0 and stats['accuracy'] < 0.8:  # Less than 80% accuracy
                report['common_issues'].append({
                    'field': field,
                    'accuracy': stats['accuracy'],
                    'total_checked': stats['total'],
                    'correct': stats['correct']
                })
        
        # Sort common issues by accuracy (worst first)
        report['common_issues'].sort(key=lambda x: x['accuracy'])
        
        self.logger.info(f"Accuracy Report Generated:")
        self.logger.info(f"  Total images: {report['total_images']}")
        self.logger.info(f"  Successfully validated: {report['successfully_validated']}")
        self.logger.info(f"  Reference matches: {report['reference_matches_found']}")
        self.logger.info(f"  Overall field accuracy: {report['overall_field_accuracy']:.1%}")
        
        if report['common_issues']:
            self.logger.warning(f"  Fields with low accuracy:")
            for issue in report['common_issues'][:5]:  # Show top 5 issues
                self.logger.warning(f"    {issue['field']}: {issue['accuracy']:.1%} ({issue['correct']}/{issue['total_checked']})")
        
        return report
