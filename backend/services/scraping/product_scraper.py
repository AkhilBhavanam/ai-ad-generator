import asyncio
import re
import logging
import os
import aiohttp
import aiofiles
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse, urljoin
from datetime import datetime

from playwright.async_api import async_playwright, Browser, Page, Playwright

from backend.core.models import ProductData

logger = logging.getLogger(__name__)

class ProductScraper:
    """Scrapes product information from various e-commerce platforms"""
    
    def __init__(self, debug=False):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.debug = debug
        self.temp_dir = "temp_assets"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.supported_platforms = {
            'amazon': self._scrape_amazon,
            'shopify': self._scrape_shopify,
            'etsy': self._scrape_etsy,
            'ebay': self._scrape_ebay,
            'generic': self._scrape_generic
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            return self
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        try:
            if self.browser:
                await self.browser.close()
        except Exception as e:
            logger.debug(f"Error closing browser: {str(e)}")
        
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.debug(f"Error stopping playwright: {str(e)}")
    
    def _detect_platform(self, url: str) -> str:
        """Detect e-commerce platform from URL"""
        domain = urlparse(url).netloc.lower()
        
        if 'amazon' in domain:
            return 'amazon'
        elif 'shopify' in domain or 'myshopify' in domain:
            return 'shopify'
        elif 'etsy' in domain:
            return 'etsy'
        elif 'ebay' in domain:
            return 'ebay'
        else:
            return 'generic'
    
    async def scrape_product(self, url: str, session_id: str) -> Optional[ProductData]:
        """Scrape product data from URL"""
        try:
            platform = self._detect_platform(url)
            logger.info(f"Detected platform: {platform} for URL: {url}")
            
            if platform not in self.supported_platforms:
                logger.warning(f"Unsupported platform: {platform}, using generic scraper")
                platform = 'generic'
            
            # Create browser page
            page = await self.browser.new_page()
            
            # Set user agent to avoid detection
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Navigate to URL
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for page to load
            await page.wait_for_timeout(2000)
            
            # Scrape based on platform
            scraper_func = self.supported_platforms[platform]
            product_data = await scraper_func(page, url, session_id)
            
            await page.close()
            
            if product_data:
                logger.info(f"Successfully scraped product: {product_data.title}")
                return product_data
            else:
                logger.warning(f"Failed to scrape product data from: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping product: {str(e)}")
            return None
    
    async def _scrape_amazon(self, page: Page, url: str, session_id: str) -> Optional[ProductData]:
        """Scrape Amazon product page"""
        try:
            # Wait for product title
            await page.wait_for_selector('#productTitle', timeout=10000)
            
            # Extract product data
            title = await page.locator('#productTitle').text_content()
            title = title.strip() if title else "Unknown Product"
            
            # Price
            price = None
            price_selectors = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '#priceblock_ourprice',
                '#priceblock_dealprice'
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = page.locator(selector).first
                    if await price_elem.count() > 0:
                        price = await price_elem.text_content()
                        break
                except:
                    continue
            
            # Description
            description = None
            desc_selectors = [
                '#productDescription p',
                '#feature-bullets ul li',
                '.a-expander-content p'
            ]
            
            for selector in desc_selectors:
                try:
                    desc_elem = page.locator(selector).first
                    if await desc_elem.count() > 0:
                        description = await desc_elem.text_content()
                        break
                except:
                    continue
            
            # Rating
            rating = None
            try:
                rating_elem = page.locator('.a-icon-alt').first
                if await rating_elem.count() > 0:
                    rating_text = await rating_elem.text_content()
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        rating = rating_match.group(1)
            except:
                pass
            
            # Review count
            review_count = None
            try:
                review_elem = page.locator('#acrCustomerReviewText').first
                if await review_elem.count() > 0:
                    review_text = await review_elem.text_content()
                    review_match = re.search(r'(\d+)', review_text)
                    if review_match:
                        review_count = review_match.group(1)
            except:
                pass
            
            # Brand
            brand = None
            try:
                brand_elem = page.locator('#bylineInfo').first
                if await brand_elem.count() > 0:
                    brand = await brand_elem.text_content()
                    brand = brand.replace('Brand: ', '').strip()
            except:
                pass
            
            # Key features
            features = []
            try:
                feature_elems = page.locator('#feature-bullets ul li span')
                for i in range(min(await feature_elems.count(), 5)):
                    feature = await feature_elems.nth(i).text_content()
                    if feature and len(feature.strip()) > 10:
                        features.append(feature.strip())
            except:
                pass
            
            # Primary image and additional images
            image_urls = []
            primary_image = None
            
            try:
                # Get primary image
                img_elem = page.locator('#landingImage').first
                if await img_elem.count() > 0:
                    primary_image = await img_elem.get_attribute('src')
                    if primary_image:
                        image_urls.append(primary_image)
                
                # Get additional images from image gallery
                gallery_imgs = page.locator('#altImages .imageThumbnail img')
                for i in range(min(await gallery_imgs.count(), 8)):  # Get up to 8 additional images
                    img_src = await gallery_imgs.nth(i).get_attribute('src')
                    if img_src and img_src not in image_urls:
                        image_urls.append(img_src)
                
                # Also try other image selectors for Amazon
                alt_selectors = [
                    '#imageBlock img',
                    '.imgTagWrapper img',
                    '.a-dynamic-image',
                    '.a-image-container img'
                ]
                
                for selector in alt_selectors:
                    if len(image_urls) >= 10:  # Stop if we have enough images
                        break
                    try:
                        imgs = page.locator(selector)
                        for i in range(min(await imgs.count(), 5)):
                            if len(image_urls) >= 10:
                                break
                            img_src = await imgs.nth(i).get_attribute('src')
                            if img_src and img_src not in image_urls and img_src.startswith('http'):
                                image_urls.append(img_src)
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Error extracting images: {str(e)}")
            
            # Download images (ensure at least 5 if available)
            downloaded_images = []
            if image_urls:
                # Take up to 10 images, but ensure we get at least 5 if available
                images_to_download = image_urls[:10] if len(image_urls) >= 5 else image_urls
                downloaded_images = await self._download_product_images(images_to_download, session_id)
            
            logger.info(f"Image collected {len(image_urls)} image URLs, downloaded {len(downloaded_images)} images")
            
            return ProductData(
                title=title,
                description=description,
                price=price,
                brand=brand,
                rating=rating,
                review_count=review_count,
                primary_image=primary_image,
                downloaded_images=downloaded_images,
                key_features=features,
                url=url
            )
            
        except Exception as e:
            logger.error(f"Error scraping Amazon: {str(e)}")
            return None
    
    async def _scrape_shopify(self, page: Page, url: str, session_id: str) -> Optional[ProductData]:
        """Scrape Shopify product page"""
        try:
            # Wait for product title
            await page.wait_for_selector('h1', timeout=10000)
            
            # Title
            title = await page.locator('h1').text_content()
            title = title.strip() if title else "Unknown Product"
            
            # Price
            price = None
            try:
                price_elem = page.locator('.price').first
                if await price_elem.count() > 0:
                    price = await price_elem.text_content()
            except:
                pass
            
            # Description
            description = None
            try:
                desc_elem = page.locator('.product-description').first
                if await desc_elem.count() > 0:
                    description = await desc_elem.text_content()
            except:
                pass
            
            # Brand
            brand = None
            try:
                brand_elem = page.locator('.vendor').first
                if await brand_elem.count() > 0:
                    brand = await brand_elem.text_content()
            except:
                pass
            
            # Features
            features = []
            try:
                feature_elems = page.locator('.product-features li')
                for i in range(min(await feature_elems.count(), 5)):
                    feature = await feature_elems.nth(i).text_content()
                    if feature:
                        features.append(feature.strip())
            except:
                pass
            
            # Primary image and additional images
            image_urls = []
            primary_image = None
            
            try:
                # Get primary image
                img_elem = page.locator('.product-image img').first
                if await img_elem.count() > 0:
                    primary_image = await img_elem.get_attribute('src')
                    if primary_image:
                        image_urls.append(primary_image)
                
                # Get additional images from gallery
                gallery_imgs = page.locator('.product-gallery img')
                for i in range(min(await gallery_imgs.count(), 8)):
                    img_src = await gallery_imgs.nth(i).get_attribute('src')
                    if img_src and img_src not in image_urls:
                        image_urls.append(img_src)
                
                # Try other Shopify image selectors
                alt_selectors = [
                    '.product__media img',
                    '.product-single__media img',
                    '.product__photo img',
                    '.product-single__photo img',
                    '.product__image img'
                ]
                
                for selector in alt_selectors:
                    if len(image_urls) >= 10:
                        break
                    try:
                        imgs = page.locator(selector)
                        for i in range(min(await imgs.count(), 5)):
                            if len(image_urls) >= 10:
                                break
                            img_src = await imgs.nth(i).get_attribute('src')
                            if img_src and img_src not in image_urls and img_src.startswith('http'):
                                image_urls.append(img_src)
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Error extracting images: {str(e)}")
            
            # Download images (ensure at least 5 if available)
            downloaded_images = []
            if image_urls:
                images_to_download = image_urls[:10] if len(image_urls) >= 5 else image_urls
                downloaded_images = await self._download_product_images(images_to_download, session_id)
            
            logger.info(f"Image collected {len(image_urls)} image URLs, downloaded {len(downloaded_images)} images")
            
            return ProductData(
                title=title,
                description=description,
                price=price,
                brand=brand,
                primary_image=primary_image,
                downloaded_images=downloaded_images,
                key_features=features,
                url=url
            )
            
        except Exception as e:
            logger.error(f"Error scraping Shopify: {str(e)}")
            return None
    
    async def _scrape_etsy(self, page: Page, url: str, session_id: str) -> Optional[ProductData]:
        """Scrape Etsy product page"""
        try:
            # Wait for product title
            await page.wait_for_selector('h1', timeout=10000)
            
            # Title
            title = await page.locator('h1').text_content()
            title = title.strip() if title else "Unknown Product"
            
            # Price
            price = None
            try:
                price_elem = page.locator('.currency-value').first
                if await price_elem.count() > 0:
                    price = await price_elem.text_content()
            except:
                pass
            
            # Description
            description = None
            try:
                desc_elem = page.locator('.product-details-content').first
                if await desc_elem.count() > 0:
                    description = await desc_elem.text_content()
            except:
                pass
            
            # Shop name (as brand)
            brand = None
            try:
                brand_elem = page.locator('.shop-name').first
                if await brand_elem.count() > 0:
                    brand = await brand_elem.text_content()
            except:
                pass
            
            # Features
            features = []
            try:
                feature_elems = page.locator('.product-details-content li')
                for i in range(min(await feature_elems.count(), 5)):
                    feature = await feature_elems.nth(i).text_content()
                    if feature:
                        features.append(feature.strip())
            except:
                pass
            
            # Primary image and additional images
            image_urls = []
            primary_image = None
            
            try:
                # Get primary image
                img_elem = page.locator('.listing-page-image img').first
                if await img_elem.count() > 0:
                    primary_image = await img_elem.get_attribute('src')
                    if primary_image:
                        image_urls.append(primary_image)
                
                # Get additional images from gallery
                gallery_imgs = page.locator('.image-carousel img')
                for i in range(min(await gallery_imgs.count(), 8)):
                    img_src = await gallery_imgs.nth(i).get_attribute('src')
                    if img_src and img_src not in image_urls:
                        image_urls.append(img_src)
                
                # Try other Etsy image selectors
                alt_selectors = [
                    '.listing-page-image-carousel img',
                    '.listing-page-image-container img',
                    '.listing-page-image-wrapper img',
                    '.listing-page-image img',
                    '.listing-page-image-carousel-container img'
                ]
                
                for selector in alt_selectors:
                    if len(image_urls) >= 10:
                        break
                    try:
                        imgs = page.locator(selector)
                        for i in range(min(await imgs.count(), 5)):
                            if len(image_urls) >= 10:
                                break
                            img_src = await imgs.nth(i).get_attribute('src')
                            if img_src and img_src not in image_urls and img_src.startswith('http'):
                                image_urls.append(img_src)
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Error extracting images: {str(e)}")
            
            # Download images (ensure at least 5 if available)
            downloaded_images = []
            if image_urls:
                images_to_download = image_urls[:10] if len(image_urls) >= 5 else image_urls
                downloaded_images = await self._download_product_images(images_to_download, session_id)
            
            logger.info(f"Image collected {len(image_urls)} image URLs, downloaded {len(downloaded_images)} images")
            
            return ProductData(
                title=title,
                description=description,
                price=price,
                brand=brand,
                primary_image=primary_image,
                downloaded_images=downloaded_images,
                key_features=features,
                url=url
            )
            
        except Exception as e:
            logger.error(f"Error scraping Etsy: {str(e)}")
            return None
    
    async def _scrape_ebay(self, page: Page, url: str, session_id: str) -> Optional[ProductData]:
        """Scrape eBay product page"""
        try:
            # Wait for product title
            await page.wait_for_selector('h1', timeout=10000)
            
            # Title
            title = await page.locator('h1').text_content()
            title = title.strip() if title else "Unknown Product"
            
            # Price
            price = None
            try:
                price_elem = page.locator('.x-price-primary').first
                if await price_elem.count() > 0:
                    price = await price_elem.text_content()
            except:
                pass
            
            # Description
            description = None
            try:
                desc_elem = page.locator('.item-description').first
                if await desc_elem.count() > 0:
                    description = await desc_elem.text_content()
            except:
                pass
            
            # Brand
            brand = None
            try:
                brand_elem = page.locator('.itemAttr').first
                if await brand_elem.count() > 0:
                    brand = await brand_elem.text_content()
            except:
                pass
            
            # Comprehensive image extraction using ux-image-carousel-item
            image_urls = []
            primary_image = None
            
            try:
                # Method 1: Get all ux-image-carousel-item elements and extract images
                carousel_items = page.locator('.ux-image-carousel-item')
                carousel_count = await carousel_items.count()
                logger.info(f"Found {carousel_count} carousel items")
                
                for i in range(carousel_count):
                    if len(image_urls) >= 10:  # Reduced limit to 10
                        break
                    
                    carousel_item = carousel_items.nth(i)
                    
                    # Get main image from carousel item
                    try:
                        img_elem = carousel_item.locator('img').first
                        if await img_elem.count() > 0:
                            img_src = await img_elem.get_attribute('src')
                            if img_src and img_src not in image_urls and img_src.startswith('http'):
                                image_urls.append(img_src)
                                if not primary_image:
                                    primary_image = img_src
                    except:
                        pass
                    
                    # Get data-src attribute (lazy loaded images)
                    try:
                        img_elem = carousel_item.locator('img').first
                        if await img_elem.count() > 0:
                            data_src = await img_elem.get_attribute('data-src')
                            if data_src and data_src not in image_urls and data_src.startswith('http'):
                                image_urls.append(data_src)
                    except:
                        pass
                
                # Method 2: Get thumbnail images (only if we need more)
                if len(image_urls) < 10:
                    thumbnail_selectors = [
                        '.ux-image-carousel-thumbnail img',
                        '.ux-image-carousel-thumbnails img',
                        '.ux-image-carousel-thumbnail-item img',
                        '.ux-image-carousel-thumbnail-wrapper img'
                    ]
                    
                    for selector in thumbnail_selectors:
                        if len(image_urls) >= 10:
                            break
                        try:
                            thumbnails = page.locator(selector)
                            for i in range(min(await thumbnails.count(), 5)):
                                if len(image_urls) >= 10:
                                    break
                                img_src = await thumbnails.nth(i).get_attribute('src')
                                data_src = await thumbnails.nth(i).get_attribute('data-src')
                                
                                for src in [img_src, data_src]:
                                    if src and src not in image_urls and src.startswith('http'):
                                        image_urls.append(src)
                        except:
                            continue
                
                # Method 3: Get images from carousel container (only if we need more)
                if len(image_urls) < 10:
                    carousel_selectors = [
                        '.ux-image-carousel img',
                        '.ux-image-carousel-container img',
                        '.ux-image-carousel-wrapper img',
                        '.ux-image-carousel-item img',
                        '.ux-image-carousel-main img'
                    ]
                    
                    for selector in carousel_selectors:
                        if len(image_urls) >= 10:
                            break
                        try:
                            imgs = page.locator(selector)
                            for i in range(min(await imgs.count(), 5)):
                                if len(image_urls) >= 10:
                                    break
                                img_src = await imgs.nth(i).get_attribute('src')
                                data_src = await imgs.nth(i).get_attribute('data-src')
                                
                                for src in [img_src, data_src]:
                                    if src and src not in image_urls and src.startswith('http'):
                                        image_urls.append(src)
                        except:
                            continue
                
                # Method 4: Look for high-resolution image URLs and prioritize them
                # eBay often has different image sizes available
                high_res_urls = []
                for img_url in image_urls:
                    # Try to get higher resolution versions
                    if 's-l64' in img_url:
                        high_res = img_url.replace('s-l64', 's-l1600')
                        high_res_urls.append(high_res)
                    elif 's-l300' in img_url:
                        high_res = img_url.replace('s-l300', 's-l1600')
                        high_res_urls.append(high_res)
                    elif 's-l500' in img_url:
                        high_res = img_url.replace('s-l500', 's-l1600')
                        high_res_urls.append(high_res)
                    elif 's-l800' in img_url:
                        high_res = img_url.replace('s-l800', 's-l1600')
                        high_res_urls.append(high_res)
                
                # Replace low-res URLs with high-res versions and limit to 10
                final_image_urls = []
                for high_res_url in high_res_urls:
                    if len(final_image_urls) >= 10:
                        break
                    if high_res_url not in final_image_urls:
                        final_image_urls.append(high_res_url)
                
                # Add remaining original URLs if we haven't reached 10
                for img_url in image_urls:
                    if len(final_image_urls) >= 10:
                        break
                    if img_url not in final_image_urls:
                        final_image_urls.append(img_url)
                
                image_urls = final_image_urls[:10]  # Ensure max 10
                        
            except Exception as e:
                logger.warning(f"Error extracting images: {str(e)}")
            
            # Download images (limit to 10 high-quality images)
            downloaded_images = []
            if image_urls:
                # Download up to 10 images
                images_to_download = image_urls[:10]
                downloaded_images = await self._download_product_images(images_to_download, session_id)
            
            logger.info(f"Image collected {len(image_urls)} image URLs, downloaded {len(downloaded_images)} images")
            
            return ProductData(
                title=title,
                description=description,
                price=price,
                brand=brand,
                primary_image=primary_image,
                downloaded_images=downloaded_images,
                key_features=[],
                url=url
            )
            
        except Exception as e:
            logger.error(f"Error scraping eBay: {str(e)}")
            return None
    
    async def _scrape_generic(self, page: Page, url: str, session_id: str) -> Optional[ProductData]:
        """Generic scraper for unknown platforms"""
        try:
            # Try to find title
            title = None
            title_selectors = ['h1', '.title', '.product-title', '.name']
            
            for selector in title_selectors:
                try:
                    title_elem = page.locator(selector).first
                    if await title_elem.count() > 0:
                        title = await title_elem.text_content()
                        break
                except:
                    continue
            
            title = title.strip() if title else "Unknown Product"
            
            # Try to find price
            price = None
            price_selectors = ['.price', '.cost', '.amount', '[class*="price"]']
            
            for selector in price_selectors:
                try:
                    price_elem = page.locator(selector).first
                    if await price_elem.count() > 0:
                        price = await price_elem.text_content()
                        break
                except:
                    continue
            
            # Try to find description
            description = None
            desc_selectors = ['.description', '.desc', '.product-desc', '[class*="desc"]']
            
            for selector in desc_selectors:
                try:
                    desc_elem = page.locator(selector).first
                    if await desc_elem.count() > 0:
                        description = await desc_elem.text_content()
                        break
                except:
                    continue
            
            # Try to find image
            primary_image = None
            try:
                img_elem = page.locator('img').first
                if await img_elem.count() > 0:
                    primary_image = await img_elem.get_attribute('src')
            except:
                pass
            
            return ProductData(
                title=title,
                description=description,
                price=price,
                primary_image=primary_image,
                key_features=[],
                url=url
            )
            
        except Exception as e:
            logger.error(f"Error in generic scraper: {str(e)}")
            return None
    
    async def _download_image(self, image_url: str, session_id: str, index: int = 0) -> Optional[str]:
        """Download image from URL and save to temp directory"""
        try:
            if not image_url:
                return None
                
            # Ensure URL is absolute
            if not image_url.startswith(('http://', 'https://')):
                return None
            
            # Generate filename
            file_extension = self._get_file_extension(image_url)
            filename = f"{session_id}_image_{index}{file_extension}"
            file_path = os.path.join(self.temp_dir, filename)
            
            logger.info(f"Image downloaded: {file_path}")
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url, timeout=30) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as f:
                            await f.write(await response.read())
                        
                        logger.info(f"✅ Image downloaded: {file_path}")
                        return file_path
                    else:
                        logger.warning(f"Failed to download image: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error downloading image {image_url}: {str(e)}")
            return None
    
    def _get_file_extension(self, url: str) -> str:
        """Extract file extension from URL"""
        try:
            # Try to get extension from URL path
            path = urlparse(url).path
            if '.' in path:
                ext = path.split('.')[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                    return f".{ext}"
            
            # Default to jpg if no valid extension found
            return ".jpg"
        except:
            return ".jpg"
    
    async def _download_product_images(self, image_urls: List[str], session_id: str) -> List[str]:
        """Download multiple product images"""
        downloaded_paths = []
        
        # Ensure we try to download at least 5 images if available
        max_images = max(5, len(image_urls))  # At least 5, or all available if less than 5
        images_to_download = image_urls[:max_images]
        
        logger.info(f"📥 Attempting to download {len(images_to_download)} images...")
        
        for i, url in enumerate(images_to_download):
            if url:
                file_path = await self._download_image(url, session_id, i)
                if file_path:
                    downloaded_paths.append(file_path)
                    logger.info(f"Downloaded image {i+1}/{len(images_to_download)}: {os.path.basename(file_path)}")
                else:
                    logger.warning(f"Failed to download image {i+1}/{len(images_to_download)}: {url}")
        
        logger.info(f"📸 Successfully downloaded {len(downloaded_paths)} out of {len(images_to_download)} images")
        return downloaded_paths 