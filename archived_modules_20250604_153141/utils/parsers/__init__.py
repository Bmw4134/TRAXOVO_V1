"""
Parsers Module

This module contains parsers for different file formats.
"""

from .excel_parser import ExcelParser

# Define custom exceptions
class ParserException(Exception):
    """Base exception for parser errors"""
    pass

class ExcelParserException(ParserException):
    """Exception raised for Excel parser errors"""
    pass

class CSVParserException(ParserException):
    """Exception raised for CSV parser errors"""
    pass

class JSONParserException(ParserException):
    """Exception raised for JSON parser errors"""
    pass

class PDFParserException(ParserException):
    """Exception raised for PDF parser errors"""
    pass