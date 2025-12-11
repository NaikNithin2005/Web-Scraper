"""
Export System Module
Handles exporting scraped data to various formats: CSV, JSON, Excel, SQL, API.
"""

import json
import csv
import sqlite3
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from loguru import logger
import pandas as pd


class ExportSystem:
    """
    Export system for scraped data.
    Supports CSV, JSON, Excel, SQL, and API endpoints.
    """
    
    def __init__(self, output_dir: str = "exports"):
        """
        Initialize export system.
        
        Args:
            output_dir: Directory to save exported files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Export system initialized with output directory: {output_dir}")
    
    def export_to_json(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        pretty: bool = True
    ) -> str:
        """
        Export data to JSON file.
        
        Args:
            data: List of dictionaries to export
            filename: Output filename (auto-generated if None)
            pretty: Pretty-print JSON
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            else:
                json.dump(data, f, ensure_ascii=False, default=str)
        
        logger.info(f"Exported {len(data)} records to JSON: {filepath}")
        return str(filepath)
    
    def export_to_csv(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        delimiter: str = ","
    ) -> str:
        """
        Export data to CSV file.
        
        Args:
            data: List of dictionaries to export
            filename: Output filename (auto-generated if None)
            delimiter: CSV delimiter
            
        Returns:
            Path to exported file
        """
        if not data:
            raise ValueError("No data to export")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        # Get all unique keys from all records
        fieldnames = set()
        for record in data:
            fieldnames.update(record.keys())
        fieldnames = sorted(list(fieldnames))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Exported {len(data)} records to CSV: {filepath}")
        return str(filepath)
    
    def export_to_excel(
        self,
        data: List[Dict[str, Any]],
        filename: Optional[str] = None,
        sheet_name: str = "Sheet1"
    ) -> str:
        """
        Export data to Excel file.
        
        Args:
            data: List of dictionaries to export
            filename: Output filename (auto-generated if None)
            sheet_name: Excel sheet name
            
        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.xlsx"
        
        filepath = self.output_dir / filename
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Exported {len(data)} records to Excel: {filepath}")
        return str(filepath)
    
    def export_to_sql(
        self,
        data: List[Dict[str, Any]],
        db_path: str,
        table_name: str = "exported_data",
        if_exists: str = "replace"
    ) -> str:
        """
        Export data to SQLite database.
        
        Args:
            data: List of dictionaries to export
            db_path: Path to SQLite database
            table_name: Table name
            if_exists: What to do if table exists ("replace", "append", "fail")
            
        Returns:
            Database path
        """
        if not data:
            raise ValueError("No data to export")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Connect to SQLite
        conn = sqlite3.connect(db_path)
        
        try:
            # Export to SQL
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            logger.info(f"Exported {len(data)} records to SQL table '{table_name}': {db_path}")
        finally:
            conn.close()
        
        return db_path
    
    def export_to_multiple_formats(
        self,
        data: List[Dict[str, Any]],
        formats: List[str],
        base_filename: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Export data to multiple formats at once.
        
        Args:
            data: List of dictionaries to export
            formats: List of formats ("json", "csv", "excel", "sql")
            base_filename: Base filename (without extension)
            
        Returns:
            Dict mapping format to file path
        """
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"export_{timestamp}"
        
        results = {}
        
        for fmt in formats:
            try:
                if fmt == "json":
                    results["json"] = self.export_to_json(data, f"{base_filename}.json")
                elif fmt == "csv":
                    results["csv"] = self.export_to_csv(data, f"{base_filename}.csv")
                elif fmt == "excel":
                    results["excel"] = self.export_to_excel(data, f"{base_filename}.xlsx")
                elif fmt == "sql":
                    db_path = self.output_dir / f"{base_filename}.db"
                    results["sql"] = self.export_to_sql(data, str(db_path))
                else:
                    logger.warning(f"Unknown format: {fmt}")
            except Exception as e:
                logger.error(f"Failed to export to {fmt}: {e}")
        
        return results
    
    def export_products(
        self,
        products: List[Dict[str, Any]],
        format: str = "json",
        filename: Optional[str] = None
    ) -> str:
        """
        Export product data.
        
        Args:
            products: List of product dictionaries
            format: Export format ("json", "csv", "excel", "sql")
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if format == "json":
            return self.export_to_json(products, filename)
        elif format == "csv":
            return self.export_to_csv(products, filename)
        elif format == "excel":
            return self.export_to_excel(products, filename)
        elif format == "sql":
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"products_{timestamp}.db"
            return self.export_to_sql(products, str(self.output_dir / filename), "products")
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_price_history(
        self,
        price_history: List[Dict[str, Any]],
        format: str = "json",
        filename: Optional[str] = None
    ) -> str:
        """
        Export price history data.
        
        Args:
            price_history: List of price history records
            format: Export format
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if format == "json":
            return self.export_to_json(price_history, filename)
        elif format == "csv":
            return self.export_to_csv(price_history, filename)
        elif format == "excel":
            return self.export_to_excel(price_history, filename)
        elif format == "sql":
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"price_history_{timestamp}.db"
            return self.export_to_sql(price_history, str(self.output_dir / filename), "price_history")
        else:
            raise ValueError(f"Unsupported format: {format}")

