"""
FastAPI REST API Endpoints
Provides API access to the scraper functionality.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
from loguru import logger

# Import core modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.scraper import UniversalScraper
from core.parser import DOMParser
from core.comparator import ProductComparator
from core.price_tracker import PriceTracker
from core.export import ExportSystem
from core.plugins import PluginManager
from ai.ai_service import AIService
from database.db import Database

app = FastAPI(
    title="AI-Driven Universal Web Scraper API",
    description="REST API for the universal web scraper with AI integration",
    version="1.0.0"
)

# Initialize components
db = Database()
scraper = UniversalScraper(use_browser=True)
parser = DOMParser("")
comparator = ProductComparator()
price_tracker = PriceTracker(db)
export_system = ExportSystem()
plugin_manager = PluginManager()
ai_service = AIService()

# Load plugins
plugin_manager.load_plugins_from_directory()

# Register default extractors
from core.plugins import AmazonExtractor, FlipkartExtractor
plugin_manager.register_extractor(AmazonExtractor())
plugin_manager.register_extractor(FlipkartExtractor())


# Request/Response Models
class ScrapeRequest(BaseModel):
    url: HttpUrl
    method: Optional[str] = "auto"
    use_ai: Optional[bool] = False
    extract_schema: Optional[Dict[str, Any]] = None


class MultiScrapeRequest(BaseModel):
    urls: List[HttpUrl]
    method: Optional[str] = "auto"
    compare: Optional[bool] = False


class PriceTrackRequest(BaseModel):
    url: HttpUrl
    schedule: Optional[str] = "daily"  # hourly, daily, weekly
    alert_threshold: Optional[float] = None


class ExportRequest(BaseModel):
    data_type: str  # "products", "price_history", "scrape_jobs"
    format: str  # "json", "csv", "excel", "sql"
    filters: Optional[Dict[str, Any]] = None


# API Endpoints

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "AI-Driven Universal Web Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "scrape": "/api/v1/scrape",
            "multi_scrape": "/api/v1/multi-scrape",
            "compare": "/api/v1/compare",
            "track_price": "/api/v1/track-price",
            "export": "/api/v1/export",
            "health": "/api/v1/health"
        }
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db.conn else "disconnected"
    }


@app.post("/api/v1/scrape")
async def scrape_url(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Scrape a single URL.
    
    Args:
        request: Scrape request with URL and options
        
    Returns:
        Scraped data
    """
    try:
        url = str(request.url)
        logger.info(f"Scraping URL: {url}")
        
        # Check for custom extractor
        extractor = plugin_manager.get_extractor_for_url(url)
        
        # Scrape the page
        result = scraper.scrape(url, method=request.method)
        
        # Parse HTML
        parser.soup = None  # Reset parser
        parser.html = result["html"]
        from bs4 import BeautifulSoup
        parser.soup = BeautifulSoup(result["html"], "html.parser")
        
        # Use custom extractor if available
        if extractor:
            data = extractor.extract(result["html"], url)
        else:
            # Generic extraction
            data = {
                "url": url,
                "title": parser.extract_text("title", clean=True),
                "text": parser.get_body_text(),
                "meta": parser.extract_meta_tags(),
                "links": parser.extract_links(url),
                "images": parser.extract_images(url)
            }
        
        # AI processing if requested
        if request.use_ai:
            if request.extract_schema:
                data["ai_extracted"] = ai_service.extract_data(
                    parser.get_body_text(),
                    request.extract_schema
                )
            else:
                data["ai_summary"] = ai_service.summarize_content(parser.get_body_text())
        
        # Store in database
        job_id = db.create_scrape_job(url, request.method)
        db.update_scrape_job(job_id, "completed", data)
        
        return {
            "success": True,
            "data": data,
            "method_used": result.get("method_used"),
            "job_id": job_id
        }
    
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/multi-scrape")
async def multi_scrape(request: MultiScrapeRequest):
    """
    Scrape multiple URLs.
    
    Args:
        request: Multi-scrape request with list of URLs
        
    Returns:
        List of scraped data
    """
    results = []
    
    for url in request.urls:
        try:
            url_str = str(url)
            result = scraper.scrape(url_str, method=request.method)
            
            parser.soup = None
            parser.html = result["html"]
            from bs4 import BeautifulSoup
            parser.soup = BeautifulSoup(result["html"], "html.parser")
            
            extractor = plugin_manager.get_extractor_for_url(url_str)
            if extractor:
                data = extractor.extract(result["html"], url_str)
            else:
                data = {
                    "url": url_str,
                    "title": parser.extract_text("title", clean=True),
                    "text": parser.get_body_text()
                }
            
            results.append(data)
        
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            results.append({
                "url": str(url),
                "error": str(e)
            })
    
    # Compare if requested
    if request.compare and len(results) > 1:
        comparison = comparator.compare_products(results)
        return {
            "success": True,
            "results": results,
            "comparison": comparison
        }
    
    return {
        "success": True,
        "results": results
    }


