import cloudinary
import cloudinary.uploader
from flask import current_app
from PIL import Image
import io

def configure_cloudinary():
    """Configure Cloudinary with credentials from config."""
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET']
    )

def resize_image(image_file, max_size=(800, 800)):
    """Resize image while maintaining aspect ratio."""
    img = Image.open(image_file)
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # Calculate new dimensions
    width, height = img.size
    if width > max_size[0] or height > max_size[1]:
        ratio = min(max_size[0] / width, max_size[1] / height)
        new_size = (int(width * ratio), int(height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    
    # Save to bytes
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=85)
    output.seek(0)
    return output

def upload_image(image_file, folder='spacer'):
    """Upload image to Cloudinary with resizing."""
    try:
        configure_cloudinary()
        
        # Resize image
        resized_image = resize_image(image_file)
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            resized_image,
            folder=folder,
            resource_type='image',
            transformation=[
                {'quality': 'auto'},
                {'fetch_format': 'auto'}
            ]
        )
        
        return result['secure_url']
    except Exception as e:
        current_app.logger.error(f"Failed to upload image to Cloudinary: {str(e)}")
        raise

def delete_image(public_id):
    """Delete image from Cloudinary."""
    try:
        configure_cloudinary()
        result = cloudinary.uploader.destroy(public_id)
        return result['result'] == 'ok'
    except Exception as e:
        current_app.logger.error(f"Failed to delete image from Cloudinary: {str(e)}")
        return False 