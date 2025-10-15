# HANA DB Reporting System
# Comprehensive reporting system for SAP HANA database integration

__version__ = "1.0.0"
__author__ = "Khanal Tech Integrations"

from .hana_query_engine_readonly import HANAReadOnlyQueryEngine, generate_comprehensive_sales_report_readonly
from .excel_report_generator import ExcelReportGenerator, create_comprehensive_sales_report
from .pivot_table_creator import HANAPivotTableCreator, create_comprehensive_pivot_analysis
from .data_comparison_engine import DataComparisonEngine, compare_sales_data
from .query_templates import QUERY_TEMPLATES, get_comprehensive_sales_query
from .configuration import HANA_CONFIG, REPORT_SETTINGS

# Optional import for report scheduler
try:
    from .report_scheduler import HANAReportScheduler
except ImportError:
    HANAReportScheduler = None

__all__ = [
    'HANAReadOnlyQueryEngine',
    'generate_comprehensive_sales_report_readonly',
    'ExcelReportGenerator',
    'create_comprehensive_sales_report', 
    'HANAPivotTableCreator',
    'create_comprehensive_pivot_analysis',
    'DataComparisonEngine',
    'compare_sales_data',
    'HANAReportScheduler',
    'QUERY_TEMPLATES',
    'get_comprehensive_sales_query',
    'HANA_CONFIG',
    'REPORT_SETTINGS'
]