@app.post("/api/v1/compare")
async def compare_products(products: List[Dict[str, Any]]):
    """
    Compare multiple products.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        Comparison report
    """
    try:
        comparison = comparator.compare_products(products)
        best_value = comparator.find_best_value(products)
        
        return {
            "success": True,
            "comparison": comparison,
            "best_value": best_value
        }
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/track-price")
async def track_price(request: PriceTrackRequest):
    """
    Start tracking a product's price.
    
    Args:
        request: Price tracking request
        
    Returns:
        Tracking information
    """
    try:
        url = str(request.url)
        
        # Scrape initial product data
        result = scraper.scrape(url)
        parser.soup = None
        parser.html = result["html"]
        from bs4 import BeautifulSoup
        parser.soup = BeautifulSoup(result["html"], "html.parser")
        
        extractor = plugin_manager.get_extractor_for_url(url)
        if extractor:
            product_data = extractor.extract(result["html"], url)
        else:
            product_data = {
                "url": url,
                "title": parser.extract_text("title", clean=True)
            }
        
        product_data["url"] = url
        product_id = price_tracker.track_product(product_data)
        
        # Set alert if threshold provided
        if request.alert_threshold:
            price_tracker.set_alert(product_id, "drop", request.alert_threshold)
        
        return {
            "success": True,
            "product_id": product_id,
            "message": f"Price tracking started for product {product_id}"
        }
    
    except Exception as e:
        logger.error(f"Price tracking setup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/price-history/{product_id}")
async def get_price_history(product_id: int, days: Optional[int] = None):
    """
    Get price history for a product.
    
    Args:
        product_id: Product ID
        days: Number of days to look back
        
    Returns:
        Price history data
    """
    try:
        history = price_tracker.get_price_history(product_id, days)
        trend = price_tracker.get_price_trend(product_id, days or 30)
        
        return {
            "success": True,
            "product_id": product_id,
            "history": history,
            "trend": trend
        }
    except Exception as e:
        logger.error(f"Failed to get price history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/export")
async def export_data(request: ExportRequest):
    """
    Export data in various formats.
    
    Args:
        request: Export request with data type and format
        
    Returns:
        Export file information
    """
    try:
        # Get data from database
        if request.data_type == "products":
            data = db.get_all_products()
        elif request.data_type == "price_history":
            # This would need product_id in request
            raise HTTPException(status_code=400, detail="product_id required for price_history export")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown data type: {request.data_type}")
        
        # Export
        if request.format == "json":
            filepath = export_system.export_to_json(data)
        elif request.format == "csv":
            filepath = export_system.export_to_csv(data)
        elif request.format == "excel":
            filepath = export_system.export_to_excel(data)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")
        
        return FileResponse(
            filepath,
            media_type="application/octet-stream",
            filename=Path(filepath).name
        )
    
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/plugins")
async def list_plugins():
    """List all available plugins."""
    return {
        "extractors": plugin_manager.list_extractors(),
        "templates": plugin_manager.list_templates()
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

